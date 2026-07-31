"""Where the API wires modules together.

**The composition boundary, and the only place that may see two modules'
infrastructure at once.** A module's own composition root takes its
neighbour's query surface as a *parameter* rather than constructing it —
building one there would mean importing another module's infrastructure — so
the assembling happens here, at the entry point, exactly as §6 requires.

### The chain is six deep, and that is a finding rather than an accident

Reading a list of accounts needs `OpportunityQueries`, which needs
`BuyingScoreQueries`, which needs `SignalQueries`, which needs
`BusinessEventQueries`, which needs `ObservationQueries`, which needs
`GraphQueries`. Each edge is one the dependency matrix already ratified
(05-module-dependencies.md); none is new.

Construction is cheap — these are objects holding a session, not queries — but
the depth is worth recording rather than smoothing over: **the attention list
uses exactly one method of the port it is handed** (`current_for`), and the
five layers beneath exist to satisfy `explanation()`, which this path never
calls. If a future read surface finds this shape genuinely costly, the
measurement belongs in that finding, not in a speculative abstraction now.
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
from modules.provider_normalization.infrastructure.claim_reader import SqlClaimReader
from modules.signal_engine.infrastructure.composition import (
    build_queries as build_signal_queries,
)
from signora_platform.api import CurrentWorkspace


def opportunity_queries(context: CurrentWorkspace) -> OpportunityQueries:
    """The account read surface, assembled for one request.

    Takes the **workspace-scoped** context, so RLS is already established and
    the workspace identifier is one the caller was verified to be a member of
    — never one they supplied.
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


OpportunityRead = Annotated[OpportunityQueries, Depends(opportunity_queries)]

__all__ = ["OpportunityRead", "opportunity_queries"]
