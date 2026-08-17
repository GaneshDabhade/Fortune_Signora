"""TASK-451 — the saved-view endpoints, through the whole authenticated stack.

**JWT verification · membership verification · RLS context · Casbin · domain ·
PostgreSQL**, as the least-privilege `signora_app` role — which is the only
place the permission model and the `UPDATE`-less table are exercised together.
"""

from collections.abc import AsyncIterator
from typing import Any
from uuid import UUID, uuid4

import pytest
from httpx import ASGITransport, AsyncClient

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
from tests.slugs import test_slug as _test_slug

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


async def _workspace(client: AsyncClient, key_pair: KeyPair, owner: UUID) -> str:
    response = await client.post(
        "/workspaces", json={"name": "Acme", "slug": _test_slug("Acme")}, headers=_auth(key_pair, owner)
    )
    assert response.status_code == 201, response.text
    workspace_id: str = response.json()["id"]
    return workspace_id


async def _member(client: AsyncClient, key_pair: KeyPair, workspace_id: str, owner: UUID) -> UUID:
    """A second person in the workspace, at `member` rather than `owner`."""
    member_id = uuid4()
    response = await client.post(
        f"/workspaces/{workspace_id}/members",
        json={"user_id": str(member_id), "role": "member"},
        headers=_auth(key_pair, owner),
    )
    assert response.status_code == 201, response.text
    return member_id


async def _save(
    client: AsyncClient,
    key_pair: KeyPair,
    workspace_id: str,
    actor: UUID,
    *,
    name: str = "Contested accounts",
    declaration: dict[str, Any] | None = None,
) -> dict[str, Any]:
    response = await client.post(
        f"/workspaces/{workspace_id}/saved-views",
        json={
            "name": name,
            "declaration": {"filter": "contested"} if declaration is None else declaration,
        },
        headers=_auth(key_pair, actor),
    )
    assert response.status_code == 201, response.text
    body: dict[str, Any] = response.json()
    return body


class TestSavingAView:
    async def test_a_member_can_save_a_view_and_it_is_theirs(
        self, client: AsyncClient, key_pair: KeyPair
    ) -> None:
        owner = uuid4()
        workspace_id = await _workspace(client, key_pair, owner)
        member = await _member(client, key_pair, workspace_id, owner)

        view = await _save(client, key_pair, workspace_id, member)

        assert view["created_by"] == str(member)
        assert view["supersedes"] is None
        assert view["retired_at"] is None

    async def test_the_author_comes_from_the_token_not_the_body(
        self, client: AsyncClient, key_pair: KeyPair
    ) -> None:
        """An author a caller could supply is an author they would supply
        somebody else's."""
        owner = uuid4()
        workspace_id = await _workspace(client, key_pair, owner)

        response = await client.post(
            f"/workspaces/{workspace_id}/saved-views",
            json={
                "name": "Mine",
                "declaration": {"a": 1},
                "created_by": str(uuid4()),
            },
            headers=_auth(key_pair, owner),
        )

        assert response.status_code == 201
        assert response.json()["created_by"] == str(owner)

    async def test_the_declaration_survives_the_round_trip_unchanged(
        self, client: AsyncClient, key_pair: KeyPair
    ) -> None:
        """D-091: nothing in this module knows what a key means, so a shape it
        has never seen must come back exactly as it went in."""
        owner = uuid4()
        workspace_id = await _workspace(client, key_pair, owner)
        odd: dict[str, Any] = {"unknown": [1, {"deep": None}], "sort": "score desc"}

        view = await _save(client, key_pair, workspace_id, owner, declaration=odd)

        assert view["declaration"] == odd

    async def test_a_nameless_view_is_refused_with_a_stable_code(
        self, client: AsyncClient, key_pair: KeyPair
    ) -> None:
        owner = uuid4()
        workspace_id = await _workspace(client, key_pair, owner)

        response = await client.post(
            f"/workspaces/{workspace_id}/saved-views",
            json={"name": "   ", "declaration": {"a": 1}},
            headers=_auth(key_pair, owner),
        )

        assert response.status_code == 422
        assert response.json()["error"]["code"] == "invalid_saved_view_name"

    async def test_an_empty_declaration_is_refused(
        self, client: AsyncClient, key_pair: KeyPair
    ) -> None:
        owner = uuid4()
        workspace_id = await _workspace(client, key_pair, owner)

        response = await client.post(
            f"/workspaces/{workspace_id}/saved-views",
            json={"name": "Named", "declaration": {}},
            headers=_auth(key_pair, owner),
        )

        assert response.status_code == 422
        assert response.json()["error"]["code"] == "empty_declaration"


