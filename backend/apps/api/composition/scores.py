"""Composing the Buying Score Engine's read surface.

Four deep — a score needs signals, which need business events, which need
observations, which need the graph. Every edge is one the dependency matrix
already ratified (05-module-dependencies.md); none is new, and none reaches
downstream.

**Not shared with the attention list's composition, deliberately.** That file
builds the same four layers and then one more, and import-linter refuses a
single shared module here: a router inherits every import the file it imports
makes, so a common composition would give the Buying Score Engine's router a
transitive dependency on the Opportunity Engine — an upstream module reaching
downstream. **One file per read surface** is what keeps each router's
dependencies to what it actually composes.
"""

from typing import Annotated

from fastapi import Depends

from modules.business_event_engine.infrastructure.composition import (
    build_queries as build_business_event_queries,
)
from modules.buying_score_engine.application.queries import BuyingScoreQueries
from modules.buying_score_engine.infrastructure.composition import (
    build_queries as build_buying_score_queries,
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
from signora_platform.api import CurrentWorkspace


def buying_score_queries(context: CurrentWorkspace) -> BuyingScoreQueries:
    """The score read surface, assembled for one request.

    Takes the **workspace-scoped** context, so RLS is already established and
    the workspace identifier is one the caller was verified to be a member of —
    never one they supplied.
    """
    session = context.session
    graph = build_graph_queries(
        session, claims=SqlClaimReader(session, workspace_id=context.workspace_id)
    )
    observations = build_observation_queries(session, graph=graph)
    events = build_business_event_queries(session, observations=observations)
    signals = build_signal_queries(session, business_events=events)
    return build_buying_score_queries(session, signals=signals)


BuyingScoreRead = Annotated[BuyingScoreQueries, Depends(buying_score_queries)]

__all__ = ["BuyingScoreRead", "buying_score_queries"]
