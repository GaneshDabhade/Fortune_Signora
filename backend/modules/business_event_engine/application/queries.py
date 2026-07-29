"""The Business Event Engine's read surface.

**Deliberately absent: any method returning a priority, a ranking, or a
"top events" list.** All three are commercial judgements. The Signal Engine
reads the events and forms its own — a convenience method here would put
that judgement behind an innocuous call, and within a year every consumer
would use it.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from modules.business_event_engine.application.ports import BusinessEventRepository
from modules.business_event_engine.domain.business_event import BusinessEvent
from modules.business_event_engine.domain.taxonomy import BusinessEventType, Taxonomy
from modules.observation_engine.public import Observation, ObservationQueries


@dataclass(frozen=True, slots=True)
class BusinessEventEvidence:
    """An event together with the observations behind it — the traversal an
    evidence export and an AI citation both need."""

    event: BusinessEvent
    observations: tuple[Observation, ...]


class BusinessEventQueries:
    """Read-only. Every method is scoped to one workspace, explicitly."""

    def __init__(
        self,
        *,
        repository: BusinessEventRepository,
        observations: ObservationQueries,
        taxonomy: Taxonomy,
    ) -> None:
        self._repository = repository
        self._observations = observations
        self._taxonomy = taxonomy

    async def business_events(
        self,
        workspace_id: UUID,
        entity_id: UUID,
        *,
        type_key: BusinessEventType | None = None,
        since: datetime | None = None,
    ) -> tuple[BusinessEvent, ...]:
        return await self._repository.for_entity(
            workspace_id, entity_id, type_key=type_key, since=since
        )

    async def business_event_evidence(
        self, workspace_id: UUID, event_id: UUID
    ) -> BusinessEventEvidence | None:
        event = await self._repository.by_id(workspace_id, event_id)
        if event is None:
            return None

        cited = set(event.evidence_observation_ids)
        observations = await self._observations.observations(workspace_id, event.entity_id)
        return BusinessEventEvidence(
            event=event,
            observations=tuple(o for o in observations if o.id in cited),
        )

    async def history(self, workspace_id: UUID, event_id: UUID) -> tuple[BusinessEvent, ...]:
        """The supersession chain, oldest first.

        *"What did we believe about this surge, and when?"* — the question
        durable business history exists to answer.
        """
        chain: list[BusinessEvent] = []
        current = await self._repository.by_id(workspace_id, event_id)
        while current is not None:
            chain.append(current)
            if current.supersedes is None:
                break
            current = await self._repository.by_id(workspace_id, current.supersedes)
        return tuple(reversed(chain))

    def taxonomy(self) -> Taxonomy:
        """The business language in force. Exposed so the product, analytics,
        and documentation all read the same definitions rather than
        re-describing them."""
        return self._taxonomy
