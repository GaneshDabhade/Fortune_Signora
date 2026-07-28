"""Invariants: accepted work is not lost, is not applied twice, and failures
end somewhere a human will find them.

These are security invariants because the pipeline carries workspace data.
An event that vanishes silently is a correctness failure; an event dispatched
under the wrong workspace, or replayed into a second write, is a tenancy
failure (docs/architecture/06-events.md, docs/architecture/07-data-flow.md).
"""

from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest
from pytest_mock import MockerFixture
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from signora_platform.event_bus import (
    MAX_ATTEMPTS,
    EventDispatcher,
    EventEnvelope,
    SubscriptionRegistry,
    backoff_seconds,
    list_unreplayed,
    record_dead_letter,
    to_envelope,
)
from signora_platform.event_bus import dispatch as dispatch_module
from signora_platform.event_bus.dead_letter import MAX_BACKOFF_SECONDS

pytestmark = pytest.mark.integration

CONSUMER = "invariant-consumer"
EVENT_TYPE = "invariant.event.occurred"


def _envelope(*, workspace_id: UUID | None = None, event_id: UUID | None = None) -> EventEnvelope:
    return EventEnvelope(
        event_id=event_id or uuid4(),
        event_type=EVENT_TYPE,
        event_version=1,
        workspace_id=workspace_id or uuid4(),
        occurred_at=datetime.now(UTC),
        producer_module="invariants",
        correlation_id=uuid4(),
        causation_id=None,
        payload={"value": "x"},
    )


class _CountingHandler:
    def __init__(self, *, fail: bool = False) -> None:
        self.calls: list[EventEnvelope] = []
        self._fail = fail

    async def __call__(self, envelope: EventEnvelope) -> None:
        self.calls.append(envelope)
        if self._fail:
            raise RuntimeError("handler failed")


def _dispatcher(
    session_factory: async_sessionmaker[AsyncSession], handler: _CountingHandler
) -> EventDispatcher:
    registry = SubscriptionRegistry()
    registry.subscribe(consumer_name=CONSUMER, event_type=EVENT_TYPE, handler=handler)
    return EventDispatcher(session_factory=session_factory, registry=registry)


class TestEventDurability:
    async def test_an_event_is_committed_atomically_with_the_state_change(
        self, session_factory: async_sessionmaker[AsyncSession]
    ) -> None:
        """The transactional outbox exists so an event cannot describe a
        write that never landed, and a write cannot land unannounced. If the
        causing transaction rolls back, the event must go with it."""
        from modules.workspace_tenancy.application.use_cases import CreateWorkspaceInput
        from modules.workspace_tenancy.infrastructure.composition import build_use_cases
        from signora_platform.db import user_scoped_session

        user_id = uuid4()
        with pytest.raises(RuntimeError):
            async with user_scoped_session(session_factory, user_id=user_id) as session:
                await build_use_cases(session).create_workspace.execute(
                    CreateWorkspaceInput(name="Rolled back", created_by=user_id),
                    correlation_id=uuid4(),
                )
                raise RuntimeError("caller fails after the domain write")

        async with session_factory() as session, session.begin():
            outbox_rows = (
                await session.execute(text("SELECT count(*) FROM outbox_event"))
            ).scalar_one()
            workspace_rows = (
                await session.execute(text("SELECT count(*) FROM workspace"))
            ).scalar_one()

        assert outbox_rows == 0, "an event survived the rollback of the write that caused it"
        assert workspace_rows == 0

    async def test_every_event_carries_the_context_needed_to_trace_it(
        self, session_factory: async_sessionmaker[AsyncSession]
    ) -> None:
        """``workspace_id`` makes an event scopable, ``correlation_id`` makes
        a pipeline run followable end to end. An event missing either is
        undebuggable once it is one of thousands."""
        envelope = _envelope()

        assert envelope.workspace_id is not None
        assert envelope.correlation_id is not None

        for required in ("event_id", "workspace_id", "correlation_id", "event_type"):
            assert required in EventEnvelope.model_fields
            assert EventEnvelope.model_fields[required].is_required()


