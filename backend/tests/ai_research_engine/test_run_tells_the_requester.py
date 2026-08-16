"""**The person who asked for research is told when it settles.**

📁 **[TASK-495](../../../docs/BACKLOG.md)** — ⚡ **the first real caller of the
notification trigger**, and the reason the trigger is not a speculative
abstraction ([§6](../../../CLAUDE.md)).

## 🔴 What these assert that a happy-path test would not

⚡ **① It PUBLISHES, rather than calling.** 📁 **[05](../../../docs/architecture/05-module-dependencies.md)
approves only READ-ONLY synchronous edges into `workspace_tenancy`**, so a
`notify()` call from here would be a synchronous write into another module —
⛔ **an architecture change no lane may make** ([§20e](../../../CLAUDE.md)).
**The assertion is on what reaches the publisher, so replacing the publish with
a direct call fails this file rather than passing it quietly.**

⚡ **② Failure is announced too, and in different words.** ⛔ **A run that failed
and told nobody is indistinguishable from one still running** — 📁
[§10](../../../CLAUDE.md) — **and the customer's next move is to click again and
spend a second model call.**

⚡ **③ The actor is an AGENT carrying a capability's name.** 📁 **Vendor
neutrality** ([§10](../../../CLAUDE.md)): provenance is recorded on the
inference and never rendered to a customer. ⛔ **And
[C-203](../../../docs/LANE_COORDINATION.md) is why there is no person name to
render either** — *"Nothing in the product can render a person's name."*

⚡ **④ It asks for `IN_APP` alone.** ⛔ **Naming a channel with no adapter would
raise at delivery** — 📁 the registry refuses rather than rerouting, which is
correct behaviour and the wrong moment to discover it.
"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from modules.ai_research_engine.application.run import FinishResearchRun
from modules.ai_research_engine.domain.request import (
    ResearchRequest,
    ResearchRequestState,
    ResearchStatus,
    next_state,
    opening_state,
)
from modules.workspace_tenancy.domain.notification import (
    NOTIFICATION_REQUESTED,
    ActorKind,
    Category,
    Channel,
    request_from_payload,
)

pytestmark = pytest.mark.asyncio

NOW = datetime(2026, 8, 16, 9, 30, tzinfo=UTC)
WORKSPACE = UUID("11111111-1111-1111-1111-111111111111")
REQUESTER = UUID("22222222-2222-2222-2222-222222222222")
OPPORTUNITY = UUID("33333333-3333-3333-3333-333333333333")
CORRELATION = UUID("44444444-4444-4444-4444-444444444444")


class CapturingPublisher:
    """⚡ **Stands in for the outbox** and keeps what was handed to it."""

    def __init__(self) -> None:
        self.published: list[object] = []
        self.producer_modules: list[str] = []

    async def publish(
        self,
        events: Sequence[object],
        *,
        session: AsyncSession | None,
        producer_module: str,
        correlation_id: UUID,
    ) -> None:
        self.published.extend(events)
        self.producer_modules.append(producer_module)


class RecordingRequests:
    """The request repository, reduced to what this file exercises."""

    def __init__(self) -> None:
        self.recorded: list[ResearchRequestState] = []

    async def by_id(
        self, workspace_id: UUID, request_id: UUID
    ) -> tuple[ResearchRequest, ResearchRequestState] | None:
        return None

    async def record(self, state: ResearchRequestState) -> None:
        self.recorded.append(state)


class ResearchOutcome:
    """⚡ **Only its identity is read**, so a real artifact would be a fixture
    proving nothing this file is about."""

    def __init__(self) -> None:
        self.id = uuid4()


class ResearchThatReturns:
    def __init__(self, outcome: ResearchOutcome | None) -> None:
        self._outcome = outcome

    async def run(self, **_: object) -> ResearchOutcome | None:
        return self._outcome


class ResearchThatRaises:
    async def run(self, **_: object) -> ResearchOutcome | None:
        raise RuntimeError("the model did not answer")


def _a_request() -> ResearchRequest:
    return ResearchRequest(
        id=uuid4(),
        workspace_id=WORKSPACE,
        entity_id=uuid4(),
        opportunity_id=OPPORTUNITY,
        requested_by=REQUESTER,
        requested_at=NOW,
    )


def _running(request: ResearchRequest) -> ResearchRequestState:
    return next_state(opening_state(request), ResearchStatus.RUNNING, occurred_at=NOW)


def _finish(research: object, publisher: CapturingPublisher) -> FinishResearchRun:
    return FinishResearchRun(
        requests=RecordingRequests(),  # type: ignore[arg-type]
        research=research,  # type: ignore[arg-type]
        # ⚡ **`None` is honest here**: the publisher is a double and never
        # touches the session, so a real one would be scaffolding.
        session=None,  # type: ignore[arg-type]
        # ⚡ **No `type: ignore` here, and its ABSENCE is a real assertion**:
        # `mypy --strict` resolves `CapturingPublisher` as an `EventPublisher`
        # structurally, so a change to the publish signature fails this file
        # rather than passing against a double that drifted from the port.
        publisher=publisher,
        clock=lambda: NOW,
    )


def _the_only_notification(publisher: CapturingPublisher) -> object:
    requests = [
        event
        for event in publisher.published
        if getattr(event, "event_type", None) == NOTIFICATION_REQUESTED
    ]
    assert len(requests) == 1, (
        f"expected exactly one notification request, got {len(requests)}. "
        "Two would tell the customer twice about one run."
    )
    return requests[0]


class TestACompletedRunTellsWhoeverAskedForIt:
    async def test_it_publishes_rather_than_calling_workspace_tenancy(self) -> None:
        """🔴 **The architectural assertion, in executable form.**

        ⛔ **Replacing the publish with a direct `Notifier` call would satisfy
        every behavioural test in this file and fail this one** — which is the
        point, because 📁 05 approves no synchronous WRITE into that module.
        """
        publisher = CapturingPublisher()
        request = _a_request()

        await _finish(ResearchThatReturns(ResearchOutcome()), publisher).execute(
            request, _running(request), correlation_id=CORRELATION
        )

        assert _the_only_notification(publisher) is not None
        assert publisher.producer_modules == ["ai_research_engine"], (
            "the notification request was attributed to another module — "
            "producer_module is what an operator traces a delivery back through"
        )

    async def test_it_is_addressed_to_the_person_who_asked(self) -> None:
        """⚡ **The one fact only this class holds.** 📁 `ResearchCompleted`
        carries no `requested_by` and deliberately still does not — widening a
        catalogued payload so a second consumer could read one field is how an
        event becomes a view."""
        publisher = CapturingPublisher()
        request = _a_request()

        await _finish(ResearchThatReturns(ResearchOutcome()), publisher).execute(
            request, _running(request), correlation_id=CORRELATION
        )

        rebuilt = request_from_payload(
            workspace_id=WORKSPACE,
            payload=_the_only_notification(publisher).to_payload(),  # type: ignore[attr-defined]
        )
        assert rebuilt.recipient_id == REQUESTER
        assert rebuilt.subject.kind == "opportunity"
        assert rebuilt.subject.id == OPPORTUNITY

    async def test_the_actor_is_an_agent_named_for_its_capability(self) -> None:
        """⛔ **Never a model and never a vendor** — 📁 [§10](../../../CLAUDE.md).
        ⚡ **And no person name, because [C-203](../../../docs/LANE_COORDINATION.md)
        is open and this is not the place to answer it.**"""
        publisher = CapturingPublisher()
        request = _a_request()

        await _finish(ResearchThatReturns(ResearchOutcome()), publisher).execute(
            request, _running(request), correlation_id=CORRELATION
        )

        rebuilt = request_from_payload(
            workspace_id=WORKSPACE,
            payload=_the_only_notification(publisher).to_payload(),  # type: ignore[attr-defined]
        )
        assert rebuilt.actor.kind is ActorKind.AGENT
        assert rebuilt.actor.agent_name == "Research"
        assert rebuilt.actor.person_id is None

    async def test_it_asks_only_for_the_channel_that_has_an_adapter(self) -> None:
        """⛔ **Naming `EMAIL` here would raise at delivery**, because no adapter
        serves it — ⚡ **and the registry refuses rather than rerouting.**"""
        publisher = CapturingPublisher()
        request = _a_request()

        await _finish(ResearchThatReturns(ResearchOutcome()), publisher).execute(
            request, _running(request), correlation_id=CORRELATION
        )

        rebuilt = request_from_payload(
            workspace_id=WORKSPACE,
            payload=_the_only_notification(publisher).to_payload(),  # type: ignore[attr-defined]
        )
        assert rebuilt.channels == frozenset({Channel.IN_APP})
        assert rebuilt.category is Category.NEEDS_YOU


class TestEverySettledOutcomeIsAnnouncedAndTheyReadDifferently:
    async def test_a_failed_run_tells_the_requester_it_failed(self) -> None:
        """🔴 **The branch most likely to be left silent.**

        ⛔ **A run that failed and told nobody is indistinguishable from one
        still running**, and the customer's next move is to click again and
        spend a second model call.
        """
        publisher = CapturingPublisher()
        request = _a_request()

        settled = await _finish(ResearchThatRaises(), publisher).execute(
            request, _running(request), correlation_id=CORRELATION
        )

        assert settled.status is ResearchStatus.FAILED
        rebuilt = request_from_payload(
            workspace_id=WORKSPACE,
            payload=_the_only_notification(publisher).to_payload(),  # type: ignore[attr-defined]
        )
        assert "could not be completed" in rebuilt.summary
        assert rebuilt.recipient_id == REQUESTER

    async def test_the_failure_message_does_not_carry_the_exception(self) -> None:
        """⚠️ **The detail is recorded on the STATE and stays there.**

        ⛔ **A customer-facing summary carrying `RuntimeError: …` is an internal
        failure rendered as product copy** — 📁 [§15](../../../CLAUDE.md) and
        R4-03's rule that a customer-facing message names no identifier.
        """
        publisher = CapturingPublisher()
        request = _a_request()

        await _finish(ResearchThatRaises(), publisher).execute(
            request, _running(request), correlation_id=CORRELATION
        )

        rebuilt = request_from_payload(
            workspace_id=WORKSPACE,
            payload=_the_only_notification(publisher).to_payload(),  # type: ignore[attr-defined]
        )
        assert "RuntimeError" not in rebuilt.summary
        assert "RuntimeError" not in rebuilt.expectation

    async def test_nothing_to_research_reads_differently_from_a_completed_brief(self) -> None:
        """🔴 **A distinct sentence, not a softer one.**

        ⛔ *"Nothing to research"* **is an outcome about the ACCOUNT** — it has
        too little evidence to compare — **and reporting it as a completed brief
        would send somebody looking for findings that do not exist.**
        """
        empty, full = CapturingPublisher(), CapturingPublisher()
        request = _a_request()

        await _finish(ResearchThatReturns(None), empty).execute(
            request, _running(request), correlation_id=CORRELATION
        )
        await _finish(ResearchThatReturns(ResearchOutcome()), full).execute(
            request, _running(request), correlation_id=CORRELATION
        )

        nothing = request_from_payload(
            workspace_id=WORKSPACE,
            payload=_the_only_notification(empty).to_payload(),  # type: ignore[attr-defined]
        )
        brief = request_from_payload(
            workspace_id=WORKSPACE,
            payload=_the_only_notification(full).to_payload(),  # type: ignore[attr-defined]
        )

        assert nothing.summary != brief.summary
        assert nothing.expectation != brief.expectation, (
            "both outcomes ask the reader to do the same thing. One has a brief "
            "to read and the other does not, and an identical expectation sends "
            "somebody looking for findings that were never produced."
        )

    async def test_every_settled_outcome_states_what_is_expected(self) -> None:
        """📁 **The Definition of Done's fourth thing** — ⛔ and the one a
        notification system usually omits."""
        for research in (
            ResearchThatReturns(ResearchOutcome()),
            ResearchThatReturns(None),
            ResearchThatRaises(),
        ):
            publisher = CapturingPublisher()
            request = _a_request()
            await _finish(research, publisher).execute(
                request, _running(request), correlation_id=CORRELATION
            )
            rebuilt = request_from_payload(
                workspace_id=WORKSPACE,
                payload=_the_only_notification(publisher).to_payload(),  # type: ignore[attr-defined]
            )
            assert rebuilt.expectation.strip()
            assert rebuilt.summary.strip()
