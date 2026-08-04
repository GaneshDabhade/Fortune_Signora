"""Withdrawing Signora's access at the vendor.

**Against `httpx.MockTransport`, and no credentials are needed for any of it.**
Revocation is a fact about a grant, which this module owns outright — nothing
here waits on how records will one day arrive
([ADR-0300](../../../docs/architecture/adr/0300-inbound-customer-systems.md)),
and nothing waits on a developer application either. What a live handshake
would add is confirmation of two URLs.

The property that matters most is the last class: **a vendor can never block a
disconnect.** Every failure below has to reach `DisconnectSystem` as *"it did
not happen"*, never as an exception that stops a customer withdrawing access.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

import httpx
import pytest

from modules.integrations.application.ports import SecretNotFound
from modules.integrations.domain.connection import ConnectedAccount, ConnectionState
from modules.integrations.domain.grant import (
    OAUTH2_KIND,
    Credential,
    IntegrationGrant,
    OAuth2Material,
)
from modules.integrations.infrastructure.revocation import HttpProviderRevoker

WORKSPACE = uuid4()
ACTOR = uuid4()
ACCOUNT_ID = uuid4()
NOW = datetime(2026, 8, 4, tzinfo=UTC)


def _account(integration: str = "hubspot") -> ConnectedAccount:
    return ConnectedAccount(
        id=ACCOUNT_ID,
        workspace_id=WORKSPACE,
        integration=integration,
        external_account_id="24601",
        endpoint=None,
        label="Acme production",
        state=ConnectionState.CONNECTED,
        connected_at=NOW,
        actor_id=ACTOR,
    )


def _grant(secret_ref: str = "integration/ref") -> IntegrationGrant:
    return IntegrationGrant(
        id=uuid4(),
        workspace_id=WORKSPACE,
        connected_account_id=ACCOUNT_ID,
        secret_ref=secret_ref,
        scopes=("crm.objects.companies.read",),
        expires_at=None,
        refreshable=True,
        revoked_at=None,
        actor_id=ACTOR,
    )


class FakeAccounts:
    def __init__(self, account: ConnectedAccount | None) -> None:
        self._account = account

    async def get(self, workspace_id: UUID, account_id: UUID) -> ConnectedAccount | None:
        if self._account is None or self._account.workspace_id != workspace_id:
            return None
        return self._account

    async def find_identity(
        self, workspace_id: UUID, integration: str, external_account_id: str
    ) -> ConnectedAccount | None:
        return None

    async def list_for_workspace(self, workspace_id: UUID) -> list[ConnectedAccount]:
        return [self._account] if self._account else []

    async def save(self, account: ConnectedAccount) -> None: ...


class FakeGrants:
    def __init__(self, grant: IntegrationGrant | None) -> None:
        self._grant = grant

    async def current_for(
        self, workspace_id: UUID, connected_account_id: UUID
    ) -> IntegrationGrant | None:
        return self._grant

    async def save(self, grant: IntegrationGrant) -> None: ...


class FakeSecrets:
    """Resolves material, or raises the way the real store does."""

    def __init__(self, credential: Credential | None) -> None:
        self._credential = credential

    async def resolve(self, secret_ref: str) -> Credential:
        if self._credential is None:
            raise SecretNotFound(secret_ref)
        return self._credential


def _oauth2(access: str = "at", refresh: str | None = "rt") -> Credential:
    return OAuth2Material(access_token=access, refresh_token=refresh).as_credential()


#: **A sentinel, because `None` is a value these tests need to pass.**
#: *"No grant at all"* and *"the default grant"* are different cases and one of
#: them is a test; defaulting on `None` silently merged them, and both tests
#: passed while asserting nothing.
_DEFAULT: Any = object()


def _revoker(
    handler: httpx.MockTransport,
    *,
    account: Any = _DEFAULT,
    grant: Any = _DEFAULT,
    credential: Any = _DEFAULT,
) -> HttpProviderRevoker:
    return HttpProviderRevoker(
        FakeAccounts(_account() if account is _DEFAULT else account),
        FakeGrants(_grant() if grant is _DEFAULT else grant),
        FakeSecrets(_oauth2() if credential is _DEFAULT else credential),
        WORKSPACE,
        transport=handler,
    )


def _records(status: int = 204) -> tuple[httpx.MockTransport, list[httpx.Request]]:
    seen: list[httpx.Request] = []

    def handle(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return httpx.Response(status)

    return httpx.MockTransport(handle), seen


class TestTellingTheVendor:
    async def test_it_calls_the_endpoint_the_table_names(self) -> None:
        transport, seen = _records()

        assert await _revoker(transport).revoke(ACCOUNT_ID) is True
        assert seen[0].method == "DELETE"
        assert str(seen[0].url) == "https://api.hubapi.com/oauth/v1/refresh-tokens/rt"

    async def test_it_sends_the_token_the_vendor_asks_for(self) -> None:
        """**HubSpot revokes a refresh token and the access token will not do.**

        Sending the wrong one returns a cheerful success that revokes nothing —
        the product would report the credential withdrawn while it still
        worked, which is the worst available outcome.
        """
        transport, seen = _records()
        await _revoker(
            transport, credential=_oauth2(access="the-access", refresh="the-refresh")
        ).revoke(ACCOUNT_ID)

        assert "the-refresh" in str(seen[0].url)
        assert "the-access" not in str(seen[0].url)

    async def test_a_token_cannot_escape_its_own_position_in_the_url(self) -> None:
        """A `/` or a `&` in material must not become a path or a parameter."""
        transport, seen = _records()
        await _revoker(transport, credential=_oauth2(refresh="a/b&c=d")).revoke(ACCOUNT_ID)

        assert str(seen[0].url).endswith("/refresh-tokens/a%2Fb%26c%3Dd")

    async def test_a_grant_already_gone_counts_as_revoked(self) -> None:
        """**404 is the outcome the customer wanted.**

        Reporting failure would send somebody to tidy up something already
        tidy, which is the same class of untruth as reporting a revocation
        that did not happen — just the cheaper direction.
        """
        transport, _ = _records(status=404)
        assert await _revoker(transport).revoke(ACCOUNT_ID) is True


class TestAVendorCanNeverBlockADisconnect:
    """Every one of these has to read as *it did not happen*, never as a raise.

    `DisconnectSystem` catches broadly, so a raise here would still not stop a
    customer — but it would arrive as a discarded traceback rather than a log
    line naming the reason, and the reason is the whole diagnosis.
    """

    async def test_a_refusal_is_reported_rather_than_raised(self) -> None:
        transport, _ = _records(status=400)
        assert await _revoker(transport).revoke(ACCOUNT_ID) is False

    async def test_an_unreachable_vendor_is_reported_rather_than_raised(self) -> None:
        def explode(request: httpx.Request) -> httpx.Response:
            raise httpx.ConnectTimeout("nope", request=request)

        assert await _revoker(httpx.MockTransport(explode)).revoke(ACCOUNT_ID) is False

    async def test_a_system_with_no_revocation_endpoint_reports_failure(self) -> None:
        """**Honest rather than incomplete**, and exactly what `NoRevoker` did.

        A system Signora can connect but not revoke at is a missing adapter,
        and the dialog already tells the customer to tidy up at the vendor.
        """
        transport, seen = _records()
        revoked = await _revoker(transport, account=_account("slack")).revoke(ACCOUNT_ID)

        assert revoked is False
        assert seen == []

    async def test_a_connection_in_another_workspace_is_not_revoked(self) -> None:
        """**Scoped, and not relying on RLS to be the only thing that refuses.**

        The workspace is passed in rather than inferred, so an adapter cannot
        reach a connection it was never given — defence in depth, which §8
        declines to skip even where RLS would also refuse.
        """
        transport, seen = _records()
        other = ConnectedAccount(
            id=ACCOUNT_ID,
            workspace_id=uuid4(),
            integration="hubspot",
            external_account_id="24601",
            endpoint=None,
            label="Someone else's",
            state=ConnectionState.CONNECTED,
            connected_at=NOW,
            actor_id=ACTOR,
        )

        assert await _revoker(transport, account=other).revoke(ACCOUNT_ID) is False
        assert seen == []

    async def test_a_grant_whose_material_is_gone_reports_failure(self) -> None:
        """There is nothing to revoke with, and the disconnect proceeds."""
        transport, seen = _records()
        revoked = await _revoker(transport, credential=None).revoke(ACCOUNT_ID)

        assert revoked is False
        assert seen == []

    async def test_a_connection_with_no_grant_reports_failure(self) -> None:
        transport, seen = _records()
        assert await _revoker(transport, grant=None).revoke(ACCOUNT_ID) is False
        assert seen == []

    @pytest.mark.parametrize(
        "credential",
        [
            Credential(kind="bearer", material=b"a-plain-token"),
            Credential(kind=OAUTH2_KIND, material=b"not json at all"),
            Credential(kind=OAUTH2_KIND, material=b'["a", "list"]'),
            Credential(kind=OAUTH2_KIND, material=b'{"access_token": "at"}'),
            Credential(kind=OAUTH2_KIND, material=b'{"refresh_token": null}'),
            Credential(kind=OAUTH2_KIND, material=b'{"refresh_token": ""}'),
        ],
        ids=[
            "a kind this revoker was not built for",
            "material that is not JSON",
            "JSON that is not an object",
            "an object with no refresh token",
            "an explicit null",
            "an empty string",
        ],
    )
    async def test_material_it_cannot_read_reports_failure(
        self, credential: Credential
    ) -> None:
        """**Guessing would be worse than admitting it.**

        Every one of these is a credential this adapter was not built for, and
        sending part of it to a vendor on the chance it works is how a
        revocation reports success it never achieved.
        """
        transport, seen = _records()
        assert await _revoker(transport, credential=credential).revoke(ACCOUNT_ID) is False
        assert seen == []
