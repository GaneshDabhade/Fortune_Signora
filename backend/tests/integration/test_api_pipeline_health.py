"""*"How are we actually doing?"* — the Executive Dashboard, over the full stack.

**Every figure below is produced by moving accounts through the product's own
endpoints**, never by writing state rows. That is the point of the test: the
funnel counts what a seller actually did, so if `POST /states` and this
endpoint ever disagree about what happened, one of them is wrong and this
notices.
"""

from collections.abc import AsyncIterator
from typing import Any
from uuid import UUID

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


async def _health(
    client: AsyncClient, key_pair: KeyPair, user_id: UUID, workspace_id: UUID, **params: Any
) -> Any:
    return await client.get(
        f"/workspaces/{workspace_id}/pipeline-health",
        params=params,
        headers=_auth(key_pair, user_id),
    )


async def _first_opportunity(
    client: AsyncClient, key_pair: KeyPair, user_id: UUID, workspace_id: UUID
) -> tuple[str, str]:
    listing = await client.get(
        f"/workspaces/{workspace_id}/accounts", headers=_auth(key_pair, user_id)
    )
    account_id = listing.json()["items"][0]["account_id"]
    brief = await client.get(
        f"/workspaces/{workspace_id}/accounts/{account_id}/opportunity",
        headers=_auth(key_pair, user_id),
    )
    return account_id, brief.json()["id"]


