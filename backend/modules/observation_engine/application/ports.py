"""Ports the Observation Engine's use cases depend on.

Protocols only. The SQLAlchemy implementation lives in `infrastructure/`
and is injected at the composition boundary, so the derivation and the use
case can be tested against fakes without a database (CLAUDE.md §11).
"""

from __future__ import annotations

from datetime import datetime
from typing import Protocol
from uuid import UUID

from modules.observation_engine.domain.observation import Observation
from modules.provider_normalization.public import ClaimAttribute


class ObservationRepository(Protocol):
    """Persistence for observations.

    There is deliberately **no update method**. Immutability is enforced at
    the database by the absent UPDATE grant; not offering the method means
    nobody writes code that would fail at runtime.
    """

    async def current_for_series(
        self, workspace_id: UUID, *, entity_id: UUID, provider: str, attribute: ClaimAttribute
    ) -> tuple[Observation, ...]:
        """Observations for one series that no later observation refines.

        A refined observation is history — it records what was believed
        before a late-arriving claim sharpened the picture — so it is
        excluded here rather than filtered by every caller.
        """
        ...

    async def record(self, observations: tuple[Observation, ...]) -> int:
        """Insert, ignoring any whose id is already present.

        Returns how many were actually new. Deduplication is a primary-key
        conflict rather than a code path: observation ids are derived from
        what they observe, so re-running derivation over the same evidence
        inserts nothing.
        """
        ...

    async def for_entity(
        self,
        workspace_id: UUID,
        entity_id: UUID,
        *,
        attribute: ClaimAttribute | None = None,
        since: datetime | None = None,
    ) -> tuple[Observation, ...]: ...

    async def by_id(self, workspace_id: UUID, observation_id: UUID) -> Observation | None: ...
