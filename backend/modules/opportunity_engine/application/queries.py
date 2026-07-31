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
    EvidenceState,
    Opportunity,
    OpportunityState,
)
from modules.opportunity_engine.domain.policy import OpportunityPolicy, resolve_policy

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

    async def attention_list(
        self,
        workspace_id: UUID,
        *,
        after: UUID | None = None,
        limit: int = DEFAULT_PAGE,
        now: datetime | None = None,
    ) -> tuple[TrackedOpportunity, ...]:
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
        moment = now or datetime.now(UTC)
        page = await self._repository.open_page(workspace_id, after=after, limit=limit)
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
        return tuple(sorted(tracked, key=_attention, reverse=True))

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

    async def for_entity(
        self, workspace_id: UUID, entity_id: UUID
    ) -> tuple[Opportunity, ...]:
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
