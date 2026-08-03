"""The segments list over the full stack, including the migrated data.

**The screen this serves did not exist in any form.** An ideal customer was
reachable only through the product it belonged to, so *"show me everything
we've said about who buys from us"* had no page.

These exercise the whole chain a real request traverses — JWT verification,
membership verification, RLS context, Casbin, PostgreSQL as the least-privileged
role — and they assert the two sentences the previous model could not hold.
"""

from collections.abc import AsyncIterator
from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from apps.api.main import create_app
from signora_platform.db import tenant_scoped_session
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

NOW = datetime(2026, 8, 2, 12, 0, tzinfo=UTC)


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


async def _segment(
    session_factory: async_sessionmaker[AsyncSession],
    workspace: UUID,
    actor: UUID,
    *,
    name: str,
    products: tuple[UUID, ...],
    state: str = "published",
    created_at: datetime | None = None,
) -> UUID:
    """A published segment, written through the same tables the migration uses.

    **Not a private door**: these are the module's own tables under its own
    RLS, written as the application role. The use case that will replace this
    lands in ICP-02 and this becomes a call to it.
    """
    segment_id, version_id = uuid4(), uuid4()
    when = created_at or NOW
    async with tenant_scoped_session(
        session_factory, workspace_id=workspace, user_id=actor
    ) as session:
        await session.execute(
            text(
                "INSERT INTO icp_segment (id, workspace_id, created_by, updated_by,"
                " created_at, updated_at) VALUES (:i,:w,:a,:a,:t,:t)"
            ),
            {"i": segment_id, "w": workspace, "a": actor, "t": when},
        )
        await session.execute(
            text(
                "INSERT INTO icp_segment_version (id, workspace_id, segment_id, version,"
                " name, criteria, supersedes, created_by, updated_by, created_at, updated_at)"
                " VALUES (:i,:w,:s,1,:n,'{\"industries\":[\"Fintech\"]}'::jsonb,NULL,:a,:a,:t,:t)"
            ),
            {"i": version_id, "w": workspace, "s": segment_id, "n": name, "a": actor, "t": when},
        )
        for product in products:
            await session.execute(
                text(
                    "INSERT INTO icp_segment_product (workspace_id, version_id, product_id)"
                    " VALUES (:w,:v,:p)"
                ),
                {"w": workspace, "v": version_id, "p": product},
            )
        await session.execute(
            text(
                "INSERT INTO icp_segment_state (id, workspace_id, segment_id, sequence,"
                " state, occurred_at, actor_id) VALUES (:i,:w,:s,0,:st,:t,:a)"
            ),
            {"i": uuid4(), "w": workspace, "s": segment_id, "st": state, "t": when, "a": actor},
        )
        await session.commit()
    return segment_id


class TestAWorkspaceThatHasSaidNothing:
    async def test_the_list_is_empty_rather_than_a_404(
        self, client: AsyncClient, key_pair: KeyPair
    ) -> None:
        user = uuid4()
        workspace = await _workspace(client, key_pair, user)

        response = await client.get(
            f"/workspaces/{workspace}/icp-segments", headers=_auth(key_pair, user)
        )

        assert response.status_code == 200, response.text
        assert response.json() == {"items": [], "next_cursor": None, "has_more": False}


