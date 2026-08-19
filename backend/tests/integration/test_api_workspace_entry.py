"""Home hierarchy 2 — recording an entry, over the full stack.

📁 `Fortune Signora Home.dc.html` hierarchy 2: *"Workspace confirmation strip, if
any. **Four seconds after a resolved entry**, per Entry rule 12. **Absent on the
second entry of the day.**"*

📁 `Fortune Signora Authenticated Entry.dc.html` rule 12: *"Several memberships,
last-used recorded and healthy. Enter the last used. **The workspace strip
confirms which for four seconds.**"*

🔴 **[D-196](../../../docs/DECISION_REGISTER.md) built the mechanism and nothing
called it.** `RecordWorkspaceEntry`, `ForgetWorkspaceEntry` and
`ResolveLastUsedWorkspace` all existed; `last_entered_at` was `NULL` for
everybody, so rule 12 could never fire. **These assert the one thing only a real
request can show: that the write persisted, and that the answer was computed
before it.**
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

ENTRY = "/workspaces/{workspace}/entry"


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


class TestRecordingAnEntry:
    """🔴 **Home hierarchy 2 · Entry rule 12**, over the full stack.

    📁 [D-196](../../../docs/DECISION_REGISTER.md) built the last-used mechanism —
    `RecordWorkspaceEntry`, `ForgetWorkspaceEntry`, `ResolveLastUsedWorkspace` —
    and **nothing ever called it**, so `last_entered_at` was `NULL` for everybody
    and rule 12 could never fire. **This is the caller, and these assert the one
    thing only a request can show: that the write persisted and that the answer
    came from before it.**
    """

    async def test_the_first_entry_says_so(self, client: AsyncClient, key_pair: KeyPair) -> None:
        owner = uuid4()
        workspace = await _workspace(client, key_pair, owner)

        response = await client.post(
            ENTRY.format(workspace=workspace), headers=_auth(key_pair, owner)
        )

        assert response.status_code == 200, response.text
        assert response.json()["first_entry_today"] is True

    async def test_a_second_entry_the_same_day_does_not(
        self, client: AsyncClient, key_pair: KeyPair
    ) -> None:
        """🔴 **The assertion the whole endpoint exists for.**

        ⚡ It also proves the write LANDED: the second call can only answer `False`
        if the first one persisted `last_entered_at`.
        """
        owner = uuid4()
        workspace = await _workspace(client, key_pair, owner)

        first = await client.post(ENTRY.format(workspace=workspace), headers=_auth(key_pair, owner))
        second = await client.post(
            ENTRY.format(workspace=workspace), headers=_auth(key_pair, owner)
        )

        assert first.json()["first_entry_today"] is True
        assert second.json()["first_entry_today"] is False

    async def test_it_is_per_person(self, client: AsyncClient, key_pair: KeyPair) -> None:
        """⛔ **One person entering is not another arriving.** ⚡ Rule 12's strip
        confirms where *you* are, so a colleague's visit must not suppress it."""
        owner, colleague = uuid4(), uuid4()
        workspace = await _workspace(client, key_pair, owner)
        added = await client.post(
            f"/workspaces/{workspace}/members",
            json={"user_id": str(colleague), "role": "member"},
            headers=_auth(key_pair, owner),
        )
        assert added.status_code == 201, added.text

        await client.post(ENTRY.format(workspace=workspace), headers=_auth(key_pair, owner))
        theirs = await client.post(
            ENTRY.format(workspace=workspace), headers=_auth(key_pair, colleague)
        )

        assert theirs.json()["first_entry_today"] is True

    async def test_it_is_per_workspace(self, client: AsyncClient, key_pair: KeyPair) -> None:
        """⛔ **Entering one organization is not entering another.** 📁 D-196's whole
        shape is *"each workspace's row records when this person last entered
        IT"*, rather than one pointer that a second workspace would overwrite."""
        owner = uuid4()
        first_workspace = await _workspace(client, key_pair, owner)
        second_workspace = await _workspace(client, key_pair, owner)

        await client.post(ENTRY.format(workspace=first_workspace), headers=_auth(key_pair, owner))
        other = await client.post(
            ENTRY.format(workspace=second_workspace), headers=_auth(key_pair, owner)
        )

        assert other.json()["first_entry_today"] is True

    async def test_a_stranger_is_refused(self, client: AsyncClient, key_pair: KeyPair) -> None:
        owner, stranger = uuid4(), uuid4()
        workspace = await _workspace(client, key_pair, owner)

        response = await client.post(
            ENTRY.format(workspace=workspace), headers=_auth(key_pair, stranger)
        )

        assert response.status_code == 404


