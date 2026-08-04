"""The competitor list over the full stack.

**The sixth declaration, and the first that is about a risk.** These exercise
the whole chain a real request traverses — JWT verification, membership
verification, RLS context, Casbin, and PostgreSQL as the least-privileged role.

**Two things are asserted that no sibling asserts**, because they are what this
declaration most needs to keep: that **nothing is announced** — no downstream
module consumes it yet, and an event with no counterparty is a contract with
one side — and that **no response field grades a competitor.**
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
    return await client.get(f"/workspaces/{workspace}/competitors", headers=_auth(key_pair, user))


async def _declare(
    client: AsyncClient,
    key_pair: KeyPair,
    user: UUID,
    workspace: UUID,
    *,
    competitors: list[dict[str, str]],
    expected_version: int,
) -> Any:
    return await client.put(
        f"/workspaces/{workspace}/competitors",
        json={"expected_version": expected_version, "competitors": competitors},
        headers=_auth(key_pair, user),
    )


def _competitor(name: str = "Salesforce") -> dict[str, str]:
    return {"id": str(uuid4()), "name": name}


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
            "competitors": [],
            "updated_at": None,
            "updated_by": None,
        }


class TestDeclaring:
    async def test_a_competitor_survives_the_round_trip(
        self, client: AsyncClient, key_pair: KeyPair
    ) -> None:
        user = uuid4()
        workspace = await _workspace(client, key_pair, user)
        entry = _competitor()

        saved = await _declare(
            client, key_pair, user, workspace, competitors=[entry], expected_version=0
        )
        assert saved.status_code == 200, saved.text

        response = await _read(client, key_pair, user, workspace)
        body = response.json()
        assert body["version"] == 1
        assert body["competitors"] == [entry]
        assert body["updated_by"] == str(user)

    async def test_the_name_is_stored_exactly_as_typed(
        self, client: AsyncClient, key_pair: KeyPair
    ) -> None:
        """Nothing here resolves or normalises a name — that is the Knowledge
        Graph's job, and doing it here would be a second resolver."""
        user = uuid4()
        workspace = await _workspace(client, key_pair, user)
        entry = _competitor("  salesforce.com  ")

        await _declare(client, key_pair, user, workspace, competitors=[entry], expected_version=0)

        body = (await _read(client, key_pair, user, workspace)).json()
        assert body["competitors"][0]["name"] == "  salesforce.com  "

    async def test_declaring_nothing_is_a_statement_and_reads_as_version_one(
        self, client: AsyncClient, key_pair: KeyPair
    ) -> None:
        """*"We do not track competitors"* must be distinguishable from never
        having said anything, which is version 0."""
        user = uuid4()
        workspace = await _workspace(client, key_pair, user)

        await _declare(client, key_pair, user, workspace, competitors=[], expected_version=0)

        body = (await _read(client, key_pair, user, workspace)).json()
        assert (body["version"], body["competitors"]) == (1, [])

    async def test_a_revision_replaces_the_whole_list(
        self, client: AsyncClient, key_pair: KeyPair
    ) -> None:
        user = uuid4()
        workspace = await _workspace(client, key_pair, user)
        await _declare(
            client, key_pair, user, workspace, competitors=[_competitor()], expected_version=0
        )

        replacement = _competitor("HubSpot")
        await _declare(
            client, key_pair, user, workspace, competitors=[replacement], expected_version=1
        )

        body = (await _read(client, key_pair, user, workspace)).json()
        assert (body["version"], body["competitors"]) == (2, [replacement])

    async def test_a_concurrent_edit_is_refused_rather_than_overwritten(
        self, client: AsyncClient, key_pair: KeyPair
    ) -> None:
        user = uuid4()
        workspace = await _workspace(client, key_pair, user)
        await _declare(
            client, key_pair, user, workspace, competitors=[_competitor()], expected_version=0
        )

        stale = await _declare(
            client,
            key_pair,
            user,
            workspace,
            competitors=[_competitor("HubSpot")],
            expected_version=0,
        )

        assert stale.status_code == 409, stale.text

    async def test_two_competitors_sharing_a_name_are_refused(
        self, client: AsyncClient, key_pair: KeyPair
    ) -> None:
        user = uuid4()
        workspace = await _workspace(client, key_pair, user)

        response = await _declare(
            client,
            key_pair,
            user,
            workspace,
            competitors=[_competitor("Salesforce"), _competitor("salesforce")],
            expected_version=0,
        )

        assert response.status_code == 422, response.text


class TestWhatItDoesNotDo:
    async def test_it_announces_nothing(
        self,
        client: AsyncClient,
        key_pair: KeyPair,
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        """**No consumer exists yet, so no event does.**

        The watch list publishes because Provider Platform is listening. This
        one has nobody listening until the `competitor_entry` signal ships, and
        an event with no counterparty is the speculative half-contract the
        roadmap already forbids twice. The event arrives with its consumer.
        """
        user = uuid4()
        workspace = await _workspace(client, key_pair, user)
        await _declare(
            client, key_pair, user, workspace, competitors=[_competitor()], expected_version=0
        )

        async with admin_session_factory() as session:
            rows = (
                await session.execute(
                    text(
                        "SELECT event_type FROM outbox_event "
                        "WHERE workspace_id = :workspace AND event_type LIKE '%competitor%'"
                    ),
                    {"workspace": workspace},
                )
            ).all()
        assert rows == []

    async def test_no_response_field_grades_a_competitor(
        self, client: AsyncClient, key_pair: KeyPair
    ) -> None:
        """`commercial_profile` records and evaluates nobody.

        A weight belongs to the reviewed scoring model, where a diff can argue
        with it — not to a customer's declaration, where nothing reviews it.
        """
        user = uuid4()
        workspace = await _workspace(client, key_pair, user)
        await _declare(
            client, key_pair, user, workspace, competitors=[_competitor()], expected_version=0
        )

        body = (await _read(client, key_pair, user, workspace)).json()
        forbidden = {"threat", "severity", "level", "score", "weight", "tier", "rank", "priority"}
        keys = set(body) | set(body["competitors"][0])
        assert not (keys & forbidden), f"a competitor is being graded: {keys & forbidden}"

    async def test_a_non_member_gets_404_rather_than_403(
        self, client: AsyncClient, key_pair: KeyPair
    ) -> None:
        """A 403 would confirm the workspace exists, which is enumeration."""
        owner = uuid4()
        workspace = await _workspace(client, key_pair, owner)

        response = await _read(client, key_pair, uuid4(), workspace)

        assert response.status_code == 404, response.text
