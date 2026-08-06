"""What happened to this organization, as a page — **TASK-443**.

⚠️ **This endpoint shipped with no test of any kind.** `GET
/workspaces/{id}/history` has existed since Team Management and nothing
exercised it, which is how its response shape could be changed from a bare
list to a paged envelope without a single assertion noticing. **That is the
finding this file closes**, and it is why the coverage here is wider than the
pagination the row asked for: a read nobody tests is a read whose contract is
whatever the last edit left behind.

**The facts are real, not seeded.** Every entry below is produced by a
customer doing something through the API — inviting, accepting, changing a
role, leaving — because a history assembled from rows inserted behind the
product would prove the assembly and not the recording (§20e).
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


def _auth(
    key_pair: KeyPair, user_id: UUID, *, email: str = "person@customer.test"
) -> dict[str, str]:
    token = mint_token(key_pair, user_id=user_id, email=email, email_verified=True)
    return {"Authorization": f"Bearer {token}"}


async def _workspace(client: AsyncClient, key_pair: KeyPair, owner: UUID) -> UUID:
    created = await client.post(
        "/workspaces", json={"name": "Acme"}, headers=_auth(key_pair, owner)
    )
    assert created.status_code == 201, created.text
    return UUID(created.json()["id"])


async def _joins(
    client: AsyncClient, key_pair: KeyPair, workspace_id: UUID, owner: UUID, *, role: str
) -> UUID:
    """A second person, by the door a customer actually uses."""
    email = f"{uuid4().hex[:8]}@customer.test"
    invited = await client.post(
        f"/workspaces/{workspace_id}/invitations",
        json={"email": email, "role": role},
        headers=_auth(key_pair, owner),
    )
    assert invited.status_code in (200, 201), invited.text
    joiner = uuid4()
    accepted = await client.post(
        f"/workspaces/{workspace_id}/invitations/accept",
        headers=_auth(key_pair, joiner, email=email),
    )
    assert accepted.status_code == 200, accepted.text
    return joiner


async def _history(
    client: AsyncClient,
    key_pair: KeyPair,
    workspace_id: UUID,
    reader: UUID,
    *,
    limit: int | None = None,
    cursor: str | None = None,
) -> Any:
    params = []
    if limit is not None:
        params.append(f"limit={limit}")
    if cursor:
        params.append(f"cursor={cursor}")
    query = f"?{'&'.join(params)}" if params else ""
    return await client.get(
        f"/workspaces/{workspace_id}/history{query}", headers=_auth(key_pair, reader)
    )


class TestTheHistoryAnswersWhatHappened:
    async def test_a_new_organization_has_its_founding_recorded(
        self, client: AsyncClient, key_pair: KeyPair
    ) -> None:
        """**Not empty.** Creating an organization is itself something that
        happened, and a history that started blank would lose the one event
        every workspace has."""
        owner = uuid4()
        workspace = await _workspace(client, key_pair, owner)

        response = await _history(client, key_pair, workspace, owner)

        assert response.status_code == 200, response.text
        body = response.json()
        assert body["items"], "the founding membership should appear"
        assert {"items", "next_cursor", "has_more"} <= set(body)

    async def test_it_records_an_invitation_and_the_joining(
        self, client: AsyncClient, key_pair: KeyPair
    ) -> None:
        owner = uuid4()
        workspace = await _workspace(client, key_pair, owner)
        await _joins(client, key_pair, workspace, owner, role="member")

        items = (await _history(client, key_pair, workspace, owner)).json()["items"]

        kinds = {entry["kind"] for entry in items}
        assert "invited" in kinds
        assert "invitation_accepted" in kinds or "joined" in kinds

    async def test_it_is_newest_first(self, client: AsyncClient, key_pair: KeyPair) -> None:
        owner = uuid4()
        workspace = await _workspace(client, key_pair, owner)
        await _joins(client, key_pair, workspace, owner, role="member")

        items = (await _history(client, key_pair, workspace, owner)).json()["items"]

        moments = [entry["occurred_at"] for entry in items]
        assert moments == sorted(moments, reverse=True)

    async def test_every_entry_carries_the_row_it_came_from(
        self, client: AsyncClient, key_pair: KeyPair
    ) -> None:
        """**`source_id` is what makes the page keyable.** Entries are derived
        rather than stored, so without the originating row there is no stable
        tiebreak when two things happen in the same microsecond."""
        owner = uuid4()
        workspace = await _workspace(client, key_pair, owner)

        items = (await _history(client, key_pair, workspace, owner)).json()["items"]

        assert all(UUID(entry["source_id"]) for entry in items)


class TestItIsPaged:
    async def test_a_page_is_bounded_by_limit(self, client: AsyncClient, key_pair: KeyPair) -> None:
        owner = uuid4()
        workspace = await _workspace(client, key_pair, owner)
        await _joins(client, key_pair, workspace, owner, role="member")

        body = (await _history(client, key_pair, workspace, owner, limit=1)).json()

        assert len(body["items"]) == 1

    async def test_the_cursor_walks_without_repeating_or_dropping(
        self, client: AsyncClient, key_pair: KeyPair
    ) -> None:
        """**The property that makes paging worth having.** A keyset that
        repeated an entry would double-count an audit; one that skipped an
        entry would hide it, which is worse."""
        owner = uuid4()
        workspace = await _workspace(client, key_pair, owner)
        await _joins(client, key_pair, workspace, owner, role="member")
        await _joins(client, key_pair, workspace, owner, role="member")

        whole = (await _history(client, key_pair, workspace, owner)).json()["items"]

        walked: list[Any] = []
        cursor: str | None = None
        for _ in range(20):
            page = (
                await _history(client, key_pair, workspace, owner, limit=1, cursor=cursor)
            ).json()
            walked.extend(page["items"])
            cursor = page["next_cursor"]
            if not page["has_more"]:
                break

        identity = [(e["occurred_at"], e["kind"], e["source_id"]) for e in walked]
        assert identity == [(e["occurred_at"], e["kind"], e["source_id"]) for e in whole]
        assert len(identity) == len(set(identity)), "an entry was repeated across pages"

    async def test_the_last_page_offers_no_cursor(
        self, client: AsyncClient, key_pair: KeyPair
    ) -> None:
        """**`has_more` false and `next_cursor` null travel together.** A
        cursor on the last page invites a request that can only return
        nothing."""
        owner = uuid4()
        workspace = await _workspace(client, key_pair, owner)

        body = (await _history(client, key_pair, workspace, owner, limit=100)).json()

        assert body["has_more"] is False
        assert body["next_cursor"] is None

    async def test_an_unreadable_cursor_is_refused(
        self, client: AsyncClient, key_pair: KeyPair
    ) -> None:
        owner = uuid4()
        workspace = await _workspace(client, key_pair, owner)

        response = await _history(client, key_pair, workspace, owner, cursor="not-a-cursor")

        assert response.status_code in (400, 422), response.text


class TestWhoMaySeeIt:
    async def test_a_member_sees_it_too(self, client: AsyncClient, key_pair: KeyPair) -> None:
        """**Deliberately not owners-only**: *"a history only administrators
        may read is a history that cannot be used to hold administrators
        accountable."*"""
        owner = uuid4()
        workspace = await _workspace(client, key_pair, owner)
        member = await _joins(client, key_pair, workspace, owner, role="member")

        response = await _history(client, key_pair, workspace, member)

        assert response.status_code == 200, response.text
        assert response.json()["items"]

    async def test_a_stranger_gets_404_rather_than_403(
        self, client: AsyncClient, key_pair: KeyPair
    ) -> None:
        """404, never 403 (§7) — a 403 would confirm the workspace exists."""
        owner = uuid4()
        workspace = await _workspace(client, key_pair, owner)

        response = await _history(client, key_pair, workspace, uuid4())

        assert response.status_code == 404, response.text

    async def test_one_organization_never_appears_in_anothers_history(
        self, client: AsyncClient, key_pair: KeyPair
    ) -> None:
        owner_a = uuid4()
        workspace_a = await _workspace(client, key_pair, owner_a)
        await _joins(client, key_pair, workspace_a, owner_a, role="member")

        owner_b = uuid4()
        workspace_b = await _workspace(client, key_pair, owner_b)
        items = (await _history(client, key_pair, workspace_b, owner_b)).json()["items"]

        assert all(entry["kind"] == "joined" for entry in items)
        assert len(items) == 1, "a fresh organization has only its own founding"
