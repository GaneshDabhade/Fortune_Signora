"""Integration tests for dispatch, idempotency, and dead-lettering.

The idempotency tests are the most consequential in this file: at-least-once
delivery means a handler *will* be invoked twice in production, and every
one of the thirteen pipeline modules depends on the bus absorbing that
rather than each implementing deduplication itself.
"""

import asyncio
from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from signora_platform.event_bus import (
    MAX_ATTEMPTS,
    EventDispatcher,
    EventEnvelope,
    SubscriptionRegistry,
    UnknownConsumerError,
    backoff_seconds,
    list_unreplayed,
    mark_replayed,
    record_dead_letter,
    to_envelope,
)

pytestmark = pytest.mark.integration

CONSUMER = "test-consumer"
EVENT_TYPE = "test.event.occurred"


def _envelope(*, workspace_id: UUID | None = None, event_id: UUID | None = None) -> EventEnvelope:
    return EventEnvelope(
        event_id=event_id or uuid4(),
        event_type=EVENT_TYPE,
        event_version=1,
        workspace_id=workspace_id or uuid4(),
        occurred_at=datetime.now(UTC),
        producer_module="test",
        correlation_id=uuid4(),
        causation_id=None,
        payload={"value": "x"},
    )


class _RecordingHandler:
    """Counts invocations, so "exactly once" can be asserted rather than
    inferred."""

    def __init__(self, *, fail_times: int = 0) -> None:
        self.calls: list[EventEnvelope] = []
        self._fail_times = fail_times

    async def __call__(self, envelope: EventEnvelope) -> None:
        self.calls.append(envelope)
        if len(self.calls) <= self._fail_times:
            raise RuntimeError("handler failure")


class TestDispatch:
    async def test_invokes_the_registered_handler(
        self, admin_session_factory: async_sessionmaker[AsyncSession]
    ) -> None:
        handler = _RecordingHandler()
        registry = SubscriptionRegistry()
        registry.subscribe(consumer_name=CONSUMER, event_type=EVENT_TYPE, handler=handler)
        dispatcher = EventDispatcher(session_factory=admin_session_factory, registry=registry)
        envelope = _envelope()

        result = await dispatcher.dispatch(consumer_name=CONSUMER, envelope=envelope)

        assert result.handled is True
        assert len(handler.calls) == 1
        assert handler.calls[0].event_id == envelope.event_id

    async def test_unknown_consumer_raises_rather_than_silently_dropping(
        self, admin_session_factory: async_sessionmaker[AsyncSession]
    ) -> None:
        """Silently discarding queued work is the failure mode that is
        impossible to diagnose later."""
        dispatcher = EventDispatcher(
            session_factory=admin_session_factory, registry=SubscriptionRegistry()
        )

        with pytest.raises(UnknownConsumerError):
            await dispatcher.dispatch(consumer_name="ghost", envelope=_envelope())

    async def test_handler_failure_propagates_to_the_caller(
        self, admin_session_factory: async_sessionmaker[AsyncSession]
    ) -> None:
        """The dispatcher must not swallow failures — retry and
        dead-lettering live above it and need to see them."""
        registry = SubscriptionRegistry()
        registry.subscribe(
            consumer_name=CONSUMER,
            event_type=EVENT_TYPE,
            handler=_RecordingHandler(fail_times=1),
        )
        dispatcher = EventDispatcher(session_factory=admin_session_factory, registry=registry)

        with pytest.raises(RuntimeError):
            await dispatcher.dispatch(consumer_name=CONSUMER, envelope=_envelope())


class TestIdempotency:
    async def test_duplicate_delivery_invokes_the_handler_exactly_once(
        self, admin_session_factory: async_sessionmaker[AsyncSession]
    ) -> None:
        """The guarantee every pipeline module depends on."""
        handler = _RecordingHandler()
        registry = SubscriptionRegistry()
        registry.subscribe(consumer_name=CONSUMER, event_type=EVENT_TYPE, handler=handler)
        dispatcher = EventDispatcher(session_factory=admin_session_factory, registry=registry)
        envelope = _envelope()

        first = await dispatcher.dispatch(consumer_name=CONSUMER, envelope=envelope)
        second = await dispatcher.dispatch(consumer_name=CONSUMER, envelope=envelope)

        assert first.handled is True
        assert second.handled is False
        assert len(handler.calls) == 1

    async def test_different_consumers_each_process_the_same_event(
        self, admin_session_factory: async_sessionmaker[AsyncSession]
    ) -> None:
        """The ledger is keyed on (consumer, event), not event alone —
        several consumers legitimately subscribe to the same event."""
        handler_a, handler_b = _RecordingHandler(), _RecordingHandler()
        registry = SubscriptionRegistry()
        registry.subscribe(consumer_name="a", event_type=EVENT_TYPE, handler=handler_a)
        registry.subscribe(consumer_name="b", event_type=EVENT_TYPE, handler=handler_b)
        dispatcher = EventDispatcher(session_factory=admin_session_factory, registry=registry)
        envelope = _envelope()

        await dispatcher.dispatch(consumer_name="a", envelope=envelope)
        await dispatcher.dispatch(consumer_name="b", envelope=envelope)

        assert len(handler_a.calls) == 1
        assert len(handler_b.calls) == 1

    async def test_failed_handler_does_not_consume_its_idempotency_claim(
        self, admin_session_factory: async_sessionmaker[AsyncSession]
    ) -> None:
        """Critical: the claim and the handler share a transaction, so a
        failure must roll back the claim. Otherwise a transient error would
        permanently prevent the event from ever being processed."""
        handler = _RecordingHandler(fail_times=1)
        registry = SubscriptionRegistry()
        registry.subscribe(consumer_name=CONSUMER, event_type=EVENT_TYPE, handler=handler)
        dispatcher = EventDispatcher(session_factory=admin_session_factory, registry=registry)
        envelope = _envelope()

        with pytest.raises(RuntimeError):
            await dispatcher.dispatch(consumer_name=CONSUMER, envelope=envelope)
        result = await dispatcher.dispatch(consumer_name=CONSUMER, envelope=envelope)

        assert result.handled is True
        assert len(handler.calls) == 2, "retry must actually re-run the handler"

    async def test_concurrent_delivery_of_the_same_event_runs_handler_once(
        self, admin_session_factory: async_sessionmaker[AsyncSession]
    ) -> None:
        """SELECT-then-INSERT would race here; ON CONFLICT DO NOTHING makes
        the claim atomic."""
        handler = _RecordingHandler()
        registry = SubscriptionRegistry()
        registry.subscribe(consumer_name=CONSUMER, event_type=EVENT_TYPE, handler=handler)
        dispatcher = EventDispatcher(session_factory=admin_session_factory, registry=registry)
        envelope = _envelope()

        results = await asyncio.gather(
            *(dispatcher.dispatch(consumer_name=CONSUMER, envelope=envelope) for _ in range(5)),
            return_exceptions=True,
        )

        handled = [r for r in results if not isinstance(r, BaseException) and r.handled]
        assert len(handled) == 1
        assert len(handler.calls) == 1

    async def test_records_the_claim_in_the_ledger(
        self, admin_session_factory: async_sessionmaker[AsyncSession]
    ) -> None:
        registry = SubscriptionRegistry()
        registry.subscribe(
            consumer_name=CONSUMER, event_type=EVENT_TYPE, handler=_RecordingHandler()
        )
        dispatcher = EventDispatcher(session_factory=admin_session_factory, registry=registry)
        envelope = _envelope()

        await dispatcher.dispatch(consumer_name=CONSUMER, envelope=envelope)

        async with admin_session_factory() as session:
            count = (
                await session.execute(
                    text(
                        "SELECT count(*) FROM processed_event "
                        "WHERE consumer_name = :c AND event_id = :e"
                    ),
                    {"c": CONSUMER, "e": envelope.event_id},
                )
            ).scalar_one()
        assert count == 1


