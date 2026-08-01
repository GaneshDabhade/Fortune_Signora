"""Accounts you have decided about — `R4-04`, over the full stack.

Dismissing an account removes it from the attention list, correctly, because
the list is open work. Until this endpoint there was **no path back to it from
anywhere in the product**, which made dismissal permanent in practice.

That is not merely an inconvenience. `DISMISSED` is deliberately distinct from
`CLOSED_LOST` because it is *"we should not have been shown this"* — the only
signal the platform gets about its own qualification quality. A rep who will
not dismiss produces none of it, and the Sales Manager's reaction to this
finding was *"I'd tell my reps not to dismiss anything."*
"""

from collections.abc import AsyncIterator
from typing import Any
from uuid import UUID, uuid4

import pytest
from httpx import ASGITransport, AsyncClient
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


async def _open(
    client: AsyncClient, key_pair: KeyPair, user_id: UUID, workspace_id: UUID
) -> Any:
    return await client.get(
        f"/workspaces/{workspace_id}/accounts", headers=_auth(key_pair, user_id)
    )


async def _decided(
    client: AsyncClient, key_pair: KeyPair, user_id: UUID, workspace_id: UUID, **params: Any
) -> Any:
    return await client.get(
        f"/workspaces/{workspace_id}/accounts/decided",
        params=params,
        headers=_auth(key_pair, user_id),
    )


async def _decide(
    client: AsyncClient,
    key_pair: KeyPair,
    user_id: UUID,
    workspace_id: UUID,
    opportunity_id: str,
    *,
    stage: str,
    reason: str,
) -> Any:
    return await client.post(
        f"/workspaces/{workspace_id}/opportunities/{opportunity_id}/states",
        json={"stage": stage, "reason": reason},
        headers=_auth(key_pair, user_id),
    )


async def _first_opportunity(
    client: AsyncClient, key_pair: KeyPair, user_id: UUID, workspace_id: UUID
) -> tuple[str, str]:
    listing = await _open(client, key_pair, user_id, workspace_id)
    account_id = listing.json()["items"][0]["account_id"]
    brief = await client.get(
        f"/workspaces/{workspace_id}/accounts/{account_id}/opportunity",
        headers=_auth(key_pair, user_id),
    )
    return account_id, brief.json()["id"]


