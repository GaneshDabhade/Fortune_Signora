"""Grants, and resolving a connection into an execution context."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import pytest

from modules.integrations.application.ports import SecretNotFound
from modules.integrations.application.resolve import (
    ConnectionUnusable,
    CredentialUnreadable,
    ExecutionContext,
    ResolveExecutionContext,
)
from modules.integrations.domain.connection import ConnectedAccount, ConnectionState
from modules.integrations.domain.grant import (
    Credential,
    GrantExpired,
    GrantRevoked,
    IntegrationGrant,
)

NOW = datetime(2026, 8, 2, 12, 0, tzinfo=UTC)
WORKSPACE = uuid4()
ACTOR = uuid4()


def _account(state: ConnectionState = ConnectionState.VALIDATED, **kw: object) -> ConnectedAccount:
    defaults: dict[str, object] = {
        "id": uuid4(),
        "workspace_id": WORKSPACE,
        "integration": "salesforce",
        "external_account_id": "00D000000000000",
        "endpoint": "https://acme.my.salesforce.com",
        "label": "Acme production",
        "state": state,
        "connected_at": NOW,
        "actor_id": ACTOR,
    }
    defaults.update(kw)
    return ConnectedAccount(**defaults)  # type: ignore[arg-type]


def _grant(account: ConnectedAccount, **kw: object) -> IntegrationGrant:
    defaults: dict[str, object] = {
        "id": uuid4(),
        "workspace_id": account.workspace_id,
        "connected_account_id": account.id,
        "secret_ref": "vault://grants/1",
        "scopes": ("refresh_token", "api"),
        "expires_at": None,
        "refreshable": True,
        "revoked_at": None,
        "actor_id": ACTOR,
    }
    defaults.update(kw)
    return IntegrationGrant(**defaults)  # type: ignore[arg-type]


class FakeAccounts:
    def __init__(self, account: ConnectedAccount | None) -> None:
        self._account = account

    async def get(self, workspace_id: UUID, account_id: UUID) -> ConnectedAccount | None:
        if self._account is None or self._account.workspace_id != workspace_id:
            return None
        return self._account if self._account.id == account_id else None

    async def list_for_workspace(self, workspace_id: UUID) -> list[ConnectedAccount]:
        return [self._account] if self._account else []

    async def save(self, account: ConnectedAccount) -> None:
        self._account = account


class FakeGrants:
    def __init__(self, grant: IntegrationGrant | None) -> None:
        self._grant = grant

    async def current_for(
        self, workspace_id: UUID, connected_account_id: UUID
    ) -> IntegrationGrant | None:
        return self._grant

    async def save(self, grant: IntegrationGrant) -> None:
        self._grant = grant


class FakeSecrets:
    def __init__(self, *, holds: bool = True) -> None:
        self._holds = holds

    async def resolve(self, secret_ref: str) -> Credential:
        if not self._holds:
            raise SecretNotFound(secret_ref)
        return Credential(kind="bearer", material=b"s3cret")


def _resolver(
    account: ConnectedAccount | None,
    grant: IntegrationGrant | None,
    *,
    secrets_hold: bool = True,
) -> ResolveExecutionContext:
    return ResolveExecutionContext(
        FakeAccounts(account), FakeGrants(grant), FakeSecrets(holds=secrets_hold)
    )


class TestCredentialsDoNotLeak:
    def test_a_credential_will_not_render_itself(self) -> None:
        """A credential in a traceback, a log line or a pytest diff is a
        credential in a log aggregator."""
        credential = Credential(kind="bearer", material=b"s3cret")
        assert "s3cret" not in repr(credential)
        assert "s3cret" not in str(credential)
        assert "redacted" in repr(credential)

    def test_an_execution_context_will_not_render_its_credential(self) -> None:
        context = ExecutionContext(
            workspace_id=WORKSPACE,
            connected_account_id=uuid4(),
            integration="salesforce",
            endpoint=None,
            scopes=(),
            credential=Credential(kind="bearer", material=b"s3cret"),
        )
        assert "s3cret" not in repr(context)

    def test_a_grant_carries_a_reference_and_never_material(self) -> None:
        """The property that keeps tokens out of a replicated, backed-up table."""
        grant = _grant(_account())
        assert not hasattr(grant, "token")
        assert grant.secret_ref.startswith("vault://")

    def test_a_grant_must_reference_something(self) -> None:
        with pytest.raises(ValueError, match="secret material"):
            _grant(_account(), secret_ref="")


class TestGrantLifecycle:
    def test_a_grant_without_an_expiry_never_expires(self) -> None:
        """An API key is a grant that does not expire — a value, not a special
        case, and this is what stops OAuth's shape becoming the type."""
        assert _grant(_account(), expires_at=None, refreshable=False).is_expired(at=NOW) is False

    def test_an_elapsed_grant_is_expired(self) -> None:
        grant = _grant(_account(), expires_at=NOW - timedelta(seconds=1))
        assert grant.is_expired(at=NOW) is True

    def test_expiry_and_revocation_raise_differently(self) -> None:
        """**Two exceptions rather than one boolean**, because a caller does
        different things: an expired refreshable grant is refreshed, and a
        revoked one needs the customer back."""
        with pytest.raises(GrantExpired):
            _grant(_account(), expires_at=NOW - timedelta(days=1)).check_usable(at=NOW)
        with pytest.raises(GrantRevoked):
            _grant(_account(), revoked_at=NOW).check_usable(at=NOW)

    def test_revocation_outranks_expiry(self) -> None:
        """A revoked grant that also expired must not look refreshable."""
        grant = _grant(_account(), expires_at=NOW - timedelta(days=1), revoked_at=NOW)
        with pytest.raises(GrantRevoked):
            grant.check_usable(at=NOW)

    def test_revocation_is_idempotent(self) -> None:
        """A second report of one withdrawal must not move the timestamp — it
        is when permission ended, not when Signora last noticed."""
        first = _grant(_account()).revoke(at=NOW, by=ACTOR)
        assert first.revoke(at=NOW + timedelta(days=1), by=ACTOR).revoked_at == NOW


