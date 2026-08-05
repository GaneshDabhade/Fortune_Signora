"""Ports the Opportunity Engine's use cases depend on.

Three, and the split is the milestone's whole point: opportunities and
their state are **workflow** — accumulated, human-authored, and
irreplaceable — while the buying score port reads **derived intelligence**
that can be regenerated at any time. Keeping them apart in the type system
is what stops a rebuild path from ever reaching workflow.
"""

from __future__ import annotations

from datetime import datetime
from typing import Protocol
from uuid import UUID

from modules.buying_score_engine.public import BuyingScore, BuyingScoreExplanation
from modules.opportunity_engine.domain.opportunity import (
    Opportunity,
    OpportunityState,
    OwnerScope,
    Stage,
)
from modules.opportunity_engine.domain.policy import WorkspaceOpportunityPolicy
from signora_platform.pagination import CursorPosition


class OpportunityRepository(Protocol):
    """Persistence for workflow.

    There is deliberately **no update method** on either the aggregate or
    its state. An opportunity is written once; progress is a new state row.
    Immutability is enforced at the database by the absent `UPDATE` grant
    (migration 0014), and not offering the method here means nobody writes
    code that would fail at runtime.

    There is also **no delete method**, which is a stronger statement than
    it looks: derived tables offer deletion because regeneration is their
    rollback. Workflow has no regeneration, so deletion has no counterpart.
    """

    async def open_for_entity(self, workspace_id: UUID, entity_id: UUID) -> Opportunity | None:
        """The opportunity for this entity that is not in a terminal stage.

        The rule this module enforces is **at most one open opportunity per
        account**; without it, auto-creation would open a new one on every
        qualifying score.
        """
        ...

    async def generations(self, workspace_id: UUID, entity_id: UUID) -> int:
        """How many opportunities this entity has had. The next one's
        `generation`, and half of the unique key that makes two concurrent
        qualifications conflict rather than both succeeding."""
        ...

    async def create(self, opportunity: Opportunity, opening: OpportunityState) -> bool:
        """Write the aggregate and its first state row **in one transaction**.

        An opportunity without a state row would be a workflow object in no
        state at all. Returns `False` when the generation is already taken —
        a concurrent qualification won, and there is nothing to reconcile.
        """
        ...

    async def append(self, state: OpportunityState) -> None:
        """Record a new complete workflow state."""
        ...

    async def open_page(
        self,
        workspace_id: UUID,
        *,
        after: CursorPosition | None,
        limit: int,
        scope: OwnerScope = OwnerScope.ALL,
        viewer_id: UUID | None = None,
    ) -> tuple[tuple[Opportunity, OpportunityState], ...]:
        """One page of open opportunities, each with its current state.

        **The pair, not the aggregate.** Every consumer of a list needs the
        stage and the holder, and fetching the state separately would make a
        page of *n* rows cost *n + 1* queries.

        Keyset on ``(created_at, id)`` — the platform's pagination position,
        reused rather than reinvented. **The cursor deliberately does not walk
        the score**: ordering a page by a live number would let a recomputation
        between two requests skip a row or repeat one. Attention ordering is
        applied above this, over the page, where it cannot corrupt the walk.
        """
        ...

    async def decided_page(
        self, workspace_id: UUID, *, after: CursorPosition | None, limit: int
    ) -> tuple[tuple[Opportunity, OpportunityState], ...]:
        """One page of opportunities in a terminal stage (**R4-04**).

        The half of the workflow the attention list correctly leaves out —
        *"which accounts have I decided about?"* — and a distinct method rather
        than a stage argument on `open_page` because the two differ in more
        than a predicate: this one walks **newest first**, since a decided list
        has no ranking to apply and the question is asked about the most recent
        decision.

        **Reachability is the point.** A dismissal that cannot be revisited is
        permanent in practice, and a rep who will not dismiss produces no
        qualification-quality signal at all — which is the one thing
        `DISMISSED` exists to capture.
        """
        ...

    async def by_id(self, workspace_id: UUID, opportunity_id: UUID) -> Opportunity | None: ...

    async def current_state(
        self, workspace_id: UUID, opportunity_id: UUID
    ) -> OpportunityState | None:
        """The highest sequence — *derived* from the log, never stored
        beside it, so the status and the audit trail cannot disagree."""
        ...

    async def history(
        self, workspace_id: UUID, opportunity_id: UUID
    ) -> tuple[OpportunityState, ...]:
        """Every state in order, oldest first. **Never rewritten.**"""
        ...

    async def for_entity(self, workspace_id: UUID, entity_id: UUID) -> tuple[Opportunity, ...]: ...

    # ── Pipeline health (TASK-438) ──────────────────────────────────────────
    #
    # **Four aggregates, not four page reads.** A dashboard describes a whole
    # workspace, so the counting belongs in the database; pulling every state
    # row across this boundary to count it in Python is the unbounded fetch
    # §14 calls a defect at write time. **What each returns is already
    # reduced**, and the rules that turn it into a figure live in
    # `domain/pipeline_health.py` where they can be read and argued with.

    async def stage_reach(self, workspace_id: UUID) -> dict[Stage, int]:
        """Distinct opportunities that have **ever** reached each stage.

        **Ever, not currently.** A deal that is closed won today also reached
        `TRACKING` and `ENGAGED`, and a funnel counting only current stages
        would show every successful account as having skipped the steps it
        actually went through.
        """
        ...

    async def stage_advance(self, workspace_id: UUID) -> dict[tuple[Stage, Stage], int]:
        """For each ordered pair, opportunities that reached **both**.

        Keyed by the pair rather than derived from `stage_reach`, because
        *"reached `ENGAGED`"* and *"reached `TRACKING` **and then** `ENGAGED`"*
        differ for any opportunity created directly into a later stage — and
        a conversion rate built from two independent totals silently assumes
        they cannot.
        """
        ...

    async def open_stage_entries(self, workspace_id: UUID) -> dict[Stage, tuple[datetime, ...]]:
        """When each currently-open opportunity entered the stage it is in.

        **The entry into the *current* run of that stage**, not the first time
        it ever entered — an account that was closed lost in March and
        reopened yesterday has been in `TRACKING` for one day, and reporting
        five months would put the wrong account at the top of an ageing list.
        """
        ...

    async def owner_loads(self, workspace_id: UUID) -> tuple[tuple[UUID | None, Stage, int], ...]:
        """Current stage counts per owner, unassigned included as `None`."""
        ...

    async def movements_since(
        self, workspace_id: UUID, since: datetime, *, limit: int
    ) -> tuple[tuple[Opportunity, OpportunityState, Stage | None], ...]:
        """State changes after `since`, newest first, with the stage each left.

        **Bounded by `limit`.** *"Everything that happened since January"* is
        an unbounded fetch wearing a date, and a dashboard section that can
        return a million rows is one that will.
        """
        ...


