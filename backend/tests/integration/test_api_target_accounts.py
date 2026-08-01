"""The target account list over the full stack, and the module's first event.

**The slice that gives the pipeline an input.** `RunProviderSync` has taken a
`subject: str` since M2.1 and nothing has ever supplied one; every company the
platform has processed so far arrived from a seeder.

These exercise the whole chain a real request traverses — JWT verification,
membership verification, RLS context, Casbin, and PostgreSQL as the
least-privileged role — plus two things no earlier slice had:

- **the announcement lands in the outbox in the same transaction as the row**,
  which is the only arrangement where a consumer can never hear about
  something that did not happen; and
- **the published read port returns what `public/` promises**, because from
  today that shape is somebody else's dependency.
"""

from collections.abc import AsyncIterator
from typing import Any
from uuid import UUID, uuid4

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from apps.api.main import create_app
from modules.commercial_profile.infrastructure.composition import (
    build_target_account_reader,
)
from signora_platform.settings import Settings
from signora_platform.tests.keys import (
    TEST_AUDIENCE,
    TEST_ISSUER,
    KeyPair,
    generate_key_pair,
    mint_token,
)
from tests.conftest import DEFAULT_APP_DATABASE_URL

pytestmark = pytest.mark.integration


@pytest.fixture(scope="session")
def key_pair() -> KeyPair:
    return generate_key_pair()


@pytest.fixture
async def client(key_pair: KeyPair) -> AsyncIterator[AsyncClient]:
    settings = Settings(
        environment="test",
        database_url=DEFAULT_APP_DATABASE_URL,
        jwt_public_key=key_pair.public_pem,
        jwt_issuer=TEST_ISSUER,
        jwt_audience=TEST_AUDIENCE,
    )
    app = create_app(settings)
    async with (
        app.router.lifespan_context(app),
        AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as http,
    ):
        yield http


def _auth(key_pair: KeyPair, user_id: UUID) -> dict[str, str]:
    return {"Authorization": f"Bearer {mint_token(key_pair, user_id=user_id)}"}


async def _workspace(client: AsyncClient, key_pair: KeyPair, user_id: UUID) -> UUID:
    response = await client.post(
        "/workspaces", json={"name": "Acme"}, headers=_auth(key_pair, user_id)
    )
    assert response.status_code == 201, response.text
    return UUID(response.json()["id"])


async def _read(client: AsyncClient, key_pair: KeyPair, user: UUID, workspace: UUID) -> Any:
    return await client.get(
        f"/workspaces/{workspace}/target-accounts", headers=_auth(key_pair, user)
    )


async def _declare(
    client: AsyncClient,
    key_pair: KeyPair,
    user: UUID,
    workspace: UUID,
    *,
    accounts: list[dict[str, str]],
    expected_version: int,
) -> Any:
    return await client.put(
        f"/workspaces/{workspace}/target-accounts",
        json={"expected_version": expected_version, "accounts": accounts},
        headers=_auth(key_pair, user),
    )


def _account(name: str = "Acme Corporation") -> dict[str, str]:
    return {"id": str(uuid4()), "name": name}


async def _announcements(
    admin_session_factory: async_sessionmaker[AsyncSession],
) -> list[Any]:
    """Read the outbox **under the privileged identity, never the app's.**

    `signora_app` publishes events and is forbidden from reading them back
    (migration `0006`). A test that read them as the application role would be
    asserting a capability the architecture deliberately removed.
    """
    async with admin_session_factory() as session:
        return list(
            (
                await session.execute(
                    text(
                        "SELECT event_type, event_version, workspace_id, payload, "
                        "producer_module, correlation_id, relayed_at "
                        "FROM outbox_event "
                        "WHERE event_type = 'commercial_profile.target_accounts_changed' "
                        "ORDER BY created_at"
                    )
                )
            ).all()
        )


