"""The outbox relay: PostgreSQL outbox → Redis queues.

This is the hand-off that turns a durably-committed event into work a
worker can pick up. Its correctness properties, in priority order:

1. **No event is ever lost.** A row is marked ``relayed_at`` only after the
   enqueue has succeeded. If the process dies between enqueue and mark, the
   event is re-enqueued on recovery — at-least-once, which consumers are
   required to tolerate (docs/architecture/06-events.md).
2. **No event is enqueued twice by two relays.** Rows are claimed with
   ``FOR UPDATE SKIP LOCKED``, so concurrent relay instances partition the
   backlog between them rather than duplicating it.
3. **A failing event does not block the queue.** Per-row failure is
   recorded and backed off; the batch continues.

The ordering of (2) before (1) would be a mistake: if we marked rows
relayed before enqueueing, a crash in between would lose the event
permanently. Marking after means the worst case is a duplicate, which the
idempotency ledger absorbs. **Prefer duplicates over loss** is the design
rule this file is built on.
"""

import asyncio
from datetime import UTC, datetime
from typing import Final

from sqlalchemy import select, text, update
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from signora_platform.event_bus.envelope import EventEnvelope
from signora_platform.event_bus.outbox_model import OutboxEventModel
from signora_platform.event_bus.queue import QueuePublisher, queue_name_for
from signora_platform.event_bus.subscriptions import SubscriptionRegistry
from signora_platform.observability import PipelineMetrics, get_logger, logging_context

logger = get_logger(__name__)

OUTBOX_CHANNEL: Final = "signora_outbox"
"""PostgreSQL LISTEN/NOTIFY channel. The relay polls on a timer *and*
listens on this channel: polling guarantees eventual delivery even if a
notification is missed (notifications are not durable), while the
notification collapses idle latency from seconds to milliseconds. Either
alone is insufficient — notification alone can lose events, polling alone
is slow."""

DEFAULT_BATCH_SIZE: Final = 100
DEFAULT_POLL_INTERVAL_SECONDS: Final = 1.0
MAX_RELAY_BACKOFF_SECONDS: Final = 30
"""Ceiling on the retry delay after a failed relay *cycle* (a lost database
connection, a DNS failure during failover, a Redis blip). Capped because an
uncapped backoff would eventually make recovery indistinguishable from the
relay having died — the thing this backoff exists to prevent."""

RELAY_FAILURE_BACKOFF_SECONDS: Final = 30
"""How long a row that failed to enqueue is skipped before being retried.
Without this the relay would spin on a persistently failing row, starving
every healthy event behind it."""


