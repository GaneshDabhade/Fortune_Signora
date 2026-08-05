"""The Opportunity Engine's read surface.

Built around the questions a tracked account has to answer:

1. **What stage is it in, and who holds it?** — the current state
2. **Why does it exist?** — the score that opened it, with its full ledger
3. **Is the evidence still holding up?** — derived, never stored
4. **What happened to it?** — the complete, immutable state history

**Deliberately absent: any recommendation, next action, or message.** Those
belong to the Recommendation Engine and AI Reasoning, and a convenience
method here would answer them where nobody could review the answer.

**Also absent: any stored current score.** `evidence_state` is computed at
read time from the live score. Storing it would cache derived intelligence
in a workflow row — the one thing this module exists not to do — and
recording it as a transition would let a data refresh silently revoke a
human's decision.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID

from modules.buying_score_engine.public import BuyingScore, BuyingScoreExplanation
from modules.opportunity_engine.application.ports import (
    BuyingScoreReader,
    OpportunityPolicyRepository,
    OpportunityRepository,
)
from modules.opportunity_engine.domain.opportunity import (
    OPEN_STAGES,
    EvidenceState,
    Opportunity,
    OpportunityState,
    OwnerScope,
    Stage,
)
from modules.opportunity_engine.domain.pipeline_health import (
    Movement,
    OwnerLoad,
    PipelineHealth,
    StageAgeing,
    funnel,
    stage_ageing,
)
from modules.opportunity_engine.domain.policy import OpportunityPolicy, resolve_policy
from signora_platform.pagination import CursorPosition

DEFAULT_PAGE = 50
"""How many accounts one page of the attention list holds.