async def _move(
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


def _step(body: Any, from_stage: str, to_stage: str) -> Any:
    return next(
        c
        for c in body["conversions"]
        if c["from_stage"] == from_stage and c["to_stage"] == to_stage
    )


class TestANewWorkspaceIsNotZeroPercent:
    async def test_the_funnel_has_its_shape_before_anything_has_happened(
        self,
        client: AsyncClient,
        key_pair: KeyPair,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        """**The steps are present and their rates are null.**

        A dashboard that rendered *"0% conversion"* on day one would be
        reporting a measurement nobody took, and a CRO would act on it.
        """
        workspace_id, user_id, _, _ = await _tracked(
            session_factory, admin_session_factory, "northwind"
        )

        response = await _health(client, key_pair, user_id, workspace_id)

        assert response.status_code == 200, response.text
        body = response.json()
        assert [(c["from_stage"], c["to_stage"]) for c in body["conversions"]] == [
            ("tracking", "engaged"),
            ("engaged", "closed_won"),
        ]
        # One account is tracked by the fixture, so tracking has an entrant
        # and nothing has advanced. The *second* step has nobody at all.
        assert _step(body, "engaged", "closed_won")["rate"] is None
        assert _step(body, "engaged", "closed_won")["entered"] == 0

    async def test_every_open_stage_appears_even_when_empty(
        self,
        client: AsyncClient,
        key_pair: KeyPair,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        """An absent row and an empty one say different things."""
        workspace_id, user_id, _, _ = await _tracked(
            session_factory, admin_session_factory, "northwind"
        )

        body = (await _health(client, key_pair, user_id, workspace_id)).json()

        assert [a["stage"] for a in body["ageing"]] == ["engaged", "tracking"]
        engaged = next(a for a in body["ageing"] if a["stage"] == "engaged")
        assert engaged["open_count"] == 0
        assert engaged["median_days"] is None


class TestTheFunnelCountsWhatASellerDid:
    async def test_advancing_an_account_moves_it_through_the_funnel(
        self,
        client: AsyncClient,
        key_pair: KeyPair,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        workspace_id, user_id, _, _ = await _tracked(
            session_factory, admin_session_factory, "northwind"
        )
        _, opportunity_id = await _first_opportunity(client, key_pair, user_id, workspace_id)

        moved = await _move(
            client,
            key_pair,
            user_id,
            workspace_id,
            opportunity_id,
            stage="engaged",
            reason="They asked for pricing.",
        )
        assert moved.status_code in (200, 201), moved.text

        body = (await _health(client, key_pair, user_id, workspace_id)).json()

        # **Two accounts qualify from the fixture's scenario**, deterministically,
        # and only one was advanced. Half the funnel moving is a more useful
        # assertion than all of it: a rate of 1.0 would pass even if the
        # denominator were being miscounted.
        first = _step(body, "tracking", "engaged")
        assert first["entered"] == 2
        assert first["advanced"] == 1
        assert first["rate"] == 0.5
        # The advanced account has left tracking; the other is still there.
        tracking = next(a for a in body["ageing"] if a["stage"] == "tracking")
        assert tracking["open_count"] == 1
        engaged = next(a for a in body["ageing"] if a["stage"] == "engaged")
        assert engaged["open_count"] == 1

    async def test_a_won_deal_still_counts_as_having_reached_the_earlier_stages(
        self,
        client: AsyncClient,
        key_pair: KeyPair,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        """**Ever reached, not currently in.**

        Counting current stages would show every successful account as having
        skipped the steps it actually went through.
        """
        workspace_id, user_id, _, _ = await _tracked(
            session_factory, admin_session_factory, "northwind"
        )
        _, opportunity_id = await _first_opportunity(client, key_pair, user_id, workspace_id)
        await _move(
            client, key_pair, user_id, workspace_id, opportunity_id,
            stage="engaged", reason="They asked for pricing.",
        )
        await _move(
            client, key_pair, user_id, workspace_id, opportunity_id,
            stage="closed_won", reason="Signed the order form.",
        )

        body = (await _health(client, key_pair, user_id, workspace_id)).json()

        assert _step(body, "tracking", "engaged")["entered"] == 2
        # The won account is counted at every stage it passed through, even
        # though it is currently in none of them.
        assert _step(body, "engaged", "closed_won")["entered"] == 1
        assert _step(body, "engaged", "closed_won")["advanced"] == 1
        # And it is no longer ageing anywhere, because it is finished.
        assert all(a["open_count"] <= 1 for a in body["ageing"])


class TestMovementCarriesTheReasonSomebodyTyped:
    async def test_a_decision_appears_with_who_made_it_and_why(
        self,
        client: AsyncClient,
        key_pair: KeyPair,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        workspace_id, user_id, _, _ = await _tracked(
            session_factory, admin_session_factory, "northwind"
        )
        account_id, opportunity_id = await _first_opportunity(
            client, key_pair, user_id, workspace_id
        )
        await _move(
            client, key_pair, user_id, workspace_id, opportunity_id,
            stage="engaged", reason="They asked for pricing.",
        )

        body = (await _health(client, key_pair, user_id, workspace_id)).json()

        latest = body["movements"][0]
        assert latest["stage"] == "engaged"
        assert latest["previous_stage"] == "tracking"
        assert latest["reason"] == "They asked for pricing."
        assert latest["actor_id"] == str(user_id)
        assert latest["account_id"] == account_id

    async def test_the_opening_state_names_no_actor_because_signora_opened_it(
        self,
        client: AsyncClient,
        key_pair: KeyPair,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        """**Intelligence suggests; humans commit.** The one machine-authored
        state is visible as such rather than attributed to whoever was
        looking."""
        workspace_id, user_id, _, _ = await _tracked(
            session_factory, admin_session_factory, "northwind"
        )

        # **An explicit `since`, because the fixture opens opportunities at the
        # moment the pipeline question was asked** rather than at wall-clock now
        # — a commitment made against a historical reading did not happen today.
        # The default fortnight is a reading window, not a filter on the data.
        body = (
            await _health(
                client, key_pair, user_id, workspace_id, since="2000-01-01T00:00:00Z"
            )
        ).json()

        opening = body["movements"][0]
        assert opening["stage"] == "tracking"
        assert opening["previous_stage"] is None
        assert opening["actor_id"] is None

    async def test_a_since_that_predates_nothing_returns_nothing(
        self,
        client: AsyncClient,
        key_pair: KeyPair,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        """A quiet fortnight is an answer, and the boundary comes back with it."""
        workspace_id, user_id, _, _ = await _tracked(
            session_factory, admin_session_factory, "northwind"
        )

        body = (
            await _health(
                client, key_pair, user_id, workspace_id, since="2030-01-01T00:00:00Z"
            )
        ).json()

        assert body["movements"] == []
        assert body["movements_since"].startswith("2030-01-01")


class TestOwnersIncludeTheWorkNobodyHas:
    async def test_unassigned_work_is_its_own_row(
        self,
        client: AsyncClient,
        key_pair: KeyPair,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        """**The column most worth looking at**, because nobody is working it."""
        workspace_id, user_id, _, _ = await _tracked(
            session_factory, admin_session_factory, "northwind"
        )

        body = (await _health(client, key_pair, user_id, workspace_id)).json()

        unassigned = [o for o in body["owners"] if o["owner_id"] is None]
        assert len(unassigned) == 1
        # Both qualified accounts, and nobody has picked either of them up.
        assert unassigned[0]["open_count"] == 2
        assert unassigned[0]["won"] == 0


class TestOneWorkspaceNeverSeesAnothersPipeline:
    async def test_a_second_tenants_accounts_are_absent_from_every_section(
        self,
        client: AsyncClient,
        key_pair: KeyPair,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        """Aggregates are the easiest place for a tenancy leak to hide: a
        count carries no id, so a wrong one looks exactly like a right one."""
        mine, my_user, _, _ = await _tracked(
            session_factory, admin_session_factory, "northwind"
        )
        await _tracked(session_factory, admin_session_factory, "contoso")

        body = (
            await _health(
                client, key_pair, my_user, mine, since="2000-01-01T00:00:00Z"
            )
        ).json()

        # Two accounts here, two in the other workspace, and every figure
        # below counts only this one's.
        assert _step(body, "tracking", "engaged")["entered"] == 2
        assert sum(o["open_count"] for o in body["owners"]) == 2
        assert len(body["movements"]) == 2

    async def test_a_non_member_is_told_the_workspace_does_not_exist(
        self,
        client: AsyncClient,
        key_pair: KeyPair,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        """**404, never 403** — a 403 confirms the workspace exists, which is
        how a workspace list gets enumerated."""
        workspace_id, _, _, _ = await _tracked(
            session_factory, admin_session_factory, "northwind"
        )
        _, stranger, _, _ = await _tracked(
            session_factory, admin_session_factory, "contoso"
        )

        response = await _health(client, key_pair, stranger, workspace_id)

        assert response.status_code == 404, response.text