class OutboxRelay:
    """Claims unrelayed outbox rows and publishes them to consumer queues."""

    def __init__(
        self,
        *,
        session_factory: async_sessionmaker[AsyncSession],
        queue_publisher: QueuePublisher,
        registry: SubscriptionRegistry,
        batch_size: int = DEFAULT_BATCH_SIZE,
        metrics: PipelineMetrics | None = None,
    ) -> None:
        self._session_factory = session_factory
        self._queue_publisher = queue_publisher
        self._registry = registry
        self._batch_size = batch_size
        # Optional so the relay can be unit-tested without a meter provider;
        # production always supplies one.
        self._metrics = metrics

    async def relay_once(self) -> int:
        """Claim and relay one batch. Returns the number of events relayed.

        Each row is claimed, enqueued, and marked inside a single
        transaction. The row lock is held for the duration of the enqueue,
        which is what prevents a second relay from taking the same row —
        the lock is doing real work here, not just guarding the read.
        """
        relayed = 0
        async with self._session_factory() as session, session.begin():
            rows = await self._claim_batch(session)
            for row in rows:
                if await self._relay_row(session, row):
                    relayed += 1
        return relayed

    async def _claim_batch(self, session: AsyncSession) -> list[OutboxEventModel]:
        """Claim up to ``batch_size`` unrelayed rows, oldest first.

        ``SKIP LOCKED`` is what makes horizontal scaling of the relay safe:
        a second instance skips rows the first has locked instead of
        blocking on them or duplicating them.
        """
        backoff_cutoff = datetime.now(UTC).timestamp() - RELAY_FAILURE_BACKOFF_SECONDS
        statement = (
            select(OutboxEventModel)
            .where(
                OutboxEventModel.relayed_at.is_(None),
                # Skip rows that failed recently, so one poison row cannot
                # consume every batch.
                (
                    OutboxEventModel.relay_failed_at.is_(None)
                    | (
                        OutboxEventModel.relay_failed_at
                        < datetime.fromtimestamp(backoff_cutoff, tz=UTC)
                    )
                ),
            )
            .order_by(OutboxEventModel.created_at)
            .limit(self._batch_size)
            .with_for_update(skip_locked=True)
        )
        return list((await session.execute(statement)).scalars().all())

    async def _relay_row(self, session: AsyncSession, row: OutboxEventModel) -> bool:
        """Publish one event to every subscribed consumer's queue.

        Returns True if the row was marked relayed. Failure is recorded on
        the row and the batch continues — one unhealthy consumer queue must
        not stall the whole backlog.
        """
        envelope = _to_envelope(row)
        with logging_context(
            correlation_id=row.correlation_id,
            workspace_id=row.workspace_id,
            event_id=row.event_id,
            causation_id=row.causation_id,
        ):
            subscriptions = self._registry.for_event_type(row.event_type)
            try:
                for subscription in subscriptions:
                    await self._queue_publisher.publish(
                        queue_name=queue_name_for(subscription.pool),
                        consumer_name=subscription.consumer_name,
                        envelope=envelope,
                    )
            except Exception as exc:
                # Enqueue failed — leave relayed_at NULL so the event is
                # retried. Recording the failure lets the backoff skip it
                # and gives operators a signal that Redis or the relay is
                # unhealthy, which is a different diagnosis from a poison
                # event failing in a handler.
                await session.execute(
                    update(OutboxEventModel)
                    .where(OutboxEventModel.event_id == row.event_id)
                    .values(
                        relay_attempts=OutboxEventModel.relay_attempts + 1,
                        relay_failed_at=datetime.now(UTC),
                    )
                )
                if self._metrics:
                    self._metrics.relay_failed(event_type=row.event_type)
                logger.warning(
                    "outbox relay failed to enqueue event",
                    extra={
                        "event_type": row.event_type,
                        "attempts": row.relay_attempts + 1,
                        "error": f"{type(exc).__name__}: {exc}",
                    },
                )
                return False

            await session.execute(
                update(OutboxEventModel)
                .where(OutboxEventModel.event_id == row.event_id)
                .values(relayed_at=datetime.now(UTC))
            )
            if self._metrics:
                self._metrics.event_relayed(
                    event_type=row.event_type, subscribers=len(subscriptions)
                )
                self._metrics.outbox_lag(
                    seconds=(datetime.now(UTC) - row.created_at).total_seconds()
                )
            logger.info(
                "outbox event relayed",
                extra={"event_type": row.event_type, "subscribers": len(subscriptions)},
            )
            return True

    async def run_forever(
        self, *, poll_interval_seconds: float = DEFAULT_POLL_INTERVAL_SECONDS
    ) -> None:
        """Relay continuously until cancelled.

        Drains fully on each wake-up rather than relaying a single batch:
        after a burst, waiting a full poll interval between batches would
        let the backlog grow faster than it drains.
        """
        logger.info("outbox relay started", extra={"batch_size": self._batch_size})
        consecutive_failures = 0
        try:
            while True:
                try:
                    while await self.relay_once() > 0:
                        pass
                except asyncio.CancelledError:
                    raise
                except Exception as exc:
                    # The relay must outlive its dependencies. Every error
                    # reaching here is a lost connection, a DNS failure
                    # during a database failover, or a Redis blip — all
                    # transient, all guaranteed to happen in a deployed
                    # environment. Letting one propagate stops the relay
                    # permanently, which silently halts the entire event
                    # pipeline: events keep accumulating in the outbox and
                    # nothing consumes them, with no error after the first.
                    #
                    # Found in M1.4 by stopping PostgreSQL and starting it
                    # again. The disaster-recovery script had missed it
                    # because `compose restart` keeps the container's DNS
                    # entry, so the relay reconnected without ever having to
                    # resolve a name that was briefly gone.
                    consecutive_failures += 1
                    backoff = min(
                        poll_interval_seconds * 2 ** min(consecutive_failures, 5),
                        MAX_RELAY_BACKOFF_SECONDS,
                    )
                    logger.warning(
                        "outbox relay cycle failed; retrying",
                        extra={
                            "error": type(exc).__name__,
                            "consecutive_failures": consecutive_failures,
                            "retry_in_seconds": backoff,
                        },
                    )
                    await asyncio.sleep(backoff)
                    continue

                if consecutive_failures:
                    logger.info(
                        "outbox relay recovered",
                        extra={"after_failures": consecutive_failures},
                    )
                    consecutive_failures = 0

                await asyncio.sleep(poll_interval_seconds)
        except asyncio.CancelledError:
            logger.info("outbox relay stopped")
            raise


async def notify_outbox(session: AsyncSession) -> None:
    """Wake relays immediately after a publish, instead of waiting for the
    next poll.

    Best-effort by design: ``NOTIFY`` is not durable and a missed
    notification is harmless, because polling remains the guarantee. This
    only collapses latency.
    """
    await session.execute(text(f"NOTIFY {OUTBOX_CHANNEL}"))


def _to_envelope(row: OutboxEventModel) -> EventEnvelope:
    return EventEnvelope(
        event_id=row.event_id,
        event_type=row.event_type,
        event_version=row.event_version,
        workspace_id=row.workspace_id,
        occurred_at=row.occurred_at,
        producer_module=row.producer_module,
        correlation_id=row.correlation_id,
        causation_id=row.causation_id,
        payload=row.payload,
    )
