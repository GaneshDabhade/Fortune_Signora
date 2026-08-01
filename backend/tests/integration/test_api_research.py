"""Asking Signora to research an account, over the full stack.

`POST /workspaces/{id}/accounts/{id}/research` is **the first endpoint in
Signora that starts work rather than reading it.** Everything else a customer
can reach either reports what the pipeline computed or records a decision they
already made; this one asks the platform to spend a model call.

These exercise the whole chain a real request traverses: JWT verification,
server-side membership verification, RLS context, Casbin authorization, the
request write, the outbox row that will start the work, and PostgreSQL as the
least-privileged role.

**No model is called anywhere in this file, and that is the point.** The
running of research is verified against a fake in `test_run.py`; what is
asserted here is that the API *accepts* an ask and *dispatches* it — which is
exactly the boundary CLAUDE.md §7 draws.

**Behaviour, not implementation.** Nothing asserts a SQL shape or a call count;
each test states something a customer would notice.
"""

from collections.abc import AsyncIterator
from typing import Any
from uuid import UUID, uuid4

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from apps.api.main import create_app
from signora_platform.settings import Settings
from signora_platform.tests.keys import (
    TEST_AUDIENCE,
    TEST_ISSUER,
    KeyPair,
    generate_key_pair,
    mint_token,
)
from tests.conftest import DEFAULT_APP_DATABASE_URL
from tests.opportunity_engine.test_opportunity_pipeline import _tracked

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
    async with app.router.lifespan_context(app), AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as http:
        yield http


def _auth(key_pair: KeyPair, user_id: UUID) -> dict[str, str]:
    return {"Authorization": f"Bearer {mint_token(key_pair, user_id=user_id)}"}


async def _ask(
    client: AsyncClient, key_pair: KeyPair, user_id: UUID, workspace_id: UUID, account_id: UUID
) -> Any:
    return await client.post(
        f"/workspaces/{workspace_id}/accounts/{account_id}/research",
        headers=_auth(key_pair, user_id),
    )


async def _read(
    client: AsyncClient, key_pair: KeyPair, user_id: UUID, workspace_id: UUID, account_id: UUID
) -> Any:
    return await client.get(
        f"/workspaces/{workspace_id}/accounts/{account_id}/research",
        headers=_auth(key_pair, user_id),
    )


async def _outbox(admin_factory: async_sessionmaker[AsyncSession]) -> list[tuple[str, Any]]:
    async with admin_factory() as session:
        rows = await session.execute(
            text("SELECT event_type, payload FROM outbox_event ORDER BY occurred_at")
        )
        return [(row[0], row[1]) for row in rows]


