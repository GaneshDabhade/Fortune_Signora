"""Asking for research. **Accepting the ask is all this does.**

    record the request  →  publish  →  return

No model is called here, no plan is made, and no finding is computed. That is
not a simplification for later — an API handler that blocked on a research run
would hold a request open for the ~54 seconds two model calls take, and
CLAUDE.md §7 forbids it in as many words. The work happens in a worker,
reached through the outbox, and this use case's entire job is to make sure the
ask survives a crash between the click and the worker picking it up.

**The request row and the event commit together.** They are published on the
caller's own session, so a request nobody stored cannot enqueue work and work
nobody enqueued cannot leave a request stranded at `REQUESTED` forever.

---

**One in-flight request per account, and it is a product rule before it is a
cost rule.** A seller who clicks twice because nothing visibly happened should
get the run they already have, not a second one — the second would finish
later, cost the same, and produce findings whose derived identities collide
with the first run's anyway. So the guard returns the existing request rather
than raising: *"you already asked"* is not an error, it is an answer.

**Membership is not re-checked here.** The interface layer resolves and
verifies workspace context before this use case is reached (11-tenancy.md), and
a second check inside the application layer would be a guard that cannot fail.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from modules.ai_research_engine.application.ports import ResearchRequestRepository
from modules.ai_research_engine.domain.events import ResearchRequested
from modules.ai_research_engine.domain.request import (
    PAYLOAD_VERSION,
    ResearchRequest,
    ResearchRequestError,
    ResearchRequestState,
    opening_state,
)
from modules.opportunity_engine.public import OpportunityQueries
from signora_platform.event_bus import EventPublisher
from signora_platform.observability import get_logger

logger = get_logger(__name__)

PRODUCER_MODULE = "ai_research_engine"


class NoOpportunityToResearch(ResearchRequestError):
    """Research was asked for an account with no open opportunity.

    **Research is invoked on qualified opportunities**, which is the module's
    existing contract and not a restriction added here: `OpportunityFactSource`
    can only assemble facts from an `OpportunityExplanation`. An account the
    pipeline has not yet qualified has no explanation to research.

    Distinguished from every other refusal so the interface can answer 404 —
    an account the caller cannot see and an account with nothing open must
    look identical from outside.
    """


@dataclass(frozen=True, slots=True)
class RequestResearchInput:
    workspace_id: UUID
    entity_id: UUID
    #: **The verified principal.** There is no machine path to this use case,
    #: and a body that could name its own requester would let one member spend
    #: another's name on a model call.
    requested_by: UUID


@dataclass(frozen=True, slots=True)
class RequestResearchResult:
    request: ResearchRequest
    state: ResearchRequestState
    #: True when the ask matched a run already in flight. The interface uses it
    #: to answer `200` rather than `202`, so a client can tell *"we started
    #: one"* from *"one is already running"* without comparing timestamps.
    already_running: bool


class RequestResearch:
    def __init__(
        self,
        *,
        requests: ResearchRequestRepository,
        opportunities: OpportunityQueries,
        publisher: EventPublisher,
        session: AsyncSession,
        clock: Callable[[], datetime] = lambda: datetime.now(UTC),
    ) -> None:
        self._requests = requests
        # Another module's published query surface, read synchronously — the
        # one ratified edge this module has (05-module-dependencies.md).
        self._opportunities = opportunities
        self._publisher = publisher
        self._session = session
        self._clock = clock

    async def execute(
        self, request: RequestResearchInput, *, correlation_id: UUID
    ) -> RequestResearchResult:
        in_flight = await self._requests.in_flight_for(request.workspace_id, request.entity_id)
        if in_flight is not None:
            existing, state = in_flight
            logger.info(
                "research already in flight",
                extra={
                    "workspace_id": str(request.workspace_id),
                    "correlation_id": str(correlation_id),
                    "request_id": str(existing.id),
                    "status": state.status.value,
                },
            )
            return RequestResearchResult(
                request=existing, state=state, already_running=True
            )

        tracked = await self._opportunities.tracked(request.workspace_id, request.entity_id)
        if tracked is None:
            raise NoOpportunityToResearch(
                "there is nothing open on this account to research. Research compares the "
                "evidence beneath an account Signora has already qualified, so an account "
                "with no open opportunity has no evidence set to compare."
            )

        now = self._clock()
        recorded = ResearchRequest(
            id=uuid4(),
            workspace_id=request.workspace_id,
            entity_id=request.entity_id,
            opportunity_id=tracked.opportunity.id,
            requested_by=request.requested_by,
            requested_at=now,
            # A uniqueness device, not a fact. Two simultaneous askers compute
            # the same number and one loses on the unique constraint — which
            # is what stops a second minute-long model call when the in-flight
            # check above raced.
            generation=await self._requests.generations(
                request.workspace_id, request.entity_id
            ),
        )
        state = opening_state(recorded)
        await self._requests.open(recorded, state)
        await self._publisher.publish(
            # See M9's reason.py: the platform's PublishableEvent Protocol
            # declares settable members, which a frozen domain event cannot
            # satisfy. A finding (F-5), not fixed here.
            [ResearchRequested(  # type: ignore[list-item]
                event_id=uuid4(),
                workspace_id=request.workspace_id,
                occurred_at=now,
                request_id=recorded.id,
                entity_id=recorded.entity_id,
                opportunity_id=recorded.opportunity_id,
                requested_by=recorded.requested_by,
                payload_version=PAYLOAD_VERSION,
                causation_id=correlation_id,
            )],
            session=self._session,
            producer_module=PRODUCER_MODULE,
            correlation_id=correlation_id,
        )

        logger.info(
            "research requested",
            extra={
                "workspace_id": str(request.workspace_id),
                "correlation_id": str(correlation_id),
                "request_id": str(recorded.id),
                "entity_id": str(recorded.entity_id),
            },
        )
        return RequestResearchResult(request=recorded, state=state, already_running=False)