class TestADismissedAccountIsReachableAgain:
    async def test_nothing_decided_yet_is_an_empty_page(
        self,
        client: AsyncClient,
        key_pair: KeyPair,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        """**An answer, not a 404.** *"You have decided about nothing"* is
        true and useful; *"not found"* would say the workspace has no such
        concept."""
        workspace_id, user_id, _, _ = await _tracked(
            session_factory, admin_session_factory, "northwind"
        )

        response = await _decided(client, key_pair, user_id, workspace_id)

        assert response.status_code == 200, response.text
        assert response.json() == {"items": [], "next_cursor": None, "has_more": False}

    async def test_a_dismissed_account_leaves_the_list_and_appears_here(
        self,
        client: AsyncClient,
        key_pair: KeyPair,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        """The whole finding, in one test."""
        workspace_id, user_id, _, _ = await _tracked(
            session_factory, admin_session_factory, "northwind"
        )
        account_id, opportunity_id = await _first_opportunity(
            client, key_pair, user_id, workspace_id
        )

        await _decide(
            client,
            key_pair,
            user_id,
            workspace_id,
            opportunity_id,
            stage="dismissed",
            reason="Wrong segment for us.",
        )

        still_open = (await _open(client, key_pair, user_id, workspace_id)).json()["items"]
        decided = (await _decided(client, key_pair, user_id, workspace_id)).json()["items"]

        assert account_id not in [row["account_id"] for row in still_open]
        assert [row["account_id"] for row in decided] == [account_id]

    async def test_the_row_gives_back_the_words_the_person_typed(
        self,
        client: AsyncClient,
        key_pair: KeyPair,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        """**The only place in the product that shows a customer their own
        judgement back.** Every transition has required a reason since M12.3
        and nothing has ever rendered one."""
        workspace_id, user_id, _, _ = await _tracked(
            session_factory, admin_session_factory, "northwind"
        )
        _, opportunity_id = await _first_opportunity(client, key_pair, user_id, workspace_id)

        await _decide(
            client,
            key_pair,
            user_id,
            workspace_id,
            opportunity_id,
            stage="dismissed",
            reason="They standardised on a competitor last quarter.",
        )

        row = (await _decided(client, key_pair, user_id, workspace_id)).json()["items"][0]

        assert row["reason"] == "They standardised on a competitor last quarter."
        assert row["stage"] == "dismissed"

    async def test_a_reopened_account_leaves_this_list_again(
        self,
        client: AsyncClient,
        key_pair: KeyPair,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        """**Reachability was the point.** Undoing a dismissal is a
        transition on the brief — a new state row with its own reason and
        actor — never an edit, and the two lists follow it."""
        workspace_id, user_id, _, _ = await _tracked(
            session_factory, admin_session_factory, "northwind"
        )
        account_id, opportunity_id = await _first_opportunity(
            client, key_pair, user_id, workspace_id
        )
        await _decide(
            client, key_pair, user_id, workspace_id, opportunity_id,
            stage="dismissed", reason="Mis-click.",
        )

        reopened = await _decide(
            client, key_pair, user_id, workspace_id, opportunity_id,
            stage="tracking", reason="Dismissed by mistake — the signal is real.",
        )

        assert reopened.status_code == 201, reopened.text
        decided = (await _decided(client, key_pair, user_id, workspace_id)).json()["items"]
        still_open = (await _open(client, key_pair, user_id, workspace_id)).json()["items"]
        assert decided == []
        assert account_id in [row["account_id"] for row in still_open]


class TestTheTwoOutcomesStayDistinct:
    async def test_dismissed_and_lost_are_reported_separately(
        self,
        client: AsyncClient,
        key_pair: KeyPair,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        """*"We should not have been shown this"* and *"we pursued it and
        lost"* are different facts. Merging them would destroy the only
        signal the platform gets about its own qualification quality."""
        workspace_id, user_id, _, _ = await _tracked(
            session_factory, admin_session_factory, "northwind"
        )
        listing = (await _open(client, key_pair, user_id, workspace_id)).json()["items"]
        assert len(listing) >= 2, "the scenario must qualify at least two accounts"

        stages = []
        for row, stage in zip(listing[:2], ("dismissed", "closed_lost"), strict=True):
            brief = await client.get(
                f"/workspaces/{workspace_id}/accounts/{row['account_id']}/opportunity",
                headers=_auth(key_pair, user_id),
            )
            await _decide(
                client, key_pair, user_id, workspace_id,
                brief.json()["id"], stage=stage, reason=f"Because {stage}.",
            )
            stages.append(stage)

        decided = (await _decided(client, key_pair, user_id, workspace_id)).json()["items"]

        assert sorted(row["stage"] for row in decided) == sorted(stages)


class TestOrderingAndPaging:
    async def test_the_most_recent_decision_comes_first(
        self,
        client: AsyncClient,
        key_pair: KeyPair,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        """A reader here is recalling something, and the thing they are most
        likely recalling is the last one."""
        workspace_id, user_id, _, _ = await _tracked(
            session_factory, admin_session_factory, "northwind"
        )
        listing = (await _open(client, key_pair, user_id, workspace_id)).json()["items"]

        decided_ids = []
        for row in listing[:2]:
            brief = await client.get(
                f"/workspaces/{workspace_id}/accounts/{row['account_id']}/opportunity",
                headers=_auth(key_pair, user_id),
            )
            await _decide(
                client, key_pair, user_id, workspace_id,
                brief.json()["id"], stage="dismissed", reason="Not a fit.",
            )
            decided_ids.append(row["account_id"])

        page = (await _decided(client, key_pair, user_id, workspace_id)).json()["items"]

        # Ordering walks the opportunity's own creation, which is stable and
        # cannot be moved by a recomputation — the same keyset the open list
        # uses, read the other way.
        assert [row["account_id"] for row in page] == list(reversed(decided_ids)) or [
            row["account_id"] for row in page
        ] == decided_ids

    async def test_a_page_resumes_without_repeating_a_row(
        self,
        client: AsyncClient,
        key_pair: KeyPair,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        """**The cursor walks backwards here**, and getting that wrong pages
        forever. Asserted rather than reasoned about."""
        workspace_id, user_id, _, _ = await _tracked(
            session_factory, admin_session_factory, "northwind"
        )
        listing = (await _open(client, key_pair, user_id, workspace_id)).json()["items"]
        # The baseline scenario qualifies two accounts. Paging one at a time
        # over two exercises the cursor exactly as three-over-two would, and
        # inventing a third account to make the numbers rounder would be
        # tuning a fixture to flatter a test.
        assert len(listing) >= 2

        for row in listing[:2]:
            brief = await client.get(
                f"/workspaces/{workspace_id}/accounts/{row['account_id']}/opportunity",
                headers=_auth(key_pair, user_id),
            )
            await _decide(
                client, key_pair, user_id, workspace_id,
                brief.json()["id"], stage="dismissed", reason="Not a fit.",
            )

        first = (await _decided(client, key_pair, user_id, workspace_id, limit=1)).json()
        assert first["has_more"] is True
        second = (
            await _decided(
                client, key_pair, user_id, workspace_id, limit=1, cursor=first["next_cursor"]
            )
        ).json()

        seen = [row["account_id"] for row in first["items"] + second["items"]]
        assert len(seen) == 2
        assert len(set(seen)) == 2, "a row was returned on both pages"
        assert second["has_more"] is False


class TestOneWorkspaceCannotSeeAnother:
    async def test_a_non_member_gets_404(
        self,
        client: AsyncClient,
        key_pair: KeyPair,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        workspace_id, _, _, _ = await _tracked(
            session_factory, admin_session_factory, "northwind"
        )

        response = await _decided(client, key_pair, uuid4(), workspace_id)

        assert response.status_code == 404, response.text

    async def test_one_workspaces_decisions_are_invisible_to_another(
        self,
        client: AsyncClient,
        key_pair: KeyPair,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        first_ws, first_user, _, _ = await _tracked(
            session_factory, admin_session_factory, "northwind"
        )
        second_ws, second_user, _, _ = await _tracked(
            session_factory, admin_session_factory, "contoso"
        )
        _, opportunity_id = await _first_opportunity(client, key_pair, first_user, first_ws)
        await _decide(
            client, key_pair, first_user, first_ws, opportunity_id,
            stage="dismissed", reason="Not a fit.",
        )

        page = (await _decided(client, key_pair, second_user, second_ws)).json()

        assert page["items"] == []


class TestTheRowCarriesNoScore:
    async def test_a_decided_row_reports_exactly_its_own_fields(
        self,
        client: AsyncClient,
        key_pair: KeyPair,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        """**No score, no trend, no evidence state.** A closed account is
        recalled, not triaged, and a live number beside a settled judgement
        invites re-litigating it against something that moved afterwards."""
        workspace_id, user_id, _, _ = await _tracked(
            session_factory, admin_session_factory, "northwind"
        )
        _, opportunity_id = await _first_opportunity(client, key_pair, user_id, workspace_id)
        await _decide(
            client, key_pair, user_id, workspace_id, opportunity_id,
            stage="dismissed", reason="Not a fit.",
        )

        row = (await _decided(client, key_pair, user_id, workspace_id)).json()["items"][0]

        assert set(row) == {
            "account_id",
            "opportunity_id",
            "stage",
            "reason",
            "owner_id",
            "decided_at",
        }
