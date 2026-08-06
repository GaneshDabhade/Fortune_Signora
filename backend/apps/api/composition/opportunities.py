"""Composing the Opportunity Engine's read surface.

### The chain is six deep, and that is a finding rather than an accident

Reading a list of accounts needs `OpportunityQueries`, which needs
`BuyingScoreQueries`, which needs `SignalQueries`, which needs
`BusinessEventQueries`, which needs `ObservationQueries`, which needs
`GraphQueries`. Each edge is one the dependency matrix already ratified
(05-module-dependencies.md); none is new.

Construction is cheap — these are objects holding a session, not queries — but
the depth is worth recording rather than smoothing over: **the attention list
uses exactly one method of the port it is handed** (`current_for`), and the five
layers beneath exist to satisfy `explanation()`, which this path never calls. If
a future read surface finds this shape genuinely costly, the measurement belongs
in that finding, not in a speculative abstraction now.
"""

from typing import Annotated

from fastapi import Depends

from modules.business_event_engine.infrastructure.composition import (
    build_queries as build_business_event_queries,
)
from modules.buying_score_engine.infrastructure.composition import (
    build_queries as build_buying_score_queries,
)
from modules.knowledge_graph.infrastructure.composition import (
    build_queries as build_graph_queries,
)
from modules.observation_engine.infrastructure.composition import (
    build_queries as build_observation_queries,
)
from modules.opportunity_engine.application.queries import OpportunityQueries
from modules.opportunity_engine.infrastructure.composition import (
    build_queries as build_opportunity_queries,
)
from modules.commercial_profile.infrastructure.icp_reader import SqlIcpReader
from modules.knowledge_graph.infrastructure.composition import build_attributes_reader
from modules.opportunity_engine.application.measure_icp import MeasureIcp
from modules.opportunity_engine.infrastructure.repository import SqlOpportunityRepository
from modules.provider_normalization.infrastructure.claim_reader import SqlClaimReader
from modules.signal_engine.infrastructure.composition import (
    build_queries as build_signal_queries,
)
from modules.opportunity_engine.application.qualify import QualifyOpportunity
from modules.opportunity_engine.infrastructure.composition import (
    build_qualify_opportunity,
)
from signora_platform.api import CurrentWorkspace
from signora_platform.event_bus import PostgresOutboxEventPublisher


def opportunity_queries(context: CurrentWorkspace) -> OpportunityQueries:
    """The account read surface, assembled for one request.

    Takes the **workspace-scoped** context, so RLS is already established and
    the workspace identifier is one the caller was verified to be a member of —
    never one they supplied.
    """
    session = context.session
    workspace_id = context.workspace_id
    graph = build_graph_queries(
        session, claims=SqlClaimReader(session, workspace_id=workspace_id)
    )
    observations = build_observation_queries(session, graph=graph)
    events = build_business_event_queries(session, observations=observations)
    signals = build_signal_queries(session, business_events=events)
    scores = build_buying_score_queries(session, signals=signals)
    return build_opportunity_queries(session, scores=scores)


def measure_icp(context: CurrentWorkspace) -> MeasureIcp:
    """The ICP measurement, assembled for one request.

    **Three dependencies from three modules, every one through `public/`.**
    The outcomes are this module's own; the criteria come from
    `commercial_profile` on the edge [C-328](../../../docs/LANE_COORDINATION.md)
    ruled open, and the observed attributes from `knowledge_graph` on the edge
    [D-111](../../../docs/DECISION_REGISTER.md) opened. **The composition root
    is where they meet**, which is what keeps all three modules ignorant of
    each other's internals.
    """
    session = context.session
    workspace_id = context.workspace_id
    return MeasureIcp(
        repository=SqlOpportunityRepository(session),
        icp=SqlIcpReader(session),
        attributes=build_attributes_reader(
            session, claims=SqlClaimReader(session, workspace_id=workspace_id)
        ),
    )


MeasureIcpDependency = Annotated[MeasureIcp, Depends(measure_icp)]


def qualify_opportunity(context: CurrentWorkspace) -> QualifyOpportunity:
    """Opening an opportunity by hand, assembled for one request.

    **Here rather than in `composition/workflow.py`**, and the split is the
    module's design showing through again. Progressing an opportunity consults
    no intelligence at all — *a falling score cannot revoke a seller's
    commitment* — so that path is given no score reader. **Opening one is the
    opposite**: the score at the moment of opening is the provenance a manual
    opportunity carries, and it is read through the Buying Score Engine's
    published port rather than recomputed.

    The publisher writes to the outbox on the request's own session, so the
    opportunity, its opening state and the event announcing it commit together
    or not at all.
    """
    session = context.session
    workspace_id = context.workspace_id
    graph = build_graph_queries(
        session, claims=SqlClaimReader(session, workspace_id=workspace_id)
    )
    observations = build_observation_queries(session, graph=graph)
    events = build_business_event_queries(session, observations=observations)
    signals = build_signal_queries(session, business_events=events)
    scores = build_buying_score_queries(session, signals=signals)
    return build_qualify_opportunity(
        session, scores=scores, publisher=PostgresOutboxEventPublisher()
    )


OpportunityRead = Annotated[OpportunityQueries, Depends(opportunity_queries)]
OpportunityOpening = Annotated[QualifyOpportunity, Depends(qualify_opportunity)]

__all__ = [
    "OpportunityOpening",
    "OpportunityRead",
    "opportunity_queries",
    "qualify_opportunity",
]
