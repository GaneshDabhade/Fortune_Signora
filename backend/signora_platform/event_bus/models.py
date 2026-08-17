"""Event bus dispatch tables.

Three tables, all owned by the platform rather than by any module:

* ``outbox_event`` (in ``outbox_model.py``) — the durable source of truth.
* ``processed_event`` — the idempotency ledger. Consumer idempotency is a
  property of the bus, not a discipline each of thirteen modules must
  remember to implement correctly.
* ``dead_letter_event`` — events whose handler exhausted its retries.

None of the three is RLS-protected. They are system infrastructure: never
queried on behalf of an end user, never exposed through any API, and swept
across every workspace by the relay — which RLS scoping would prevent.
``workspace_id`` is stored as event data the relay and operators need, not
as a scope key. Same reasoning as ``outbox_event``; see
docs/architecture/11-tenancy.md.
"""

from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import DateTime, Integer, PrimaryKeyConstraint, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from signora_platform.db.base import Base


class ProcessedEventModel(Base):
    """One row per (consumer, event) pair that has been handled successfully.

    Delivery is at-least-once (docs/architecture/06-events.md), so a handler
    can legitimately be invoked more than once for the same event. The
    dispatcher inserts here inside the same transaction as the handler's own
    work; a primary-key conflict means "already done" and the redelivery
    becomes a no-op.

    Keying on (consumer_name, event_id) rather than event_id alone is
    essential: several consumers subscribe to the same event, and each must
    process it exactly once independently of the others.
    """

    __tablename__ = "processed_event"
    __table_args__ = (PrimaryKeyConstraint("consumer_name", "event_id"),)

    consumer_name: Mapped[str] = mapped_column(String(255), nullable=False)
    event_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    processed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class DeadLetterEventModel(Base):
    """An event whose handler failed more times than the retry policy allows.

    Retains the full envelope rather than a reference to ``outbox_event``:
    the outbox is append-only but may eventually be pruned, and a dead letter
    must remain independently replayable and diagnosable long after that.
    """

    __tablename__ = "dead_letter_event"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True)

    consumer_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    event_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False, index=True)
    event_type: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    event_version: Mapped[int] = mapped_column(Integer, nullable=False)
    workspace_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False, index=True)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    producer_module: Mapped[str] = mapped_column(String(255), nullable=False)
    correlation_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False, index=True)
    causation_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), nullable=True)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)

    attempts: Mapped[int] = mapped_column(Integer, nullable=False)
    failure_reason: Mapped[str] = mapped_column(Text, nullable=False)
    """Exception type and message from the final attempt. Diagnostic only —
    never returned to an end user."""

    failed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    replayed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    """Set when an operator replays this event. Retained rather than deleted
    so the record of what failed, and that it was addressed, survives."""