class TestTheSharedReading:
    async def test_a_colleagues_view_appears_in_everybodys_list(
        self, client: AsyncClient, key_pair: KeyPair
    ) -> None:
        """452: *"a shared view looks the same for everybody."* **This is the
        permission-aware part of the listing** — awareness that a view is
        shared, not filtered by author."""
        owner = uuid4()
        workspace_id = await _workspace(client, key_pair, owner)
        member = await _member(client, key_pair, workspace_id, owner)
        await _save(client, key_pair, workspace_id, member, name="Theirs")

        listed = await client.get(
            f"/workspaces/{workspace_id}/saved-views", headers=_auth(key_pair, owner)
        )

        assert listed.status_code == 200
        assert [v["name"] for v in listed.json()["items"]] == ["Theirs"]

    async def test_a_non_member_cannot_see_the_list_at_all(
        self, client: AsyncClient, key_pair: KeyPair
    ) -> None:
        """**404, never 403** — a caller who is not a member gets the same
        answer as for a workspace that does not exist, which is what stops
        workspace ids being enumerable."""
        owner = uuid4()
        workspace_id = await _workspace(client, key_pair, owner)
        await _save(client, key_pair, workspace_id, owner)

        response = await client.get(
            f"/workspaces/{workspace_id}/saved-views", headers=_auth(key_pair, uuid4())
        )

        assert response.status_code == 404

    async def test_one_view_is_fetchable_by_id(
        self, client: AsyncClient, key_pair: KeyPair
    ) -> None:
        owner = uuid4()
        workspace_id = await _workspace(client, key_pair, owner)
        view = await _save(client, key_pair, workspace_id, owner)

        response = await client.get(
            f"/workspaces/{workspace_id}/saved-views/{view['id']}",
            headers=_auth(key_pair, owner),
        )

        assert response.status_code == 200
        assert response.json()["id"] == view["id"]

    async def test_an_unknown_id_is_not_found(self, client: AsyncClient, key_pair: KeyPair) -> None:
        owner = uuid4()
        workspace_id = await _workspace(client, key_pair, owner)

        response = await client.get(
            f"/workspaces/{workspace_id}/saved-views/{uuid4()}",
            headers=_auth(key_pair, owner),
        )

        assert response.status_code == 404
        assert response.json()["error"]["code"] == "saved_view_not_found"

    async def test_another_workspaces_view_is_not_found_rather_than_forbidden(
        self, client: AsyncClient, key_pair: KeyPair
    ) -> None:
        first_owner, second_owner = uuid4(), uuid4()
        mine = await _workspace(client, key_pair, first_owner)
        theirs = await _workspace(client, key_pair, second_owner)
        view = await _save(client, key_pair, mine, first_owner)

        response = await client.get(
            f"/workspaces/{theirs}/saved-views/{view['id']}",
            headers=_auth(key_pair, second_owner),
        )

        assert response.status_code == 404


class TestRevising:
    async def test_a_revision_supersedes_and_leaves_the_original_readable(
        self, client: AsyncClient, key_pair: KeyPair
    ) -> None:
        owner = uuid4()
        workspace_id = await _workspace(client, key_pair, owner)
        first = await _save(client, key_pair, workspace_id, owner)

        response = await client.post(
            f"/workspaces/{workspace_id}/saved-views/{first['id']}/revisions",
            json={"name": "Contested, EMEA"},
            headers=_auth(key_pair, owner),
        )
        original = await client.get(
            f"/workspaces/{workspace_id}/saved-views/{first['id']}",
            headers=_auth(key_pair, owner),
        )

        assert response.status_code == 201
        assert response.json()["supersedes"] == first["id"]
        assert original.status_code == 200
        assert original.json()["name"] == first["name"]

    async def test_the_list_shows_the_revision_and_not_the_original(
        self, client: AsyncClient, key_pair: KeyPair
    ) -> None:
        owner = uuid4()
        workspace_id = await _workspace(client, key_pair, owner)
        first = await _save(client, key_pair, workspace_id, owner)
        revision = await client.post(
            f"/workspaces/{workspace_id}/saved-views/{first['id']}/revisions",
            json={"declaration": {"filter": "all"}},
            headers=_auth(key_pair, owner),
        )

        listed = await client.get(
            f"/workspaces/{workspace_id}/saved-views", headers=_auth(key_pair, owner)
        )

        assert [v["id"] for v in listed.json()["items"]] == [revision.json()["id"]]

    async def test_a_member_may_revise_a_view_they_did_not_write(
        self, client: AsyncClient, key_pair: KeyPair
    ) -> None:
        """**Revising is the same grant as declaring**, because it is the same
        act: writing a question down under your own name."""
        owner = uuid4()
        workspace_id = await _workspace(client, key_pair, owner)
        member = await _member(client, key_pair, workspace_id, owner)
        first = await _save(client, key_pair, workspace_id, owner)

        response = await client.post(
            f"/workspaces/{workspace_id}/saved-views/{first['id']}/revisions",
            json={"name": "Renamed by a colleague"},
            headers=_auth(key_pair, member),
        )

        assert response.status_code == 201
        assert response.json()["created_by"] == str(member)