class TestResolution:
    @pytest.mark.asyncio
    async def test_a_usable_connection_resolves(self) -> None:
        account = _account()
        context = await _resolver(account, _grant(account)).execute(
            WORKSPACE, account.id, at=NOW
        )
        assert context.integration == "salesforce"
        assert context.endpoint == "https://acme.my.salesforce.com"
        assert context.scopes == ("refresh_token", "api")
        assert context.credential.material == b"s3cret"

    @pytest.mark.asyncio
    async def test_the_context_carries_no_hint_of_how_it_was_acquired(self) -> None:
        """**The rule that must survive every future mechanism.** An adapter
        able to ask *"was this OAuth?"* is vendor-shaped, and the abstraction
        would not survive mTLS."""
        account = _account()
        context = await _resolver(account, _grant(account)).execute(
            WORKSPACE, account.id, at=NOW
        )
        fields = set(ExecutionContext.__dataclass_fields__)
        assert not fields & {"mechanism", "auth_type", "oauth", "grant_type", "flow"}
        assert context.credential.kind == "bearer"

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "state",
        [ConnectionState.REVOKED, ConnectionState.EXPIRED, ConnectionState.DISCONNECTED],
    )
    async def test_an_unusable_connection_refuses_and_says_which(
        self, state: ConnectionState
    ) -> None:
        account = _account(state)
        with pytest.raises(ConnectionUnusable) as raised:
            await _resolver(account, _grant(account)).execute(WORKSPACE, account.id, at=NOW)
        assert raised.value.state is state

    @pytest.mark.asyncio
    async def test_another_workspace_gets_nothing(self) -> None:
        """Belt and braces beside RLS, and it reads as *no such connection*
        rather than *not yours* — the 404-not-403 rule."""
        account = _account()
        with pytest.raises(ConnectionUnusable, match="no such connection"):
            await _resolver(account, _grant(account)).execute(uuid4(), account.id, at=NOW)

    @pytest.mark.asyncio
    async def test_a_connection_with_no_grant_refuses(self) -> None:
        account = _account()
        with pytest.raises(ConnectionUnusable, match="no grant"):
            await _resolver(account, None).execute(WORKSPACE, account.id, at=NOW)

    @pytest.mark.asyncio
    async def test_a_revoked_grant_refuses_even_on_a_usable_connection(self) -> None:
        """The two lifecycles are independent, so both are checked."""
        account = _account(ConnectionState.VALIDATED)
        with pytest.raises(GrantRevoked):
            await _resolver(account, _grant(account, revoked_at=NOW)).execute(
                WORKSPACE, account.id, at=NOW
            )

    @pytest.mark.asyncio
    async def test_a_purged_secret_surfaces_rather_than_resolving_empty(self) -> None:
        """A grant row can outlive its material when a purge runs at
        offboarding. Resolving to nothing would call a vendor unauthenticated.

        **Surfaced as `CredentialUnreadable`, not as the storage failure.** A
        rotated key and a purged secret are the same fact above the adapter —
        this connection has to be made again — and a customer can act on that.
        """
        account = _account()
        with pytest.raises(CredentialUnreadable):
            await _resolver(account, _grant(account), secrets_hold=False).execute(
                WORKSPACE, account.id, at=NOW
            )
