"""Unit tests for structured logging and secret redaction.

The redaction tests are security tests, not formatting tests. A token
reaching a log aggregator is a credential disclosure, and log retention
means it stays disclosed.
"""

import json
import logging
from typing import Any
from uuid import uuid4

import pytest

from signora_platform.observability import (
    REDACTED,
    JsonFormatter,
    current_context,
    logging_context,
    redact,
)


def _format(
    record_kwargs: dict[str, object] | None = None, message: str = "hello"
) -> dict[str, Any]:
    record = logging.LogRecord(
        name="test", level=logging.INFO, pathname="p", lineno=1, msg=message, args=(), exc_info=None
    )
    for key, value in (record_kwargs or {}).items():
        setattr(record, key, value)
    parsed: dict[str, Any] = json.loads(JsonFormatter().format(record))
    return parsed


class TestJsonFormatting:
    def test_emits_valid_json_with_core_fields(self) -> None:
        payload = _format()

        assert payload["level"] == "INFO"
        assert payload["logger"] == "test"
        assert payload["message"] == "hello"
        assert "timestamp" in payload

    def test_includes_extra_fields(self) -> None:
        payload = _format({"provider": "apollo", "records": 42})

        assert payload["provider"] == "apollo"
        assert payload["records"] == 42

    def test_omits_context_keys_that_are_unset(self) -> None:
        """A request with no event_id should not carry a null one — nulls
        make lines noisier without adding information."""
        payload = _format()

        assert "event_id" not in payload
        assert "workspace_id" not in payload


class TestContextPropagation:
    def test_context_appears_in_log_output(self) -> None:
        correlation_id, workspace_id, user_id = uuid4(), uuid4(), uuid4()

        with logging_context(
            correlation_id=correlation_id, workspace_id=workspace_id, user_id=user_id
        ):
            payload = _format()

        assert payload["correlation_id"] == str(correlation_id)
        assert payload["workspace_id"] == str(workspace_id)
        assert payload["user_id"] == str(user_id)

    def test_context_is_restored_on_exit(self) -> None:
        """Leaked context would attribute one workspace's log lines to
        another — a correctness problem when debugging a tenant issue."""
        with logging_context(workspace_id=uuid4()):
            assert "workspace_id" in current_context()

        assert current_context() == {}

    def test_context_is_restored_even_when_the_block_raises(self) -> None:
        with pytest.raises(RuntimeError), logging_context(workspace_id=uuid4()):
            raise RuntimeError("boom")

        assert current_context() == {}

    def test_nested_contexts_restore_the_outer_value(self) -> None:
        outer, inner = uuid4(), uuid4()

        with logging_context(workspace_id=outer):
            with logging_context(workspace_id=inner):
                assert current_context()["workspace_id"] == str(inner)
            assert current_context()["workspace_id"] == str(outer)

    def test_event_context_is_carried_for_worker_jobs(self) -> None:
        event_id, causation_id = uuid4(), uuid4()

        with logging_context(
            event_id=event_id, causation_id=causation_id, consumer_name="timeline"
        ):
            payload = _format()

        assert payload["event_id"] == str(event_id)
        assert payload["causation_id"] == str(causation_id)
        assert payload["consumer_name"] == "timeline"


class TestSecretRedaction:
    @pytest.mark.parametrize(
        "key",
        [
            "password",
            "secret",
            "access_token",
            "Authorization",
            "api_key",
            "apiKey",
            "private_key",
            "db_credential",
            "cookie",
        ],
    )
    def test_redacts_sensitively_named_keys(self, key: str) -> None:
        assert redact({key: "s3cret"})[key] == REDACTED

    def test_redacts_nested_structures(self) -> None:
        result = redact({"outer": {"items": [{"api_key": "abc"}]}})

        assert result["outer"]["items"][0]["api_key"] == REDACTED

    def test_redacts_a_jwt_appearing_in_free_text(self) -> None:
        """Tokens reach logs most often inside an exception message or URL,
        not as a conveniently-named field."""
        jwt = "eyJhbGciOiJSUzI1NiJ9.eyJzdWIiOiIxMjMifQ.c2lnbmF0dXJl"

        result = redact(f"verification failed for {jwt} at boundary")

        assert jwt not in result
        assert REDACTED in result

    def test_redacts_bearer_header_values(self) -> None:
        result = redact("Authorization: Bearer abc123def456")

        assert "abc123def456" not in result
        assert REDACTED in result

    def test_leaves_ordinary_values_untouched(self) -> None:
        payload = {"workspace_id": "abc", "count": 3, "name": "Acme"}

        assert redact(payload) == payload

    def test_redaction_is_applied_to_formatted_log_output(self) -> None:
        """End-to-end: redaction must happen inside the formatter, not be
        left to each call site."""
        jwt = "eyJhbGciOiJIUzI1NiJ9.eyJhIjoxfQ.sig"

        payload = _format({"api_key": "leaked"}, message=f"token was {jwt}")

        assert payload["api_key"] == REDACTED
        assert jwt not in payload["message"]

    def test_exception_text_is_redacted(self) -> None:
        record = logging.LogRecord(
            name="t",
            level=logging.ERROR,
            pathname="p",
            lineno=1,
            msg="failed",
            args=(),
            exc_info=None,
        )
        try:
            raise ValueError("Bearer supersecrettoken")
        except ValueError:
            import sys

            record.exc_info = sys.exc_info()

        payload = json.loads(JsonFormatter().format(record))

        assert "supersecrettoken" not in payload["exception"]
