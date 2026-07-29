"""Composition root for the Signal Engine.

The Business Event Engine's query surface is a **parameter, not a
construction**: building it here would mean importing another module's
infrastructure.
"""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from modules.business_event_engine.public import BusinessEventQueries
from modules.signal_engine.application.generate import GenerateSignals
from modules.signal_engine.application.queries import SignalQueries
from modules.signal_engine.infrastructure.catalog_loader import load_catalog
from modules.signal_engine.infrastructure.repository import (
    SqlProfileRepository,
    SqlSignalRepository,
)
from signora_platform.event_bus import EventPublisher


def build_generate_signals(
    session: AsyncSession, *, business_events: BusinessEventQueries, publisher: EventPublisher
) -> GenerateSignals:
    return GenerateSignals(
        repository=SqlSignalRepository(session),
        profiles=SqlProfileRepository(session),
        business_events=business_events,
        catalog=load_catalog(),
        publisher=publisher,
        session=session,
    )


def build_queries(session: AsyncSession, *, business_events: BusinessEventQueries) -> SignalQueries:
    return SignalQueries(
        repository=SqlSignalRepository(session),
        profiles=SqlProfileRepository(session),
        business_events=business_events,
        catalog=load_catalog(),
    )


def build_profiles(session: AsyncSession) -> SqlProfileRepository:
    """Customer-authored configuration, deliberately reachable on its own —
    it is not derived data and must not be rebuilt with the rest."""
    return SqlProfileRepository(session)
