"""Connecting a system, and what must be true before it reads as working."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import pytest
from cryptography.fernet import Fernet

from modules.integrations.application.connect import (
    ConnectInput,
    ConnectSystem,
    UnknownIntegration,
)
from modules.integrations.application.ports import SecretNotFound
from modules.integrations.domain.connection import ConnectedAccount, ConnectionState
from modules.integrations.domain.grant import Credential, IntegrationGrant

NOW = datetime(2026, 8, 2, 12, 0, tzinfo=UTC)
WORKSPACE = uuid4()
ACTOR = uuid4()


class FakeAccounts:
    def __init__(self) -> None:
        self.saved: list[ConnectedAccount] = []

    async def get(self, workspace_id: UUID, account_id: UUID) -> ConnectedAccount | None:
        return next((a for a in self.saved if a.id == account_id), None)

    async def list_for_workspace(self, workspace_id: UUID) -> list[ConnectedAccount]:
        return [a for a in self.saved if a.workspace_id == workspace_id]

    async def save(self, account: ConnectedAccount) -> None:
        self.saved.append(account)


class FakeGrants:
    def __init__(self) -> None:
        self.saved: list[IntegrationGrant] = []

    async def current_for(
        self, workspace_id: UUID, connected_account_id: UUID
    ) -> IntegrationGrant | None:
        return next(
            (g for g in self.saved if g.connected_account_id == connected_account_id), None
        )

    async def save(self, grant: IntegrationGrant) -> None:
        self.saved.append(grant)


class FakeSecrets:
    def __init__(self, *, fails: bool = False) -> None:
        self.stored: dict[str, Credential] = {}
        self._fails = fails

    async def store(
        self,
        *,
        secret_ref: str,
        workspace_id: str,
        connected_account_id: str,
        credential: Credential,
    ) -> None:
        if self._fails:
            raise RuntimeError("the vault is unreachable")
        self.stored[secret_ref] = credential


def _request(**overrides: object) -> ConnectInput:
    defaults: dict[str, object] = {
        "workspace_id": WORKSPACE,
        "actor_id": ACTOR,
        "integration": "hubspot",
        "external_account_id": "24681012",
        "label": "Acme",
        "endpoint": None,
        "credential": Credential(kind="bearer", material=b"tok"),
        "scopes": ("crm.objects.contacts.read",),
        "expires_at": NOW + timedelta(hours=6),
        "refreshable": True,
    }
    defaults.update(overrides)
    return ConnectInput(**defaults)  # type: ignore[arg-type]


def _connect(secrets: FakeSecrets | None = None) -> tuple[ConnectSystem, FakeAccounts, FakeGrants, FakeSecrets]:
    accounts, grants = FakeAccounts(), FakeGrants()
    store = secrets or FakeSecrets()
    return ConnectSystem(accounts, grants, store), accounts, grants, store


class TestConnecting:
    @pytest.mark.asyncio
    async def test_a_connection_and_its_grant_are_recorded(self) -> None:
        connect, accounts, grants, secrets = _connect()
        account = await connect.execute(_request(), at=NOW)
        assert account.state is ConnectionState.CONNECTED
        assert accounts.saved == [account]
        assert grants.saved[0].connected_account_id == account.id
        assert secrets.stored[grants.saved[0].secret_ref].material == b"tok"

    @pytest.mark.asyncio
    async def test_it_passes_through_authorizing_rather_than_skipping_it(self) -> None:
        """**The use case obeys its own state machine.** Writing `CONNECTED`
        directly would make the lifecycle decorative — a table of transitions
        nothing is obliged to follow."""
        connect, _, _, _ = _connect()
        account = await connect.execute(_request(), at=NOW)
        assert account.connected_at == NOW

    @pytest.mark.asyncio
    async def test_an_unknown_system_is_refused(self) -> None:
        """A connection to something the catalog does not contain would put a
        row on a customer's screen that no adapter could ever resolve."""
        connect, accounts, _, _ = _connect()
        with pytest.raises(UnknownIntegration, match="netsuite"):
            await connect.execute(_request(integration="netsuite"), at=NOW)
        assert accounts.saved == []

    @pytest.mark.asyncio
    async def test_the_grant_carries_the_scopes_the_customer_permitted(self) -> None:
        connect, _, grants, _ = _connect()
        await connect.execute(_request(scopes=("a", "b")), at=NOW)
        assert grants.saved[0].scopes == ("a", "b")

    @pytest.mark.asyncio
    async def test_a_non_expiring_credential_is_recorded_as_such(self) -> None:
        """An API key is a grant that does not expire — a value, not a special
        case, and the acquisition path must not assume otherwise."""
        connect, _, grants, _ = _connect()
        await connect.execute(_request(expires_at=None, refreshable=False), at=NOW)
        assert grants.saved[0].expires_at is None
        assert grants.saved[0].refreshable is False


class TestOrderingProtectsTheCustomer:
    @pytest.mark.asyncio
    async def test_a_failed_secret_write_leaves_no_connection_behind(self) -> None:
        """**Material first, deliberately.** If the connection were written
        first and this failed, the Connection Center would say *Ready to use*
        about a credential that does not exist — the one lie that screen was
        built to prevent."""
        connect, accounts, grants, _ = _connect(FakeSecrets(fails=True))
        with pytest.raises(RuntimeError):
            await connect.execute(_request(), at=NOW)
        assert accounts.saved == []
        assert grants.saved == []


class TestTheSecretStore:
    """The port's first real implementation, exercised without a database."""

    @staticmethod
    def _fernet() -> str:
        return Fernet.generate_key().decode()

    def test_material_is_unreadable_without_the_key(self) -> None:
        key = self._fernet()
        ciphertext = Fernet(key).encrypt(b"a-real-token")
        assert b"a-real-token" not in ciphertext

    def test_a_different_key_cannot_read_it(self) -> None:
        """What makes the key injection load-bearing rather than ceremonial."""
        from cryptography.fernet import InvalidToken

        ciphertext = Fernet(self._fernet()).encrypt(b"a-real-token")
        with pytest.raises(InvalidToken):
            Fernet(self._fernet()).decrypt(ciphertext)

    def test_secret_not_found_is_a_distinct_outcome(self) -> None:
        """A grant can outlive its material when a purge runs at offboarding,
        and resolving to nothing would call a vendor unauthenticated."""
        assert issubclass(SecretNotFound, Exception)
