"""Asking a vendor to renew a grant — RFC 6749 §6.

**Against `httpx.MockTransport`, and no developer application is needed.** §6
is the same standard as the authorization-code exchange with a different
`grant_type`, so what a live handshake would confirm is one URL per vendor and
nothing about the behaviour below.

**Where the client credentials come from is an interface**, so these exercise
the adapter against a substituted store — and the last class exercises the real
one, which reads the module's own typed configuration.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import httpx
import pytest

from modules.integrations.application.refresh import ClientCredentials
from modules.integrations.infrastructure.refreshing import (
    HttpTokenRefresher,
    SettingsClientCredentials,
)
from modules.integrations.infrastructure.settings import (
    ClientCredentialPair,
    IntegrationSettings,
)

NOW = datetime(2026, 8, 4, 12, tzinfo=UTC)
CREDENTIALS = ClientCredentials(client_id="the-client", client_secret="the-secret")


class Configured:
    """A store that answers for HubSpot and nothing else."""

    def for_integration(self, integration: str) -> ClientCredentials | None:
        return CREDENTIALS if integration == "hubspot" else None


def _refresher(
    handler: httpx.MockTransport, *, credentials: object = None
) -> HttpTokenRefresher:
    return HttpTokenRefresher(
        credentials or Configured(),  # type: ignore[arg-type]
        transport=handler,
        now=lambda: NOW,
    )


def _records(
    body: object, status: int = 200
) -> tuple[httpx.MockTransport, list[httpx.Request]]:
    seen: list[httpx.Request] = []

    def handle(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        if isinstance(body, str):
            return httpx.Response(status, text=body)
        return httpx.Response(status, json=body)

    return httpx.MockTransport(handle), seen


class TestRenewingAtTheVendor:
    async def test_it_sends_what_rfc_6749_section_6_requires(self) -> None:
        transport, seen = _records({"access_token": "new-access"})

        await _refresher(transport).renew("hubspot", "the-refresh-token")

        sent = dict(pair.split("=") for pair in seen[0].content.decode().split("&"))
        assert str(seen[0].url) == "https://api.hubapi.com/oauth/v1/token"
        assert sent == {
            "grant_type": "refresh_token",
            "refresh_token": "the-refresh-token",
            "client_id": "the-client",
            "client_secret": "the-secret",
        }

    async def test_it_returns_the_new_material(self) -> None:
        transport, _ = _records(
            {
                "access_token": "new-access",
                "refresh_token": "new-refresh",
                "expires_in": 1800,
            }
        )

        renewed = await _refresher(transport).renew("hubspot", "old")

        assert renewed is not None
        assert renewed.access_token == "new-access"
        assert renewed.refresh_token == "new-refresh"
        assert renewed.expires_at == NOW + timedelta(minutes=30)

    async def test_a_vendor_that_issues_no_new_refresh_token_reports_none(self) -> None:
        """**Google's behaviour**, and `RefreshGrant` keeps the old one.

        An empty string here would look like a new token and would replace a
        working one with nothing.
        """
        transport, _ = _records({"access_token": "new-access", "refresh_token": ""})

        renewed = await _refresher(transport).renew("hubspot", "old")

        assert renewed is not None
        assert renewed.refresh_token is None

    async def test_an_expiry_that_has_already_passed_is_not_an_expiry(self) -> None:
        """`expires_in: 0` is a vendor saying nothing useful. Recording it
        would mark a brand-new grant as already lapsed."""
        transport, _ = _records({"access_token": "new-access", "expires_in": 0})

        renewed = await _refresher(transport).renew("hubspot", "old")

        assert renewed is not None
        assert renewed.expires_at is None

    async def test_material_without_an_expiry_does_not_invent_one(self) -> None:
        transport, _ = _records({"access_token": "new-access"})

        renewed = await _refresher(transport).renew("hubspot", "old")

        assert renewed is not None
        assert renewed.expires_at is None


class TestWhenItCannotRenew:
    async def test_a_refusal_leaves_the_grant_alone(self) -> None:
        """**The commonest 400 is `invalid_grant`** — the customer withdrew
        Signora at the vendor. Reported as *could not renew*, and the outcome a
        caller sees is `RefreshGrant`'s to name."""
        transport, _ = _records({"error": "invalid_grant"}, status=400)

        assert await _refresher(transport).renew("hubspot", "old") is None

    async def test_an_unreachable_vendor_is_reported_rather_than_raised(self) -> None:
        def explode(request: httpx.Request) -> httpx.Response:
            raise httpx.ConnectTimeout("nope", request=request)

        assert await _refresher(httpx.MockTransport(explode)).renew("hubspot", "old") is None

    async def test_a_maintenance_page_where_json_was_expected(self) -> None:
        transport, _ = _records("<html>down</html>")

        assert await _refresher(transport).renew("hubspot", "old") is None

    async def test_a_200_carrying_no_token_keeps_the_old_material(self) -> None:
        """**Refusing is what keeps the connection alive.** The old material
        still works until it expires; storing an empty token ends it now."""
        transport, _ = _records({"token_type": "bearer"})

        assert await _refresher(transport).renew("hubspot", "old") is None

    async def test_a_response_that_is_not_an_object_is_refused(self) -> None:
        """A JSON array where §5.1 requires an object. The vendor's contract
        broken, and the old material still works."""
        transport, _ = _records([{"access_token": "x"}])

        assert await _refresher(transport).renew("hubspot", "old") is None

    async def test_a_vendor_with_no_endpoint_is_never_called(self) -> None:
        transport, seen = _records({"access_token": "x"})

        assert await _refresher(transport).renew("slack", "old") is None
        assert seen == []

    async def test_a_vendor_with_no_client_credentials_is_never_called(self) -> None:
        """A deployment that configured nothing for this system. **A working
        state, not a fault** — and the same refusal the acquisition tier
        performs when its environment holds no client id."""
        transport, seen = _records({"access_token": "x"})

        assert await _refresher(transport).renew("google_calendar", "old") is None
        assert seen == []


