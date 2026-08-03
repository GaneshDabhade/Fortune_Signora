"""*"Which accounts should I work on today?"* — the first list in the product.

M6 answered questions about **one** account. J1 asks the question a seller
actually opens Signora with, and these assert what the answer must be: ordered
by live evidence, stable under pagination, and never quietly shortened.

Ordering is domain behaviour and is tested against fakes. Nothing here calls a
model or reaches a database — the cursor's behaviour against real SQL is proven
by `test_opportunity_pipeline.py`, which runs the whole pipeline.
"""

from __future__ import annotations

from datetime import timedelta
from dataclasses import replace
from uuid import UUID, uuid4

import pytest

from modules.buying_score_engine.public import BuyingScore
from modules.opportunity_engine.application.queries import DEFAULT_PAGE, OpportunityQueries
from modules.opportunity_engine.domain.opportunity import (
    OwnerScope,
    EvidenceState,
    Opportunity,
    OpportunityState,
    Qualification,
    Stage,
)
from modules.opportunity_engine.infrastructure.policy_loader import load_policy
from signora_platform.pagination import CursorPosition
from tests.opportunity_engine.fakes import (
    NOW,
    SELLER,
    WORKSPACE,
    FakeOpportunityRepository,
    FakePolicyRepository,
    make_score,
)


class _Scores:
    """A reader with a score per account, and a record of how it was asked."""

    def __init__(self, scores: dict[UUID, BuyingScore]) -> None:
        self._scores = scores
        self.batches: list[tuple[UUID, ...]] = []
        self.singles = 0

    async def current(self, workspace_id: UUID, entity_id: UUID) -> BuyingScore | None:
        self.singles += 1
        return self._scores.get(entity_id)

    async def current_for(
        self, workspace_id: UUID, entity_ids: tuple[UUID, ...]
    ) -> dict[UUID, BuyingScore]:
        self.batches.append(entity_ids)
        return {e: s for e, s in self._scores.items() if e in entity_ids}

    async def explanation(self, workspace_id: UUID, score_id: UUID) -> None:
        return None


def _opportunity(entity_id: UUID, *, opened_at: int = 50) -> Opportunity:
    return Opportunity(
        id=uuid4(),
        workspace_id=WORKSPACE,
        entity_id=entity_id,
        generation=0,
        originating_buying_score_id=uuid4(),
        score_at_creation=opened_at,
        contested_at_creation=False,
        qualification=Qualification.AUTOMATIC,
        policy_version=0,
        created_at=NOW,
        created_by=SELLER,
    )


def _opening(opportunity: Opportunity) -> OpportunityState:
    return OpportunityState(
        id=uuid4(),
        workspace_id=WORKSPACE,
        opportunity_id=opportunity.id,
        sequence=0,
        stage=Stage.TRACKING,
        owner_id=None,
        actor_id=SELLER,
        reason="qualified automatically",
        occurred_at=NOW,
    )


def _world(
    *scores: int | None, contested: tuple[int, ...] = (), stale: tuple[int, ...] = ()
) -> tuple[OpportunityQueries, FakeOpportunityRepository, _Scores, list[UUID]]:
    """One workspace, one account per score. `None` means no current score."""
    repository = FakeOpportunityRepository()
    entities: list[UUID] = []
    live: dict[UUID, BuyingScore] = {}

    for index, value in enumerate(scores):
        entity = uuid4()
        entities.append(entity)
        opportunity = _opportunity(entity)
        repository.rows.append(opportunity)
        repository.states.append(_opening(opportunity))
        if value is None:
            continue
        # A stale account is one whose score was computed long enough ago that
        # its stated validity has run out — not one edited to expire before it
        # was computed, which the domain rightly refuses.
        live[entity] = make_score(
            value=value,
            contested=index in contested,
            computed_at=NOW - timedelta(days=60) if index in stale else NOW,
        )

    return (
        OpportunityQueries(
            repository=repository,
            policies=FakePolicyRepository(),
            scores=(reader := _Scores(live)),
            artifact=load_policy(),
        ),
        repository,
        reader,
        entities,
    )


