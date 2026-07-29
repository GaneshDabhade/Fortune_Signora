"""Re-score accounts whose evidence has aged.

**Shelf-life expiry is the one input to this module that arrives without an
event.** A signal simply stops being live when the clock passes
`relevant_until`, and nothing publishes that. Without a sweep, every score
would drift permanently upward and every account would decay into a false
hot state — the most dangerous failure this module could have, because it
is invisible.

The sweep is **deterministic rather than a polling heuristic**. It does not
guess an interval; it reads `valid_until`, a boundary each score derived
from its own evidence. An account is re-scored when — and only when —
something it depends on has demonstrably changed, and the resulting score
explains itself as `EVIDENCE_AGED` rather than as an unexplained drop.

**One workspace per pass, inside an already-scoped session.** Ageing is not
a workspace-scoped *event*, and a cross-tenant sweep looks tempting — but
it cannot be served under forced RLS without a role that bypasses it, and
introducing one to make a background job convenient would void the tenancy
model for every table it touches. Choosing which workspaces to sweep is the
scheduler's job; sweeping one is this module's.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID, uuid4

from modules.buying_score_engine.application.compute import (
    ComputeBuyingScore,
    ComputeBuyingScoreInput,
)
from modules.buying_score_engine.application.ports import BuyingScoreRepository
from modules.buying_score_engine.domain.score import ScoreTrigger
from signora_platform.observability import get_logger

logger = get_logger(__name__)

DEFAULT_BATCH_SIZE = 200
"""How many stale scores one sweep pass claims. Bounded so a long backlog
becomes several short passes rather than one transaction holding a table
open — not a tuning parameter for throughput."""


@dataclass(frozen=True, slots=True)
class SweepResult:
    examined: int
    rescored: int


class SweepStaleScores:
    """One pass over one workspace's scores whose validity has lapsed."""

    def __init__(
        self,
        *,
        repository: BuyingScoreRepository,
        compute: ComputeBuyingScore,
        clock: Callable[[], datetime] = lambda: datetime.now(UTC),
    ) -> None:
        self._repository = repository
        self._compute = compute
        self._clock = clock

    async def execute(
        self, workspace_id: UUID, *, batch_size: int = DEFAULT_BATCH_SIZE
    ) -> SweepResult:
        moment = self._clock()
        stale = await self._repository.stale(workspace_id, moment, limit=batch_size)
        if not stale:
            return SweepResult(examined=0, rescored=0)

        correlation_id = uuid4()
        rescored = 0
        for score in stale:
            result = await self._compute.execute(
                ComputeBuyingScoreInput(
                    workspace_id=workspace_id,
                    entity_id=score.entity_id,
                    trigger=ScoreTrigger.EVIDENCE_AGED,
                ),
                correlation_id=correlation_id,
            )
            if result.changed:
                rescored += 1

        logger.info(
            "stale buying scores swept",
            extra={
                "workspace_id": str(workspace_id),
                "examined": len(stale),
                "rescored": rescored,
                "correlation_id": str(correlation_id),
            },
        )
        return SweepResult(examined=len(stale), rescored=rescored)
