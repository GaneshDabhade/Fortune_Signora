"""The queue transport port and its ARQ/Redis implementation.

Modules never touch this directly — the relay publishes, the worker
consumes. It exists as a Protocol so the relay can be integration-tested
against an in-memory implementation without Redis, and so the transport can
be replaced (a dedicated broker, per the trigger conditions in
docs/architecture/12-scalability.md) without touching relay logic.
"""

from typing import Any, Final, Protocol

from arq.connections import ArqRedis

from signora_platform.event_bus.envelope import EventEnvelope

DISPATCH_TASK_NAME: Final = "dispatch_event"
"""The single ARQ task every consumer's work is enqueued as. One task name
rather than one per consumer keeps worker configuration uniform: a pool
processes whatever arrives on its queue, and the consumer name travels in
the job arguments."""

QUEUE_PREFIX: Final = "signora:events"


def queue_name_for(pool: str) -> str:
    """Redis queue name for a worker pool.

    Pool-scoped rather than consumer-scoped so a slow consumer can be
    isolated by moving it to its own pool, without changing how anything
    is enqueued.
    """
    return f"{QUEUE_PREFIX}:{pool}"


class QueuePublisher(Protocol):
    async def publish(
        self, *, queue_name: str, consumer_name: str, envelope: EventEnvelope
    ) -> None: ...


class ArqQueuePublisher:
    """Publishes dispatch jobs onto an ARQ queue backed by Redis."""

    def __init__(self, redis: ArqRedis) -> None:
        self._redis = redis

    async def publish(
        self, *, queue_name: str, consumer_name: str, envelope: EventEnvelope
    ) -> None:
        await self._redis.enqueue_job(
            DISPATCH_TASK_NAME,
            consumer_name,
            envelope.model_dump(mode="json"),
            _queue_name=queue_name,
        )


class InMemoryQueuePublisher:
    """Records published jobs instead of sending them.

    Lets the relay's claiming, marking, and failure semantics — the parts
    most likely to harbour a correctness bug — be tested against a real
    database without also requiring Redis.
    """

    def __init__(self) -> None:
        self.published: list[dict[str, Any]] = []
        self.fail_next: bool = False

    async def publish(
        self, *, queue_name: str, consumer_name: str, envelope: EventEnvelope
    ) -> None:
        if self.fail_next:
            raise RuntimeError("simulated queue failure")
        self.published.append(
            {
                "queue_name": queue_name,
                "consumer_name": consumer_name,
                "envelope": envelope,
            }
        )
