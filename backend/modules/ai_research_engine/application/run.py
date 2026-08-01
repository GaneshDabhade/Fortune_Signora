"""Running a request that was asked for. **The only path a customer can start.**

    begin()   mark RUNNING                    one transaction
    finish()  research, then say how it ended another

`Research` itself is unchanged and knows nothing about requests: it produces an
artifact from an account's evidence, exactly as it did when the only caller was
a test. This wraps it in the one thing a customer-triggered run needs and a
pipeline-triggered one does not — **a story the person who clicked can read
while it happens.**

---

**Two methods rather than one, and the reason is the customer, not the code.**
`RUNNING` is only worth recording if somebody can *see* it, and a status written
inside the same transaction as the minute-long run it describes becomes visible
only once that run is over. So beginning commits on its own, and the caller
that owns the transaction boundary — `interface/handlers.py` — makes it two.

**Every ending is recorded, including the ones that are not failures.** Three
statuses come out of `finish()` and the distinction between them is most of why
this file exists:

| Outcome | Status | What the customer is told |
|---|---|---|
| An artifact exists | `COMPLETED` | Here it is |
| `Research.run()` returned `None` | `NOTHING_TO_RESEARCH` | There was nothing to compare |
| It raised | `FAILED` | Why, verbatim |

**`NOTHING_TO_RESEARCH` is not a failure and must never be shown as one.** An
account with two business events from a single provider has nothing to
corroborate and nothing to dissent from; reporting that as an error would have
the product apologising for behaving correctly.

**A failure is recorded rather than re-raised, and this is the one place that
choice is not obvious.** Re-raising would give ARQ its retry, and the platform's
retry policy is genuinely valuable for a transient blip. It is the wrong tool
here: a research run costs two model calls and about a minute, and the failures
this stage actually produces — an unreleased prompt, a model that refuses the
schema, an account whose plan cannot be grounded — are every one of them
permanent within a redelivery window. Retrying them would spend the budget three
times to record the same reason. **So the reason is stored, the request settles,
and the customer may ask again** — a decision they can make and the platform
cannot.

**Idempotency is the platform's, not ours.** The dispatcher records
`(consumer, event_id)` and will not run a handler twice for one event, so this
file holds no seen-before check. What it does hold is the domain's refusal to
advance a request that is not where it should be, which is what a *replay* after
a ledger reset runs into — a different thing from a redelivery, and one the
transition rules already know how to answer.
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime
from uuid import UUID

from modules.ai_research_engine.application.ports import ResearchRequestRepository
from modules.ai_research_engine.application.research import Research
from modules.ai_research_engine.domain.request import (
    ResearchRequest,
    ResearchRequestError,
    ResearchRequestState,
    ResearchStatus,
    next_state,
)
from signora_platform.observability import get_logger

logger = get_logger(__name__)


class RequestNotFound(ResearchRequestError):
    """The request the event names is not visible in this workspace."""


class BeginResearchRun:
    """Marks a request as running. **Its own unit of work, deliberately.**"""

    def __init__(
        self,
        *,
        requests: ResearchRequestRepository,
        clock: Callable[[], datetime] = lambda: datetime.now(UTC),
    ) -> None:
        self._requests = requests
        self._clock = clock

    async def execute(
        self, workspace_id: UUID, request_id: UUID
    ) -> tuple[ResearchRequest, ResearchRequestState]:
        found = await self._requests.by_id(workspace_id, request_id)
        if found is None:
            raise RequestNotFound(
                # No identifier: this reaches a customer as a 422 (R4-03).
                "That research request does not exist in this workspace."
            )
        request, current = found
        # The domain refuses anything that is not `REQUESTED`, which is what
        # stops a replay re-running a settled request.
        running = next_state(current, ResearchStatus.RUNNING, occurred_at=self._clock())
        await self._requests.record(running)
        return request, running


class FinishResearchRun:
    """Researches the account, then records how it went."""

    def __init__(
        self,
        *,
        requests: ResearchRequestRepository,
        research: Research,
        clock: Callable[[], datetime] = lambda: datetime.now(UTC),
    ) -> None:
        self._requests = requests
        self._research = research
        self._clock = clock

    async def execute(
        self,
        request: ResearchRequest,
        running: ResearchRequestState,
        *,
        correlation_id: UUID,
    ) -> ResearchRequestState:
        try:
            task = await self._research.run(
                workspace_id=request.workspace_id,
                entity_id=request.entity_id,
                opportunity_id=request.opportunity_id,
                correlation_id=correlation_id,
            )
        except Exception as exc:
            settled = next_state(
                running,
                ResearchStatus.FAILED,
                occurred_at=self._clock(),
                detail=f"{type(exc).__name__}: {exc}",
            )
            await self._requests.record(settled)
            logger.warning(
                "research run failed",
                extra={
                    "workspace_id": str(request.workspace_id),
                    "correlation_id": str(correlation_id),
                    "request_id": str(request.id),
                    "error": settled.detail,
                },
            )
            return settled

        settled = (
            next_state(
                running,
                ResearchStatus.COMPLETED,
                occurred_at=self._clock(),
                task_id=task.id,
            )
            if task is not None
            else next_state(
                running, ResearchStatus.NOTHING_TO_RESEARCH, occurred_at=self._clock()
            )
        )
        await self._requests.record(settled)
        logger.info(
            "research run settled",
            extra={
                "workspace_id": str(request.workspace_id),
                "correlation_id": str(correlation_id),
                "request_id": str(request.id),
                "status": settled.status.value,
            },
        )
        return settled
