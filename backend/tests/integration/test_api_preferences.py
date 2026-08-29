"""Two preferences changed at once, over the full stack.

🔴 **[B-280](../../../docs/BUGS.md)'s live defect, found in the browser.** 📁
`profile-journey.spec.ts` sets a text size and a screen-reader verbosity in
quick succession, reloads, and asserts both survived. ⛔ **One of them does
not**, and which one depends on which request commits last.

**The layer a unit test cannot reach.** ⚡ A lost update needs two *requests* —
two sessions, two transactions, overlapping in time. A single-session test
applies one change after another and can never produce it, which is why this
survived a module suite that covers `ChangePreferences` thoroughly.
"""

import asyncio
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

PREFERENCES = "/workspaces/{workspace}/preferences"


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


class TestTwoPreferencesChangedAtOnce:
    async def test_neither_change_is_lost(
        self, client: AsyncClient, key_pair: KeyPair
    ) -> None:
        """🔴 **The defect, and it is a customer-visible one.**

        ⚡ **Six controls changed in quick succession are six `PATCH`es in
        flight** — the panel's own words — **and each one read the row, replaced
        every column, and wrote it back.** ⛔ **So whichever committed last
        carried the state from before its sibling**, and a preference somebody
        had just set was gone on the next reload.

        ⚠️ **Two fields from two different panels**, deliberately: a caller
        cannot batch them, because they are set by two separate controls.
        """
        owner = uuid4()
        workspace = await _workspace(client, key_pair, owner)

        first, second = await asyncio.gather(
            client.patch(
                PREFERENCES.format(workspace=workspace),
                json={"text_size": "125"},
                headers=_auth(key_pair, owner),
            ),
            client.patch(
                PREFERENCES.format(workspace=workspace),
                json={"screen_reader_verbosity": "concise"},
                headers=_auth(key_pair, owner),
            ),
        )

        assert first.status_code == 200, first.text
        assert second.status_code == 200, second.text

        # ⛔ **Read back through a SEPARATE request**, so what is asserted is
        # the durable row rather than the response a write happened to compose.
        reread = await client.get(
            PREFERENCES.format(workspace=workspace), headers=_auth(key_pair, owner)
        )
        settled = reread.json()

        assert settled["text_size"] == "125", (
            "the text size was lost — a concurrent write replaced every column "
            "with the values it had read before that change existed"
        )
        assert settled["screen_reader_verbosity"] == "concise", (
            "the verbosity was lost — same defect, whichever request happened "
            "to commit last"
        )

    async def test_a_change_still_leaves_untouched_fields_alone(
        self, client: AsyncClient, key_pair: KeyPair
    ) -> None:
        """⛔ **The control, and it is what stops the fix being *write only the
        column you were given and nothing else*.**

        ⚡ **`ChangePreferences` is *"apply only what the request actually
        mentioned"*** — so a field somebody set earlier must survive a later
        change to a different one. ⚠️ **Asserted with the two writes SEPARATED
        in time**, which is the case that already worked and must keep working.
        """
        owner = uuid4()
        workspace = await _workspace(client, key_pair, owner)

        await client.patch(
            PREFERENCES.format(workspace=workspace),
            json={"theme": "dark"},
            headers=_auth(key_pair, owner),
        )
        await client.patch(
            PREFERENCES.format(workspace=workspace),
            json={"density": "compact"},
            headers=_auth(key_pair, owner),
        )

        settled = (
            await client.get(
                PREFERENCES.format(workspace=workspace), headers=_auth(key_pair, owner)
            )
        ).json()

        assert settled["theme"] == "dark"
        assert settled["density"] == "compact"
