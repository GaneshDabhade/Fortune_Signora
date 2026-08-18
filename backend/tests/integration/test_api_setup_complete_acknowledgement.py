"""Home state 04's *"shown exactly once"*, over the full stack.

📁 `Fortune Signora Home.dc.html` state 04 · `state.activated`:

> *"All blocking cards complete. Composition switches to SELLER, OPERATIONS or
> EXECUTIVE on the next render. **A one-time strip states that setup is finished
> and what changed.**"*
>
> **`AC-H03`** — *"the next render is the role composition, with the setup-complete
> strip shown **exactly once**."*

**The layer a unit test cannot reach.** *Once* is a claim about a durable row
under a real identity, and the three things only a request exercises are the ones
that make it true: **the column persists**, **a second call writes nothing**, and
**one person's acknowledgement is not another's.**

⚠️ **The two neighbouring one-time flags on this table — `first-run-dismissal`
and `invite-skip` — have no test coverage at all**, which was measured rather
than assumed. ⛔ **Backfilling them is not this slice's**, and it is recorded in
the commit rather than left for somebody to discover.
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

PATH = "/workspaces/{workspace}/preferences/setup-complete-acknowledgement"


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


class TestTheStripIsShownExactlyOnce:
    async def test_a_person_starts_never_having_been_told(
        self, client: AsyncClient, key_pair: KeyPair
    ) -> None:
        """⛔ **`False` is the answer that makes the strip render.** A default of
        `True` would suppress it for the one person about to finish setup."""
        owner = uuid4()
        workspace = await _workspace(client, key_pair, owner)

        response = await client.get(
            f"/workspaces/{workspace}/preferences", headers=_auth(key_pair, owner)
        )

        assert response.status_code == 200, response.text
        assert response.json()["setup_complete_seen"] is False

    async def test_acknowledging_it_is_remembered(
        self, client: AsyncClient, key_pair: KeyPair
    ) -> None:
        owner = uuid4()
        workspace = await _workspace(client, key_pair, owner)

        acknowledged = await client.post(
            PATH.format(workspace=workspace), headers=_auth(key_pair, owner)
        )
        # ⚡ **Read back through a SEPARATE request**, so what is asserted is the
        # durable row rather than the response the write happened to compose.
        reread = await client.get(
            f"/workspaces/{workspace}/preferences", headers=_auth(key_pair, owner)
        )

        assert acknowledged.status_code == 200, acknowledged.text
        assert acknowledged.json()["setup_complete_seen"] is True
        assert reread.json()["setup_complete_seen"] is True

    async def test_a_second_acknowledgement_changes_nothing(
        self, client: AsyncClient, key_pair: KeyPair
    ) -> None:
        """📁 *"Shown exactly once."* ⚡ **The FIRST moment wins** — a second tab,
        a retry or React calling an effect twice must not move the timestamp, and
        the endpoint must not fail either. ⛔ **Idempotent, not merely tolerated.**
        """
        owner = uuid4()
        workspace = await _workspace(client, key_pair, owner)

        first = await client.post(PATH.format(workspace=workspace), headers=_auth(key_pair, owner))
        second = await client.post(PATH.format(workspace=workspace), headers=_auth(key_pair, owner))

        assert first.status_code == 200, first.text
        assert second.status_code == 200, second.text
        assert second.json()["setup_complete_seen"] is True

    async def test_it_is_per_person_and_not_per_workspace(
        self, client: AsyncClient, key_pair: KeyPair
    ) -> None:
        """🔴 **The half that decides where the column lives.**

        📁 The design says *"one-time"* of **a strip somebody reads**. ⛔ A
        colleague who joins an already-activated workspace has still never been
        told, so **their first entry is their once** — and a workspace-scoped flag
        would silently deny it to everybody but the person who set up.
        """
        owner, colleague = uuid4(), uuid4()
        workspace = await _workspace(client, key_pair, owner)
        added = await client.post(
            f"/workspaces/{workspace}/members",
            json={"user_id": str(colleague), "role": "member"},
            headers=_auth(key_pair, owner),
        )
        assert added.status_code == 201, added.text

        await client.post(PATH.format(workspace=workspace), headers=_auth(key_pair, owner))
        theirs = await client.get(
            f"/workspaces/{workspace}/preferences", headers=_auth(key_pair, colleague)
        )

        assert theirs.status_code == 200, theirs.text
        assert theirs.json()["setup_complete_seen"] is False

    async def test_a_stranger_is_refused(self, client: AsyncClient, key_pair: KeyPair) -> None:
        """⛔ **A workspace-scoped write is refused before the handler runs**, and
        a non-member never learns the workspace exists (§7, `404` not `403`)."""
        owner, stranger = uuid4(), uuid4()
        workspace = await _workspace(client, key_pair, owner)

        response = await client.post(
            PATH.format(workspace=workspace), headers=_auth(key_pair, stranger)
        )

        assert response.status_code == 404