class TestTheTwoSentencesTheOldModelRefused:
    async def test_one_segment_buys_several_products(
        self,
        client: AsyncClient,
        key_pair: KeyPair,
        session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        """*"Revenue Cloud + CPQ + Billing, sold together to mid-market
        fintech."* One statement, and it took three rows before."""
        user = uuid4()
        workspace = await _workspace(client, key_pair, user)
        products = (uuid4(), uuid4(), uuid4())
        await _segment(
            session_factory, workspace, user, name="Mid-market Fintech", products=products
        )

        body = (
            await client.get(
                f"/workspaces/{workspace}/icp-segments", headers=_auth(key_pair, user)
            )
        ).json()

        assert len(body["items"]) == 1
        assert set(body["items"][0]["product_ids"]) == {str(p) for p in products}

    async def test_one_product_is_bought_by_several_segments(
        self,
        client: AsyncClient,
        key_pair: KeyPair,
        session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        """*"We sell Revenue Cloud to fintech, and separately to insurers."*
        Refused outright by the previous model's uniqueness rule."""
        user = uuid4()
        workspace = await _workspace(client, key_pair, user)
        product = uuid4()
        await _segment(session_factory, workspace, user, name="Fintech", products=(product,))
        await _segment(session_factory, workspace, user, name="Insurance", products=(product,))

        body = (
            await client.get(
                f"/workspaces/{workspace}/icp-segments", headers=_auth(key_pair, user)
            )
        ).json()

        assert {row["name"] for row in body["items"]} == {"Fintech", "Insurance"}
        assert all(row["product_ids"] == [str(product)] for row in body["items"])


class TestWhatTheListSays:
    async def test_it_carries_what_a_customer_scans_for(
        self,
        client: AsyncClient,
        key_pair: KeyPair,
        session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        user = uuid4()
        workspace = await _workspace(client, key_pair, user)
        await _segment(session_factory, workspace, user, name="UK Insurance", products=(uuid4(),))

        row = (
            await client.get(
                f"/workspaces/{workspace}/icp-segments", headers=_auth(key_pair, user)
            )
        ).json()["items"][0]

        assert set(row) == {
            "id",
            "name",
            "state",
            "version",
            "product_ids",
            "last_changed_at",
            "last_changed_by",
        }
        assert row["name"] == "UK Insurance"
        assert row["state"] == "published"
        assert row["version"] == 1

    async def test_no_bookkeeping_reaches_the_response(
        self,
        client: AsyncClient,
        key_pair: KeyPair,
        session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        """A version id, a transition sequence and a `supersedes` pointer are
        how the module keeps its promises, not something a customer asked."""
        user = uuid4()
        workspace = await _workspace(client, key_pair, user)
        await _segment(session_factory, workspace, user, name="Fintech", products=(uuid4(),))

        row = (
            await client.get(
                f"/workspaces/{workspace}/icp-segments", headers=_auth(key_pair, user)
            )
        ).json()["items"][0]

        assert not set(row) & {"version_id", "supersedes", "sequence", "criteria", "workspace_id"}


class TestArchived:
    async def test_an_archived_segment_is_not_what_who_do_we_sell_to_means(
        self,
        client: AsyncClient,
        key_pair: KeyPair,
        session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        user = uuid4()
        workspace = await _workspace(client, key_pair, user)
        await _segment(session_factory, workspace, user, name="Live", products=(uuid4(),))
        await _segment(
            session_factory, workspace, user, name="Retired", products=(uuid4(),), state="archived"
        )

        body = (
            await client.get(
                f"/workspaces/{workspace}/icp-segments", headers=_auth(key_pair, user)
            )
        ).json()

        assert [row["name"] for row in body["items"]] == ["Live"]

    async def test_but_it_is_never_hidden(
        self,
        client: AsyncClient,
        key_pair: KeyPair,
        session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        """Archiving is not deletion with a nicer word. Everything Signora
        found under a segment was found because of it."""
        user = uuid4()
        workspace = await _workspace(client, key_pair, user)
        await _segment(
            session_factory, workspace, user, name="Retired", products=(uuid4(),), state="archived"
        )

        body = (
            await client.get(
                f"/workspaces/{workspace}/icp-segments?include_archived=true",
                headers=_auth(key_pair, user),
            )
        ).json()

        assert [row["name"] for row in body["items"]] == ["Retired"]
        assert body["items"][0]["state"] == "archived"


class TestPaging:
    async def test_walking_every_page_yields_each_segment_exactly_once(
        self,
        client: AsyncClient,
        key_pair: KeyPair,
        session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        from datetime import timedelta

        user = uuid4()
        workspace = await _workspace(client, key_pair, user)
        for i in range(7):
            await _segment(
                session_factory,
                workspace,
                user,
                name=f"Segment {i}",
                products=(uuid4(),),
                created_at=NOW + timedelta(minutes=i),
            )

        seen: list[str] = []
        cursor: str | None = None
        while True:
            url = f"/workspaces/{workspace}/icp-segments?limit=3"
            if cursor:
                url += f"&cursor={cursor}"
            body = (await client.get(url, headers=_auth(key_pair, user))).json()
            seen.extend(row["id"] for row in body["items"])
            if not body["has_more"]:
                break
            cursor = body["next_cursor"]

        assert len(seen) == 7
        assert len(set(seen)) == 7

    async def test_the_last_page_offers_no_cursor(
        self,
        client: AsyncClient,
        key_pair: KeyPair,
        session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        user = uuid4()
        workspace = await _workspace(client, key_pair, user)
        await _segment(session_factory, workspace, user, name="Only", products=(uuid4(),))

        body = (
            await client.get(
                f"/workspaces/{workspace}/icp-segments", headers=_auth(key_pair, user)
            )
        ).json()

        assert body["has_more"] is False
        assert body["next_cursor"] is None


class TestAuthorization:
    async def test_a_member_may_read_the_segments(
        self, client: AsyncClient, key_pair: KeyPair
    ) -> None:
        owner, member = uuid4(), uuid4()
        workspace = await _workspace(client, key_pair, owner)
        added = await client.post(
            f"/workspaces/{workspace}/members",
            json={"user_id": str(member), "role": "member"},
            headers=_auth(key_pair, owner),
        )
        assert added.status_code in (200, 201), added.text

        response = await client.get(
            f"/workspaces/{workspace}/icp-segments", headers=_auth(key_pair, member)
        )

        assert response.status_code == 200, response.text

    async def test_a_stranger_gets_a_404_rather_than_a_403(
        self, client: AsyncClient, key_pair: KeyPair
    ) -> None:
        owner, stranger = uuid4(), uuid4()
        workspace = await _workspace(client, key_pair, owner)

        response = await client.get(
            f"/workspaces/{workspace}/icp-segments", headers=_auth(key_pair, stranger)
        )

        assert response.status_code == 404, response.text

    async def test_another_organizations_segments_are_invisible(
        self,
        client: AsyncClient,
        key_pair: KeyPair,
        session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        owner, other = uuid4(), uuid4()
        theirs = await _workspace(client, key_pair, owner)
        mine = await _workspace(client, key_pair, other)
        await _segment(session_factory, theirs, owner, name="Theirs", products=(uuid4(),))

        body = (
            await client.get(
                f"/workspaces/{mine}/icp-segments", headers=_auth(key_pair, other)
            )
        ).json()

        assert body["items"] == []
