"""Segments through the API — [TASK-1479](../../../docs/BACKLOG.md) ⓶b.

🔴 **Two things are the subject here and neither is reachable from a unit
test**: **an empty grouping still appears in the panel**, and **`New segment`
answers `201` where `Add tag` answers `200`.**

📁 The second is the design's distinction, not a preference: *Add tag* is a
control meant to be pressed twice, and **`New segment` opens a naming
affordance** — a customer who types a name they already used has made a
mistake worth telling them about.
"""

from __future__ import annotations

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
        "/workspaces", json={"name": "Acme", "slug": _test_slug("Acme")}, headers=_auth(key_pair, user_id)
    )
    assert response.status_code == 201, response.text
    return UUID(response.json()["id"])


async def _create_segment(
    client: AsyncClient, key_pair: KeyPair, user: UUID, workspace: UUID, name: str
) -> Any:
    return await client.post(
        f"/workspaces/{workspace}/account-segments",
        json={"name": name},
        headers=_auth(key_pair, user),
    )


async def _add(
    client: AsyncClient,
    key_pair: KeyPair,
    user: UUID,
    workspace: UUID,
    segment: UUID,
    accounts: list[UUID],
) -> Any:
    return await client.post(
        f"/workspaces/{workspace}/account-segments/{segment}/accounts",
        json={"account_ids": [str(account) for account in accounts]},
        headers=_auth(key_pair, user),
    )


class TestNamingAGrouping:
    async def test_a_new_segment_is_created(
        self, client: AsyncClient, key_pair: KeyPair
    ) -> None:
        user = uuid4()
        workspace = await _workspace(client, key_pair, user)

        response = await _create_segment(
            client, key_pair, user, workspace, "Board reporting set"
        )

        assert response.status_code == 201, response.text
        assert response.json()["name"] == "Board reporting set"

    async def test_a_duplicate_name_is_refused_rather_than_selected(
        self, client: AsyncClient, key_pair: KeyPair
    ) -> None:
        """⚠️ **The contrast with `Add tag`'s `200`, at the boundary.**

        ⛔ **Two customer-facing controls, two different intentions** — and the
        status code is where a caller can tell them apart without reading a
        docstring.
        """
        user = uuid4()
        workspace = await _workspace(client, key_pair, user)
        await _create_segment(client, key_pair, user, workspace, "Board reporting set")

        response = await _create_segment(
            client, key_pair, user, workspace, "board REPORTING set"
        )

        assert response.status_code == 422, response.text
        # 🔴 **The code is pinned, not just the status.** ⛔ Without its own row
        # in the error map this refusal reports `catalog_refused` — **a code
        # naming a document the customer was not editing** — and 422 alone
        # would not have caught it. **This assertion is what found it.**
        assert response.json()["error"]["code"] == "account_segment_refused"

    async def test_renaming_keeps_the_companies_in_it(
        self, client: AsyncClient, key_pair: KeyPair
    ) -> None:
        """⚡ **The whole reason a segment carries an id.**"""
        user = uuid4()
        workspace = await _workspace(client, key_pair, user)
        segment = UUID(
            (await _create_segment(client, key_pair, user, workspace, "Board reporting set"))
            .json()["segment_id"]
        )
        account = uuid4()
        await _add(client, key_pair, user, workspace, segment, [account])

        renamed = await client.patch(
            f"/workspaces/{workspace}/account-segments/{segment}",
            json={"name": "Quarterly pack"},
            headers=_auth(key_pair, user),
        )

        assert renamed.status_code == 200, renamed.text
        panel = (
            await client.get(
                f"/workspaces/{workspace}/account-segments", headers=_auth(key_pair, user)
            )
        ).json()["segments"]
        assert panel[0]["name"] == "Quarterly pack"
        assert panel[0]["account_count"] == 1


class TestThePanelShowsAnEmptyGroupingRatherThanHidingIt:
    async def test_a_segment_nobody_is_in_reports_zero(
        self, client: AsyncClient, key_pair: KeyPair
    ) -> None:
        """🔴 **The state every segment passes through** — between being named
        and being curated. ⛔ **A join would have made it vanish from the
        customer's own panel in exactly the window they are looking at**
        ([P-A](../../../docs/DOMAIN_DISCOVERY_REGISTER.md)), and *"did my
        segment get created?"* would have no visible answer.
        """
        user = uuid4()
        workspace = await _workspace(client, key_pair, user)
        await _create_segment(client, key_pair, user, workspace, "Board reporting set")

        panel = await client.get(
            f"/workspaces/{workspace}/account-segments", headers=_auth(key_pair, user)
        )

        assert panel.status_code == 200, panel.text
        assert panel.json()["segments"] == [
            {
                "segment_id": panel.json()["segments"][0]["segment_id"],
                "name": "Board reporting set",
                "account_count": 0,
            }
        ]

    async def test_a_workspace_with_no_segments_gets_an_empty_list_not_an_error(
        self, client: AsyncClient, key_pair: KeyPair
    ) -> None:
        user = uuid4()
        workspace = await _workspace(client, key_pair, user)

        panel = await client.get(
            f"/workspaces/{workspace}/account-segments", headers=_auth(key_pair, user)
        )

        assert panel.status_code == 200
        assert panel.json()["segments"] == []