class TestRetiring:
    async def test_an_owner_retires_a_view_and_it_leaves_the_list(
        self, client: AsyncClient, key_pair: KeyPair
    ) -> None:
        owner = uuid4()
        workspace_id = await _workspace(client, key_pair, owner)
        view = await _save(client, key_pair, workspace_id, owner)

        retired = await client.post(
            f"/workspaces/{workspace_id}/saved-views/{view['id']}/retirement",
            headers=_auth(key_pair, owner),
        )
        listed = await client.get(
            f"/workspaces/{workspace_id}/saved-views", headers=_auth(key_pair, owner)
        )

        assert retired.status_code == 200
        assert retired.json()["retired_at"] is not None
        assert listed.json()["items"] == []

    async def test_a_retired_view_is_still_fetchable(
        self, client: AsyncClient, key_pair: KeyPair
    ) -> None:
        """Retired, never deleted — a view that explained a decision must still
        explain it afterwards."""
        owner = uuid4()
        workspace_id = await _workspace(client, key_pair, owner)
        view = await _save(client, key_pair, workspace_id, owner)
        await client.post(
            f"/workspaces/{workspace_id}/saved-views/{view['id']}/retirement",
            headers=_auth(key_pair, owner),
        )

        response = await client.get(
            f"/workspaces/{workspace_id}/saved-views/{view['id']}",
            headers=_auth(key_pair, owner),
        )

        assert response.status_code == 200
        assert response.json()["retired_at"] is not None

    async def test_a_member_may_not_retire_a_shared_view(
        self, client: AsyncClient, key_pair: KeyPair
    ) -> None:
        """⚡ **The one asymmetry.** Reading and writing are every member's;
        retiring removes a capability *from everybody else*, which is the same
        shape as removing a member and is granted the same way."""
        owner = uuid4()
        workspace_id = await _workspace(client, key_pair, owner)
        member = await _member(client, key_pair, workspace_id, owner)
        view = await _save(client, key_pair, workspace_id, member)

        response = await client.post(
            f"/workspaces/{workspace_id}/saved-views/{view['id']}/retirement",
            headers=_auth(key_pair, member),
        )

        assert response.status_code == 403

    async def test_retiring_twice_conflicts_rather_than_re_stamping(
        self, client: AsyncClient, key_pair: KeyPair
    ) -> None:
        owner = uuid4()
        workspace_id = await _workspace(client, key_pair, owner)
        view = await _save(client, key_pair, workspace_id, owner)
        first = await client.post(
            f"/workspaces/{workspace_id}/saved-views/{view['id']}/retirement",
            headers=_auth(key_pair, owner),
        )

        second = await client.post(
            f"/workspaces/{workspace_id}/saved-views/{view['id']}/retirement",
            headers=_auth(key_pair, owner),
        )
        fetched = await client.get(
            f"/workspaces/{workspace_id}/saved-views/{view['id']}",
            headers=_auth(key_pair, owner),
        )

        assert second.status_code == 409
        assert second.json()["error"]["code"] == "saved_view_already_retired"
        assert fetched.json()["retired_at"] == first.json()["retired_at"]

    async def test_a_retired_view_cannot_be_revived_by_revising_it(
        self, client: AsyncClient, key_pair: KeyPair
    ) -> None:
        owner = uuid4()
        workspace_id = await _workspace(client, key_pair, owner)
        view = await _save(client, key_pair, workspace_id, owner)
        await client.post(
            f"/workspaces/{workspace_id}/saved-views/{view['id']}/retirement",
            headers=_auth(key_pair, owner),
        )

        response = await client.post(
            f"/workspaces/{workspace_id}/saved-views/{view['id']}/revisions",
            json={"name": "Back please"},
            headers=_auth(key_pair, owner),
        )

        assert response.status_code == 409
