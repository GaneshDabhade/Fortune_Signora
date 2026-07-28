"""Retry policy and dead-lettering.

An event whose handler keeps failing must not be retried forever — it would
occupy a worker slot indefinitely and, at sufficient volume, starve healthy
events behind it. After a bounded number of attempts the event is moved to
``dead_letter_event``, where it stops consuming capacity but remains
diagnosable and replayable.

The retained envelope is a full copy rather than a reference to
``outbox_event``, because the outbox is expected to be pruned eventually
while a dead letter must survive independently.
"""

from datetime import UTC, datetime
from typing import Final
from uuid import UUID, uuid4

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from signora_platform.event_bus.envelope import EventEnvelope
from signora_platform.event_bus.models import DeadLetterEventModel
from signora_platform.observability import get_logger, logging_context

logger = get_logger(__name__)

MAX_ATTEMPTS: Final = 5
"""Total handler attempts before dead-lettering.

Five covers the transient failures worth retrying — a brief database
blip, a rate-limited vendor — without spending minutes of worker capacity
on a deterministic bug, which no number of retries will fix.
"""

BASE_BACKOFF_SECONDS: Final = 2
MAX_BACKOFF_SECONDS: Final = 300


def backoff_seconds(attempt: int) -> int:
    """Exponential backoff, capped.

    The cap matters: uncapped exponential backoff on attempt 10+ produces
    delays measured in hours, which looks indistinguishable from the event
    having been lost.
    """
    scaled: int = BASE_BACKOFF_SECONDS * (2 ** max(attempt - 1, 0))
    return min(scaled, MAX_BACKOFF_SECONDS)


async def record_dead_letter(
    session_factory: async_sessionmaker[AsyncSession],
    *,
    consumer_name: str,
    envelope: EventEnvelope,
    attempts: int,
    failure_reason: str,
) -> UUID:
    """Persist a permanently-failed event and return its dead-letter id.

    Uses its own session rather than the handler's: the handler's
    transaction has already rolled back by the time we get here, so writing
    the dead letter inside it would roll back too, losing the only record
    of the failure.
    """
    dead_letter_id = uuid4()
    async with session_factory() as session, session.begin():
        session.add(
            DeadLetterEventModel(
                id=dead_letter_id,
                consumer_name=consumer_name,
                event_id=envelope.event_id,
                event_type=envelope.event_type,
                event_version=envelope.event_version,
                workspace_id=envelope.workspace_id,
                occurred_at=envelope.occurred_at,
                producer_module=envelope.producer_module,
                correlation_id=envelope.correlation_id,
                causation_id=envelope.causation_id,
                payload=envelope.payload,
                attempts=attempts,
                failure_reason=failure_reason,
                failed_at=datetime.now(UTC),
            )
        )

    with logging_context(
        correlation_id=envelope.correlation_id,
        workspace_id=envelope.workspace_id,
        event_id=envelope.event_id,
        consumer_name=consumer_name,
    ):
        # Error level deliberately: every dead letter warrants human
        # attention at this stage of the system's life.
        logger.error(
            "event dead-lettered",
            extra={
                "event_type": envelope.event_type,
                "attempts": attempts,
                "dead_letter_id": str(dead_letter_id),
                "failure_reason": failure_reason,
            },
        )
    return dead_letter_id


async def list_unreplayed(session: AsyncSession, *, limit: int = 100) -> list[DeadLetterEventModel]:
    """Dead letters awaiting operator attention, oldest first."""
    statement = (
        select(DeadLetterEventModel)
        .where(DeadLetterEventModel.replayed_at.is_(None))
        .order_by(DeadLetterEventModel.failed_at)
        .limit(limit)
    )
    return list((await session.execute(statement)).scalars().all())


async def mark_replayed(session: AsyncSession, *, dead_letter_id: UUID) -> None:
    """Mark a dead letter as replayed.

    The row is retained rather than deleted so the record of what failed —
    and that it was addressed — survives the fix.
    """
    await session.execute(
        update(DeadLetterEventModel)
        .where(DeadLetterEventModel.id == dead_letter_id)
        .values(replayed_at=datetime.now(UTC))
    )


def to_envelope(row: DeadLetterEventModel) -> EventEnvelope:
    """Reconstruct the original envelope, for replay."""
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
