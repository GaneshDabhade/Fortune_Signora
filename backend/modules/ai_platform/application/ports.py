"""What the AI Platform needs from the world outside it.

Three ports, all narrow, both declared here rather than imported from
anywhere: **this layer knows nothing of the pipeline** (28-ai-platform.md).
An adapter in ``infrastructure/`` satisfies each — which is what keeps the
substrate extractable, testable with fakes alone, and still pure substrate
on the day M9 arrives.
"""

from __future__ import annotations

from typing import Protocol
from uuid import UUID

from modules.ai_platform.domain.evidence import EvidenceSet
from modules.ai_platform.domain.narration import MaterializedNarration
from modules.ai_platform.domain.record import InferenceRecord


class InferenceRecorder(Protocol):
    """Persists what happened on a model call.

    Called on **every** outcome, not only success. A recorder that saw only
    successes could not report the ungrounded rate, which is the number this
    platform most needs about itself.
    """

    async def record(self, record: InferenceRecord) -> None: ...


class ExplanationSource(Protocol):
    """Somewhere an evidence set can be assembled from.

    Declared as a Protocol so this layer never learns what an opportunity or
    a buying score is. The adapter that satisfies it reads
    ``opportunity_engine.public``; that import lives in ``infrastructure/``
    and goes no deeper than a published contract.

    The M5B finding applied forward: *if a fake cannot stand in for a
    dependency, the dependency was never really a boundary.*
    """

    async def evidence_for(self, workspace_id: UUID, entity_id: UUID) -> EvidenceSet | None: ...


class NarrationRepository(Protocol):
    """Stores a materialized narration.

    Offers ``save`` and a read, and deliberately **no update and no delete**.
    A narration is a historical fact: a better explanation is a new row, and
    the absent update is enforced at the database by the missing ``UPDATE``
    grant (migration 0016). The absent delete is the weaker statement — a
    workspace must stay erasable — it simply is not this port's job.
    """

    async def save(self, narration: MaterializedNarration) -> None: ...

    async def latest_for(
        self, workspace_id: UUID, subject_id: UUID
    ) -> MaterializedNarration | None: ...
