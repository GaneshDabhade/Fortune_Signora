"""Composing the Signal Center — the queue, and the decision that leaves it.

**Its own file, like every other surface.** A router inherits every import the
module it imports makes, so folding this into `validation.py` would hand the
validation router a dependency on a write it never performs.

**The write is composed separately from the read**, and deliberately so: they
are the only two things this screen does, but a handler that received both
could resolve a signal while answering a question about it.
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
from modules.signal_engine.application.resolve import ResolveSignal
from modules.signal_engine.application.triage import TriageQueries
from modules.signal_engine.infrastructure.composition import build_resolve_signal, build_triage
from signora_platform.api import CurrentWorkspace
from signora_platform.event_bus import PostgresOutboxEventPublisher


def triage_queries(context: CurrentWorkspace) -> TriageQueries:
    """The queue, assembled for one request.

    The same two-levels-deep chain the validation surface builds — signals need
    business events, which need observations, which need the graph. **Every
    edge is one the dependency matrix already ratified; none is new**, and the
    resolution repository this adds is inside the module doing the reading.
    """
    session = context.session
    graph = build_graph_queries(
        session, claims=SqlClaimReader(session, workspace_id=context.workspace_id)
    )
    observations = build_observation_queries(session, graph=graph)
    events = build_business_event_queries(session, observations=observations)
    return build_triage(session, business_events=events)


def resolve_signal(context: CurrentWorkspace) -> ResolveSignal:
    """Recording a decision.

    **Needs none of the chain above.** Writing a resolution reads one signal to
    prove it exists and nothing else — no evidence, no observations, no graph.
    Building the whole read stack here would make a write depend on four
    modules it never asks a question of.

    **The publisher is the real one, writing to the outbox on the request's own
    session** — so the announcement commits with the row or neither does.
    """
    return build_resolve_signal(context.session, publisher=PostgresOutboxEventPublisher())


TriageRead = Annotated[TriageQueries, Depends(triage_queries)]
ResolveWrite = Annotated[ResolveSignal, Depends(resolve_signal)]

__all__ = ["ResolveWrite", "TriageRead", "resolve_signal", "triage_queries"]
