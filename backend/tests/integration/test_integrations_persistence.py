"""Integrations against a real PostgreSQL 17, as the least-privilege role.

**These exist because a fake cannot refuse an insert.** Every repository in this
module was exercised only through test doubles, and the doubles accepted a
`ConnectedAccount` the database would not: `connected_account.created_by` and
`updated_by` are `NOT NULL`, nothing supplied them, and **every insert would
have failed the first time a customer connected anything.** The unit suite was
green throughout. That is [B-024](../../../docs/BUGS.md) — the defect the
coverage gap was hiding rather than the percentage it was reported as.

The other half is the credential store. `EncryptedSecretStore` is the file the
bug report singled out: *"a guarantee about credential confidentiality that no
test exercises is a guarantee nobody has checked."* What is asserted here is the
guarantee itself — that what lands in the column is **not** the material, that a
wrong key is refused rather than silently returning something, and that purging
actually removes it.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import pytest
from cryptography.fernet import Fernet
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from modules.integrations.application.connect import ConnectInput, ConnectSystem
from modules.integrations.application.disconnect import DisconnectSystem
from modules.integrations.application.ports import SecretNotFound
from modules.integrations.domain.connection import ConnectedAccount, ConnectionState
from modules.integrations.domain.grant import Credential, IntegrationGrant
from modules.integrations.infrastructure.repository import (
    SqlConnectedAccountRepository,
    SqlGrantStore,
)
from modules.integrations.infrastructure.secrets import (
    EncryptedSecretStore,
    SecretUndecryptable,
)
from signora_platform.db import tenant_scoped_session

pytestmark = pytest.mark.integration

NOW = datetime(2026, 8, 2, 12, 0, tzinfo=UTC)
ACTOR = UUID("22222222-2222-4222-8222-222222222222")
OTHER_ACTOR = UUID("33333333-3333-4333-8333-333333333333")


def _account(
    workspace_id: UUID,
    *,
    integration: str = "hubspot",
    label: str = "Acme production",
    external: str = "24681012",
    state: ConnectionState = ConnectionState.CONNECTED,
    actor: UUID = ACTOR,
) -> ConnectedAccount:
    return ConnectedAccount(
        id=uuid4(),
        workspace_id=workspace_id,
        integration=integration,
        external_account_id=external,
        endpoint=None,
        label=label,
        state=state,
        connected_at=NOW,
        actor_id=actor,
    )


def _grant(account: ConnectedAccount, *, actor: UUID = ACTOR, **kw: object) -> IntegrationGrant:
    return IntegrationGrant(
        id=uuid4(),
        workspace_id=account.workspace_id,
        connected_account_id=account.id,
        secret_ref=kw.pop("secret_ref", f"integration/{account.id}"),  # type: ignore[arg-type]
        scopes=("crm.objects.contacts.read",),
        expires_at=kw.pop("expires_at", None),  # type: ignore[arg-type]
        refreshable=True,
        revoked_at=kw.pop("revoked_at", None),  # type: ignore[arg-type]
        actor_id=actor,
    )


class TestAConnectionSurvivesTheDatabase:
    """**The tests that would have caught it.** Each one writes and reads back
    through the real schema, which is the only place the `NOT NULL` lives."""

    async def test_a_connection_can_actually_be_stored(
        self, session_factory: async_sessionmaker[AsyncSession]
    ) -> None:
        workspace = uuid4()
        account = _account(workspace)

        async with tenant_scoped_session(
            session_factory, workspace_id=workspace, user_id=ACTOR
        ) as session:
            await SqlConnectedAccountRepository(session).save(account)
            await session.commit()

        async with tenant_scoped_session(
            session_factory, workspace_id=workspace, user_id=ACTOR
        ) as session:
            stored = await SqlConnectedAccountRepository(session).get(workspace, account.id)

        assert stored is not None
        assert stored.label == "Acme production"
        assert stored.state is ConnectionState.CONNECTED
        assert stored.actor_id == ACTOR

    async def test_who_connected_it_is_not_overwritten_by_who_disconnected_it(
        self, session_factory: async_sessionmaker[AsyncSession]
    ) -> None:
        """*"Who connected our CRM?"* and *"who disconnected it?"* are different
        questions, and an update that reassigned `created_by` would destroy the
        first answer at the moment somebody needed both."""
        workspace = uuid4()
        account = _account(workspace)

        async with tenant_scoped_session(
            session_factory, workspace_id=workspace, user_id=ACTOR
        ) as session:
            repository = SqlConnectedAccountRepository(session)
            await repository.save(account)
            await session.commit()

        async with tenant_scoped_session(
            session_factory, workspace_id=workspace, user_id=OTHER_ACTOR
        ) as session:
            repository = SqlConnectedAccountRepository(session)
            current = await repository.get(workspace, account.id)
            assert current is not None
            await repository.save(
                current.transition(ConnectionState.DISCONNECTED, at=NOW, by=OTHER_ACTOR)
            )
            await session.commit()

        async with tenant_scoped_session(
            session_factory, workspace_id=workspace, user_id=ACTOR
        ) as session:
            row = (
                await session.execute(
                    text(
                        "SELECT created_by, updated_by, state FROM connected_account "
                        "WHERE id = :id"
                    ),
                    {"id": account.id},
                )
            ).one()

        assert row.created_by == ACTOR
        assert row.updated_by == OTHER_ACTOR
        assert row.state == "disconnected"

    async def test_connections_are_ordered_so_a_screen_does_not_shuffle(
        self, session_factory: async_sessionmaker[AsyncSession]
    ) -> None:
        workspace = uuid4()
        async with tenant_scoped_session(
            session_factory, workspace_id=workspace, user_id=ACTOR
        ) as session:
            repository = SqlConnectedAccountRepository(session)
            for integration, label, external in [
                ("hubspot", "Zed", "1"),
                ("google_calendar", "Sam", "2"),
                ("google_calendar", "Ana", "3"),
            ]:
                await repository.save(
                    _account(workspace, integration=integration, label=label, external=external)
                )
            await session.commit()

        async with tenant_scoped_session(
            session_factory, workspace_id=workspace, user_id=ACTOR
        ) as session:
            listed = await SqlConnectedAccountRepository(session).list_for_workspace(workspace)

        assert [(a.integration, a.label) for a in listed] == [
            ("google_calendar", "Ana"),
            ("google_calendar", "Sam"),
            ("hubspot", "Zed"),
        ]

    async def test_the_same_account_cannot_be_connected_twice(
        self, session_factory: async_sessionmaker[AsyncSession]
    ) -> None:
        """Two rows for one Salesforce org is two grants racing to refresh one
        token. The constraint is the control; this proves it is live."""
        from sqlalchemy.exc import IntegrityError

        workspace = uuid4()
        async with tenant_scoped_session(
            session_factory, workspace_id=workspace, user_id=ACTOR
        ) as session:
            repository = SqlConnectedAccountRepository(session)
            await repository.save(_account(workspace, external="dup"))
            await session.commit()

        with pytest.raises(IntegrityError):
            async with tenant_scoped_session(
                session_factory, workspace_id=workspace, user_id=ACTOR
            ) as session:
                await SqlConnectedAccountRepository(session).save(
                    _account(workspace, external="dup", label="Second attempt")
                )
                await session.commit()

    async def test_another_organizations_connection_is_invisible(
        self, session_factory: async_sessionmaker[AsyncSession]
    ) -> None:
        """RLS is the authoritative control; the explicit filter is defence in
        depth. Read under a *different* workspace context so both are in play."""
        owner, intruder = uuid4(), uuid4()
        account = _account(owner)

        async with tenant_scoped_session(
            session_factory, workspace_id=owner, user_id=ACTOR
        ) as session:
            await SqlConnectedAccountRepository(session).save(account)
            await session.commit()

        async with tenant_scoped_session(
            session_factory, workspace_id=intruder, user_id=ACTOR
        ) as session:
            repository = SqlConnectedAccountRepository(session)
            assert await repository.get(intruder, account.id) is None
            assert await repository.list_for_workspace(intruder) == []


class TestTheLiveGrantIsTheOneNotRevoked:
    async def test_a_grant_round_trips(
        self, session_factory: async_sessionmaker[AsyncSession]
    ) -> None:
        workspace = uuid4()
        account = _account(workspace)
        expiry = NOW + timedelta(hours=6)

        async with tenant_scoped_session(
            session_factory, workspace_id=workspace, user_id=ACTOR
        ) as session:
            await SqlConnectedAccountRepository(session).save(account)
            await SqlGrantStore(session).save(_grant(account, expires_at=expiry))
            await session.commit()

        async with tenant_scoped_session(
            session_factory, workspace_id=workspace, user_id=ACTOR
        ) as session:
            grant = await SqlGrantStore(session).current_for(workspace, account.id)

        assert grant is not None
        assert grant.scopes == ("crm.objects.contacts.read",)
        assert grant.expires_at == expiry
        assert grant.refreshable is True

    async def test_a_revoked_grant_is_history_rather_than_a_candidate(
        self, session_factory: async_sessionmaker[AsyncSession]
    ) -> None:
        """A connection accumulates revoked grants across reconnections. Reading
        one back as current would authenticate with a credential the customer
        withdrew."""
        workspace = uuid4()
        account = _account(workspace)

        async with tenant_scoped_session(
            session_factory, workspace_id=workspace, user_id=ACTOR
        ) as session:
            await SqlConnectedAccountRepository(session).save(account)
            grants = SqlGrantStore(session)
            revoked = _grant(account, secret_ref="integration/old")
            await grants.save(revoked)
            await grants.save(revoked.revoke(at=NOW, by=ACTOR))
            await session.commit()

        async with tenant_scoped_session(
            session_factory, workspace_id=workspace, user_id=ACTOR
        ) as session:
            assert await SqlGrantStore(session).current_for(workspace, account.id) is None

    async def test_a_connection_with_no_grant_reads_as_none(
        self, session_factory: async_sessionmaker[AsyncSession]
    ) -> None:
        workspace = uuid4()
        account = _account(workspace, state=ConnectionState.AUTHORIZING)
        async with tenant_scoped_session(
            session_factory, workspace_id=workspace, user_id=ACTOR
        ) as session:
            await SqlConnectedAccountRepository(session).save(account)
            await session.commit()

        async with tenant_scoped_session(
            session_factory, workspace_id=workspace, user_id=ACTOR
        ) as session:
            assert await SqlGrantStore(session).current_for(workspace, account.id) is None


class TestTheCredentialIsNotReadable:
    """**The file the bug report named.** These assert the guarantee rather
    than executing the lines."""

    async def test_the_material_is_not_what_lands_in_the_column(
        self, session_factory: async_sessionmaker[AsyncSession]
    ) -> None:
        """The whole reason the table exists. A token in a plain column is a
        token in every backup, every replica and every `psql` session."""
        workspace = uuid4()
        account = _account(workspace)
        key = Fernet.generate_key().decode()

        async with tenant_scoped_session(
            session_factory, workspace_id=workspace, user_id=ACTOR
        ) as session:
            await SqlConnectedAccountRepository(session).save(account)
            await EncryptedSecretStore(session, key).store(
                secret_ref=f"integration/{account.id}",
                workspace_id=str(workspace),
                connected_account_id=str(account.id),
                credential=Credential(kind="bearer", material=b"pat-na1-super-secret"),
            )
            await session.commit()

        async with tenant_scoped_session(
            session_factory, workspace_id=workspace, user_id=ACTOR
        ) as session:
            ciphertext = (
                await session.execute(
                    text("SELECT ciphertext FROM integration_secret WHERE secret_ref = :ref"),
                    {"ref": f"integration/{account.id}"},
                )
            ).scalar_one()

        assert b"pat-na1-super-secret" not in bytes(ciphertext)

    async def test_it_resolves_back_to_exactly_what_was_stored(
        self, session_factory: async_sessionmaker[AsyncSession]
    ) -> None:
        workspace = uuid4()
        account = _account(workspace)
        key = Fernet.generate_key().decode()

        async with tenant_scoped_session(
            session_factory, workspace_id=workspace, user_id=ACTOR
        ) as session:
            await SqlConnectedAccountRepository(session).save(account)
            await EncryptedSecretStore(session, key).store(
                secret_ref=f"integration/{account.id}",
                workspace_id=str(workspace),
                connected_account_id=str(account.id),
                credential=Credential(kind="bearer", material=b"round-trip"),
            )
            await session.commit()

        async with tenant_scoped_session(
            session_factory, workspace_id=workspace, user_id=ACTOR
        ) as session:
            credential = await EncryptedSecretStore(session, key).resolve(f"integration/{account.id}")

        assert credential.kind == "bearer"
        assert credential.material == b"round-trip"

    async def test_a_rotated_key_refuses_rather_than_returning_something(
        self, session_factory: async_sessionmaker[AsyncSession]
    ) -> None:
        """**The failure that must not be silent.** Reading a credential with
        the wrong key must not resolve to anything — a caller would take it to a
        vendor and get an unexplainable 401."""
        workspace = uuid4()
        account = _account(workspace)
        written, rotated = Fernet.generate_key().decode(), Fernet.generate_key().decode()

        async with tenant_scoped_session(
            session_factory, workspace_id=workspace, user_id=ACTOR
        ) as session:
            await SqlConnectedAccountRepository(session).save(account)
            await EncryptedSecretStore(session, written).store(
                secret_ref=f"integration/{account.id}",
                workspace_id=str(workspace),
                connected_account_id=str(account.id),
                credential=Credential(kind="bearer", material=b"unreachable"),
            )
            await session.commit()

        async with tenant_scoped_session(
            session_factory, workspace_id=workspace, user_id=ACTOR
        ) as session:
            store = EncryptedSecretStore(session, rotated)
            with pytest.raises(SecretUndecryptable):
                await store.resolve(f"integration/{account.id}")

    async def test_a_missing_reference_is_not_found(
        self, session_factory: async_sessionmaker[AsyncSession]
    ) -> None:
        workspace = uuid4()
        async with tenant_scoped_session(
            session_factory, workspace_id=workspace, user_id=ACTOR
        ) as session:
            store = EncryptedSecretStore(session, Fernet.generate_key().decode())
            with pytest.raises(SecretNotFound):
                await store.resolve(f"integration/{uuid4()}")

    async def test_purging_actually_removes_the_material(
        self, session_factory: async_sessionmaker[AsyncSession]
    ) -> None:
        """**What makes *"Signora can no longer read from this"* true rather
        than believed.** Marking a grant revoked leaves the credential behind."""
        workspace = uuid4()
        account = _account(workspace)
        key = Fernet.generate_key().decode()

        async with tenant_scoped_session(
            session_factory, workspace_id=workspace, user_id=ACTOR
        ) as session:
            await SqlConnectedAccountRepository(session).save(account)
            store = EncryptedSecretStore(session, key)
            for suffix in ("a", "b"):
                await store.store(
                    secret_ref=f"integration/{account.id}/{suffix}",
                    workspace_id=str(workspace),
                    connected_account_id=str(account.id),
                    credential=Credential(kind="bearer", material=b"gone"),
                )
            await session.commit()

        async with tenant_scoped_session(
            session_factory, workspace_id=workspace, user_id=ACTOR
        ) as session:
            await EncryptedSecretStore(session, key).purge_for(str(account.id))
            await session.commit()

        async with tenant_scoped_session(
            session_factory, workspace_id=workspace, user_id=ACTOR
        ) as session:
            remaining = (
                await session.execute(
                    text(
                        "SELECT count(*) FROM integration_secret "
                        "WHERE connected_account_id = :id"
                    ),
                    {"id": account.id},
                )
            ).scalar_one()

        assert remaining == 0

    async def test_another_organizations_credential_is_invisible(
        self, session_factory: async_sessionmaker[AsyncSession]
    ) -> None:
        """Credentials are not exempt from tenancy. Read under a different
        workspace, where RLS is the only thing standing in the way."""
        owner, intruder = uuid4(), uuid4()
        account = _account(owner)
        key = Fernet.generate_key().decode()

        async with tenant_scoped_session(
            session_factory, workspace_id=owner, user_id=ACTOR
        ) as session:
            await SqlConnectedAccountRepository(session).save(account)
            await EncryptedSecretStore(session, key).store(
                secret_ref=f"integration/{account.id}",
                workspace_id=str(owner),
                connected_account_id=str(account.id),
                credential=Credential(kind="bearer", material=b"not-yours"),
            )
            await session.commit()

        async with tenant_scoped_session(
            session_factory, workspace_id=intruder, user_id=ACTOR
        ) as session:
            store = EncryptedSecretStore(session, key)
            with pytest.raises(SecretNotFound):
                await store.resolve(f"integration/{account.id}")


class TestConnectAndDisconnectOverTheRealSchema:
    """The two use cases end to end, against PostgreSQL rather than fakes."""

    async def test_connecting_writes_the_connection_the_grant_and_the_material(
        self, session_factory: async_sessionmaker[AsyncSession]
    ) -> None:
        workspace = uuid4()
        key = Fernet.generate_key().decode()

        async with tenant_scoped_session(
            session_factory, workspace_id=workspace, user_id=ACTOR
        ) as session:
            secrets = EncryptedSecretStore(session, key)
            account = await ConnectSystem(
                SqlConnectedAccountRepository(session), SqlGrantStore(session), secrets
            ).execute(
                ConnectInput(
                    workspace_id=workspace,
                    actor_id=ACTOR,
                    integration="hubspot",
                    external_account_id="24681012",
                    label="Acme production",
                    endpoint=None,
                    credential=Credential(kind="bearer", material=b"token"),
                    scopes=("crm.objects.contacts.read",),
                    expires_at=NOW + timedelta(hours=6),
                    refreshable=True,
                ),
                at=NOW,
            )
            await session.commit()

        async with tenant_scoped_session(
            session_factory, workspace_id=workspace, user_id=ACTOR
        ) as session:
            stored = await SqlConnectedAccountRepository(session).get(workspace, account.id)
            grant = await SqlGrantStore(session).current_for(workspace, account.id)
            credential = await EncryptedSecretStore(session, key).resolve(
                f"integration/{account.id}"
            )

        assert stored is not None and stored.state is ConnectionState.CONNECTED
        assert grant is not None and grant.secret_ref == f"integration/{account.id}"
        assert credential.material == b"token"

    async def test_disconnecting_leaves_nothing_to_read_with(
        self, session_factory: async_sessionmaker[AsyncSession]
    ) -> None:
        """**The property the whole capability exists for**, asserted against
        the storage rather than against a fake's call log."""
        workspace = uuid4()
        key = Fernet.generate_key().decode()

        async with tenant_scoped_session(
            session_factory, workspace_id=workspace, user_id=ACTOR
        ) as session:
            account = await ConnectSystem(
                SqlConnectedAccountRepository(session),
                SqlGrantStore(session),
                EncryptedSecretStore(session, key),
            ).execute(
                ConnectInput(
                    workspace_id=workspace,
                    actor_id=ACTOR,
                    integration="hubspot",
                    external_account_id="1357",
                    label="Acme",
                    endpoint=None,
                    credential=Credential(kind="bearer", material=b"token"),
                    scopes=("crm.objects.contacts.read",),
                    expires_at=None,
                    refreshable=True,
                ),
                at=NOW,
            )
            await session.commit()

        async with tenant_scoped_session(
            session_factory, workspace_id=workspace, user_id=OTHER_ACTOR
        ) as session:
            result = await DisconnectSystem(
                SqlConnectedAccountRepository(session),
                SqlGrantStore(session),
                EncryptedSecretStore(session, key),
            ).execute(workspace, account.id, at=NOW, actor_id=OTHER_ACTOR)
            await session.commit()

        assert result.account.state is ConnectionState.DISCONNECTED
        # No adapter calls a vendor's revocation endpoint yet, so this is
        # `False` — and the screen tells the customer so rather than implying
        # the vendor was told.
        assert result.revoked_at_provider is False

        async with tenant_scoped_session(
            session_factory, workspace_id=workspace, user_id=ACTOR
        ) as session:
            stored = await SqlConnectedAccountRepository(session).get(workspace, account.id)
            grant = await SqlGrantStore(session).current_for(workspace, account.id)
            store = EncryptedSecretStore(session, key)
            with pytest.raises(SecretNotFound):
                await store.resolve(f"integration/{account.id}")

        assert stored is not None and stored.state is ConnectionState.DISCONNECTED
        assert grant is None