class TestTheListAnswersWhichAccountsDeserveAttention:
    async def test_accounts_are_ordered_by_their_live_score(self) -> None:
        queries, _, _, entities = _world(30, 90, 60)

        listed = (await queries.attention_list(WORKSPACE, now=NOW)).items

        assert [t.opportunity.entity_id for t in listed] == [
            entities[1],
            entities[2],
            entities[0],
        ]

    async def test_a_contested_account_outranks_a_quiet_one_at_the_same_score(self) -> None:
        """**The Buying Score Engine's rule, carried into the list.** Opposing
        readings never average the score down — *a fought-over account warrants
        more attention, not average attention* — so at equal value the contested
        one is the one to open first."""
        queries, _, _, entities = _world(70, 70, contested=(1,))

        listed = (await queries.attention_list(WORKSPACE, now=NOW)).items

        assert listed[0].opportunity.entity_id == entities[1]

    async def test_the_score_that_opened_it_does_not_decide_the_order(self) -> None:
        """`score_at_creation` is a fact about the past. A seller ordering
        their day by it would be working yesterday's list."""
        queries, _, _, entities = _world(20, 80)
        # Both were opened at 50; only the live scores differ.
        listed = (await queries.attention_list(WORKSPACE, now=NOW)).items

        assert {t.opportunity.score_at_creation for t in listed} == {50}
        assert listed[0].opportunity.entity_id == entities[1]


class TestNothingIsQuietlyDroppedFromTheList:
    async def test_an_account_whose_evidence_went_stale_still_appears(self) -> None:
        """**An opportunity outlives the score that created it.** Hiding one
        because its evidence expired would be this module deciding a human's
        workload, which is exactly the line M6 drew: intelligence suggests,
        humans commit."""
        queries, _, _, entities = _world(80, None)

        listed = (await queries.attention_list(WORKSPACE, now=NOW)).items

        assert len(listed) == 2
        assert listed[-1].opportunity.entity_id == entities[1]
        assert listed[-1].current_score is None
        assert listed[-1].evidence_state is EvidenceState.STALE

    async def test_a_stale_score_reads_as_stale_rather_than_current(self) -> None:
        queries, _, _, _ = _world(80, stale=(0,))

        (only,) = (await queries.attention_list(WORKSPACE, now=NOW)).items

        assert only.evidence_state is EvidenceState.STALE

    async def test_an_empty_workspace_is_an_empty_list_not_an_error(self) -> None:
        queries, _, _, _ = _world()

        assert (await queries.attention_list(WORKSPACE, now=NOW)).items == ()

    async def test_a_closed_opportunity_never_appears(self) -> None:
        queries, repository, _, entities = _world(90, 40)
        closed = repository.rows[0]
        repository.states.append(
            OpportunityState(
                id=uuid4(),
                workspace_id=WORKSPACE,
                opportunity_id=closed.id,
                sequence=1,
                stage=Stage.CLOSED_LOST,
                owner_id=None,
                actor_id=SELLER,
                reason="no budget this year",
                occurred_at=NOW,
            )
        )

        listed = (await queries.attention_list(WORKSPACE, now=NOW)).items

        assert [t.opportunity.entity_id for t in listed] == [entities[1]]


class TestTheListCostsOneBatchRatherThanOnePerRow:
    async def test_scores_are_fetched_in_a_single_call(self) -> None:
        """**An obvious N+1 is a defect at write time**, not a future
        optimisation (CLAUDE.md §14). A page of fifty accounts must not be
        fifty score queries."""
        queries, _, scores, entities = _world(*range(10, 60, 10))

        await queries.attention_list(WORKSPACE, now=NOW)

        assert len(scores.batches) == 1
        assert set(scores.batches[0]) == set(entities)
        assert scores.singles == 0

    async def test_no_score_query_is_made_for_an_empty_page(self) -> None:
        queries, _, scores, _ = _world()

        await queries.attention_list(WORKSPACE, now=NOW)

        assert scores.batches in ([], [()])


