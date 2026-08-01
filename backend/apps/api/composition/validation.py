"""Composing the Signal Engine's validation read surface.

Two levels deep — signals need business events, which need observations, which
need the graph. Every edge is one the dependency matrix already ratified; none
is new.

**Its own file, like every other read surface.** A router inherits every import
the module it imports makes, so a shared composition would hand this router a
transitive dependency on the Buying Score Engine it never touches.
"""

from typing import Annotated

from fastapi import Depends

from modules.business_event_engine.infrastructure.composition import (
    build_queries as build_business_event_queries,
)
from modules.knowledge_graph.infrastructure.composition import (
    build_queries as build_graph_queries,
)
from modules.observation_engine.infrastructure.composition import (
    build_queries as build_observation_queries,
)
from modules.provider_normalization.infrastructure.claim_reader import SqlClaimReader
from modules.signal_engine.infrastructure.composition import (
    build_queries as build_signal_queries,
)
from modules.signal_engine.public import SignalQueries
from signora_platform.api import CurrentWorkspace


def signal_queries(context: CurrentWorkspace) -> SignalQueries:
    """The hypothesis read surface, assembled for one request.

    Takes the **workspace-scoped** context, so RLS is already established and
    the workspace identifier is one the caller was verified to be a member of.
    """
    session = context.session
    graph = build_graph_queries(
        session, claims=SqlClaimReader(session, workspace_id=context.workspace_id)
    )
    observations = build_observation_queries(session, graph=graph)
    events = build_business_event_queries(session, observations=observations)
    return build_signal_queries(session, business_events=events)


SignalRead = Annotated[SignalQueries, Depends(signal_queries)]

__all__ = ["SignalRead", "signal_queries"]