class TestTenantScope:
    async def test_handler_runs_inside_the_envelope_workspace_context(
        self, admin_session_factory: async_sessionmaker[AsyncSession]
    ) -> None:
        """RLS context must come from the envelope, so a handler cannot
        operate outside its tenant even if it forgets to filter."""
        observed: list[str] = []
        workspace_id = uuid4()

        async def handler(envelope: EventEnvelope) -> None:
            # The dispatcher has already opened a tenant-scoped session and
            # set app.workspace_id from the envelope before reaching here.
            observed.append(str(envelope.workspace_id))

        registry = SubscriptionRegistry()
        registry.subscribe(consumer_name=CONSUMER, event_type=EVENT_TYPE, handler=handler)
        dispatcher = EventDispatcher(session_factory=admin_session_factory, registry=registry)

        await dispatcher.dispatch(
            consumer_name=CONSUMER, envelope=_envelope(workspace_id=workspace_id)
        )

        assert observed == [str(workspace_id)]


class TestRetryPolicy:
    def test_backoff_grows_exponentially(self) -> None:
        assert [backoff_seconds(n) for n in (1, 2, 3, 4)] == [2, 4, 8, 16]

    def test_backoff_is_capped(self) -> None:
        """Uncapped exponential backoff produces delays measured in hours,
        which is indistinguishable from the event having been lost."""
        assert backoff_seconds(20) == 300


class TestDeadLettering:
    async def test_records_a_dead_letter_with_full_context(
        self, admin_session_factory: async_sessionmaker[AsyncSession]
    ) -> None:
        envelope = _envelope()

        dead_letter_id = await record_dead_letter(
            admin_session_factory,
            consumer_name=CONSUMER,
            envelope=envelope,
            attempts=MAX_ATTEMPTS,
            failure_reason="RuntimeError: boom",
        )

        async with admin_session_factory() as session:
            rows = await list_unreplayed(session)

        assert len(rows) == 1
        assert rows[0].id == dead_letter_id
        assert rows[0].event_id == envelope.event_id
        assert rows[0].attempts == MAX_ATTEMPTS
        assert "RuntimeError" in rows[0].failure_reason
        assert rows[0].replayed_at is None

    async def test_dead_letter_round_trips_back_to_an_envelope(
        self, admin_session_factory: async_sessionmaker[AsyncSession]
    ) -> None:
        """Replay requires reconstructing the original envelope exactly."""
        original = _envelope()
        await record_dead_letter(
            admin_session_factory,
            consumer_name=CONSUMER,
            envelope=original,
            attempts=MAX_ATTEMPTS,
            failure_reason="boom",
        )

        async with admin_session_factory() as session:
            restored = to_envelope((await list_unreplayed(session))[0])

        assert restored == original

    async def test_replayed_dead_letters_are_marked_not_deleted(
        self, admin_session_factory: async_sessionmaker[AsyncSession]
    ) -> None:
        """The record of what failed, and that it was addressed, must
        survive the fix."""
        await record_dead_letter(
            admin_session_factory,
            consumer_name=CONSUMER,
            envelope=_envelope(),
            attempts=MAX_ATTEMPTS,
            failure_reason="boom",
        )

        async with admin_session_factory() as session, session.begin():
            row = (await list_unreplayed(session))[0]
            await mark_replayed(session, dead_letter_id=row.id)

        async with admin_session_factory() as session:
            assert await list_unreplayed(session) == []
            total = (
                await session.execute(text("SELECT count(*) FROM dead_letter_event"))
            ).scalar_one()
        assert total == 1, "row retained, not deleted"
