"""SQLAlchemy model for the Timeline projection."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, Index, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from signora_platform.db.base import Base, TimestampMixin, WorkspaceScopedMixin


class TimelineEntryModel(Base, WorkspaceScopedMixin, TimestampMixin):
    """Immutable. The application role holds no `UPDATE` grant (migration
    `0026`), so a correction is a new entry and never an edit.

    **No `AuditMixin`, deliberately.** It requires a non-nullable `created_by`,
    and a projection row has no actor — nobody *did* this, an upstream module
    published a fact and the projection recorded it. Filling the column with a
    system UUID would be inventing an author for an audit trail, which is worth
    less than the honest absence.
    """

    __tablename__ = "timeline_entry"
    __table_args__ = (
        # The one query this module exists to serve: everything for this
        # account, newest first. `id` breaks ties so a cursor is total —
        # two entries can share `occurred_at`, and a paginated feed whose
        # order is not total silently drops or repeats rows at a boundary.
        Index(
            "ix_timeline_entry_feed",
            "workspace_id",
            "entity_id",
            "occurred_at",
            "id",
            postgresql_using="btree",
        ),
    )

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True)
    entity_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("entity.id", ondelete="CASCADE"), nullable=False
    )
    kind: Mapped[str] = mapped_column(String(32), nullable=False)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    # Unique rather than merely indexed: it is the idempotency key. Two
    # deliveries of one event derive the same `id`, so the primary key already
    # refuses the second — this states the same guarantee against the value the
    # guarantee is actually about, so a future id scheme cannot weaken it
    # without the constraint failing loudly.
    event_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False, unique=True)
    source_module: Mapped[str] = mapped_column(String(64), nullable=False)
    source_ref: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    detail: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