class TestAskingIsAcceptedAndDispatched:
    async def test_a_member_can_ask_for_research(
        self,
        client: AsyncClient,
        key_pair: KeyPair,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        workspace_id, user_id, entity_id, _ = await _tracked(
            session_factory, admin_session_factory, "northwind"
        )

        response = await _ask(client, key_pair, user_id, workspace_id, entity_id)

        assert response.status_code == 202, response.text
        body = response.json()
        assert body["status"] == "requested"
        assert body["artifact"] is None, "nothing has run yet"

    async def test_the_ask_publishes_the_event_that_will_start_the_work(
        self,
        client: AsyncClient,
        key_pair: KeyPair,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        """**Through the outbox, in the request's own transaction.**

        An event published before its cause committed would be a worker
        researching an account nobody successfully asked about.
        """
        workspace_id, user_id, entity_id, _ = await _tracked(
            session_factory, admin_session_factory, "northwind"
        )

        response = await _ask(client, key_pair, user_id, workspace_id, entity_id)

        events = [e for e in await _outbox(admin_session_factory) if e[0] == "ai_research.requested"]
        assert len(events) == 1
        assert events[0][1]["request_id"] == response.json()["request_id"]
        assert events[0][1]["entity_id"] == str(entity_id)

    async def test_the_response_returns_before_anything_runs(
        self,
        client: AsyncClient,
        key_pair: KeyPair,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        """`202`, not `201`. **Nothing has been produced**, and a status code
        implying otherwise would be the API's own version of a spinner that
        lies."""
        workspace_id, user_id, entity_id, _ = await _tracked(
            session_factory, admin_session_factory, "northwind"
        )

        response = await _ask(client, key_pair, user_id, workspace_id, entity_id)

        assert response.status_code == 202
        assert (await _read(client, key_pair, user_id, workspace_id, entity_id)).json()[
            "artifact"
        ] is None


class TestAskingTwiceDoesNotSpendTwice:
    async def test_the_second_ask_returns_the_first_run(
        self,
        client: AsyncClient,
        key_pair: KeyPair,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        """A seller who clicks again because nothing visibly happened has not
        made a mistake worth an error — *"one is already running"* is an
        answer, and `200` rather than `202` is how a client tells them apart."""
        workspace_id, user_id, entity_id, _ = await _tracked(
            session_factory, admin_session_factory, "northwind"
        )

        first = await _ask(client, key_pair, user_id, workspace_id, entity_id)
        second = await _ask(client, key_pair, user_id, workspace_id, entity_id)

        assert first.status_code == 202
        assert second.status_code == 200
        assert second.json()["request_id"] == first.json()["request_id"]

    async def test_the_second_ask_dispatches_no_second_run(
        self,
        client: AsyncClient,
        key_pair: KeyPair,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        workspace_id, user_id, entity_id, _ = await _tracked(
            session_factory, admin_session_factory, "northwind"
        )

        await _ask(client, key_pair, user_id, workspace_id, entity_id)
        await _ask(client, key_pair, user_id, workspace_id, entity_id)

        events = [e for e in await _outbox(admin_session_factory) if e[0] == "ai_research.requested"]
        assert len(events) == 1, "a second minute-long model call was dispatched"


class TestNothingIsResearchableUntilItIsQualified:
    async def test_an_unknown_account_cannot_be_researched(
        self,
        client: AsyncClient,
        key_pair: KeyPair,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        """`404`, deliberately identical to an account outside the workspace.
        Learning that research *could* be requested here is learning that the
        account exists."""
        workspace_id, user_id, _, _ = await _tracked(
            session_factory, admin_session_factory, "northwind"
        )

        response = await _ask(client, key_pair, user_id, workspace_id, uuid4())

        assert response.status_code == 404, response.text
        assert response.json()["error"]["code"] == "nothing_to_research"


class TestReadingBeforeAnybodyAsked:
    async def test_an_account_nobody_asked_about_is_a_404(
        self,
        client: AsyncClient,
        key_pair: KeyPair,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        workspace_id, user_id, entity_id, _ = await _tracked(
            session_factory, admin_session_factory, "northwind"
        )

        response = await _read(client, key_pair, user_id, workspace_id, entity_id)

        assert response.status_code == 404, response.text


class TestOneWorkspaceCannotReachAnother:
    async def test_a_non_member_asking_gets_404_not_403(
        self,
        client: AsyncClient,
        key_pair: KeyPair,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        """The same rule the workspace itself follows — anything else lets
        workspaces be enumerated one status code at a time."""
        workspace_id, _, entity_id, _ = await _tracked(
            session_factory, admin_session_factory, "northwind"
        )
        outsider = uuid4()

        response = await _ask(client, key_pair, outsider, workspace_id, entity_id)

        assert response.status_code == 404, response.text

    async def test_a_non_member_reading_gets_404(
        self,
        client: AsyncClient,
        key_pair: KeyPair,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        workspace_id, user_id, entity_id, _ = await _tracked(
            session_factory, admin_session_factory, "northwind"
        )
        await _ask(client, key_pair, user_id, workspace_id, entity_id)

        response = await _read(client, key_pair, uuid4(), workspace_id, entity_id)

        assert response.status_code == 404, response.text

    async def test_one_workspaces_request_is_invisible_to_another(
        self,
        client: AsyncClient,
        key_pair: KeyPair,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        first_workspace, first_user, first_entity, _ = await _tracked(
            session_factory, admin_session_factory, "northwind"
        )
        second_workspace, second_user, _, _ = await _tracked(
            session_factory, admin_session_factory, "contoso"
        )
        await _ask(client, key_pair, first_user, first_workspace, first_entity)

        response = await _read(client, key_pair, second_user, second_workspace, first_entity)

        assert response.status_code == 404, response.text


class TestWhoAskedComesFromTheToken:
    async def test_the_requester_is_the_verified_principal(
        self,
        client: AsyncClient,
        key_pair: KeyPair,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        """A request that could name its own requester would let one member
        spend another's name on a model call — and cost attribution is not
        something a later reader can reconstruct."""
        workspace_id, user_id, entity_id, _ = await _tracked(
            session_factory, admin_session_factory, "northwind"
        )

        await _ask(client, key_pair, user_id, workspace_id, entity_id)

        async with admin_session_factory() as session:
            requested_by = await session.scalar(
                text("SELECT requested_by FROM research_request WHERE entity_id = :e"),
                {"e": str(entity_id)},
            )
        assert requested_by == user_id


class TestTheRequestIsAppendOnly:
    async def test_the_application_role_cannot_update_a_request(
        self, session_factory: async_sessionmaker[AsyncSession]
    ) -> None:
        """**The status is the audit trail.** Progress is an append, and no
        `UPDATE` grant exists — so the two cannot disagree."""
        async with session_factory() as session:
            granted = await session.scalar(
                text(
                    "SELECT has_table_privilege('signora_app', 'research_request_state', 'UPDATE')"
                )
            )
        assert granted is False
