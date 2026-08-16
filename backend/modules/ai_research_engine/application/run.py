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
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from modules.ai_research_engine.application.ports import ResearchRequestRepository
from modules.ai_research_engine.application.research import PRODUCER_MODULE, Research
from modules.ai_research_engine.domain.request import (
    ResearchRequest,
    ResearchRequestError,
    ResearchRequestState,
    ResearchStatus,
    next_state,
)
from modules.workspace_tenancy.public.notifications import (
    Actor,
    ActorKind,
    Category,
    Channel,
    NotificationRequested,
    Subject,
)
from signora_platform.event_bus import EventPublisher
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
    """Researches the account, then records how it went — **and tells whoever asked.**

    ## 🔴 Why the person who asked is told here and nowhere else

    ⚡ **This is the only place that holds both halves at once**: 📁 the
    `ResearchRequest` carries `requested_by`, and the settled state carries the
    outcome. ⛔ **`ResearchCompleted` carries neither** — it is published inside
    `Research.run`, which never sees a request — **and it deliberately stays
    that way**: 📁 *events carry identity*, and widening a catalogued payload so
    a second consumer could read one field is how an event becomes a view.

    ## ⛔ It publishes a REQUEST to notify; it does not notify

    📁 **[05](../../../../docs/architecture/05-module-dependencies.md) approves
    only read-only synchronous edges into `workspace_tenancy`**, so calling a
    notify port from here would be a synchronous write into another module —
    🔴 **an architecture change, not an implementation detail** ([§20e](../../../../CLAUDE.md)).
    ✅ **Publishing conforms to that module's published language instead**, which
    is the edge 05 already ratifies.

    ## ⚡ Every settled outcome is worth telling somebody about, including failure

    ⛔ **Especially failure.** 📁 A person clicked, waited a minute, and 📁
    [§10](../../../../CLAUDE.md) is explicit that a silent failure is worse than
    a loud one — **a run that failed and told nobody is indistinguishable from
    one still running**, and the customer's next move is to click again and
    spend a second model call.
    """

    def __init__(
        self,
        *,
        requests: ResearchRequestRepository,
        research: Research,
        session: AsyncSession,
        publisher: EventPublisher,
        clock: Callable[[], datetime] = lambda: datetime.now(UTC),
    ) -> None:
        self._requests = requests
        self._research = research
        # ⚡ **The outbox row commits with the state row it announces**, which is
        # the whole point of the pattern — 📁 [§9](../../../../CLAUDE.md).
        self._session = session
        self._publisher = publisher
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
            await self._tell_the_requester(
                request,
                correlation_id=correlation_id,
                at=settled.occurred_at,
                summary="Research on this account could not be completed.",
                expectation="Open the account and ask for research again.",
            )
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
        await self._tell_the_requester(
            request,
            correlation_id=correlation_id,
            at=settled.occurred_at,
            summary=(
                "Signora finished researching this account."
                if task is not None
                # ⚡ **A distinct sentence, not a softer one.** ⛔ *"Nothing to
                # research"* is an outcome about the ACCOUNT — it has too little
                # evidence to compare — **and reporting it as a completed brief
                # would send somebody looking for findings that do not exist.**
                else "There was not enough evidence to research this account yet."
            ),
            expectation=(
                "Open the account to read what Signora found."
                if task is not None
                else "Connect more sources, or try again once this account has activity."
            ),
        )
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

    async def _tell_the_requester(
        self,
        request: ResearchRequest,
        *,
        correlation_id: UUID,
        at: datetime,
        summary: str,
        expectation: str,
    ) -> None:
        """Publish a notification request addressed to the person who asked.

        ⚡ **`ActorKind.AGENT`, and `agent_name` is a CAPABILITY's name.** ⛔ **Not
        the model and not the vendor** — 📁 [§10](../../../../CLAUDE.md), vendor
        neutrality: **provenance is recorded on the inference, never rendered to
        a customer**, and this module has spent a whole registry making sure
        nothing above an adapter can name one.

        ⚠️ **`Actor` carries no display name for a person and none is needed
        here** — 📁 [C-203](../../../../docs/LANE_COORDINATION.md) is `DEFERRED` on
        a stated trigger and an agent's name is the platform's own to give.

        ⛔ **`IN_APP` alone.** ⚡ **Naming `EMAIL` would raise**: no adapter serves
        it, and 📁 the registry refuses rather than rerouting — which is the
        correct behaviour and the wrong moment to discover it.
        """
        await self._publisher.publish(
            # See M9's reason.py: the platform's PublishableEvent Protocol
            # declares settable members, which a frozen domain event cannot
            # satisfy. A finding (F-5), not fixed here.
            [NotificationRequested(  # type: ignore[list-item]
                event_id=uuid4(),
                workspace_id=request.workspace_id,
                occurred_at=at,
                recipient_id=request.requested_by,
                # ⚡ **The reader asked for this and it is waiting on them** —
                # ⛔ never `MENTION`, which is a colleague naming somebody.
                category=Category.NEEDS_YOU,
                actor=Actor(kind=ActorKind.AGENT, agent_name="Research"),
                subject=Subject(kind="opportunity", id=request.opportunity_id),
                summary=summary,
                expectation=expectation,
                channels=frozenset({Channel.IN_APP}),
                causation_id=correlation_id,
            )],
            session=self._session,
            producer_module=PRODUCER_MODULE,
            correlation_id=correlation_id,
        )


__all__ = ["BeginResearchRun", "FinishResearchRun", "RequestNotFound", "ResearchRequestError"]
