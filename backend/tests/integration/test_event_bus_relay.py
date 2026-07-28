"""Integration tests for the outbox relay.

These assert the relay's correctness properties against a real PostgreSQL,
in priority order: no event is lost, no event is enqueued twice by
concurrent relays, and a failing event does not block the queue.

The relay is tested with an in-memory queue publisher so that claiming,
marking, and failure semantics — the parts most likely to harbour a
correctness bug — are exercised without also requiring Redis. Redis-backed
delivery is covered in ``test_event_bus_dispatch.py``.
"""

from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID, uuid4

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from signora_platform.event_bus import (
    EventEnvelope,
    InMemoryQueuePublisher,
    OutboxEventModel,
    OutboxRelay,
    SubscriptionRegistry,
    queue_name_for,
)

pytestmark = pytest.mark.integration

CONSUMER = "test-consumer"
EVENT_TYPE = "test.event.occurred"


async def _noop_handler(envelope: EventEnvelope) -> None:
    return None


@pytest.fixture
def registry() -> SubscriptionRegistry:
    reg = SubscriptionRegistry()
    reg.subscribe(consumer_name=CONSUMER, event_type=EVENT_TYPE, handler=_noop_handler)
    return reg


@pytest.fixture
def publisher() -> InMemoryQueuePublisher:
    return InMemoryQueuePublisher()


@pytest.fixture
def relay(
    admin_session_factory: async_sessionmaker[AsyncSession],
    publisher: InMemoryQueuePublisher,
    registry: SubscriptionRegistry,
) -> OutboxRelay:
    return OutboxRelay(
        session_factory=admin_session_factory, queue_publisher=publisher, registry=registry
    )


async def _insert_outbox_event(
    session_factory: async_sessionmaker[AsyncSession],
    *,
    event_type: str = EVENT_TYPE,
    created_at: datetime | None = None,
    **overrides: Any,
) -> UUID:
    event_id = uuid4()
    async with session_factory() as session, session.begin():
        session.add(
            OutboxEventModel(
                event_id=event_id,
                event_type=event_type,
                event_version=1,
                workspace_id=overrides.get("workspace_id", uuid4()),
                occurred_at=datetime.now(UTC),
                producer_module="test",
                correlation_id=overrides.get("correlation_id", uuid4()),
                causation_id=None,
                payload={"value": "x"},
                created_at=created_at or datetime.now(UTC),
            )
        )
    return event_id


