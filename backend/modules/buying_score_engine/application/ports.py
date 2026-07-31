"""Ports the Buying Score Engine's use cases depend on.

Two repositories, deliberately separate: scores are **derived** and can be
rebuilt from signals, while workspace scoring models are
**customer-authored** and cannot be regenerated from anything. Conflating
them would invite a rebuild that quietly discards a customer's weighting.
"""

from __future__ import annotations

from datetime import datetime
from typing import Protocol
from uuid import UUID

from modules.buying_score_engine.domain.score import BuyingScore
from modules.buying_score_engine.domain.workspace_model import WorkspaceScoringModel
from modules.signal_engine.public import (
    Signal,
    SignalCatalog,
    SignalExplanation,
    SignalProfile,
    SignalType,
)


class BuyingScoreRepository(Protocol):
    """Persistence for scores. There is deliberately **no update method**:
    a recomputation is a new score naming the one it replaces, which is what
    makes trend a fact about history rather than a guess."""

    async def current(self, workspace_id: UUID, entity_id: UUID) -> BuyingScore | None:
        """The reading no later score replaces."""
        ...

    async def current_for(
        self, workspace_id: UUID, entity_ids: tuple[UUID, ...]
    ) -> dict[UUID, BuyingScore]:
        """The current reading for each of these accounts, in one query.

        The plural exists so a list of accounts costs one round trip rather
        than one per row. Accounts with no current score are absent from the
        mapping rather than present with a null.
        """
        ...

    async def record(self, score: BuyingScore) -> bool:
        """Insert, ignoring an id already present. Ids are derived from the
        configuration and evidence, so recomputing an unchanged situation
        inserts nothing. Returns whether a row was written."""
        ...

    async def by_id(self, workspace_id: UUID, score_id: UUID) -> BuyingScore | None: ...

    async def for_entity(
        self, workspace_id: UUID, entity_id: UUID, *, limit: int | None = None
    ) -> tuple[BuyingScore, ...]:
        """Every reading for this entity, newest first — the audit trail of
        what a customer was shown."""
        ...

    async def stale(
        self, workspace_id: UUID, moment: datetime, *, limit: int
    ) -> tuple[BuyingScore, ...]:
        """Current scores whose stated validity has passed.

        The sweep's whole query. It reads a boundary the evidence itself
        declared rather than polling on an interval somebody guessed, so a
        score is recomputed when — and only when — something it depends on
        has demonstrably changed.

        **Workspace-scoped, like every other read.** Ageing is not a
        workspace-scoped *event*, and an earlier draft had this span every
        tenant — but a cross-workspace query cannot be served under forced
        RLS without a role that bypasses it, and no such role may exist.
        Deciding *which* workspaces to sweep is the scheduler's job; doing
        it for one is this module's.
        """
        ...


class ScoringModelRepository(Protocol):
    """Persistence for customer-authored weighting.

    Immutable and versioned: a new model is a new row naming the one it
    supersedes. An edited model would make every historical score
    unexplainable.
    """

    async def current(self, workspace_id: UUID) -> WorkspaceScoringModel | None:
        """The version nothing supersedes, or None when the workspace has
        configured nothing and the shipped artifact applies."""
        ...

    async def by_version(self, workspace_id: UUID, version: int) -> WorkspaceScoringModel | None:
        """A specific version — what **historical replay** needs to
        reproduce the number a customer was originally shown."""
        ...

    async def save(self, model: WorkspaceScoringModel) -> None: ...


class SignalReader(Protocol):
    """The Signal Engine's read surface, as this module depends on it.

    Declared as a port rather than taking `SignalQueries` concretely, for
    the reason every other boundary here has one: the use case should state
    what it needs — **live hypotheses, their explanations, the profile
    version in force, and the vocabulary** — rather than inherit whatever
    the neighbouring module happens to expose. `SignalQueries` satisfies it
    structurally, and nothing about scoring learns that it is backed by SQL.

    Note what is *not* here: no ranking, no top-N, no score. The Signal
    Engine has none to give, and this module is where the first one is made.
    """

    async def signals(
        self,
        workspace_id: UUID,
        entity_id: UUID,
        *,
        signal_type: SignalType | None = None,
        live_only: bool = True,
        now: datetime | None = None,
    ) -> tuple[Signal, ...]: ...

    async def explanation(
        self, workspace_id: UUID, signal_id: UUID
    ) -> SignalExplanation | None: ...

    async def stored_profile(self, workspace_id: UUID) -> SignalProfile | None: ...

    def catalog(self) -> SignalCatalog: ...
