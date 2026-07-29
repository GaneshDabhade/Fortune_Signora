"""SQLAlchemy models for the Observation Engine."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Numeric, String
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from signora_platform.db.base import AuditMixin, Base, TimestampMixin, WorkspaceScopedMixin


class ObservationModel(Base, WorkspaceScopedMixin, TimestampMixin, AuditMixin):
    """Immutable. The application role holds no UPDATE grant (migration
    0010), so a refinement must be a new row naming the coarser observation
    it replaces."""

    __tablename__ = "observation"
    __table_args__ = (
        CheckConstraint(
            "array_length(evidence_claim_ids, 1) >= 1", name="ck_observation_cites_evidence"
        ),
        CheckConstraint(
            "(kind = 'value_changed' AND previous_observed_at IS NOT NULL)"
            " OR (kind = 'occurrence_observed' AND previous_value IS NULL"
            " AND previous_observed_at IS NULL)",
            name="ck_observation_shape_matches_kind",
        ),
    )

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True)
    entity_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("entity.id", ondelete="CASCADE")
    )
    provider: Mapped[str] = mapped_column(String(64), nullable=False)
    attribute: Mapped[str] = mapped_column(String(64), nullable=False)
    kind: Mapped[str] = mapped_column(String(32), nullable=False)
    # `none_as_null` matters: without it SQLAlchemy writes JSON `null` into
    # the column rather than SQL NULL, and the constraint distinguishing an
    # occurrence from a change would never see the absence it tests for.
    previous_value: Mapped[dict[str, Any] | None] = mapped_column(
        JSONB(none_as_null=True), nullable=True
    )
    current_value: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    direction: Mapped[str] = mapped_column(String(16), nullable=False)
    magnitude: Mapped[Decimal | None] = mapped_column(Numeric, nullable=True)
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    previous_observed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    evidence_claim_ids: Mapped[list[UUID]] = mapped_column(
        ARRAY(PGUUID(as_uuid=True)), nullable=False
    )
    supersedes: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("observation.id", ondelete="SET NULL"), nullable=True
    )
