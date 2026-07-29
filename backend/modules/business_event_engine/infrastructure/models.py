"""SQLAlchemy models for the Business Event Engine."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from signora_platform.db.base import AuditMixin, Base, TimestampMixin, WorkspaceScopedMixin


class BusinessEventModel(Base, WorkspaceScopedMixin, TimestampMixin, AuditMixin):
    """Durable business history. The application role holds no UPDATE grant
    (migration 0011), so a phenomenon that extends must be a new row naming
    the one it replaces.

    There is deliberately no priority, score, urgency, or rank column.
    """

    __tablename__ = "business_event"
    __table_args__ = (
        CheckConstraint(
            "array_length(evidence_observation_ids, 1) >= 1",
            name="ck_business_event_cites_evidence",
        ),
        CheckConstraint(
            "array_length(corroborating_providers, 1) >= 1",
            name="ck_business_event_names_a_provider",
        ),
        CheckConstraint("window_end >= window_start", name="ck_business_event_window_ordered"),
    )

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True)
    entity_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("entity.id", ondelete="CASCADE")
    )
    type_key: Mapped[str] = mapped_column(String(64), nullable=False)
    domain: Mapped[str] = mapped_column(String(32), nullable=False)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    window_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    window_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    detected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    summary: Mapped[str] = mapped_column(String(512), nullable=False)
    facts: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    evidence_observation_ids: Mapped[list[UUID]] = mapped_column(
        ARRAY(PGUUID(as_uuid=True)), nullable=False
    )
    corroborating_providers: Mapped[list[str]] = mapped_column(ARRAY(String(64)), nullable=False)
    taxonomy_version: Mapped[int] = mapped_column(Integer, nullable=False)
    payload_version: Mapped[int] = mapped_column(Integer, nullable=False)
    supersedes: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("business_event.id", ondelete="SET NULL"), nullable=True
    )
