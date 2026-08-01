"""Composing the Business Event Engine's evidence read surface.

Two levels deep — business events need observations, which need the graph.
Both edges are already in the dependency matrix.

**Its own file, like every other read surface**: a router inherits every import
the module it imports makes, so a shared composition would give this one a
transitive dependency on modules it never touches.
"""

from typing import Annotated

from fastapi import Depends

from modules.business_event_engine.infrastructure.composition import (
    build_queries as build_business_event_queries,
)
from modules.business_event_engine.public import BusinessEventQueries
from modules.knowledge_graph.infrastructure.composition import (
    build_queries as build_graph_queries,
)
from modules.observation_engine.infrastructure.composition import (
    build_queries as build_observation_queries,
)
from modules.provider_normalization.infrastructure.claim_reader import SqlClaimReader
from signora_platform.api import CurrentWorkspace


def business_event_queries(context: CurrentWorkspace) -> BusinessEventQueries:
    """The evidence read surface, assembled for one request."""
    session = context.session
    graph = build_graph_queries(
        session, claims=SqlClaimReader(session, workspace_id=context.workspace_id)
    )
    observations = build_observation_queries(session, graph=graph)
    return build_business_event_queries(session, observations=observations)


BusinessEventRead = Annotated[BusinessEventQueries, Depends(business_event_queries)]

__all__ = ["BusinessEventRead", "business_event_queries"]
