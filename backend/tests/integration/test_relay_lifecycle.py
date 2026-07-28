"""Integration tests for the relay's continuous-run loop.

``run_forever`` is the mode the relay actually runs in, so its drain
behaviour and shutdown semantics deserve direct coverage rather than being
inferred from ``relay_once``.
"""

import asyncio
from datetime import UTC, datetime
from uuid import uuid4

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from signora_platform.event_bus import (
    EventEnvelope,
    InMemoryQueuePublisher,
    OutboxEventModel,
    OutboxRelay,
    SubscriptionRegistry,
)

pytestmark = pytest.mark.integration

CONSUMER = "lifecycle-consumer"
EVENT_TYPE = "lifecycle.test.event"


async def _noop(envelope: EventEnvelope) -> None:
    return None


@pytest.fixture
def registry() -> SubscriptionRegistry:
    reg = SubscriptionRegistry()
    reg.subscribe(consumer_name=CONSUMER, event_type=EVENT_TYPE, handler=_noop)
    return reg


async def _insert(factory: async_sessionmaker[AsyncSession], count: int) -> None:
    async with factory() as session, session.begin():
        for _ in range(count):
            session.add(
                OutboxEventModel(
                    event_id=uuid4(),
                    event_type=EVENT_TYPE,
                    event_version=1,
                    workspace_id=uuid4(),
                    occurred_at=datetime.now(UTC),
                    producer_module="test",
                    correlation_id=uuid4(),
                    causation_id=None,
                    payload={},
                    created_at=datetime.now(UTC),
                )
            )


async def test_run_forever_drains_the_backlog_then_idles(
    admin_session_factory: async_sessionmaker[AsyncSession], registry: SubscriptionRegistry
) -> None:
    """Drains fully on each wake-up rather than one batch per interval —
    otherwise a burst grows the backlog faster than it drains."""
    publisher = InMemoryQueuePublisher()
    relay = OutboxRelay(
        session_factory=admin_session_factory,
        queue_publisher=publisher,
        registry=registry,
        batch_size=5,
    )
    await _insert(admin_session_factory, 12)

    task = asyncio.create_task(relay.run_forever(poll_interval_seconds=0.05))
    await asyncio.sleep(0.4)
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task

    assert len(publisher.published) == 12, "backlog drained across multiple batches"
    async with admin_session_factory() as session:
        remaining = (
            await session.execute(
                text("SELECT count(*) FROM outbox_event WHERE relayed_at IS NULL")
            )
        ).scalar_one()
    assert remaining == 0


async def test_run_forever_picks_up_events_arriving_after_start(
    admin_session_factory: async_sessionmaker[AsyncSession], registry: SubscriptionRegistry
) -> None:
    publisher = InMemoryQueuePublisher()
    relay = OutboxRelay(
        session_factory=admin_session_factory, queue_publisher=publisher, registry=registry
    )

    task = asyncio.create_task(relay.run_forever(poll_interval_seconds=0.05))
    await asyncio.sleep(0.1)
    await _insert(admin_session_factory, 3)
    await asyncio.sleep(0.3)
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task

    assert len(publisher.published) == 3


async def test_cancellation_is_clean_and_loses_nothing(
    admin_session_factory: async_sessionmaker[AsyncSession], registry: SubscriptionRegistry
) -> None:
    """SIGTERM during a rolling deploy must not strand events. Each batch
    runs in a transaction that commits or rolls back atomically, so a
    cancelled relay never leaves an event half-relayed."""
    publisher = InMemoryQueuePublisher()
    relay = OutboxRelay(
        session_factory=admin_session_factory, queue_publisher=publisher, registry=registry
    )
    await _insert(admin_session_factory, 4)

    task = asyncio.create_task(relay.run_forever(poll_interval_seconds=0.05))
    await asyncio.sleep(0.2)
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task

    async with admin_session_factory() as session:
        half_relayed = (
            await session.execute(
                text(
                    "SELECT count(*) FROM outbox_event "
                    "WHERE relayed_at IS NULL AND relay_attempts > 0"
                )
            )
        ).scalar_one()
    assert half_relayed == 0
