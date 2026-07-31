"""Composing the Knowledge Graph's identity read surface.

One level deep: naming an account needs bindings and claims, and nothing
downstream of them. `provider_normalization` is upstream of `knowledge_graph`
in the dependency matrix, so this file reaches nothing it should not.
"""

from typing import Annotated

from fastapi import Depends

from modules.knowledge_graph.infrastructure.composition import (
    build_queries as build_graph_queries,
)
from modules.knowledge_graph.public import GraphQueries
from modules.provider_normalization.infrastructure.claim_reader import SqlClaimReader
from signora_platform.api import CurrentWorkspace


def graph_queries(context: CurrentWorkspace) -> GraphQueries:
    """The identity read surface, assembled for one request.

    Takes the **workspace-scoped** context, so RLS is already established and
    the workspace identifier is one the caller was verified to be a member of —
    never one they supplied.
    """
    return build_graph_queries(
        context.session,
        claims=SqlClaimReader(context.session, workspace_id=context.workspace_id),
    )


GraphRead = Annotated[GraphQueries, Depends(graph_queries)]

__all__ = ["GraphRead", "graph_queries"]