class TestRelayHappyPath:
    async def test_relays_an_event_to_its_subscriber_queue(
        self,
        relay: OutboxRelay,
        publisher: InMemoryQueuePublisher,
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        event_id = await _insert_outbox_event(admin_session_factory)

        relayed = await relay.relay_once()

        assert relayed == 1
        assert len(publisher.published) == 1
        assert publisher.published[0]["consumer_name"] == CONSUMER
        assert publisher.published[0]["queue_name"] == queue_name_for("default")
        assert publisher.published[0]["envelope"].event_id == event_id

    async def test_marks_the_row_relayed(
        self,
        relay: OutboxRelay,
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        event_id = await _insert_outbox_event(admin_session_factory)

        await relay.relay_once()

        async with admin_session_factory() as session:
            relayed_at = (
                await session.execute(
                    text("SELECT relayed_at FROM outbox_event WHERE event_id = :id"),
                    {"id": event_id},
                )
            ).scalar_one()
        assert relayed_at is not None

    async def test_does_not_relay_the_same_event_twice(
        self,
        relay: OutboxRelay,
        publisher: InMemoryQueuePublisher,
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        await _insert_outbox_event(admin_session_factory)

        first = await relay.relay_once()
        second = await relay.relay_once()

        assert (first, second) == (1, 0)
        assert len(publisher.published) == 1

    async def test_preserves_envelope_fields_end_to_end(
        self,
        relay: OutboxRelay,
        publisher: InMemoryQueuePublisher,
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        """Correlation identifiers must survive the hand-off — they are the
        only way to trace a pipeline run across processes."""
        workspace_id, correlation_id = uuid4(), uuid4()
        await _insert_outbox_event(
            admin_session_factory, workspace_id=workspace_id, correlation_id=correlation_id
        )

        await relay.relay_once()

        envelope = publisher.published[0]["envelope"]
        assert envelope.workspace_id == workspace_id
        assert envelope.correlation_id == correlation_id
        assert envelope.producer_module == "test"

    async def test_relays_oldest_events_first(
        self,
        relay: OutboxRelay,
        publisher: InMemoryQueuePublisher,
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        now = datetime.now(UTC)
        older = await _insert_outbox_event(
            admin_session_factory, created_at=now - timedelta(minutes=5)
        )
        newer = await _insert_outbox_event(admin_session_factory, created_at=now)

        await relay.relay_once()

        order = [p["envelope"].event_id for p in publisher.published]
        assert order == [older, newer]


class TestFanOut:
    async def test_publishes_once_per_subscriber(
        self,
        admin_session_factory: async_sessionmaker[AsyncSession],
        publisher: InMemoryQueuePublisher,
    ) -> None:
        registry = SubscriptionRegistry()
        registry.subscribe(consumer_name="a", event_type=EVENT_TYPE, handler=_noop_handler)
        registry.subscribe(
            consumer_name="b", event_type=EVENT_TYPE, handler=_noop_handler, pool="graph"
        )
        relay = OutboxRelay(
            session_factory=admin_session_factory,
            queue_publisher=publisher,
            registry=registry,
        )
        await _insert_outbox_event(admin_session_factory)

        await relay.relay_once()

        assert {p["consumer_name"] for p in publisher.published} == {"a", "b"}
        assert {p["queue_name"] for p in publisher.published} == {
            queue_name_for("default"),
            queue_name_for("graph"),
        }

    async def test_event_with_no_subscribers_is_marked_relayed(
        self,
        relay: OutboxRelay,
        publisher: InMemoryQueuePublisher,
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        """Publishing before anyone consumes is how the pipeline is built
        incrementally — an unsubscribed event is not an error and must not
        accumulate forever in the backlog."""
        await _insert_outbox_event(admin_session_factory, event_type="nobody.listens")

        relayed = await relay.relay_once()

        assert relayed == 1
        assert publisher.published == []


class TestFailureHandling:
    async def test_enqueue_failure_leaves_the_event_unrelayed(
        self,
        relay: OutboxRelay,
        publisher: InMemoryQueuePublisher,
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        """The core no-loss guarantee: if the hand-off fails, the event
        stays claimable rather than being marked done."""
        event_id = await _insert_outbox_event(admin_session_factory)
        publisher.fail_next = True

        relayed = await relay.relay_once()

        assert relayed == 0
        async with admin_session_factory() as session:
            row = (
                await session.execute(
                    text(
                        "SELECT relayed_at, relay_attempts, relay_failed_at "
                        "FROM outbox_event WHERE event_id = :id"
                    ),
                    {"id": event_id},
                )
            ).one()
        assert row.relayed_at is None
        assert row.relay_attempts == 1
        assert row.relay_failed_at is not None

    async def test_failed_event_is_retried_after_backoff_elapses(
        self,
        relay: OutboxRelay,
        publisher: InMemoryQueuePublisher,
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        event_id = await _insert_outbox_event(admin_session_factory)
        publisher.fail_next = True
        await relay.relay_once()

        # Simulate the backoff window having passed.
        async with admin_session_factory() as session, session.begin():
            await session.execute(
                text(
                    "UPDATE outbox_event SET relay_failed_at = now() - interval '1 hour' "
                    "WHERE event_id = :id"
                ),
                {"id": event_id},
            )

        publisher.fail_next = False
        relayed = await relay.relay_once()

        assert relayed == 1

    async def test_recently_failed_event_is_skipped_during_backoff(
        self,
        relay: OutboxRelay,
        publisher: InMemoryQueuePublisher,
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        """A persistently failing row must not consume every batch and
        starve healthy events behind it."""
        await _insert_outbox_event(admin_session_factory)
        publisher.fail_next = True
        await relay.relay_once()

        publisher.fail_next = False
        relayed = await relay.relay_once()

        assert relayed == 0, "should still be inside the backoff window"

    async def test_healthy_events_still_relay_while_one_is_backing_off(
        self,
        relay: OutboxRelay,
        publisher: InMemoryQueuePublisher,
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        now = datetime.now(UTC)
        await _insert_outbox_event(admin_session_factory, created_at=now - timedelta(minutes=5))
        publisher.fail_next = True
        await relay.relay_once()

        publisher.fail_next = False
        healthy = await _insert_outbox_event(admin_session_factory, created_at=now)
        relayed = await relay.relay_once()

        assert relayed == 1
        assert publisher.published[0]["envelope"].event_id == healthy


class TestConcurrency:
    async def test_two_relays_never_enqueue_the_same_event_twice(
        self,
        admin_session_factory: async_sessionmaker[AsyncSession],
        registry: SubscriptionRegistry,
    ) -> None:
        """FOR UPDATE SKIP LOCKED is what makes horizontal relay scaling
        safe. Without it, two instances would each claim and enqueue the
        same backlog."""
        import asyncio

        for _ in range(20):
            await _insert_outbox_event(admin_session_factory)

        publisher_a, publisher_b = InMemoryQueuePublisher(), InMemoryQueuePublisher()
        relay_a = OutboxRelay(
            session_factory=admin_session_factory,
            queue_publisher=publisher_a,
            registry=registry,
        )
        relay_b = OutboxRelay(
            session_factory=admin_session_factory,
            queue_publisher=publisher_b,
            registry=registry,
        )

        await asyncio.gather(relay_a.relay_once(), relay_b.relay_once())

        ids_a = [p["envelope"].event_id for p in publisher_a.published]
        ids_b = [p["envelope"].event_id for p in publisher_b.published]
        assert len(ids_a) + len(ids_b) == 20, "every event relayed exactly once in total"
        assert set(ids_a).isdisjoint(set(ids_b)), "no event claimed by both relays"