class TestIdempotency:
    async def test_a_redelivered_event_runs_its_handler_once(
        self, session_factory: async_sessionmaker[AsyncSession]
    ) -> None:
        """At-least-once delivery guarantees a handler *will* see duplicates.
        The bus absorbs them centrally so that thirteen modules do not each
        implement deduplication, and none forgets."""
        handler = _CountingHandler()
        dispatcher = _dispatcher(session_factory, handler)
        envelope = _envelope()

        await dispatcher.dispatch(consumer_name=CONSUMER, envelope=envelope)
        await dispatcher.dispatch(consumer_name=CONSUMER, envelope=envelope)

        assert len(handler.calls) == 1

    async def test_a_failed_handler_does_not_consume_its_idempotency_claim(
        self, session_factory: async_sessionmaker[AsyncSession]
    ) -> None:
        """Otherwise the first failure would permanently suppress every
        retry — the event would be marked processed while having done
        nothing, which is worse than losing it outright because it looks
        successful."""
        failing = _CountingHandler(fail=True)
        envelope = _envelope()

        with pytest.raises(RuntimeError):
            await _dispatcher(session_factory, failing).dispatch(
                consumer_name=CONSUMER, envelope=envelope
            )

        succeeding = _CountingHandler()
        await _dispatcher(session_factory, succeeding).dispatch(
            consumer_name=CONSUMER, envelope=envelope
        )

        assert len(succeeding.calls) == 1

    async def test_idempotency_is_scoped_per_consumer(
        self, session_factory: async_sessionmaker[AsyncSession]
    ) -> None:
        """Two consumers of the same event must each see it. A ledger keyed
        on ``event_id`` alone would let whichever consumer ran first silently
        starve the others."""
        first, second = _CountingHandler(), _CountingHandler()
        registry = SubscriptionRegistry()
        registry.subscribe(consumer_name="consumer-a", event_type=EVENT_TYPE, handler=first)
        registry.subscribe(consumer_name="consumer-b", event_type=EVENT_TYPE, handler=second)
        dispatcher = EventDispatcher(session_factory=session_factory, registry=registry)
        envelope = _envelope()

        await dispatcher.dispatch(consumer_name="consumer-a", envelope=envelope)
        await dispatcher.dispatch(consumer_name="consumer-b", envelope=envelope)

        assert len(first.calls) == 1
        assert len(second.calls) == 1

    async def test_every_dispatch_establishes_tenant_scope_from_the_envelope(
        self, session_factory: async_sessionmaker[AsyncSession], mocker: MockerFixture
    ) -> None:
        """Background work is subject to the same tenancy rules as a request.
        A handler running with no workspace context — or with the previous
        event's — is the async equivalent of a cross-tenant read.

        The dispatcher is spied rather than the handler inspected, because
        the handler is never given the session: the scoping happens above it,
        which is exactly the property worth pinning. Asserting only that the
        envelope reached the handler would pass even if the session were
        never scoped at all.
        """
        spy = mocker.spy(dispatch_module, "tenant_scoped_session")
        workspace_id = uuid4()

        await _dispatcher(session_factory, _CountingHandler()).dispatch(
            consumer_name=CONSUMER, envelope=_envelope(workspace_id=workspace_id)
        )

        spy.assert_called_once()
        assert spy.call_args.kwargs["workspace_id"] == workspace_id

    async def test_a_handler_receives_its_events_workspace(
        self, session_factory: async_sessionmaker[AsyncSession]
    ) -> None:
        """The complement to the above: scope is set from the same envelope
        the handler sees, so the two cannot drift apart."""
        handler = _CountingHandler()
        workspace_id = uuid4()

        await _dispatcher(session_factory, handler).dispatch(
            consumer_name=CONSUMER, envelope=_envelope(workspace_id=workspace_id)
        )

        assert [call.workspace_id for call in handler.calls] == [workspace_id]


class TestRetryPolicy:
    def test_backoff_grows_exponentially(self) -> None:
        delays = [backoff_seconds(attempt) for attempt in range(1, 5)]

        assert delays == sorted(delays)
        assert delays[-1] > delays[0]

    def test_backoff_is_capped_at_an_operationally_sane_bound(self) -> None:
        """Uncapped exponential backoff reaches days by attempt 15, which is
        indistinguishable from the event having been dropped.

        Asserted against an absolute number of seconds, not against
        ``MAX_BACKOFF_SECONDS``. Comparing the function to the constant it
        uses is a tautology that passes for any cap, including a nine-figure
        one — verified by raising the constant and watching this test stay
        green before it was rewritten.
        """
        one_hour = 3600

        assert backoff_seconds(50) <= one_hour
        assert one_hour >= MAX_BACKOFF_SECONDS

    def test_retries_are_finite(self) -> None:
        """A permanently-failing handler must eventually stop and
        dead-letter. Infinite retry burns a worker slot forever and hides the
        failure behind a queue that never drains."""
        assert 1 < MAX_ATTEMPTS <= 10


class TestDeadLetterQueue:
    async def test_an_exhausted_event_is_recorded_with_enough_context_to_replay(
        self, admin_session_factory: async_sessionmaker[AsyncSession]
    ) -> None:
        """A dead letter that cannot be turned back into the original event
        is an alert, not a recovery mechanism."""
        envelope = _envelope()

        await record_dead_letter(
            admin_session_factory,
            envelope=envelope,
            consumer_name=CONSUMER,
            failure_reason="handler failed",
            attempts=MAX_ATTEMPTS,
        )

        async with admin_session_factory() as session, session.begin():
            rows = await list_unreplayed(session)
            restored = to_envelope(rows[0])

        assert len(rows) == 1
        assert restored.event_id == envelope.event_id
        assert restored.workspace_id == envelope.workspace_id
        assert restored.correlation_id == envelope.correlation_id
        assert restored.payload == envelope.payload

    async def test_a_replayed_dead_letter_is_marked_rather_than_deleted(
        self, admin_session_factory: async_sessionmaker[AsyncSession]
    ) -> None:
        """The record of a failure is evidence. Deleting on replay destroys
        the only trace that the pipeline dropped something, and with it any
        chance of noticing a pattern."""
        from signora_platform.event_bus import mark_replayed

        await record_dead_letter(
            admin_session_factory,
            envelope=_envelope(),
            consumer_name=CONSUMER,
            failure_reason="boom",
            attempts=MAX_ATTEMPTS,
        )

        async with admin_session_factory() as session, session.begin():
            row_id = (await list_unreplayed(session))[0].id
            await mark_replayed(session, dead_letter_id=row_id)

        async with admin_session_factory() as session, session.begin():
            assert await list_unreplayed(session) == []
            still_present = (
                await session.execute(text("SELECT count(*) FROM dead_letter_event"))
            ).scalar_one()

        assert still_present == 1
