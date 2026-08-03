"""Composing the Observation Engine's read surface.

Two levels deep, both edges already in the ratified matrix: observations need
the graph to resolve the claims behind one, and the graph needs a claim reader.
`observations()` itself uses neither — that chain exists for
`observation_evidence`, and is recorded here rather than smoothed over.

Its own file, like every other surface: a shared composition would hand each
router the transitive imports of every other one.
"""

from typing import Annotated

from fastapi import Depends

from modules.knowledge_graph.infrastructure.composition import (
    build_queries as build_graph_queries,
)
from modules.observation_engine.application.queries import ObservationQueries
from modules.observation_engine.infrastructure.composition import (
    build_queries as build_observation_queries,
)
from modules.provider_normalization.infrastructure.claim_reader import SqlClaimReader
from signora_platform.api import CurrentWorkspace


def observation_queries(context: CurrentWorkspace) -> ObservationQueries:
    """The change history for one account, assembled for one request.

    Takes the **workspace-scoped** context, so RLS is established and the
    workspace identifier is one the caller was verified to be a member of —
    never one they supplied.
    """
    session = context.session
    graph = build_graph_queries(
        session, claims=SqlClaimReader(session, workspace_id=context.workspace_id)
    )
    return build_observation_queries(session, graph=graph)


ObservationRead = Annotated[ObservationQueries, Depends(observation_queries)]

__all__ = ["ObservationRead", "observation_queries"]
