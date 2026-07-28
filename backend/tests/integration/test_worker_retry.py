"""Integration tests for the worker's retry and dead-letter behaviour.

This is the layer that decides whether a failing event is retried or
abandoned. Getting it wrong in either direction is costly: retry forever and
one poison event consumes a worker slot indefinitely; abandon too eagerly
and a transient database blip silently drops real work.
"""

from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from apps.worker.main import dispatch_event
from signora_platform.event_bus import (
    MAX_ATTEMPTS,
    EventDispatcher,
    EventEnvelope,
    SubscriptionRegistry,
)

pytestmark = pytest.mark.integration

CONSUMER = "retry-consumer"
EVENT_TYPE = "retry.test.event"


def _envelope() -> EventEnvelope:
    return EventEnvelope(
        event_id=uuid4(),
        event_type=EVENT_TYPE,
        event_version=1,
        workspace_id=uuid4(),
        occurred_at=datetime.now(UTC),
        producer_module="test",
        correlation_id=uuid4(),
        causation_id=None,
        payload={},
    )


def _context(
    factory: async_sessionmaker[AsyncSession],
    registry: SubscriptionRegistry,
    *,
    attempt: int,
) -> dict[str, Any]:
    return {
        "session_factory": factory,
        "dispatcher": EventDispatcher(session_factory=factory, registry=registry),
        "job_try": attempt,
    }


class _AlwaysFails:
    def __init__(self) -> None:
        self.calls = 0

    async def __call__(self, envelope: EventEnvelope) -> None:
        self.calls += 1
        raise RuntimeError("deterministic failure")


async def test_non_final_attempt_raises_so_arq_retries(
    admin_session_factory: async_sessionmaker[AsyncSession], monkeypatch: pytest.MonkeyPatch
) -> None:
    """Re-raising is what triggers ARQ's retry — swallowing here would
    silently drop the event after one attempt."""
    # Backoff is real in production; skipped here so the test is fast.
    monkeypatch.setattr("apps.worker.main.asyncio.sleep", _no_sleep)

    handler = _AlwaysFails()
    registry = SubscriptionRegistry()
    registry.subscribe(consumer_name=CONSUMER, event_type=EVENT_TYPE, handler=handler)
    ctx = _context(admin_session_factory, registry, attempt=1)

    with pytest.raises(RuntimeError):
        await dispatch_event(ctx, CONSUMER, _envelope().model_dump(mode="json"))

    assert handler.calls == 1


async def test_final_attempt_dead_letters_and_does_not_raise(
    admin_session_factory: async_sessionmaker[AsyncSession], monkeypatch: pytest.MonkeyPatch
) -> None:
    """On the last attempt the event is dead-lettered and the task returns
    normally. Raising there would leave ARQ retrying an event we have
    deliberately given up on."""
    monkeypatch.setattr("apps.worker.main.asyncio.sleep", _no_sleep)

    handler = _AlwaysFails()
    registry = SubscriptionRegistry()
    registry.subscribe(consumer_name=CONSUMER, event_type=EVENT_TYPE, handler=handler)
    ctx = _context(admin_session_factory, registry, attempt=MAX_ATTEMPTS)
    envelope = _envelope()

    await dispatch_event(ctx, CONSUMER, envelope.model_dump(mode="json"))

    async with admin_session_factory() as session:
        row = (
            await session.execute(
                text(
                    "SELECT attempts, failure_reason, replayed_at "
                    "FROM dead_letter_event WHERE event_id = :e"
                ),
                {"e": envelope.event_id},
            )
        ).one()
    assert row.attempts == MAX_ATTEMPTS
    assert "RuntimeError" in row.failure_reason
    assert row.replayed_at is None


async def test_successful_handler_neither_retries_nor_dead_letters(
    admin_session_factory: async_sessionmaker[AsyncSession],
) -> None:
    calls: list[EventEnvelope] = []

    async def handler(envelope: EventEnvelope) -> None:
        calls.append(envelope)

    registry = SubscriptionRegistry()
    registry.subscribe(consumer_name=CONSUMER, event_type=EVENT_TYPE, handler=handler)
    ctx = _context(admin_session_factory, registry, attempt=1)

    await dispatch_event(ctx, CONSUMER, _envelope().model_dump(mode="json"))

    assert len(calls) == 1
    async with admin_session_factory() as session:
        dead = (await session.execute(text("SELECT count(*) FROM dead_letter_event"))).scalar_one()
    assert dead == 0


async def test_envelope_survives_json_round_trip_through_the_queue(
    admin_session_factory: async_sessionmaker[AsyncSession],
) -> None:
    """The envelope crosses a process boundary as JSON; every field must
    survive, or correlation breaks precisely where it is needed most."""
    received: list[EventEnvelope] = []

    async def handler(envelope: EventEnvelope) -> None:
        received.append(envelope)

    registry = SubscriptionRegistry()
    registry.subscribe(consumer_name=CONSUMER, event_type=EVENT_TYPE, handler=handler)
    ctx = _context(admin_session_factory, registry, attempt=1)
    original = _envelope()

    await dispatch_event(ctx, CONSUMER, original.model_dump(mode="json"))

    assert received[0] == original


async def _no_sleep(_seconds: float) -> None:
    return None
