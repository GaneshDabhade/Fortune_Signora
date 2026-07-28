"""The transactional outbox table — the durable source of truth for every
domain event, per docs/architecture/06-events.md.

This table is written to by every module's ``EventPublisher`` call, in the
same transaction as the domain state change that caused the event. It is
never RLS-protected: it is purely internal system infrastructure (never
queried on behalf of an end user, never exposed via any API), and the
Redis/ARQ relay process that will eventually dispatch these rows must sweep
across every workspace, which RLS scoping would prevent. ``workspace_id`` is
still stored on every row — as event data the relay needs, not as an RLS
scope key. See docs/architecture/11-tenancy.md for the workspace-scoped
taxonomy-table exception this follows the same reasoning as.

The relay itself (LISTEN/NOTIFY -> Redis enqueue) is intentionally not
implemented yet: with zero consumer modules in this revision, there is
nothing to dispatch to and no way to test dispatch behavior meaningfully.
It will be built alongside the first consuming module.
"""

from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import DateTime, Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from signora_platform.db.base import Base


class OutboxEventModel(Base):
    __tablename__ = "outbox_event"

    event_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True)
    event_type: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    event_version: Mapped[int] = mapped_column(Integer, nullable=False)
    workspace_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False, index=True)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    producer_module: Mapped[str] = mapped_column(String(255), nullable=False)
    correlation_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False, index=True)
    causation_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), nullable=True)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    # Set by the future relay process once the event has been handed off for
    # dispatch. NULL means "not yet relayed" — the query the relay will poll
    # (or be woken up via LISTEN/NOTIFY to re-check) once it exists.
    relayed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