class TestPagingIsStableWhileScoresMove:
    async def test_the_cursor_walks_every_account_exactly_once(self) -> None:
        queries, _, _, entities = _world(*range(5, 55, 5))

        seen: list[UUID] = []
        cursor: CursorPosition | None = None
        while True:
            page = await queries.attention_list(WORKSPACE, after=cursor, limit=3, now=NOW)
            seen.extend(t.opportunity.entity_id for t in page.items)
            cursor = page.next_position
            if cursor is None:
                break

        assert sorted(seen, key=lambda e: e.bytes) == sorted(entities, key=lambda e: e.bytes)
        assert len(seen) == len(set(seen)), "an account appeared on two pages"

    async def test_the_page_is_selected_by_identity_and_only_then_ranked(self) -> None:
        """**The cursor cannot depend on a number that moves.**

        Selecting the page by a live score would let a recomputation between
        two requests skip a row or repeat one. So the page is the lowest
        identifiers, and ranking is applied *over* that page — which is why the
        four rows returned here are the four lowest ids regardless of how they
        happen to score.
        """
        queries, repository, _, _ = _world(*range(10, 110, 10))

        page = (await queries.attention_list(WORKSPACE, limit=4, now=NOW)).items

        lowest = sorted((o.id for o in repository.rows), key=lambda i: i.bytes)[:4]
        assert sorted((t.opportunity.id for t in page), key=lambda i: i.bytes) == lowest

    async def test_within_a_page_the_ranking_still_applies(self) -> None:
        queries, _, _, _ = _world(*range(10, 110, 10))

        page = (await queries.attention_list(WORKSPACE, limit=4, now=NOW)).items
        values = [t.current_score.value for t in page if t.current_score]

        assert values == sorted(values, reverse=True)

    async def test_a_default_page_is_a_working_list_not_a_report(self) -> None:
        assert DEFAULT_PAGE == 50

        queries, _, _, _ = _world(*([50] * 60))

        assert len((await queries.attention_list(WORKSPACE, now=NOW)).items) == DEFAULT_PAGE


@pytest.mark.parametrize("limit", [1, 2, 7])
async def test_every_page_size_returns_at_most_that_many(limit: int) -> None:
    queries, _, _, _ = _world(*range(10, 100, 10))

    assert len((await queries.attention_list(WORKSPACE, limit=limit, now=NOW)).items) <= limit


#: A colleague. Named here because *mine* is only meaningful against a *not
#: mine*, and the fakes module's `SELLER` is the viewer in every other test.
OTHER = UUID("66666666-6666-4666-8666-666666666666")


class TestWhoseWorkTheListShows:
    """**Filtering happens in the page query, never over the page.**

    The list is cursor-paginated, so filtering returned rows would mean *"mine
    on this page"* — correct at twelve accounts and silently a lie at two
    hundred. These assert the semantics rather than the SQL, so the rule
    survives a rewrite of either.
    """

    @staticmethod
    def _held(repository: FakeOpportunityRepository, *owners: UUID | None) -> None:
        """One open opportunity per owner, in the order given."""
        for owner in owners:
            opportunity = _opportunity(uuid4())
            repository.rows.append(opportunity)
            opening = _opening(opportunity)
            repository.states.append(
                replace(opening, owner_id=owner, stage=Stage.ENGAGED)
                if owner is not None
                else opening
            )

    async def test_all_is_the_default_and_shows_everybody_s(self) -> None:
        queries, repository, _, _ = _world()
        self._held(repository, SELLER, None, OTHER)

        page = await queries.attention_list(WORKSPACE)

        assert len(page.items) == 3

    async def test_mine_shows_only_what_i_hold(self) -> None:
        queries, repository, _, _ = _world()
        self._held(repository, SELLER, OTHER, None)

        page = await queries.attention_list(
            WORKSPACE, scope=OwnerScope.MINE, viewer_id=SELLER
        )

        assert [item.state.owner_id for item in page.items] == [SELLER]

    async def test_unassigned_shows_only_what_nobody_holds(self) -> None:
        queries, repository, _, _ = _world()
        self._held(repository, SELLER, None)

        page = await queries.attention_list(WORKSPACE, scope=OwnerScope.UNASSIGNED)

        assert [item.state.owner_id for item in page.items] == [None]

    async def test_a_full_page_of_mine_is_a_full_page(self) -> None:
        # **The defect this design exists to prevent.** Nine accounts held by
        # somebody else, then two of mine. Filtering *after* the query would
        # return a page of nothing while claiming to be a page of ten.
        queries, repository, _, _ = _world()
        self._held(repository, *([OTHER] * 9), SELLER, SELLER)

        page = await queries.attention_list(
            WORKSPACE, scope=OwnerScope.MINE, viewer_id=SELLER, limit=10
        )

        assert len(page.items) == 2
        assert page.has_more is False

    async def test_mine_without_a_viewer_is_refused(self) -> None:
        # There is no *mine* without a *me*, and defaulting to nobody would
        # return an empty list that looks like having no work.
        queries, _, _, _ = _world()

        with pytest.raises(ValueError):
            await queries.attention_list(WORKSPACE, scope=OwnerScope.MINE)
