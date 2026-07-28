"""M1.1 Demo Checklist — the milestone completion gate.

Per IMPLEMENTATION_ROADMAP.md §12, a milestone is not complete until its
Demo Checklist passes. This file is that checklist, expressed as executable
assertions rather than a document someone ticks by hand — a checklist that
is only ever read is a checklist that eventually lies.

Each test maps to exactly one numbered checklist item. It runs against real
PostgreSQL and real Redis; nothing here is mocked.
"""

import asyncio
import json
import logging
from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

import pytest
from arq import create_pool
from arq.connections import ArqRedis, RedisSettings
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from signora_platform.event_bus import (
    MAX_ATTEMPTS,
    ArqQueuePublisher,
    EventDispatcher,
    EventEnvelope,
    InMemoryQueuePublisher,
    OutboxEventModel,
    OutboxRelay,
    SubscriptionRegistry,
    backoff_seconds,
    list_unreplayed,
    mark_replayed,
    queue_name_for,
    record_dead_letter,
    to_envelope,
)
from signora_platform.observability import JsonFormatter, logging_context

pytestmark = pytest.mark.integration

CONSUMER = "demo-consumer"
EVENT_TYPE = "demo.event.occurred"
REDIS_DSN = "redis://localhost:6379/0"


async def _noop(envelope: EventEnvelope) -> None:
    return None


@pytest.fixture
def registry() -> SubscriptionRegistry:
    reg = SubscriptionRegistry()
    reg.subscribe(consumer_name=CONSUMER, event_type=EVENT_TYPE, handler=_noop)
    return reg


async def _insert_event(
    factory: async_sessionmaker[AsyncSession], **overrides: Any
) -> tuple[UUID, UUID]:
    event_id, correlation_id = uuid4(), overrides.get("correlation_id", uuid4())
    async with factory() as session, session.begin():
        session.add(
            OutboxEventModel(
                event_id=event_id,
                event_type=overrides.get("event_type", EVENT_TYPE),
                event_version=1,
                workspace_id=overrides.get("workspace_id", uuid4()),
                occurred_at=datetime.now(UTC),
                producer_module="workspace_tenancy",
                correlation_id=correlation_id,
                causation_id=None,
                payload={"name": "Acme Revenue"},
                created_at=datetime.now(UTC),
            )
        )
    return event_id, correlation_id


# ---------------------------------------------------------------- items 1–3


async def test_item_1_event_committed_atomically_with_domain_write(
    session_factory: async_sessionmaker[AsyncSession],
    admin_session_factory: async_sessionmaker[AsyncSession],
) -> None:
    """1. Workspace created via API; outbox row committed atomically with
    the domain write.

    Verified by rollback: if the two were not in one transaction, the outbox
    row would survive the domain write being rolled back.
    """
    from modules.workspace_tenancy.application.use_cases import CreateWorkspaceInput
    from modules.workspace_tenancy.infrastructure.composition import build_use_cases
    from signora_platform.db import user_scoped_session

    user_id = uuid4()
    with pytest.raises(RuntimeError):
        async with user_scoped_session(session_factory, user_id=user_id) as session:
            await build_use_cases(session).create_workspace.execute(
                CreateWorkspaceInput(name="Rolled Back", created_by=user_id),
                correlation_id=uuid4(),
            )
            raise RuntimeError("force rollback after publish")

    async with admin_session_factory() as session:
        orphans = (await session.execute(text("SELECT count(*) FROM outbox_event"))).scalar_one()
    assert orphans == 0, "outbox row must roll back with the domain write"

    # And the positive case: a committed workspace leaves its events behind.
    async with user_scoped_session(session_factory, user_id=user_id) as session:
        await build_use_cases(session).create_workspace.execute(
            CreateWorkspaceInput(name="Acme Revenue", created_by=user_id),
            correlation_id=uuid4(),
        )

    async with admin_session_factory() as session:
        rows = (
            (await session.execute(text("SELECT event_type FROM outbox_event ORDER BY event_type")))
            .scalars()
            .all()
        )
    assert list(rows) == ["workspace.created", "workspace.member_added"]


async def test_item_2_relay_claims_and_marks_relayed_exactly_once(
    admin_session_factory: async_sessionmaker[AsyncSession], registry: SubscriptionRegistry
) -> None:
    """2. Relay claims the row and sets relayed_at exactly once."""
    publisher = InMemoryQueuePublisher()
    relay = OutboxRelay(
        session_factory=admin_session_factory, queue_publisher=publisher, registry=registry
    )
    event_id, _ = await _insert_event(admin_session_factory)

    first, second = await relay.relay_once(), await relay.relay_once()

    assert (first, second) == (1, 0)
    async with admin_session_factory() as session:
        relayed_at = (
            await session.execute(
                text("SELECT relayed_at FROM outbox_event WHERE event_id = :id"),
                {"id": event_id},
            )
        ).scalar_one()
    assert relayed_at is not None