class TestCredentialsComeFromTheModulesOwnConfiguration:
    def _settings(self, **pairs: ClientCredentialPair) -> IntegrationSettings:
        return IntegrationSettings(secret_key="k", client_credentials=dict(pairs))

    def test_a_configured_vendor_resolves(self) -> None:
        store = SettingsClientCredentials(
            self._settings(hubspot=ClientCredentialPair(client_id="i", client_secret="s"))
        )

        resolved = store.for_integration("hubspot")

        assert resolved == ClientCredentials(client_id="i", client_secret="s")
        assert store.any_configured() is True

    def test_an_unconfigured_vendor_resolves_to_nothing(self) -> None:
        store = SettingsClientCredentials(
            self._settings(hubspot=ClientCredentialPair(client_id="i", client_secret="s"))
        )

        assert store.for_integration("google_calendar") is None

    def test_an_empty_configuration_is_a_working_state(self) -> None:
        """**Empty by default and deliberately.** A defaulted client secret is
        a known secret that reads as configuration, so there is none — and a
        deployment that configured nothing refreshes nothing rather than
        failing per connection."""
        store = SettingsClientCredentials(self._settings())

        assert store.any_configured() is False
        assert store.for_integration("hubspot") is None

    def test_the_secret_does_not_render(self) -> None:
        """A credential in a traceback is a credential in a log aggregator."""
        rendered = repr(ClientCredentials(client_id="i", client_secret="the-secret"))

        assert "the-secret" not in rendered
        assert "redacted" in rendered

    def test_a_half_configured_vendor_is_refused_by_the_type(self) -> None:
        """**Unrepresentable rather than validated later** (§2).

        A pair missing its secret cannot be constructed, so a deployment
        mistake fails at startup with the field named rather than at the first
        renewal with a vendor's 401.
        """
        with pytest.raises(ValueError):
            IntegrationSettings(
                secret_key="k",
                client_credentials={"hubspot": {"client_id": "i"}},
            )
