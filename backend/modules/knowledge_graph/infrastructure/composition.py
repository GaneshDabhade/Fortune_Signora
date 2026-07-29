"""Composition root for the Knowledge Graph.

The only place that knows which concrete repository is in use.

The claim reader is a **parameter, not a construction**. Building
Provider Normalization's SQL reader here would mean the Knowledge Graph
importing another module's infrastructure — which runs, and is exactly the
"just this once" coupling that makes a modular monolith stop being modular.
The process composition root supplies it.
"""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from modules.knowledge_graph.application.queries import GraphQueries
from modules.knowledge_graph.application.relationships import DeriveRelationships
from modules.knowledge_graph.application.resolve import ResolveEntity
from modules.knowledge_graph.infrastructure.repository import SqlGraphRepository
from modules.provider_normalization.public import ClaimReader
from signora_platform.event_bus import EventPublisher


def build_resolve_entity(
    session: AsyncSession, *, claims: ClaimReader, publisher: EventPublisher
) -> ResolveEntity:
    return ResolveEntity(
        repository=SqlGraphRepository(session),
        claims=claims,
        publisher=publisher,
        session=session,
    )


def build_derive_relationships(
    session: AsyncSession, *, publisher: EventPublisher
) -> DeriveRelationships:
    return DeriveRelationships(
        repository=SqlGraphRepository(session), publisher=publisher, session=session
    )


def build_queries(session: AsyncSession, *, claims: ClaimReader) -> GraphQueries:
    return GraphQueries(repository=SqlGraphRepository(session), claims=claims)