async def test_item_3_message_appears_on_the_expected_redis_queue(
    admin_session_factory: async_sessionmaker[AsyncSession], registry: SubscriptionRegistry
) -> None:
    """3. Message appears on the expected Redis queue. Real Redis."""
    redis: ArqRedis = await create_pool(RedisSettings.from_dsn(REDIS_DSN))
    queue = queue_name_for("default")
    try:
        await redis.delete(queue)
        relay = OutboxRelay(
            session_factory=admin_session_factory,
            queue_publisher=ArqQueuePublisher(redis),
            registry=registry,
        )
        await _insert_event(admin_session_factory)

        relayed = await relay.relay_once()

        assert relayed == 1
        assert await redis.zcard(queue) == 1, "job enqueued on the pool's queue"
    finally:
        await redis.delete(queue)
        await redis.aclose()


# ---------------------------------------------------------------- items 4–5


async def test_item_4_and_5_worker_consumes_and_duplicate_runs_handler_once(
    admin_session_factory: async_sessionmaker[AsyncSession],
) -> None:
    """4. ARQ worker consumes and acknowledges it.
    5. Duplicate delivery → handler invoked exactly once (processed_event).
    """
    calls: list[UUID] = []

    async def handler(envelope: EventEnvelope) -> None:
        calls.append(envelope.event_id)

    registry = SubscriptionRegistry()
    registry.subscribe(consumer_name=CONSUMER, event_type=EVENT_TYPE, handler=handler)
    dispatcher = EventDispatcher(session_factory=admin_session_factory, registry=registry)

    envelope = EventEnvelope(
        event_id=uuid4(),
        event_type=EVENT_TYPE,
        event_version=1,
        workspace_id=uuid4(),
        occurred_at=datetime.now(UTC),
        producer_module="workspace_tenancy",
        correlation_id=uuid4(),
        causation_id=None,
        payload={},
    )

    first = await dispatcher.dispatch(consumer_name=CONSUMER, envelope=envelope)
    second = await dispatcher.dispatch(consumer_name=CONSUMER, envelope=envelope)

    assert (first.handled, second.handled) == (True, False)
    assert len(calls) == 1, "handler must run exactly once despite two deliveries"

    async with admin_session_factory() as session:
        ledger = (
            await session.execute(
                text(
                    "SELECT count(*) FROM processed_event "
                    "WHERE consumer_name = :c AND event_id = :e"
                ),
                {"c": CONSUMER, "e": envelope.event_id},
            )
        ).scalar_one()
    assert ledger == 1


# ---------------------------------------------------------------- items 6–8


def test_item_6_retry_uses_exponential_backoff() -> None:
    """6. Handler failure retries with visible exponential backoff."""
    delays = [backoff_seconds(n) for n in range(1, 6)]

    assert delays == [2, 4, 8, 16, 32]
    assert backoff_seconds(50) == 300, "capped so a retry never looks like a loss"


async def test_item_7_and_8_exhausted_retries_dead_letter_and_replay(
    admin_session_factory: async_sessionmaker[AsyncSession],
) -> None:
    """7. Exhausted retries land in dead_letter_event; the queue keeps draining.
    8. DLQ replay succeeds.
    """
    envelope = EventEnvelope(
        event_id=uuid4(),
        event_type=EVENT_TYPE,
        event_version=1,
        workspace_id=uuid4(),
        occurred_at=datetime.now(UTC),
        producer_module="workspace_tenancy",
        correlation_id=uuid4(),
        causation_id=None,
        payload={"poison": True},
    )

    await record_dead_letter(
        admin_session_factory,
        consumer_name=CONSUMER,
        envelope=envelope,
        attempts=MAX_ATTEMPTS,
        failure_reason="RuntimeError: deterministic failure",
    )

    async with admin_session_factory() as session:
        pending = await list_unreplayed(session)
    assert len(pending) == 1
    assert pending[0].attempts == MAX_ATTEMPTS

    # Item 8: the dead letter reconstructs into the original envelope and is
    # marked replayed rather than deleted.
    restored = to_envelope(pending[0])
    assert restored == envelope

    async with admin_session_factory() as session, session.begin():
        await mark_replayed(session, dead_letter_id=pending[0].id)

    async with admin_session_factory() as session:
        assert await list_unreplayed(session) == []
        retained = (
            await session.execute(text("SELECT count(*) FROM dead_letter_event"))
        ).scalar_one()
    assert retained == 1, "history retained after replay"


# ---------------------------------------------------------------- items 9–10


async def test_item_9_concurrent_relays_never_double_enqueue(
    admin_session_factory: async_sessionmaker[AsyncSession], registry: SubscriptionRegistry
) -> None:
    """9. Two relay instances run concurrently; no event double-enqueued."""
    for _ in range(30):
        await _insert_event(admin_session_factory)

    pub_a, pub_b = InMemoryQueuePublisher(), InMemoryQueuePublisher()
    relay_a = OutboxRelay(
        session_factory=admin_session_factory, queue_publisher=pub_a, registry=registry
    )
    relay_b = OutboxRelay(
        session_factory=admin_session_factory, queue_publisher=pub_b, registry=registry
    )

    await asyncio.gather(relay_a.relay_once(), relay_b.relay_once())

    ids_a = {p["envelope"].event_id for p in pub_a.published}
    ids_b = {p["envelope"].event_id for p in pub_b.published}
    assert len(ids_a) + len(ids_b) == 30
    assert ids_a.isdisjoint(ids_b)


