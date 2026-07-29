"""Ports the Opportunity Engine's use cases depend on.

Three, and the split is the milestone's whole point: opportunities and
their state are **workflow** — accumulated, human-authored, and
irreplaceable — while the buying score port reads **derived intelligence**
that can be regenerated at any time. Keeping them apart in the type system
is what stops a rebuild path from ever reaching workflow.
"""

from __future__ import annotations

from typing import Protocol
from uuid import UUID

from modules.buying_score_engine.public import BuyingScore, BuyingScoreExplanation
from modules.opportunity_engine.domain.opportunity import Opportunity, OpportunityState
from modules.opportunity_engine.domain.policy import WorkspaceOpportunityPolicy


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

    async def open_for_entity(
        self, workspace_id: UUID, entity_id: UUID
    ) -> Opportunity | None:
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

    async def for_entity(
        self, workspace_id: UUID, entity_id: UUID
    ) -> tuple[Opportunity, ...]: ...


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

    async def explanation(
        self, workspace_id: UUID, score_id: UUID
    ) -> BuyingScoreExplanation | None: ...
