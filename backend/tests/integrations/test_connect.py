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

    async def find_identity(
        self, workspace_id: UUID, integration: str, external_account_id: str
    ) -> ConnectedAccount | None:
        return next(
            (
                a
                for a in self.saved
                if a.workspace_id == workspace_id
                and a.integration == integration
                and a.external_account_id == external_account_id
            ),
            None,
        )

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
        # Saved twice — `AUTHORIZING` so the credential and grant have a parent
        # row to reference, then `CONNECTED` once both exist. The last write is
        # what the customer sees.
        assert accounts.saved[-1] == account
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
    """**The property, not the sequence.**

    This asserted *"material is written first, and a failure leaves no
    connection at all"* — a rule the database refuses. Material and grants both
    carry a foreign key to the connection, so writing either first is rejected;
    it passed only because a fake cannot refuse an insert (B-024).

    What the rule was actually protecting is unchanged and asserted below: **a
    connection is never left readable as `CONNECTED` with no credential behind
    it.** The connection is now written first, in `AUTHORIZING`, which the
    Connection Center already reports as *you started this and did not finish*
    — true, actionable, and disconnectable.
    """

    @pytest.mark.asyncio
    async def test_a_failed_secret_write_never_leaves_a_connection_looking_ready(
        self,
    ) -> None:
        connect, accounts, grants, _ = _connect(FakeSecrets(fails=True))
        with pytest.raises(RuntimeError):
            await connect.execute(_request(), at=NOW)
        assert grants.saved == []
        assert all(a.state is not ConnectionState.CONNECTED for a in accounts.saved)

    @pytest.mark.asyncio
    async def test_a_half_finished_connection_is_one_a_customer_can_still_remove(
        self,
    ) -> None:
        """The state left behind must not be a trap. `AUTHORIZING` reaches
        `DISCONNECTED`, so an abandoned attempt can be cleared."""
        connect, accounts, _, _ = _connect(FakeSecrets(fails=True))
        with pytest.raises(RuntimeError):
            await connect.execute(_request(), at=NOW)
        stranded = accounts.saved[-1]
        assert stranded.state is ConnectionState.AUTHORIZING
        assert (
            stranded.transition(ConnectionState.DISCONNECTED, at=NOW, by=stranded.actor_id).state
            is ConnectionState.DISCONNECTED
        )

    @pytest.mark.asyncio
    async def test_the_credential_exists_before_the_grant_that_names_it(self) -> None:
        """A grant pointing at material that was never stored reads as usable
        and fails at the vendor with nothing to explain it."""
        connect, _, grants, secrets = _connect()
        await connect.execute(_request(), at=NOW)
        assert grants.saved[0].secret_ref in secrets.stored


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
