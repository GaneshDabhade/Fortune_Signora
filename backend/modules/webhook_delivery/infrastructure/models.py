"""The delivery table — [TASK-1481](../../../../docs/BACKLOG.md), migration ``0061``.

## ⚡ Why this is a module and not the platform

**[C-1519](../../../../docs/LANE_COORDINATION.md) / [C-108](../../../../docs/LANE_COORDINATION.md)
asked who owns `platform_foundation`, and the answer made the question
irrelevant**: the product owner ruled a **bounded context**, on the
[C-1404](../../../../docs/LANE_COORDINATION.md) → [D-237](../../../../docs/DECISION_REGISTER.md)
→ [ADR-0414](../../../../docs/architecture/adr/0414-machine-credentials-bounded-context.md)
precedent, 2026-08-17.

⛔ **This was first written into `signora_platform/event_bus/`**, which QE
raised as [C-108](../../../../docs/LANE_COORDINATION.md): [§20a](../../../../CLAUDE.md)
freezes the platform except `simulation/`, and *"adding a worker pool"* did not
stretch to a tenant-owned table with its own RLS policy. ✅ **Moved here rather
than argued about** — **the ownership conflict simply does not apply to a
module.**

📁 **D-237 ② already pointed here**: *"webhooks are treated separately —
outbound delivery on the existing outbox/relay pattern"*, and deliberately NOT
inside the credential context.
"""

from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from signora_platform.db.base import Base

class WebhookDeliveryModel(Base):
    """A delivery a customer's endpoint is owed — TASK-1481, migration ``0060``.

    **Tenant-owned, unlike the three platform tables it used to sit beside.** ``outbox_event``,
    ``processed_event`` and ``dead_letter_event`` are platform infrastructure:
    the application role inserts and cannot read. This one carries
    ``workspace_id`` under forced RLS, because the design puts its state on a
    screen a customer opens — and a row ``signora_app`` cannot read is a column
    that renders nothing.

    The policy that moves ``state`` lives in
    :mod:`modules.webhook_delivery.domain.delivery` and is a pure function
    of ``(first_attempted_at, attempts, now)``. Nothing here decides when to
    retry; this is where the answer is kept.
    """

    __tablename__ = "webhook_delivery"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True)
    workspace_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)

    endpoint_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    event_type: Mapped[str] = mapped_column(String(255), nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    """**Retained through parking**, and the design says so in the same
    sentence that sets the window. A parked delivery whose payload a customer
    cannot inspect is indistinguishable from one that was dropped."""

    state: Mapped[str] = mapped_column(String(16), nullable=False)

    first_attempted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    """The window runs from here, never from the last attempt — otherwise a
    delivery extends its own deadline by failing."""

    attempts: Mapped[int] = mapped_column(Integer, nullable=False)
    next_attempt_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    """Non-null exactly while ``pending``, enforced by a CHECK constraint
    rather than by convention."""

    last_attempted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    last_failure_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
