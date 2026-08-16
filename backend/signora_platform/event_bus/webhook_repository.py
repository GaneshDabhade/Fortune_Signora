"""Reading and moving webhook deliveries — TASK-1481.

**The policy decides; this executes.** Every state transition here is the
return value of :mod:`signora_platform.event_bus.webhook_delivery`, never a
branch of its own. Two places deciding when to retry is two places that
eventually disagree, and the one nobody is maintaining is the one somebody
will read (``CLAUDE.md`` §2).

## ⚡ Claiming is ``SKIP LOCKED``, and it is the whole concurrency model

More than one worker will run. Without a claim, two of them read the same due
row and a customer's endpoint receives the delivery twice — which is worse than
late, because a webhook consumer that is not idempotent has now acted twice on
one event.

``FOR UPDATE SKIP LOCKED`` is the boring, proven answer: the second worker
steps over the locked row rather than blocking on it, so throughput scales with
workers instead of serialising on the oldest due delivery.
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from signora_platform.event_bus.models import WebhookDeliveryModel
from signora_platform.event_bus.webhook_delivery import (
    Attempt,
    DeliveryState,
    delivered,
    next_attempt,
)
from signora_platform.observability import get_logger

logger = get_logger(__name__)


async def enqueue(
    session: AsyncSession,
    *,
    workspace_id: UUID,
    endpoint_id: UUID,
    event_type: str,
    payload: dict[str, object],
    now: datetime,
) -> UUID:
    """Accept a delivery, due immediately.

    **In the caller's session, deliberately.** A delivery is owed because
    something happened; if the transaction that recorded that thing rolls back,
    the delivery must roll back with it. This is the outbox rule
    (`ADR-0011`) applied one layer out — never publish before the causing write
    commits.
    """
    delivery_id = uuid4()
    session.add(
        WebhookDeliveryModel(
            id=delivery_id,
            workspace_id=workspace_id,
            endpoint_id=endpoint_id,
            event_type=event_type,
            payload=payload,
            state=DeliveryState.PENDING.value,
            first_attempted_at=now,
            attempts=0,
            next_attempt_at=now,
            last_attempted_at=None,
            last_failure_reason=None,
        )
    )
    return delivery_id


async def claim_due(
    session: AsyncSession, *, now: datetime, limit: int = 50
) -> list[WebhookDeliveryModel]:
    """Take up to ``limit`` deliveries that are due, locking them for this worker.

    Ordered by ``next_attempt_at`` so the longest-waiting endpoint is served
    first. **Oldest-first matters more here than throughput**: a delivery that
    keeps losing to newer ones consumes its twenty-four hour window without ever
    being tried, and parks having never reached the endpoint at all.
    """
    result = await session.execute(
        select(WebhookDeliveryModel)
        .where(
            WebhookDeliveryModel.state == DeliveryState.PENDING.value,
            WebhookDeliveryModel.next_attempt_at <= now,
        )
        .order_by(WebhookDeliveryModel.next_attempt_at)
        .limit(limit)
        .with_for_update(skip_locked=True)
    )
    return list(result.scalars().all())


def record_success(delivery: WebhookDeliveryModel, *, now: datetime) -> Attempt:
    """The endpoint accepted it."""
    attempts = delivery.attempts + 1
    decision = delivered(attempts=attempts)
    _apply(delivery, decision, attempts=attempts, now=now, failure_reason=None)
    return decision


def record_failure(
    delivery: WebhookDeliveryModel, *, now: datetime, reason: str
) -> Attempt:
    """The endpoint refused, timed out, or could not be reached.

    **``reason`` is retained on the row rather than only logged** (§17): the
    design's table shows a `State` per endpoint, and *"parked"* without *why* is
    a state a customer can see and cannot act on.
    """
    attempts = delivery.attempts + 1
    decision = next_attempt(
        first_attempted_at=delivery.first_attempted_at,
        attempts=attempts,
        now=now,
    )
    _apply(delivery, decision, attempts=attempts, now=now, failure_reason=reason)

    if decision.state is DeliveryState.PARKED:
        # ⚡ **Parking is the one transition worth an operator's attention** —
        # it is the end of the guarantee, and the only one a customer may ask
        # about. `logging_context` is not used: this is not inside a request,
        # and `workspace_id` is on the row.
        logger.warning(
            "webhook delivery parked",
            extra={
                "workspace_id": str(delivery.workspace_id),
                "endpoint_id": str(delivery.endpoint_id),
                "delivery_id": str(delivery.id),
                "event_type": delivery.event_type,
                "attempts": attempts,
                "reason": decision.reason,
            },
        )
    return decision


def _apply(
    delivery: WebhookDeliveryModel,
    decision: Attempt,
    *,
    attempts: int,
    now: datetime,
    failure_reason: str | None,
) -> None:
    """Write a decision onto the row.

    **One place**, so the CHECK constraint binding ``pending`` to
    ``next_attempt_at`` cannot be violated by a caller that set one and forgot
    the other — the database would refuse it, and a refusal at commit is a
    worse place to learn it than here.
    """
    delivery.attempts = attempts
    delivery.last_attempted_at = now
    delivery.state = decision.state.value
    delivery.next_attempt_at = decision.next_attempt_at
    if failure_reason is not None:
        delivery.last_failure_reason = failure_reason
