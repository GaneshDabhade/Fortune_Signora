"""Event dispatch: envelope → the right handler, exactly once, in tenant scope.

This is the contract thirteen modules will program against, so its
guarantees matter more than its size:

* **Exactly-once effect** from at-least-once delivery, via the idempotency
  ledger (``idempotency.py``).
* **Tenant scope established before the handler runs.** RLS context comes
  from the envelope's ``workspace_id``, so a handler cannot accidentally
  operate outside its tenant even if it forgets to filter
  (docs/architecture/11-tenancy.md).
* **Handler work and the idempotency record share one transaction**, so a
  crash can never leave one without the other.
* **Failures propagate** so the retry/dead-letter layer above can act on
  them. Swallowing here would silently drop events.
"""

from dataclasses import dataclass
from time import perf_counter
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from signora_platform.db import tenant_scoped_session
from signora_platform.event_bus import idempotency
from signora_platform.event_bus.envelope import EventEnvelope
from signora_platform.event_bus.subscriptions import SubscriptionRegistry
from signora_platform.observability import PipelineMetrics, get_logger, logging_context

logger = get_logger(__name__)

SYSTEM_USER_ID: UUID = UUID("00000000-0000-0000-0000-000000000000")
"""Identity workers act under.

Event processing has no authenticated human behind it, but ``app.user_id``
must still be set: the ``workspace`` table's RLS policies are
membership-based on it. A dedicated sentinel makes worker-originated rows
distinguishable from user-originated ones in audit columns, which a real
user's id borrowed from the event would not.
"""


class UnknownConsumerError(Exception):
    """A job named a consumer/event pair with no registered subscription.

    Happens when a subscription is removed while jobs for it are still
    queued. Treated as an error rather than ignored, because silently
    discarding queued work is exactly the failure mode that is impossible
    to diagnose later.
    """

    def __init__(self, consumer_name: str, event_type: str) -> None:
        super().__init__(
            f"No subscription registered for consumer '{consumer_name}' "
            f"and event type '{event_type}'."
        )


@dataclass(frozen=True)
class DispatchResult:
    handled: bool
    """False when the event was a redelivery already recorded as processed."""


class EventDispatcher:
    def __init__(
        self,
        *,
        session_factory: async_sessionmaker[AsyncSession],
        registry: SubscriptionRegistry,
        metrics: PipelineMetrics | None = None,
    ) -> None:
        self._session_factory = session_factory
        self._registry = registry
        self._metrics = metrics

    async def dispatch(self, *, consumer_name: str, envelope: EventEnvelope) -> DispatchResult:
        """Run one consumer's handler for one event.

        Raises if the handler raises — the caller (the ARQ task) owns retry
        and dead-lettering.
        """
        subscription = self._registry.find(
            consumer_name=consumer_name, event_type=envelope.event_type
        )
        if subscription is None:
            raise UnknownConsumerError(consumer_name, envelope.event_type)

        with logging_context(
            correlation_id=envelope.correlation_id,
            workspace_id=envelope.workspace_id,
            causation_id=envelope.causation_id,
            event_id=envelope.event_id,
            consumer_name=consumer_name,
        ):
            async with tenant_scoped_session(
                self._session_factory,
                workspace_id=envelope.workspace_id,
                user_id=SYSTEM_USER_ID,
            ) as session:
                claimed = await idempotency.claim(
                    session, consumer_name=consumer_name, event_id=envelope.event_id
                )
                if not claimed:
                    if self._metrics:
                        self._metrics.event_redelivered(
                            event_type=envelope.event_type, consumer_name=consumer_name
                        )
                    logger.info(
                        "event redelivery skipped",
                        extra={"event_type": envelope.event_type},
                    )
                    return DispatchResult(handled=False)

                started = perf_counter()
                await subscription.handler(envelope)
                latency_ms = (perf_counter() - started) * 1000

                if self._metrics:
                    self._metrics.event_handled(
                        event_type=envelope.event_type,
                        consumer_name=consumer_name,
                        latency_ms=latency_ms,
                    )
                logger.info(
                    "event handled",
                    extra={
                        "event_type": envelope.event_type,
                        "latency_ms": round(latency_ms, 2),
                    },
                )
                return DispatchResult(handled=True)
