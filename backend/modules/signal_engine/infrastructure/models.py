"""SQLAlchemy models for the Signal Engine."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from signora_platform.db.base import AuditMixin, Base, TimestampMixin, WorkspaceScopedMixin


class SignalProfileModel(Base, WorkspaceScopedMixin, TimestampMixin, AuditMixin):
    """**Customer-authored configuration**, not derived intelligence.

    Immutable and versioned: a new profile is a new row naming the one it
    supersedes. It cannot be regenerated from anything, so a rebuild that
    dropped it would destroy customer data (migration 0012).
    """

    __tablename__ = "signal_profile"
    __table_args__ = (
        UniqueConstraint("workspace_id", "version", name="uq_signal_profile_version"),
        CheckConstraint("version > 0", name="ck_signal_profile_version_positive"),
    )

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    entries: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, nullable=False)
    supersedes: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("signal_profile.id", ondelete="SET NULL"), nullable=True
    )


class SignalModel(Base, WorkspaceScopedMixin, TimestampMixin, AuditMixin):
    """Derived intelligence. Rebuildable from business events, and immutable:
    a hypothesis that gains evidence becomes a new signal naming the one it
    replaces.

    There is deliberately no score, priority, likelihood, or rank column.
    """

    __tablename__ = "signal"
    __table_args__ = (
        CheckConstraint(
            "array_length(contributing_event_ids, 1) >= 1", name="ck_signal_cites_business_events"
        ),
        CheckConstraint(
            "array_length(contributing_event_types, 1) >= 1", name="ck_signal_names_event_types"
        ),
        CheckConstraint("relevance <> 'ignored'", name="ck_signal_relevance_is_held"),
        CheckConstraint("window_end >= window_start", name="ck_signal_window_ordered"),
        CheckConstraint("relevant_until >= occurred_at", name="ck_signal_shelf_life_ordered"),
    )

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True)
    entity_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("entity.id", ondelete="CASCADE")
    )
    signal_type: Mapped[str] = mapped_column(String(64), nullable=False)
    relevance: Mapped[str] = mapped_column(String(16), nullable=False)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    window_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    window_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    relevant_until: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    rationale: Mapped[str] = mapped_column(String(1024), nullable=False)
    contributing_event_ids: Mapped[list[UUID]] = mapped_column(
        ARRAY(PGUUID(as_uuid=True)), nullable=False
    )
    contributing_event_types: Mapped[list[str]] = mapped_column(ARRAY(String(64)), nullable=False)
    constituent_signal_ids: Mapped[list[UUID]] = mapped_column(
        ARRAY(PGUUID(as_uuid=True)), nullable=False, default=list
    )
    catalog_version: Mapped[int] = mapped_column(Integer, nullable=False)
    profile_version: Mapped[int] = mapped_column(Integer, nullable=False)
    payload_version: Mapped[int] = mapped_column(Integer, nullable=False)
    supersedes: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("signal.id", ondelete="SET NULL"), nullable=True
    )