class OpportunityPolicyRepository(Protocol):
    """Persistence for customer-authored qualification settings.

    Immutable and versioned: a new policy is a new row naming the one it
    supersedes. An edited policy would make every historical opportunity
    unexplainable.
    """

    async def current(self, workspace_id: UUID) -> WorkspaceOpportunityPolicy | None: ...

    async def by_version(
        self, workspace_id: UUID, version: int
    ) -> WorkspaceOpportunityPolicy | None: ...

    async def save(self, policy: WorkspaceOpportunityPolicy) -> None: ...


class BuyingScoreReader(Protocol):
    """The Buying Score Engine's read surface, as this module depends on it.

    Declared as a port for the reason every boundary here has one: the use
    case states what it needs rather than inheriting whatever the
    neighbouring module exposes. `BuyingScoreQueries` satisfies it
    structurally.

    **Read-only, and read live.** The Opportunity Engine never stores a
    current score — it cites the one that caused an opportunity to exist and
    asks this port for everything else, so no stale copy of the pipeline's
    output can accumulate in a workflow table.
    """

    async def current(self, workspace_id: UUID, entity_id: UUID) -> BuyingScore | None: ...

    async def current_for(
        self, workspace_id: UUID, entity_ids: tuple[UUID, ...]
    ) -> dict[UUID, BuyingScore]:
        """The plural, for the attention list. Stated on the port rather than
        reached for on the concrete type, so a fake can still stand in — *if a
        fake cannot stand in for a dependency, the dependency was never really
        a boundary.*"""
        ...

    async def explanation(
        self, workspace_id: UUID, score_id: UUID
    ) -> BuyingScoreExplanation | None: ...
