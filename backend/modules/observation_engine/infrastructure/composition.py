"""Composition root for the Observation Engine.

The only place that knows which concrete repository is in use. The
Knowledge Graph's query surface is a **parameter, not a construction**:
building it here would mean importing another module's infrastructure,
which is exactly the "just this once" coupling that makes a modular
monolith stop being modular.
"""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from modules.knowledge_graph.public import GraphQueries
from modules.observation_engine.application.queries import ObservationQueries
from modules.observation_engine.application.record import RecordObservations
from modules.observation_engine.infrastructure.repository import SqlObservationRepository
from signora_platform.event_bus import EventPublisher


def build_record_observations(
    session: AsyncSession, *, graph: GraphQueries, publisher: EventPublisher
) -> RecordObservations:
    return RecordObservations(
        repository=SqlObservationRepository(session),
        graph=graph,
        publisher=publisher,
        session=session,
    )


def build_queries(session: AsyncSession, *, graph: GraphQueries) -> ObservationQueries:
    return ObservationQueries(repository=SqlObservationRepository(session), graph=graph)
