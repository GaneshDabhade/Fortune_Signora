"""Composition root for the Business Event Engine.

The Observation Engine's query surface is a **parameter, not a
construction**: building it here would mean importing another module's
infrastructure, which is the coupling that makes a modular monolith stop
being modular.
"""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from modules.business_event_engine.application.detect import DetectBusinessEvents
from modules.business_event_engine.application.queries import BusinessEventQueries
from modules.business_event_engine.infrastructure.repository import SqlBusinessEventRepository
from modules.business_event_engine.infrastructure.taxonomy_loader import load_taxonomy
from modules.observation_engine.public import ObservationQueries
from signora_platform.event_bus import EventPublisher


def build_detect_business_events(
    session: AsyncSession, *, observations: ObservationQueries, publisher: EventPublisher
) -> DetectBusinessEvents:
    return DetectBusinessEvents(
        repository=SqlBusinessEventRepository(session),
        observations=observations,
        taxonomy=load_taxonomy(),
        publisher=publisher,
        session=session,
    )


def build_queries(
    session: AsyncSession, *, observations: ObservationQueries
) -> BusinessEventQueries:
    return BusinessEventQueries(
        repository=SqlBusinessEventRepository(session),
        observations=observations,
        taxonomy=load_taxonomy(),
    )
