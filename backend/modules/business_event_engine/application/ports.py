"""Ports the Business Event Engine's use cases depend on.

Protocols only. The SQLAlchemy implementation lives in `infrastructure/`
and is injected at the composition boundary, so rules and the use case can
be tested against fakes without a database (CLAUDE.md §11).
"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime
from typing import Protocol
from uuid import UUID

from modules.business_event_engine.domain.business_event import BusinessEvent
from modules.business_event_engine.domain.taxonomy import BusinessEventType


class BusinessEventRepository(Protocol):
    """Persistence for business events.

    There is deliberately **no update method**. Business history is
    durable: a phenomenon that extends or a conclusion that is corrected
    produces a new event, never an edit.
    """

    async def current_for_entity(
        self, workspace_id: UUID, entity_id: UUID, *, type_key: BusinessEventType
    ) -> tuple[BusinessEvent, ...]:
        """Events of this type that no later event replaces.

        A replaced event is history — what was believed before the
        phenomenon extended — so it is excluded here rather than filtered
        by every caller.
        """
        ...

    async def record(self, events: tuple[BusinessEvent, ...]) -> int:
        """Insert, ignoring any whose id is already present.

        Returns how many were new. Deduplication is a primary-key conflict:
        ids are derived from the evidence, so re-detecting over the same
        observations inserts nothing.
        """
        ...

    async def for_entity(
        self,
        workspace_id: UUID,
        entity_id: UUID,
        *,
        type_key: BusinessEventType | None = None,
        since: datetime | None = None,
    ) -> tuple[BusinessEvent, ...]: ...

    async def by_id(self, workspace_id: UUID, event_id: UUID) -> BusinessEvent | None: ...

    async def citing_observations(
        self, workspace_id: UUID, observation_ids: Sequence[UUID]
    ) -> tuple[BusinessEvent, ...]:
        """Events built on any of these observations.

        The query that makes citation worth its cost: when an observation is
        refined, the conclusions resting on it are findable rather than
        silently stale.
        """
        ...
