"""Unit tests for API-tier authentication events and configuration health.

The event tests are security tests: an auth event carrying a token or an
email address puts credentials and PII into a log aggregator, where
retention means they stay there.

The health tests cover the misconfigurations that are invisible until a
request arrives — most importantly a *private* key configured on the API,
which would make it capable of minting tokens it accepts.
"""

import json
import logging
from uuid import uuid4

import pytest

from signora_platform.auth import AuthEvent, check_auth_health, emit_auth_event
from signora_platform.observability import JsonFormatter
from signora_platform.settings import Settings
from signora_platform.tests.keys import generate_key_pair

_DB_URL = "postgresql+asyncpg://u:p@localhost:5432/db"


def _settings(public_key: str, *, issuer: str = "iss", audience: str = "aud") -> Settings:
    return Settings(
        environment="test",
        database_url=_DB_URL,
        jwt_public_key=public_key,
        jwt_issuer=issuer,
        jwt_audience=audience,
    )


class TestAuthEvents:
    def test_emits_a_structured_event(self, caplog: pytest.LogCaptureFixture) -> None:
        user_id, workspace_id = uuid4(), uuid4()

        with caplog.at_level(logging.INFO, logger="signora.auth"):
            emit_auth_event(AuthEvent.WORKSPACE_SWITCH, user_id=user_id, workspace_id=workspace_id)

        record = caplog.records[0]
        assert record.auth_event == "AUTH_WORKSPACE_SWITCH"  # type: ignore[attr-defined]
        assert record.auth_user_id == str(user_id)  # type: ignore[attr-defined]
        assert record.auth_workspace_id == str(workspace_id)  # type: ignore[attr-defined]

    def test_derives_failure_outcome_from_the_event(self, caplog: pytest.LogCaptureFixture) -> None:
        """Outcome is derived, not passed in, so a failure cannot be recorded
        as a success by a mistaken argument."""
        with caplog.at_level(logging.WARNING, logger="signora.auth"):
            emit_auth_event(AuthEvent.TOKEN_REJECTED, reason="ExpiredTokenError")

        record = caplog.records[0]
        assert record.outcome == "failure"  # type: ignore[attr-defined]
        assert record.levelname == "WARNING"

    def test_success_events_are_info_level(self, caplog: pytest.LogCaptureFixture) -> None:
        with caplog.at_level(logging.INFO, logger="signora.auth"):
            emit_auth_event(AuthEvent.TOKEN_ACCEPTED, user_id=uuid4())

        assert caplog.records[0].outcome == "success"  # type: ignore[attr-defined]
        assert caplog.records[0].levelname == "INFO"

    def test_omits_fields_that_were_not_supplied(self, caplog: pytest.LogCaptureFixture) -> None:
        with caplog.at_level(logging.INFO, logger="signora.auth"):
            emit_auth_event(AuthEvent.TOKEN_ACCEPTED)

        assert not hasattr(caplog.records[0], "auth_user_id")

    def test_token_id_is_carried_but_no_token_ever_is(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        """jti is an opaque identifier, not a credential — it is what makes a
        token traceable to a future revocation decision."""
        with caplog.at_level(logging.INFO, logger="signora.auth"):
            emit_auth_event(AuthEvent.TOKEN_ACCEPTED, token_id="tok_abc", session_id="sess_1")

        record = caplog.records[0]
        assert record.auth_token_id == "tok_abc"  # type: ignore[attr-defined]
        assert record.auth_session_id == "sess_1"  # type: ignore[attr-defined]

    def test_a_jwt_in_a_reason_is_redacted_by_the_formatter(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Defence in depth: the emitter accepts only coarse reasons, and the
        formatter redacts regardless."""
        jwt = "eyJhbGciOiJSUzI1NiJ9.eyJzdWIiOiJhIn0.sig"

        with caplog.at_level(logging.WARNING, logger="signora.auth"):
            emit_auth_event(AuthEvent.TOKEN_REJECTED, reason=f"bad token {jwt}")

        rendered = JsonFormatter().format(caplog.records[0])
        assert jwt not in rendered
        assert "[REDACTED]" in rendered

    def test_rendered_event_is_valid_json_with_the_shared_shape(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        with caplog.at_level(logging.INFO, logger="signora.auth"):
            emit_auth_event(AuthEvent.TOKEN_ACCEPTED, user_id=uuid4())

        payload = json.loads(JsonFormatter().format(caplog.records[0]))
        assert payload["auth_event"] == "AUTH_TOKEN_ACCEPTED"
        assert payload["tier"] == "api"
        assert payload["outcome"] == "success"


class TestAuthHealth:
    def test_valid_configuration_is_healthy(self) -> None:
        report = check_auth_health(_settings(generate_key_pair().public_pem))

        assert report.status == "ok"
        assert report.detail is None

    def test_a_private_key_configured_on_the_api_is_unavailable(self) -> None:
        """The most serious misconfiguration this tier can have: it would make
        the API able to mint tokens it accepts, defeating the entire reason
        ADR-0026 chose asymmetric signing."""
        report = check_auth_health(_settings(generate_key_pair().private_pem))

        assert report.status == "unavailable"
        assert report.public_key == "unavailable"
        assert report.detail is not None
        assert "PRIVATE key" in report.detail

    @pytest.mark.parametrize("bad_key", ["", "   ", "not-a-pem", "ssh-rsa AAAAB3Nz"])
    def test_malformed_public_keys_are_unavailable(self, bad_key: str) -> None:
        report = check_auth_health(_settings(bad_key))

        assert report.status == "unavailable"
        assert report.public_key == "unavailable"

    @pytest.mark.parametrize(("issuer", "audience"), [("", "aud"), ("iss", ""), ("", "")])
    def test_missing_issuer_or_audience_is_unavailable(self, issuer: str, audience: str) -> None:
        report = check_auth_health(
            _settings(generate_key_pair().public_pem, issuer=issuer, audience=audience)
        )

        assert report.status == "unavailable"
        assert report.jwt_configuration == "unavailable"

    def test_algorithm_pinning_is_reported_healthy(self) -> None:
        """Guards against a future change widening the allowed-algorithm
        list, which would reopen alg:none and algorithm-confusion attacks."""
        report = check_auth_health(_settings(generate_key_pair().public_pem))

        assert report.algorithm_pinning == "ok"


class TestSentryScrubbing:
    """Sentry receives the exception detail the API withholds from callers,
    so it is the one place a secret is most likely to escape."""

    def test_redacts_secrets_before_an_event_leaves_the_process(self) -> None:
        from signora_platform.observability.errors import _scrub_event

        jwt = "eyJhbGciOiJSUzI1NiJ9.eyJzdWIiOiJhIn0.sig"
        event = {
            "message": f"failed with {jwt}",
            "extra": {"api_key": "leaked", "workspace_id": "ws-1"},
        }

        scrubbed = _scrub_event(event, {})

        assert jwt not in json.dumps(scrubbed)
        assert scrubbed["extra"]["api_key"] == "[REDACTED]"
        assert scrubbed["extra"]["workspace_id"] == "ws-1"

    def test_attaches_correlation_context_as_tags(self) -> None:
        """The correlation id is what turns a support conversation quoting an
        error into a specific captured exception."""
        from signora_platform.observability import logging_context
        from signora_platform.observability.errors import _scrub_event

        correlation_id, workspace_id = uuid4(), uuid4()

        with logging_context(correlation_id=correlation_id, workspace_id=workspace_id):
            scrubbed = _scrub_event({"message": "boom"}, {})

        assert scrubbed["tags"]["correlation_id"] == str(correlation_id)
        assert scrubbed["tags"]["workspace_id"] == str(workspace_id)

    def test_leaves_an_event_untagged_when_there_is_no_context(self) -> None:
        from signora_platform.observability.errors import _scrub_event

        assert "tags" not in _scrub_event({"message": "boom"}, {})