class TestTheRoleChangeNotice:
    """🔴 **Authenticated Entry rule 21**, over the full stack.

    📁 *"Role changed since last session — Home, with a notice naming **what
    changed and by whom**. The composition may differ from yesterday and **that
    must not be silent**."*

    **The layer a unit test cannot reach.** The read joins `membership` twice —
    once to find whose role changed and once to find the address of whoever
    changed it — and 🔴 **the fake cannot exercise a join**.
    """

    async def test_an_ordinary_arrival_says_nothing(
        self, client: AsyncClient, key_pair: KeyPair
    ) -> None:
        owner = uuid4()
        workspace = await _workspace(client, key_pair, owner)

        first = await client.post(ENTRY.format(workspace=workspace), headers=_auth(key_pair, owner))
        second = await client.post(
            ENTRY.format(workspace=workspace), headers=_auth(key_pair, owner)
        )

        assert first.json()["role_change"] is None
        assert second.json()["role_change"] is None

    async def test_a_change_since_the_last_session_is_reported(
        self, client: AsyncClient, key_pair: KeyPair
    ) -> None:
        """🔴 **The whole rule.** ⚡ Enter once, have the role changed, enter
        again — and the second arrival names what changed and who did it."""
        owner, colleague = uuid4(), uuid4()
        workspace = await _workspace(client, key_pair, owner)
        added = await client.post(
            f"/workspaces/{workspace}/members",
            json={"user_id": str(colleague), "role": "member"},
            headers=_auth(key_pair, owner),
        )
        assert added.status_code == 201, added.text
        membership = added.json()["id"]

        # They were here before the change.
        await client.post(ENTRY.format(workspace=workspace), headers=_auth(key_pair, colleague))
        promoted = await client.post(
            f"/workspaces/{workspace}/members/{membership}/role",
            json={"role": "owner"},
            headers=_auth(key_pair, owner),
        )
        assert promoted.status_code == 200, promoted.text
        arrival = await client.post(
            ENTRY.format(workspace=workspace), headers=_auth(key_pair, colleague)
        )

        change = arrival.json()["role_change"]
        assert change is not None, arrival.text
        assert change["previous_role"] == "member"
        assert change["new_role"] == "owner"
        assert change["changed_by"] == str(owner)

    async def test_it_is_reported_once_and_not_again(
        self, client: AsyncClient, key_pair: KeyPair
    ) -> None:
        """⛔ **`last_entered_at` is what makes it once.** ⚡ The arrival that
        reports the change also records itself, so the next arrival is *after* it
        and the change is no longer *since last session*."""
        owner, colleague = uuid4(), uuid4()
        workspace = await _workspace(client, key_pair, owner)
        added = await client.post(
            f"/workspaces/{workspace}/members",
            json={"user_id": str(colleague), "role": "member"},
            headers=_auth(key_pair, owner),
        )
        membership = added.json()["id"]
        await client.post(ENTRY.format(workspace=workspace), headers=_auth(key_pair, colleague))
        await client.post(
            f"/workspaces/{workspace}/members/{membership}/role",
            json={"role": "owner"},
            headers=_auth(key_pair, owner),
        )

        told = await client.post(
            ENTRY.format(workspace=workspace), headers=_auth(key_pair, colleague)
        )
        again = await client.post(
            ENTRY.format(workspace=workspace), headers=_auth(key_pair, colleague)
        )

        assert told.json()["role_change"] is not None
        assert again.json()["role_change"] is None

    async def test_somebody_elses_change_is_not_reported_to_you(
        self, client: AsyncClient, key_pair: KeyPair
    ) -> None:
        """🔴 **The half the join decides.** ⛔ A notice about a colleague's
        promotion, addressed to somebody else, would be the read answering *"what
        changed in this workspace"* when the rule asks *"what changed for you"*.
        """
        owner, colleague, bystander = uuid4(), uuid4(), uuid4()
        workspace = await _workspace(client, key_pair, owner)
        added = await client.post(
            f"/workspaces/{workspace}/members",
            json={"user_id": str(colleague), "role": "member"},
            headers=_auth(key_pair, owner),
        )
        await client.post(
            f"/workspaces/{workspace}/members",
            json={"user_id": str(bystander), "role": "member"},
            headers=_auth(key_pair, owner),
        )
        await client.post(ENTRY.format(workspace=workspace), headers=_auth(key_pair, bystander))
        await client.post(
            f"/workspaces/{workspace}/members/{added.json()['id']}/role",
            json={"role": "owner"},
            headers=_auth(key_pair, owner),
        )

        theirs = await client.post(
            ENTRY.format(workspace=workspace), headers=_auth(key_pair, bystander)
        )

        assert theirs.json()["role_change"] is None

    async def test_somebody_who_has_never_been_here_is_told_nothing(
        self, client: AsyncClient, key_pair: KeyPair
    ) -> None:
        """📁 Rule 21 is *"changed since last session"* — ⚡ **somebody who has had
        no last session has had nothing change since it.** Their role is simply
        their role, and a notice would be the product explaining a history they
        were never part of."""
        owner, colleague = uuid4(), uuid4()
        workspace = await _workspace(client, key_pair, owner)
        added = await client.post(
            f"/workspaces/{workspace}/members",
            json={"user_id": str(colleague), "role": "member"},
            headers=_auth(key_pair, owner),
        )
        await client.post(
            f"/workspaces/{workspace}/members/{added.json()['id']}/role",
            json={"role": "owner"},
            headers=_auth(key_pair, owner),
        )

        first = await client.post(
            ENTRY.format(workspace=workspace), headers=_auth(key_pair, colleague)
        )

        assert first.json()["role_change"] is None
