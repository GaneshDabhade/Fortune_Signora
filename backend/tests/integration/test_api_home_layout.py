"""Home §10's *Customise* arrangement, over the full stack.

📁 `Fortune Signora Home.dc.html` §10: *"**Customise** — opens the card-order
panel as a drawer."* 📁 `3.2.3`: *"**Card order within a composition is stable
across visits.**"* 📁 `U-05`'s interim: *"**reorder and remove only.**"*

**The layer a unit test cannot reach.** *Stable across visits* is a claim about a
durable row under a real identity, and the three things only a request shows are
the ones that make it true: **the JSONB round-trips**, **one composition's write
leaves the others alone**, and **one person's arrangement is not another's**.
"""

from collections.abc import AsyncIterator
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

LAYOUT = "/workspaces/{workspace}/preferences/home-layout/{composition}"


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
        "/workspaces",
        json={"name": "Acme", "slug": _test_slug("Acme")},
        headers=_auth(key_pair, user_id),
    )
    assert response.status_code == 201, response.text
    return UUID(response.json()["id"])


class TestArrangingHomesCards:
    async def test_nobody_has_arranged_anything_to_begin_with(
        self, client: AsyncClient, key_pair: KeyPair
    ) -> None:
        """⛔ **`{}` is *never customised***, which renders the registry's own
        order — not *customised to nothing*, which would be an empty Home."""
        owner = uuid4()
        workspace = await _workspace(client, key_pair, owner)

        response = await client.get(
            f"/workspaces/{workspace}/preferences", headers=_auth(key_pair, owner)
        )

        assert response.status_code == 200, response.text
        assert response.json()["home_layout"] == {}

    async def test_an_arrangement_survives_the_round_trip(
        self, client: AsyncClient, key_pair: KeyPair
    ) -> None:
        """🔴 **`3.2.3` — *"stable across visits"*.** ⚡ Read back through a
        SEPARATE request, so what is asserted is the durable row rather than the
        response the write happened to compose."""
        owner = uuid4()
        workspace = await _workspace(client, key_pair, owner)

        written = await client.put(
            LAYOUT.format(workspace=workspace, composition="seller"),
            json={"order": ["recents", "needs-you-today"], "hidden": ["meetings"]},
            headers=_auth(key_pair, owner),
        )
        reread = await client.get(
            f"/workspaces/{workspace}/preferences", headers=_auth(key_pair, owner)
        )

        assert written.status_code == 200, written.text
        assert reread.json()["home_layout"]["seller"] == {
            "order": ["recents", "needs-you-today"],
            "hidden": ["meetings"],
        }

    async def test_one_composition_at_a_time(
        self, client: AsyncClient, key_pair: KeyPair
    ) -> None:
        """🔴 **The rule the endpoint exists in this shape for.**

        ⚡ The panel shows the composition the person is looking at. ⛔ **A write
        that replaced the whole map would wipe an arrangement they cannot see**,
        which they would meet the next time they switched.
        """
        owner = uuid4()
        workspace = await _workspace(client, key_pair, owner)

        await client.put(
            LAYOUT.format(workspace=workspace, composition="seller"),
            json={"order": ["recents"], "hidden": []},
            headers=_auth(key_pair, owner),
        )
        await client.put(
            LAYOUT.format(workspace=workspace, composition="executive"),
            json={"order": ["top-risks"], "hidden": []},
            headers=_auth(key_pair, owner),
        )
        reread = await client.get(
            f"/workspaces/{workspace}/preferences", headers=_auth(key_pair, owner)
        )

        layouts = reread.json()["home_layout"]
        assert layouts["seller"]["order"] == ["recents"]
        assert layouts["executive"]["order"] == ["top-risks"]

    async def test_a_composition_home_cannot_render_is_refused(
        self, client: AsyncClient, key_pair: KeyPair
    ) -> None:
        """⛔ **Refused rather than stored.** ⚡ An arrangement filed under a name
        Home does not know is one nobody would ever see."""
        owner = uuid4()
        workspace = await _workspace(client, key_pair, owner)

        response = await client.put(
            LAYOUT.format(workspace=workspace, composition="dashboard"),
            json={"order": [], "hidden": []},
            headers=_auth(key_pair, owner),
        )

        assert response.status_code == 422
        assert response.json()["error"]["code"] == "invalid_home_composition"

    async def test_it_is_per_person(self, client: AsyncClient, key_pair: KeyPair) -> None:
        """⛔ **One person's home is not another's.** 📁 The whole control is
        *"this changes your home only"*."""
        owner, colleague = uuid4(), uuid4()
        workspace = await _workspace(client, key_pair, owner)
        added = await client.post(
            f"/workspaces/{workspace}/members",
            json={"user_id": str(colleague), "role": "member"},
            headers=_auth(key_pair, owner),
        )
        assert added.status_code == 201, added.text

        await client.put(
            LAYOUT.format(workspace=workspace, composition="seller"),
            json={"order": ["recents"], "hidden": ["meetings"]},
            headers=_auth(key_pair, owner),
        )
        theirs = await client.get(
            f"/workspaces/{workspace}/preferences", headers=_auth(key_pair, colleague)
        )

        assert theirs.json()["home_layout"] == {}

    async def test_a_card_id_cannot_carry_prose(
        self, client: AsyncClient, key_pair: KeyPair
    ) -> None:
        """⛔ **Bounded at the boundary.** ⚡ The server does not know Home's card
        catalogue — that is the frontend's registry — **so what it validates is
        shape and size**, which is the boundary's own job."""
        owner = uuid4()
        workspace = await _workspace(client, key_pair, owner)

        response = await client.put(
            LAYOUT.format(workspace=workspace, composition="seller"),
            json={"order": ["x" * 200], "hidden": []},
            headers=_auth(key_pair, owner),
        )

        assert response.status_code == 422

    async def test_a_stranger_is_refused(self, client: AsyncClient, key_pair: KeyPair) -> None:
        owner, stranger = uuid4(), uuid4()
        workspace = await _workspace(client, key_pair, owner)

        response = await client.put(
            LAYOUT.format(workspace=workspace, composition="seller"),
            json={"order": [], "hidden": []},
            headers=_auth(key_pair, stranger),
        )

        assert response.status_code == 404