class TestAWorkspaceThatHasNamedNobody:
    async def test_it_reads_an_empty_list_rather_than_a_404(
        self, client: AsyncClient, key_pair: KeyPair
    ) -> None:
        user = uuid4()
        workspace = await _workspace(client, key_pair, user)

        response = await _read(client, key_pair, user, workspace)

        assert response.status_code == 200, response.text
        assert response.json() == {
            "version": 0,
            "accounts": [],
            "updated_at": None,
            "updated_by": None,
        }

    async def test_and_announces_nothing(
        self,
        client: AsyncClient,
        key_pair: KeyPair,
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        await _workspace(client, key_pair, uuid4())

        assert await _announcements(admin_session_factory) == []


class TestDeclaringAWatchList:
    async def test_it_is_stored_and_read_back_exactly_as_typed(
        self, client: AsyncClient, key_pair: KeyPair
    ) -> None:
        """**Never resolved, never tidied.** Working out which company the
        customer means is Signora's job, and it happens later, elsewhere."""
        user = uuid4()
        workspace = await _workspace(client, key_pair, user)
        account = _account("ACME Corp.")

        declared = await _declare(
            client, key_pair, user, workspace, accounts=[account], expected_version=0
        )

        assert declared.status_code == 200, declared.text
        body = (await _read(client, key_pair, user, workspace)).json()
        assert body["version"] == 1
        assert body["accounts"] == [{"id": account["id"], "name": "ACME Corp."}]

    async def test_it_records_who_named_them_and_when(
        self, client: AsyncClient, key_pair: KeyPair
    ) -> None:
        """Choosing which companies Signora spends money watching is a
        decision, and the record of one names its author permanently."""
        user = uuid4()
        workspace = await _workspace(client, key_pair, user)

        await _declare(client, key_pair, user, workspace, accounts=[_account()], expected_version=0)

        body = (await _read(client, key_pair, user, workspace)).json()
        assert body["updated_by"] == str(user)
        assert body["updated_at"] is not None

    async def test_an_entry_keeps_its_identity_when_renamed(
        self, client: AsyncClient, key_pair: KeyPair
    ) -> None:
        """**What ADR-0036 asked for.** Without a stable id a rename is
        indistinguishable from a remove-and-add, and those are different
        instructions about spending money."""
        user = uuid4()
        workspace = await _workspace(client, key_pair, user)
        account = _account("Acme")

        await _declare(client, key_pair, user, workspace, accounts=[account], expected_version=0)
        renamed = await _declare(
            client,
            key_pair,
            user,
            workspace,
            accounts=[{**account, "name": "Acme Corporation"}],
            expected_version=1,
        )

        assert renamed.status_code == 200, renamed.text
        body = (await _read(client, key_pair, user, workspace)).json()
        assert body["accounts"][0]["id"] == account["id"]
        assert body["accounts"][0]["name"] == "Acme Corporation"

    async def test_watching_nobody_is_a_new_version_not_a_deletion(
        self, client: AsyncClient, key_pair: KeyPair
    ) -> None:
        user = uuid4()
        workspace = await _workspace(client, key_pair, user)

        await _declare(client, key_pair, user, workspace, accounts=[_account()], expected_version=0)
        await _declare(client, key_pair, user, workspace, accounts=[], expected_version=1)

        body = (await _read(client, key_pair, user, workspace)).json()
        assert (body["version"], body["accounts"]) == (2, [])


class TestTheAnnouncement:
    async def test_it_reaches_the_outbox_with_the_declaration(
        self,
        client: AsyncClient,
        key_pair: KeyPair,
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        """**The row and the event commit together or not at all.** Seeing the
        event here means the transaction that wrote the list also wrote the
        announcement — which is the whole point of the outbox."""
        user = uuid4()
        workspace = await _workspace(client, key_pair, user)

        await _declare(client, key_pair, user, workspace, accounts=[_account()], expected_version=0)

        rows = await _announcements(admin_session_factory)
        assert len(rows) == 1
        assert rows[0].event_type == "commercial_profile.target_accounts_changed"
        assert rows[0].workspace_id == workspace
        assert rows[0].producer_module == "commercial_profile"
        assert rows[0].correlation_id is not None
        # Nothing has been relayed — the relay is a separate process.
        assert rows[0].relayed_at is None

    async def test_the_payload_is_the_version_and_nothing_else(
        self,
        client: AsyncClient,
        key_pair: KeyPair,
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        """**ADR-0036 §3, asserted on the wire it actually travels on.** A
        company name here would put a copy of an aggregate's truth on a bus,
        where it can be stale, replayed, and contradicted by the aggregate it
        copies."""
        user = uuid4()
        workspace = await _workspace(client, key_pair, user)

        await _declare(
            client,
            key_pair,
            user,
            workspace,
            accounts=[_account("Acme"), _account("Globex")],
            expected_version=0,
        )

        rows = await _announcements(admin_session_factory)
        assert rows[0].payload == {"declaration_version": 1}

    async def test_every_accepted_declaration_is_announced(
        self,
        client: AsyncClient,
        key_pair: KeyPair,
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        user = uuid4()
        workspace = await _workspace(client, key_pair, user)

        await _declare(client, key_pair, user, workspace, accounts=[_account()], expected_version=0)
        await _declare(client, key_pair, user, workspace, accounts=[], expected_version=1)

        rows = await _announcements(admin_session_factory)
        assert [row.payload["declaration_version"] for row in rows] == [1, 2]

    async def test_a_refused_declaration_announces_nothing(
        self,
        client: AsyncClient,
        key_pair: KeyPair,
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        """**The failure that would be worst.** A consumer told a list changed
        when it did not would sync against a version that never existed."""
        user = uuid4()
        workspace = await _workspace(client, key_pair, user)

        await _declare(client, key_pair, user, workspace, accounts=[_account()], expected_version=0)
        stale = await _declare(
            client,
            key_pair,
            user,
            workspace,
            accounts=[_account("Globex")],
            expected_version=0,
        )

        assert stale.status_code == 409
        rows = await _announcements(admin_session_factory)
        assert len(rows) == 1, "the refused declaration must not have been announced"

    async def test_a_refused_declaration_writes_nothing_either(
        self, client: AsyncClient, key_pair: KeyPair
    ) -> None:
        user = uuid4()
        workspace = await _workspace(client, key_pair, user)
        kept = _account("Kept")

        await _declare(client, key_pair, user, workspace, accounts=[kept], expected_version=0)
        await _declare(
            client,
            key_pair,
            user,
            workspace,
            accounts=[_account("Lost")],
            expected_version=0,
        )

        body = (await _read(client, key_pair, user, workspace)).json()
        assert body["accounts"][0]["id"] == kept["id"]


class TestThePublishedReadPort:
    async def test_it_returns_the_whole_list_in_force(
        self,
        client: AsyncClient,
        key_pair: KeyPair,
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        """**The module's first public contract, exercised as a consumer will
        use it.** Read under the privileged identity because a consumer's
        composition root supplies its own session; what matters here is the
        shape `public/` promises, not who opened the connection."""
        user = uuid4()
        workspace = await _workspace(client, key_pair, user)
        first = _account("Acme")
        await _declare(
            client,
            key_pair,
            user,
            workspace,
            accounts=[first, _account("Globex")],
            expected_version=0,
        )

        async with admin_session_factory() as session:
            view = await build_target_account_reader(session).current(workspace)

        assert view is not None
        assert view.workspace_id == workspace
        assert view.version == 1
        assert [account.name for account in view.accounts] == ["Acme", "Globex"]
        assert str(view.accounts[0].id) == first["id"]

    async def test_it_answers_none_before_anything_is_declared(
        self,
        client: AsyncClient,
        key_pair: KeyPair,
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        """**`None` and an empty list are different facts.** *"They have not
        told us yet"* is a state to wait in; *"they told us to watch nobody"*
        is an instruction to act on."""
        workspace = await _workspace(client, key_pair, uuid4())

        async with admin_session_factory() as session:
            view = await build_target_account_reader(session).current(workspace)

        assert view is None

    async def test_an_empty_declaration_is_not_none(
        self,
        client: AsyncClient,
        key_pair: KeyPair,
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        user = uuid4()
        workspace = await _workspace(client, key_pair, user)
        await _declare(client, key_pair, user, workspace, accounts=[], expected_version=0)

        async with admin_session_factory() as session:
            view = await build_target_account_reader(session).current(workspace)

        assert view is not None
        assert view.accounts == ()

    async def test_the_version_it_reports_matches_the_announced_one(
        self,
        client: AsyncClient,
        key_pair: KeyPair,
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        """**How a consumer knows it is acting on the right declaration.**
        The event carries a version for ordering; the port reports the version
        it is returning, so the two can be compared."""
        user = uuid4()
        workspace = await _workspace(client, key_pair, user)
        await _declare(client, key_pair, user, workspace, accounts=[_account()], expected_version=0)
        await _declare(
            client,
            key_pair,
            user,
            workspace,
            accounts=[_account("Globex")],
            expected_version=1,
        )

        rows = await _announcements(admin_session_factory)
        async with admin_session_factory() as session:
            view = await build_target_account_reader(session).current(workspace)

        assert view is not None
        assert view.version == rows[-1].payload["declaration_version"] == 2


class TestWhatTheDomainRefuses:
    async def test_two_companies_sharing_a_name_are_refused(
        self, client: AsyncClient, key_pair: KeyPair
    ) -> None:
        user = uuid4()
        workspace = await _workspace(client, key_pair, user)

        response = await _declare(
            client,
            key_pair,
            user,
            workspace,
            accounts=[_account("Acme"), _account("acme")],
            expected_version=0,
        )

        assert response.status_code == 422
        assert response.json()["error"]["code"] == "target_accounts_refused"
        assert "share a name" in response.json()["error"]["message"]

    async def test_an_unknown_field_is_refused(
        self, client: AsyncClient, key_pair: KeyPair
    ) -> None:
        """`extra="forbid"`. The fields this exists to catch are a domain, a
        sync status or a priority added client-side — each of which belongs to
        a different module, and none of which may be silently ignored."""
        user = uuid4()
        workspace = await _workspace(client, key_pair, user)

        response = await _declare(
            client,
            key_pair,
            user,
            workspace,
            accounts=[{**_account(), "domain": "acme.com"}],
            expected_version=0,
        )

        assert response.status_code == 422


class TestConcurrentEdits:
    async def test_a_stale_version_is_refused_with_the_one_in_force(
        self, client: AsyncClient, key_pair: KeyPair
    ) -> None:
        user = uuid4()
        workspace = await _workspace(client, key_pair, user)

        await _declare(client, key_pair, user, workspace, accounts=[_account()], expected_version=0)
        stale = await _declare(
            client,
            key_pair,
            user,
            workspace,
            accounts=[_account("Globex")],
            expected_version=0,
        )

        assert stale.status_code == 409
        assert stale.json()["error"]["code"] == "target_accounts_version_conflict"
        assert "version 1" in stale.json()["error"]["message"]


class TestTenancyAndAuthorization:
    async def test_another_workspace_s_watch_list_is_not_readable(
        self, client: AsyncClient, key_pair: KeyPair
    ) -> None:
        """**The most commercially sensitive list in the platform.** It names
        exactly which companies a business is pursuing."""
        theirs_user = uuid4()
        theirs = await _workspace(client, key_pair, theirs_user)
        await _declare(
            client,
            key_pair,
            theirs_user,
            theirs,
            accounts=[_account("Their biggest prospect")],
            expected_version=0,
        )

        response = await _read(client, key_pair, uuid4(), theirs)

        assert response.status_code == 404, "a non-member gets 404, never 403"

    async def test_a_member_may_read_but_not_declare(
        self, client: AsyncClient, key_pair: KeyPair
    ) -> None:
        owner = uuid4()
        member = uuid4()
        workspace = await _workspace(client, key_pair, owner)
        added = await client.post(
            f"/workspaces/{workspace}/members",
            json={"user_id": str(member), "role": "member"},
            headers=_auth(key_pair, owner),
        )
        assert added.status_code == 201, added.text

        assert (await _read(client, key_pair, member, workspace)).status_code == 200
        refused = await _declare(
            client,
            key_pair,
            member,
            workspace,
            accounts=[_account()],
            expected_version=0,
        )
        assert refused.status_code == 403

    async def test_an_unauthenticated_request_is_refused(
        self, client: AsyncClient, key_pair: KeyPair
    ) -> None:
        workspace = await _workspace(client, key_pair, uuid4())

        response = await client.get(f"/workspaces/{workspace}/target-accounts")

        assert response.status_code == 401


class TestTheWireContract:
    async def test_every_response_field_is_documented(self, client: AsyncClient) -> None:
        schema = (await client.get("/openapi.json")).json()["components"]["schemas"]

        for name in ("TargetAccountListResponse", "TargetAccountResponse"):
            undocumented = sorted(
                field
                for field, spec in schema[name]["properties"].items()
                if not spec.get("description")
            )
            assert undocumented == [], f"{name}: {undocumented} reach the wire undocumented"

    async def test_it_reports_nothing_about_synchronization(self, client: AsyncClient) -> None:
        """**The boundary, asserted on the wire.** A watch list looks like a
        job queue, and the first field to arrive would be a status."""
        schema = (await client.get("/openapi.json")).json()["components"]["schemas"]

        fields = {
            field
            for name in ("TargetAccountListResponse", "TargetAccountResponse")
            for field in schema[name]["properties"]
        }

        assert not {
            field
            for field in fields
            for term in (
                "status",
                "sync",
                "provider",
                "last_",
                "fetched",
                "schedule",
                "priority",
                "rank",
                "score",
            )
            if term in field.casefold()
        }
