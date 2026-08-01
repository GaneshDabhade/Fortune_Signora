"""Composing the AI Research Engine's surfaces — the read and the ask.

**Two dependencies, and neither can call a model.** The read needs the request
history and the artifact store; the ask needs the request store, the
opportunity that makes an account researchable, and the outbox. Nothing here is
handed an `Infer`, so an API handler that tried to research an account
synchronously would have nothing to research it with (CLAUDE.md §7).

Producing research needs the prompt registry, the provider and the model, and
that wiring lives in the worker's composition root — where a minute-long call
belongs.

The opportunity chain is reused from `opportunities.py` rather than rebuilt:
two constructions of one chain would be two things to keep in step.
"""

from typing import Annotated

from fastapi import Depends

from apps.api.composition.opportunities import opportunity_queries
from modules.ai_research_engine.application.queries import ResearchQueries
from modules.ai_research_engine.application.request import RequestResearch
from modules.ai_research_engine.infrastructure.composition import (
    build_request_research,
    build_research_queries,
)
from modules.opportunity_engine.application.queries import OpportunityQueries
from signora_platform.api import CurrentWorkspace
from signora_platform.event_bus import PostgresOutboxEventPublisher


def research_queries(context: CurrentWorkspace) -> ResearchQueries:
    return build_research_queries(context.session)


def request_research(
    context: CurrentWorkspace,
    opportunities: Annotated[OpportunityQueries, Depends(opportunity_queries)],
) -> RequestResearch:
    """The ask, assembled for one request.

    The publisher writes to the outbox **on the request's own session**, so the
    request row and the event that will start the work commit together or not
    at all. An event published before its cause committed is the failure the
    outbox exists to prevent; here it would be a worker researching an account
    nobody successfully asked about (06-events.md).
    """
    return build_request_research(
        context.session,
        opportunities=opportunities,
        publisher=PostgresOutboxEventPublisher(),
    )


ResearchRead = Annotated[ResearchQueries, Depends(research_queries)]
ResearchRequestWrite = Annotated[RequestResearch, Depends(request_research)]

__all__ = [
    "ResearchRead",
    "ResearchRequestWrite",
    "request_research",
    "research_queries",
]
