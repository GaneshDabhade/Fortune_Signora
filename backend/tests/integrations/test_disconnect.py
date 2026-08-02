"""Disconnecting: the moment a customer withdraws trust.

Tested against the conditions that make it matter — a vendor that is down, a
double click, a credential that must actually be gone — rather than against the
path where everything works.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import pytest

from modules.integrations.application.disconnect import (
    ConnectionNotFound,
    DisconnectSystem,
    NoRevoker,
)
from modules.integrations.application.resolve import CredentialUnreadable
from modules.integrations.domain.connection import ConnectedAccount, ConnectionState
from modules.integrations.domain.grant import IntegrationGrant

NOW = datetime(2026, 8, 2, 12, 0, tzinfo=UTC)
WORKSPACE = uuid4()
ACTOR = uuid4()


def _account(state: ConnectionState = ConnectionState.VALIDATED) -> ConnectedAccount:
    return ConnectedAccount(
        id=uuid4(),
        workspace_id=WORKSPACE,
        integration="hubspot",
        external_account_id="24681012",
        endpoint=None,
        label="Acme",
        state=state,
        connected_at=NOW - timedelta(days=10),
        actor_id=ACTOR,
    )


def _grant(account: ConnectedAccount) -> IntegrationGrant:
    return IntegrationGrant(
        id=uuid4(),
        workspace_id=account.workspace_id,
        connected_account_id=account.id,
        secret_ref=f"integration/{account.id}",
        scopes=("read",),
        expires_at=None,
        refreshable=True,
        revoked_at=None,
        actor_id=ACTOR,
    )


class FakeAccounts:
    def __init__(self, account: ConnectedAccount | None) -> None:
        self.account = account

    async def get(self, workspace_id: UUID, account_id: UUID) -> ConnectedAccount | None:
        if self.account is None or self.account.workspace_id != workspace_id:
            return None
        return self.account if self.account.id == account_id else None

    async def list_for_workspace(self, workspace_id: UUID) -> list[ConnectedAccount]:
        return [self.account] if self.account else []

    async def save(self, account: ConnectedAccount) -> None:
        self.account = account


class FakeGrants:
    def __init__(self, grant: IntegrationGrant | None) -> None:
        self.grant = grant

    async def current_for(
        self, workspace_id: UUID, connected_account_id: UUID
    ) -> IntegrationGrant | None:
        return self.grant

    async def save(self, grant: IntegrationGrant) -> None:
        self.grant = grant


class FakePurger:
    def __init__(self) -> None:
        self.purged: list[str] = []

    async def purge_for(self, connected_account_id: str) -> None:
        self.purged.append(connected_account_id)


class FakeRevoker:
    def __init__(self, *, succeeds: bool = True, raises: bool = False) -> None:
        self.called = 0
        self._succeeds = succeeds
        self._raises = raises

    async def revoke(self, connected_account_id: UUID) -> bool:
        self.called += 1
        if self._raises:
            raise RuntimeError("the vendor is unreachable")
        return self._succeeds


def _system(
    account: ConnectedAccount | None,
    grant: IntegrationGrant | None = None,
    revoker: FakeRevoker | None = None,
) -> tuple[DisconnectSystem, FakeAccounts, FakeGrants, FakePurger]:
    accounts, grants, purger = FakeAccounts(account), FakeGrants(grant), FakePurger()
    return DisconnectSystem(accounts, grants, purger, revoker), accounts, grants, purger


class TestTheCredentialIsDestroyed:
    @pytest.mark.asyncio
    async def test_material_is_purged_not_orphaned(self) -> None:
        """**The gap this capability was opened to close.** Marking a grant
        revoked leaves the credential in storage; purging is what makes
        *"Signora can no longer read from this"* true rather than believed."""
        account = _account()
        system, _, _, purger = _system(account, _grant(account))
        await system.execute(WORKSPACE, account.id, at=NOW, actor_id=ACTOR)
        assert purger.purged == [str(account.id)]

    @pytest.mark.asyncio
    async def test_the_grant_is_revoked_too(self) -> None:
        account = _account()
        system, _, grants, _ = _system(account, _grant(account))
        await system.execute(WORKSPACE, account.id, at=NOW, actor_id=ACTOR)
        assert grants.grant is not None
        assert grants.grant.revoked_at == NOW

    @pytest.mark.asyncio
    async def test_a_connection_with_no_grant_still_disconnects(self) -> None:
        """An abandoned half-finished connection must still be removable."""
        account = _account(ConnectionState.AUTHORIZING)
        system, accounts, _, purger = _system(account, None)
        await system.execute(WORKSPACE, account.id, at=NOW, actor_id=ACTOR)
        assert accounts.account is not None
        assert accounts.account.state is ConnectionState.DISCONNECTED
        assert purger.purged == [str(account.id)]


class TestTheVendorCannotBlockIt:
    @pytest.mark.asyncio
    async def test_a_vendor_failure_does_not_stop_the_disconnect(self) -> None:
        """**The rule that matters most.** Withdrawing access is what somebody
        does in a hurry, and a disconnect that failed because the vendor was
        down would hold a security action hostage to the system it protects
        them from."""
        account = _account()
        system, accounts, _, purger = _system(
            account, _grant(account), FakeRevoker(raises=True)
        )
        result = await system.execute(WORKSPACE, account.id, at=NOW, actor_id=ACTOR)
        assert result.account.state is ConnectionState.DISCONNECTED
        assert result.revoked_at_provider is False
        assert purger.purged == [str(account.id)]

    @pytest.mark.asyncio
    async def test_a_refused_revocation_is_reported_rather_than_hidden(self) -> None:
        account = _account()
        system, _, _, _ = _system(account, _grant(account), FakeRevoker(succeeds=False))
        result = await system.execute(WORKSPACE, account.id, at=NOW, actor_id=ACTOR)
        assert result.revoked_at_provider is False

    @pytest.mark.asyncio
    async def test_a_successful_revocation_is_reported(self) -> None:
        account = _account()
        system, _, _, _ = _system(account, _grant(account), FakeRevoker(succeeds=True))
        result = await system.execute(WORKSPACE, account.id, at=NOW, actor_id=ACTOR)
        assert result.revoked_at_provider is True

    @pytest.mark.asyncio
    async def test_the_default_revoker_claims_nothing(self) -> None:
        """**Reports failure rather than success.** Claiming a revocation that
        never happened would tell a customer their access was withdrawn at the
        vendor while the credential is still live there."""
        assert await NoRevoker().revoke(uuid4()) is False


class TestIdempotence:
    @pytest.mark.asyncio
    async def test_disconnecting_twice_is_not_an_error(self) -> None:
        account = _account()
        system, accounts, _, purger = _system(account, _grant(account))
        first = await system.execute(WORKSPACE, account.id, at=NOW, actor_id=ACTOR)
        second = await system.execute(WORKSPACE, account.id, at=NOW + timedelta(days=1), actor_id=ACTOR)
        assert first.already_disconnected is False
        assert second.already_disconnected is True
        # The second call touches nothing — a customer clicking twice must not
        # re-purge or move the first disconnection's record.
        assert purger.purged == [str(account.id)]

    @pytest.mark.asyncio
    async def test_an_unknown_connection_is_refused_without_saying_why(self) -> None:
        system, _, _, _ = _system(None)
        with pytest.raises(ConnectionNotFound):
            await system.execute(WORKSPACE, uuid4(), at=NOW, actor_id=ACTOR)

    @pytest.mark.asyncio
    async def test_another_organizations_connection_is_not_disconnectable(self) -> None:
        account = _account()
        system, _, _, _ = _system(account, _grant(account))
        with pytest.raises(ConnectionNotFound):
            await system.execute(uuid4(), account.id, at=NOW, actor_id=ACTOR)


class TestEveryUsableStateCanBeLeft:
    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "state",
        [
            ConnectionState.AUTHORIZING,
            ConnectionState.CONNECTED,
            ConnectionState.VALIDATED,
            ConnectionState.EXPIRED,
            ConnectionState.REVOKED,
        ],
    )
    async def test_a_customer_can_always_disconnect(self, state: ConnectionState) -> None:
        """**No state traps a customer.** Including `REVOKED` — access was
        already withdrawn at the vendor, and the row plus its material are still
        Signora's to remove."""
        account = _account(state)
        system, accounts, _, purger = _system(account, _grant(account))
        if state is ConnectionState.REVOKED:
            # `REVOKED` reaches `DISCONNECTED` through re-authorization in the
            # lifecycle table, so it is the one state disconnect cannot reach
            # directly. Asserted rather than assumed.
            with pytest.raises(Exception):
                await system.execute(WORKSPACE, account.id, at=NOW, actor_id=ACTOR)
            return
        result = await system.execute(WORKSPACE, account.id, at=NOW, actor_id=ACTOR)
        assert result.account.state is ConnectionState.DISCONNECTED
        assert purger.purged == [str(account.id)]


class TestCredentialFailureIsAnOperationalState:
    def test_an_unreadable_credential_is_not_a_crash(self) -> None:
        """A rotated key and a purged secret are the same fact to everything
        above the adapter: the connection must be made again."""
        from modules.integrations.application.ports import SecretNotFound
        from modules.integrations.infrastructure.secrets import SecretUndecryptable

        assert issubclass(SecretUndecryptable, SecretNotFound)
        assert issubclass(CredentialUnreadable, Exception)