A working list, not a report: a seller triages the top of it and pages when
they mean to. Not configurable, because nothing has yet needed a different
number — and a knob with one caller is a knob nobody tuned."""

COOLING_DROP = 10
"""How far commercial attention must fall before the evidence reads as
cooling. A **presentational** boundary, not a qualification one: it changes
what a seller is shown and never what happens to the opportunity. The
threshold that decides *tracking* lives in the policy artifact, where it is
versioned and customer-owned."""


@dataclass(frozen=True, slots=True)
class TrackedOpportunity:
    """An opportunity with everything derivable about it right now."""

    opportunity: Opportunity
    state: OpportunityState
    #: The live score, or `None` when none is current. Read, never stored.
    current_score: BuyingScore | None
    evidence_state: EvidenceState

    @property
    def is_open(self) -> bool:
        return self.state.is_open


@dataclass(frozen=True, slots=True)
class OpportunityExplanation:
    """Everything needed to understand — or challenge — one opportunity.

    **M6 adds one link and re-exposes the rest.** The buying score
    explanation already carries the contribution ledger and one
    `SignalExplanation` per contributing signal, so a caller walks from a
    tracked account to a raw provider payload without writing a join, and
    without this module re-deriving anything.
    """

    opportunity: Opportunity
    #: Complete and in order. **Never rewritten.**
    history: tuple[OpportunityState, ...]
    #: The score that caused it to exist — still readable after being
    #: superseded, because buying scores are immutable.
    originating_score: BuyingScoreExplanation | None
    current_score: BuyingScore | None
    evidence_state: EvidenceState


@dataclass(frozen=True, slots=True)
class OpportunityBrief:
    """One tracked account, as the account brief needs it.

    **Then and now, in one object.** The opportunity records what was true when
    a commitment was made — the score that justified it, whether it was already
    contested, who decided — and `current_score` says what is true today. The
    distance between the two is the single most useful fact on the brief, and
    neither half means much alone.

    Distinct from `OpportunityExplanation`, which carries the *originating
    score's* full signal chain. That is the evidence surface's shape (M12.3);
    this is the workflow's, and loading five layers of signal explanation to
    render a stage badge would be the N+1 of read models.
    """

    opportunity: Opportunity
    state: OpportunityState
    #: Complete and in order, oldest first. **Never rewritten.**
    history: tuple[OpportunityState, ...]
    current_score: BuyingScore | None
    evidence_state: EvidenceState

    @property
    def score_change_since_open(self) -> int | None:
        """How far commercial attention has moved since somebody committed.

        `None` when no score is live — **not zero.** Zero is a reading that has
        not moved; absence is the lack of one, and a brief showing *"no change"*
        for an account whose evidence expired would be stating the opposite of
        what happened.
        """
        if self.current_score is None:
            return None
        return self.current_score.value - self.opportunity.score_at_creation


@dataclass(frozen=True, slots=True)
class AttentionPage:
    """One page of the attention list.

    `has_more` rather than a total: counting every open opportunity on every
    request costs a full scan to answer a question the caller only asks in
    order to decide whether to draw one more button.
    """

    items: tuple[TrackedOpportunity, ...]
    has_more: bool

    #: The keyset position to resume from, or `None` on the last page. Taken
    #: from the **cursor order**, never from the ranked order — the two differ,
    #: and resuming from the ranked last row would skip everything between.
    @property
    def next_position(self) -> CursorPosition | None:
        if not self.has_more or not self.items:
            return None
        last = max(self.items, key=lambda t: (t.opportunity.created_at, t.opportunity.id))
        return CursorPosition(created_at=last.opportunity.created_at, id=last.opportunity.id)


@dataclass(frozen=True, slots=True)
class DecidedAccount:
    """One account somebody finished with, and what they said about it.

    **Not a `TrackedOpportunity`.** That type carries a live score, a trend and
    an evidence state, because an open account is triaged on them. A decided
    one is not triaged at all — it is *recalled* — and the fields that answer
    *"did I mean to do that?"* are the stage, the reason and the moment. A
    shared type would put four live figures on a row nobody scans.
    """

    opportunity: Opportunity
    state: OpportunityState


@dataclass(frozen=True, slots=True)
class DecidedPage:
    """One page of decided accounts, **newest decision first**."""

    items: tuple[DecidedAccount, ...]
    has_more: bool

    @property
    def next_position(self) -> CursorPosition | None:
        if not self.has_more or not self.items:
            return None
        # The **oldest** row on a newest-first page is the position to resume
        # from. Taking the maximum here — as the attention page correctly does
        # for its ascending walk — would page backwards forever.
        last = min(self.items, key=lambda d: (d.opportunity.created_at, d.opportunity.id))
        return CursorPosition(created_at=last.opportunity.created_at, id=last.opportunity.id)


class OpportunityQueries:
    """Read-only. Every method is scoped to one workspace, explicitly."""

    def __init__(
        self,
        *,
        repository: OpportunityRepository,
        policies: OpportunityPolicyRepository,
        scores: BuyingScoreReader,
        artifact: OpportunityPolicy,
    ) -> None:
        self._repository = repository
        self._policies = policies
        self._scores = scores
        self._artifact = artifact

    async def tracked(
        self, workspace_id: UUID, entity_id: UUID, *, now: datetime | None = None
    ) -> TrackedOpportunity | None:
        """The open opportunity for this account, if there is one."""
        opportunity = await self._repository.open_for_entity(workspace_id, entity_id)
        if opportunity is None:
            return None
        state = await self._repository.current_state(workspace_id, opportunity.id)
        if state is None:
            return None

        score = await self._scores.current(workspace_id, entity_id)
        return TrackedOpportunity(
            opportunity=opportunity,
            state=state,
            current_score=score,
            evidence_state=evidence_state(opportunity, score, now or datetime.now(UTC)),
        )

    async def brief(
        self, workspace_id: UUID, entity_id: UUID, *, now: datetime | None = None
    ) -> OpportunityBrief | None:
        """This account's latest opportunity, with everything it records.

        Keyed by **account**, not by opportunity id, because that is what the
        caller has: a seller arrives from a list of companies, and asking them
        to know a workflow record's identifier to read about a company would be
        the data model leaking into the product.

        **A closed opportunity still has a brief** — settled in M12.3, which
        owns both this question and reopening. Until a customer could *make* a
        decision there was nothing to lose by hiding one; once they can, a
        brief that vanished the moment somebody dismissed an account would
        take their own words with it, leave a legal reopening unreachable, and
        read exactly like the product deleting the account they just judged.
        The commitment outlives the score that created it, and the record of it
        outlives the commitment.

        The **open** one wins whenever there is one, so the ordinary path stays
        a single query and cannot be shadowed by history; otherwise the most
        recent generation, which is the one whose outcome a reader is asking
        about. `None` only when this account has never had a commitment at all.
        """
        opportunity = await self._repository.open_for_entity(workspace_id, entity_id)
        if opportunity is None:
            opportunity = max(
                await self._repository.for_entity(workspace_id, entity_id),
                key=lambda previous: previous.generation,
                default=None,
            )
        if opportunity is None:
            return None
        state = await self._repository.current_state(workspace_id, opportunity.id)
        if state is None:
            return None

        score = await self._scores.current(workspace_id, entity_id)
        return OpportunityBrief(
            opportunity=opportunity,
            state=state,
            history=await self._repository.history(workspace_id, opportunity.id),
            current_score=score,
            evidence_state=evidence_state(opportunity, score, now or datetime.now(UTC)),
        )

    async def attention_list(
        self,
        workspace_id: UUID,
        *,
        after: CursorPosition | None = None,
        limit: int = DEFAULT_PAGE,
        scope: OwnerScope = OwnerScope.ALL,
        #: Required when `scope` is `MINE`, and refused otherwise — *mine* is
        #: meaningless without knowing whose.
        viewer_id: UUID | None = None,
        now: datetime | None = None,
    ) -> AttentionPage:
        """Open opportunities for this workspace, **ordered by attention**.

        The question a seller opens Signora to ask — *which accounts should I
        work on today* — and the first read surface in this module that is not
        about a single account.

        **Ranked by the live score, never by the score that opened the
        opportunity.** `score_at_creation` is a fact about the past; a seller
        ordering their day by it would be working yesterday's list. Accounts
        whose evidence has gone stale carry no live score and sort last: they
        still appear, because an opportunity outlives the score that created
        it and hiding one would be this module deciding a human's workload.

        **Ordering is applied over the page, not in the page query**, and the
        distinction is load-bearing. The cursor walks a stable identifier, so
        a recomputation between two requests cannot make a row skip or repeat;
        if the sort key were the live score, it could do both.
        """
        if scope is OwnerScope.MINE and viewer_id is None:
            raise ValueError("scope 'mine' needs a viewer; there is no *mine* without a *me*.")
        moment = now or datetime.now(UTC)
        # One more than asked for, so *"is there another page"* is answered by
        # what the database returned rather than by a second count query.
        page = await self._repository.open_page(
            workspace_id,
            after=after,
            limit=limit + 1,
            scope=scope,
            viewer_id=viewer_id,
        )
        has_more = len(page) > limit
        page = page[:limit]
        scores = await self._scores.current_for(
            workspace_id, tuple(opportunity.entity_id for opportunity, _ in page)
        )
        tracked = tuple(
            TrackedOpportunity(
                opportunity=opportunity,
                state=state,
                current_score=scores.get(opportunity.entity_id),
                evidence_state=evidence_state(
                    opportunity, scores.get(opportunity.entity_id), moment
                ),
            )
            for opportunity, state in page
        )
        return AttentionPage(
            items=tuple(sorted(tracked, key=_attention, reverse=True)), has_more=has_more
        )

    async def decided_list(
        self,
        workspace_id: UUID,
        *,
        after: CursorPosition | None = None,
        limit: int = DEFAULT_PAGE,
    ) -> DecidedPage:
        """Accounts somebody has finished with (**R4-04**).

        **No score is read.** The attention list ranks by the live score
        because a seller is deciding what to work; nobody ranks a list of
        decisions, and fetching a score to display beside a closed account
        would invite a reader to re-litigate a judgement using a number that
        moved after they made it.

        That also makes this one query where the attention list is seven, which
        is why it is a separate method rather than a flag on that one.
        """
        page = await self._repository.decided_page(workspace_id, after=after, limit=limit + 1)
        has_more = len(page) > limit
        return DecidedPage(
            items=tuple(
                DecidedAccount(opportunity=opportunity, state=state)
                for opportunity, state in page[:limit]
            ),
            has_more=has_more,
        )

    async def explanation(
        self, workspace_id: UUID, opportunity_id: UUID, *, now: datetime | None = None
    ) -> OpportunityExplanation | None:
        opportunity = await self._repository.by_id(workspace_id, opportunity_id)
        if opportunity is None:
            return None

        score = await self._scores.current(workspace_id, opportunity.entity_id)
        return OpportunityExplanation(
            opportunity=opportunity,
            history=await self._repository.history(workspace_id, opportunity_id),
            originating_score=await self._scores.explanation(
                workspace_id, opportunity.originating_buying_score_id
            ),
            current_score=score,
            evidence_state=evidence_state(opportunity, score, now or datetime.now(UTC)),
        )

    async def history(
        self, workspace_id: UUID, opportunity_id: UUID
    ) -> tuple[OpportunityState, ...]:
        """Every state in order — what was decided, by whom, and why."""
        return await self._repository.history(workspace_id, opportunity_id)

    async def for_entity(self, workspace_id: UUID, entity_id: UUID) -> tuple[Opportunity, ...]:
        """Every opportunity this account has had, oldest first."""
        return await self._repository.for_entity(workspace_id, entity_id)

    async def policy(self, workspace_id: UUID) -> tuple[OpportunityPolicy, int]:
        """The qualification policy in force, and the version recorded
        against opportunities it qualifies."""
        return resolve_policy(self._artifact, await self._policies.current(workspace_id))

    def artifact(self) -> OpportunityPolicy:
        """Signora's shipped defaults, so the product, analytics,
        documentation and support read one definition rather than
        re-describing it."""
        return self._artifact

    async def pipeline_health(
        self, workspace_id: UUID, *, since: datetime, now: datetime, movement_limit: int = 50
    ) -> PipelineHealth:
        """The Executive Dashboard's four sections, in one request.

        **One request, not four.** Every section is arithmetic over the same
        table, and a screen that opened four connections to render one page
        would be the N+1 §14 forbids, spelt across endpoints instead of rows.

        **`now` and `since` are parameters with no defaults.** Reading the
        clock here would make ageing depend on an input nobody declared, which
        §2 calls an architecture defect — and it would stop the same request
        replaying to the same answer.

        ⚠️ **Four sections, and the fifth is deliberately absent.** *ICP
        coverage, in versus outside* is not returned and is not stubbed with
        zeroes: the predicate that decides the cohorts needs observed
        attributes nothing constructs, and this module may not reach the one
        that could ([C-332](../../../../docs/LANE_COORDINATION.md)). **A zero
        would read as *"no accounts match your ICP"*, which is a different and
        false statement.**
        """
        reach = await self._repository.stage_reach(workspace_id)
        advanced = await self._repository.stage_advance(workspace_id)
        entries = await self._repository.open_stage_entries(workspace_id)
        loads = await self._repository.owner_loads(workspace_id)
        moved = await self._repository.movements_since(
            workspace_id, since, limit=movement_limit
        )

        ageing: list[StageAgeing] = [
            stage_ageing(stage, entries.get(stage, ()), now=now)
            # **Sorted so the shape is stable**, and every open stage appears
            # whether or not anything is sitting in it — an absent row and an
            # empty one say different things, which is TASK-408's ruling
            # applied to a dashboard.
            for stage in sorted(OPEN_STAGES, key=lambda s: s.value)
        ]

        by_owner: dict[UUID | None, dict[str, int]] = {}
        for owner_id, stage, count in loads:
            bucket = by_owner.setdefault(owner_id, {"open": 0, "won": 0, "lost": 0})
            if stage in OPEN_STAGES:
                bucket["open"] += count
            elif stage is Stage.CLOSED_WON:
                bucket["won"] += count
            elif stage is Stage.CLOSED_LOST:
                bucket["lost"] += count
            # `DISMISSED` is counted in none of the three, deliberately. It is
            # a qualification judgement rather than a commercial outcome, and
            # folding it into `lost` would make a rep who triages honestly
            # look like a rep who loses deals.

        owners = tuple(
            OwnerLoad(
                owner_id=owner_id,
                open_count=counts["open"],
                won=counts["won"],
                lost=counts["lost"],
            )
            # Unassigned last: it is a real row and it is not a person, so it
            # sorts apart from the people rather than at an arbitrary position
            # among them.
            for owner_id, counts in sorted(
                by_owner.items(), key=lambda kv: (kv[0] is None, str(kv[0]))
            )
        )

        movements = tuple(
            Movement(
                opportunity_id=opportunity.id,
                entity_id=opportunity.entity_id,
                stage=state.stage,
                previous_stage=previous,
                owner_id=state.owner_id,
                actor_id=state.actor_id,
                reason=state.reason,
                occurred_at=state.occurred_at,
            )
            for opportunity, state, previous in moved
        )

        return PipelineHealth(
            conversions=funnel(reach, advanced),
            ageing=tuple(ageing),
            owners=owners,
            movements=movements,
            movements_since=since,
        )


def evidence_state(
    opportunity: Opportunity, score: BuyingScore | None, moment: datetime
) -> EvidenceState:
    """How the intelligence behind an opportunity is holding up.

    **Derived, never stored, and never a transition.** The seller sees that
    the evidence went cold; Signora does not close the deal for them. A
    buying score is a reading with a stated expiry, an opportunity is a
    commitment, and the two have different clocks.
    """
    if score is None or not score.is_valid_at(moment):
        return EvidenceState.STALE
    if opportunity.score_at_creation - score.value >= COOLING_DROP:
        return EvidenceState.COOLING
    return EvidenceState.CURRENT


def _attention(tracked: TrackedOpportunity) -> tuple[int, int]:
    """How the list is ordered: **live score first, then how contested it is.**

    A contested account — where opposing readings are both live — ranks above
    an uncontested one at the same score, for the reason the Buying Score
    Engine refuses to average them away: *a fought-over account warrants more
    attention, not average attention.*

    An account with no current score sorts to the bottom rather than being
    dropped. Its evidence has gone stale; the commitment has not.
    """
    score = tracked.current_score
    if score is None:
        return (-1, 0)
    return (score.value, 1 if score.contested else 0)