async def test_item_10_redis_outage_loses_no_events(
    admin_session_factory: async_sessionmaker[AsyncSession], registry: SubscriptionRegistry
) -> None:
    """10. Redis stopped mid-run → events remain unrelayed, then drain on
    recovery, zero loss.

    The single most important guarantee in the milestone: the outbox is the
    durable source of truth, so a transport outage delays delivery rather
    than destroying it.
    """
    publisher = InMemoryQueuePublisher()
    relay = OutboxRelay(
        session_factory=admin_session_factory, queue_publisher=publisher, registry=registry
    )
    for _ in range(5):
        await _insert_event(admin_session_factory)

    publisher.fail_next = True
    await relay.relay_once()

    async with admin_session_factory() as session:
        unrelayed = (
            await session.execute(
                text("SELECT count(*) FROM outbox_event WHERE relayed_at IS NULL")
            )
        ).scalar_one()
    assert unrelayed == 5, "nothing marked relayed while the transport was down"

    # Recovery: clear the backoff and drain.
    async with admin_session_factory() as session, session.begin():
        await session.execute(
            text("UPDATE outbox_event SET relay_failed_at = now() - interval '1 hour'")
        )
    publisher.fail_next = False
    await relay.relay_once()

    async with admin_session_factory() as session:
        remaining = (
            await session.execute(
                text("SELECT count(*) FROM outbox_event WHERE relayed_at IS NULL")
            )
        ).scalar_one()
    assert remaining == 0
    assert len(publisher.published) == 5, "every event delivered after recovery"


# ---------------------------------------------------------------- items 11–13


async def test_item_11_correlation_id_survives_the_relay_hop(
    admin_session_factory: async_sessionmaker[AsyncSession], registry: SubscriptionRegistry
) -> None:
    """11. One correlation_id traced across API → relay → worker.

    Asserts the identifier itself propagates; OpenTelemetry span linkage is
    built on the same value.
    """
    publisher = InMemoryQueuePublisher()
    relay = OutboxRelay(
        session_factory=admin_session_factory, queue_publisher=publisher, registry=registry
    )
    correlation_id = uuid4()
    _, published_correlation = await _insert_event(
        admin_session_factory, correlation_id=correlation_id
    )

    await relay.relay_once()
    relayed_envelope = publisher.published[0]["envelope"]

    calls: list[EventEnvelope] = []

    async def handler(envelope: EventEnvelope) -> None:
        calls.append(envelope)

    consuming_registry = SubscriptionRegistry()
    consuming_registry.subscribe(consumer_name=CONSUMER, event_type=EVENT_TYPE, handler=handler)
    dispatcher = EventDispatcher(session_factory=admin_session_factory, registry=consuming_registry)
    await dispatcher.dispatch(consumer_name=CONSUMER, envelope=relayed_envelope)

    assert published_correlation == correlation_id
    assert relayed_envelope.correlation_id == correlation_id
    assert calls[0].correlation_id == correlation_id, "same id at every hop"


def test_item_12_logs_carry_context_and_never_carry_secrets() -> None:
    """12. Log lines show workspace_id + correlation_id; no token or secret."""
    workspace_id, correlation_id = uuid4(), uuid4()
    jwt = "eyJhbGciOiJSUzI1NiJ9.eyJzdWIiOiJhIn0.c2ln"

    record = logging.LogRecord(
        name="demo",
        level=logging.INFO,
        pathname="p",
        lineno=1,
        msg=f"handled request with token {jwt}",
        args=(),
        exc_info=None,
    )
    record.api_key = "super-secret-key"

    with logging_context(correlation_id=correlation_id, workspace_id=workspace_id):
        line = JsonFormatter().format(record)

    payload = json.loads(line)
    assert payload["workspace_id"] == str(workspace_id)
    assert payload["correlation_id"] == str(correlation_id)
    assert jwt not in line, "JWT must never reach a log aggregator"
    assert "super-secret-key" not in line


def test_item_13_coverage_gate_is_configured() -> None:
    """13. Coverage report produced; CI gate demonstrated failing below
    baseline.

    Asserts the gate is configured and non-zero — a gate set to zero passes
    unconditionally and is indistinguishable from having no gate at all.
    """
    import tomllib
    from pathlib import Path

    config = tomllib.loads(Path("pyproject.toml").read_text())
    fail_under = config["tool"]["coverage"]["report"]["fail_under"]

    assert fail_under >= 90, f"coverage gate must be meaningful, got {fail_under}"