class TestAddingCompaniesReportsWhatChanged:
    async def test_it_counts_what_moved_and_what_was_already_there(
        self, client: AsyncClient, key_pair: KeyPair
    ) -> None:
        """⚠️ **Two numbers, because one would have to lie.** *"1 added, 1
        already there"* is checkable against the table in front of them;
        *"2 updated"* is disprovable by looking."""
        user = uuid4()
        workspace = await _workspace(client, key_pair, user)
        segment = UUID(
            (await _create_segment(client, key_pair, user, workspace, "Board reporting set"))
            .json()["segment_id"]
        )
        already, fresh = uuid4(), uuid4()
        await _add(client, key_pair, user, workspace, segment, [already])

        response = await _add(client, key_pair, user, workspace, segment, [already, fresh])

        assert response.status_code == 200, response.text
        assert response.json()["added"] == 1
        assert response.json()["unchanged"] == 1

    async def test_a_segment_that_does_not_exist_is_refused(
        self, client: AsyncClient, key_pair: KeyPair
    ) -> None:
        user = uuid4()
        workspace = await _workspace(client, key_pair, user)

        response = await _add(client, key_pair, user, workspace, uuid4(), [uuid4()])

        assert response.status_code == 422, response.text
        assert response.json()["error"]["code"] == "account_segment_refused"

    async def test_an_empty_selection_is_refused_by_the_schema(
        self, client: AsyncClient, key_pair: KeyPair
    ) -> None:
        """⛔ **422 rather than 400** — the request is malformed, not the
        instruction. ⚡ **A successful no-op would let a broken selection look
        like a completed action.**"""
        user = uuid4()
        workspace = await _workspace(client, key_pair, user)
        segment = UUID(
            (await _create_segment(client, key_pair, user, workspace, "Board reporting set"))
            .json()["segment_id"]
        )

        response = await _add(client, key_pair, user, workspace, segment, [])

        assert response.status_code == 422, response.text


class TestTheCompaniesRead:
    async def test_membership_comes_back_for_the_accounts_asked_about(
        self, client: AsyncClient, key_pair: KeyPair
    ) -> None:
        user = uuid4()
        workspace = await _workspace(client, key_pair, user)
        segment = UUID(
            (await _create_segment(client, key_pair, user, workspace, "Board reporting set"))
            .json()["segment_id"]
        )
        listed, unlisted = uuid4(), uuid4()
        await _add(client, key_pair, user, workspace, segment, [listed])

        response = await client.post(
            f"/workspaces/{workspace}/account-segment-memberships",
            json={"account_ids": [str(listed), str(unlisted)]},
            headers=_auth(key_pair, user),
        )

        assert response.status_code == 200, response.text
        memberships = response.json()["memberships"]
        assert memberships == [
            {"account_id": str(listed), "segment_ids": [str(segment)]}
        ]

    async def test_an_account_in_no_segment_is_absent_rather_than_an_error(
        self, client: AsyncClient, key_pair: KeyPair
    ) -> None:
        """⛔ **Absent, not an empty entry and not a 404.** The screen asked
        about forty accounts and this answers about the ones with something to
        say — **and the caller must not read an absent account as an unread
        one**, which is why the request names its accounts."""
        user = uuid4()
        workspace = await _workspace(client, key_pair, user)

        response = await client.post(
            f"/workspaces/{workspace}/account-segment-memberships",
            json={"account_ids": [str(uuid4())]},
            headers=_auth(key_pair, user),
        )

        assert response.status_code == 200
        assert response.json()["memberships"] == []


class TestProposingABulkAdd:
    async def test_it_answers_202_because_nothing_has_happened_yet(
        self, client: AsyncClient, key_pair: KeyPair
    ) -> None:
        """📁 [ADR-0405](../../../docs/architecture/adr/\
0405-an-action-is-approved-before-it-is-effective.md):
        an action is approved before it is effective.

        ⛔ **A `200` would say the companies are in the grouping, and they are
        not** — somebody still has to approve it.
        """
        user = uuid4()
        workspace = await _workspace(client, key_pair, user)
        segment = UUID(
            (await _create_segment(client, key_pair, user, workspace, "Board reporting set"))
            .json()["segment_id"]
        )

        response = await client.post(
            f"/workspaces/{workspace}/account-segments/{segment}/batches",
            json={"account_ids": [str(uuid4()), str(uuid4())]},
            headers=_auth(key_pair, user),
        )

        assert response.status_code == 202, response.text
        assert UUID(response.json()["batch_id"])

    async def test_the_proposal_changes_nothing_until_it_is_approved(
        self, client: AsyncClient, key_pair: KeyPair
    ) -> None:
        """🔴 **The assertion that makes the 202 mean something.**"""
        user = uuid4()
        workspace = await _workspace(client, key_pair, user)
        segment = UUID(
            (await _create_segment(client, key_pair, user, workspace, "Board reporting set"))
            .json()["segment_id"]
        )

        await client.post(
            f"/workspaces/{workspace}/account-segments/{segment}/batches",
            json={"account_ids": [str(uuid4())]},
            headers=_auth(key_pair, user),
        )

        panel = (
            await client.get(
                f"/workspaces/{workspace}/account-segments", headers=_auth(key_pair, user)
            )
        ).json()["segments"]
        assert panel[0]["account_count"] == 0


class TestAnotherWorkspaceCannotBeReached:
    async def test_a_non_member_gets_404_and_never_403(
        self, client: AsyncClient, key_pair: KeyPair
    ) -> None:
        """⛔ **404, because a 403 confirms the workspace exists** — the same
        rule every other route in this module follows."""
        owner, stranger = uuid4(), uuid4()
        workspace = await _workspace(client, key_pair, owner)

        response = await client.get(
            f"/workspaces/{workspace}/account-segments", headers=_auth(key_pair, stranger)
        )

        assert response.status_code == 404, response.text
