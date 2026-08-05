"""Composition root for the Signal Engine.

The Business Event Engine's query surface is a **parameter, not a
construction**: building it here would mean importing another module's
infrastructure. **The Commercial Profile's competitor reader is a parameter
for the identical reason** (ADR-0403) — this module depends on the Protocol in
that module's `public/`, and the application composition root supplies the
implementation.
"""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from modules.business_event_engine.public import BusinessEventQueries
from modules.commercial_profile.public import DeclaredCompetitorReader
from modules.signal_engine.application.generate import GenerateSignals
from modules.signal_engine.application.queries import SignalQueries
from modules.signal_engine.application.resolve import ResolveSignal
from modules.signal_engine.application.triage import TriageQueries
from modules.signal_engine.infrastructure.catalog_loader import load_catalog
from modules.signal_engine.infrastructure.repository import (
    SqlProfileRepository,
    SqlResolutionRepository,
    SqlSignalRepository,
)
from signora_platform.event_bus import EventPublisher


def build_generate_signals(
    session: AsyncSession,
    *,
    business_events: BusinessEventQueries,
    competitors: DeclaredCompetitorReader,
    publisher: EventPublisher,
) -> GenerateSignals:
    """**The competitor reader is a parameter, not a construction** — the same
    rule the business event queries follow, and for the same reason: building
    it here would mean importing another module's infrastructure (ADR-0403)."""
    return GenerateSignals(
        repository=SqlSignalRepository(session),
        profiles=SqlProfileRepository(session),
        competitors=competitors,
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


def build_resolve_signal(session: AsyncSession) -> ResolveSignal:
    """Recording a decision. **Its own builder, not a method on the queries** —
    the read surface is handed to other modules through `public/`, and a write
    reachable from there would let a consumer resolve a signal it may not even
    name."""
    return ResolveSignal(
        signals=SqlSignalRepository(session),
        resolutions=SqlResolutionRepository(session),
    )


def build_triage(session: AsyncSession, *, business_events: BusinessEventQueries) -> TriageQueries:
    """The Signal Center's read. **Composed from the module's own query surface
    rather than duplicating it**, so *live* means exactly what it means
    everywhere else in this module — superseded, expired and
    profile-deactivated all excluded, decided in one place."""
    return TriageQueries(
        signals=build_queries(session, business_events=business_events),
        resolutions=SqlResolutionRepository(session),
    )
