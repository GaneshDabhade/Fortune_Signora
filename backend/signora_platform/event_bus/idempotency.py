"""Platform-owned consumer idempotency.

Delivery is at-least-once, so a handler can legitimately be invoked more
than once for the same event. Rather than requiring each of thirteen
modules to implement deduplication correctly, the bus owns it: the
dispatcher records ``(consumer_name, event_id)`` in the same transaction as
the handler's own work.

That transactional coupling is the whole point. If the ledger were written
in a separate transaction, a crash between the two would either re-run a
completed handler (if the ledger write came second) or silently skip a
handler that never ran (if it came first). Sharing one transaction makes
"handled" and "recorded as handled" atomically the same fact.
"""

from datetime import UTC, datetime

from sqlalchemy import CursorResult
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from signora_platform.event_bus.models import ProcessedEventModel


async def claim(session: AsyncSession, *, consumer_name: str, event_id: object) -> bool:
    """Attempt to claim an event for a consumer.

    Returns ``True`` if this consumer has not processed the event before and
    the caller should proceed; ``False`` if it is a redelivery to be skipped.

    Uses ``ON CONFLICT DO NOTHING`` rather than a SELECT-then-INSERT: the
    check-then-act version has a race window in which two concurrent workers
    both see "not processed" and both run the handler. Letting the primary
    key arbitrate makes the claim atomic.
    """
    statement = (
        insert(ProcessedEventModel)
        .values(
            consumer_name=consumer_name,
            event_id=event_id,
            processed_at=datetime.now(UTC),
        )
        .on_conflict_do_nothing(index_elements=["consumer_name", "event_id"])
    )
    result: CursorResult[object] = await session.execute(statement)  # type: ignore[assignment]
    # rowcount is 1 when the row was inserted, 0 when ON CONFLICT skipped it.
    return result.rowcount > 0
