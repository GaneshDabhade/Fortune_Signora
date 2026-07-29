"""SQLAlchemy models for the Buying Score Engine."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from signora_platform.db.base import AuditMixin, Base, TimestampMixin, WorkspaceScopedMixin


class WorkspaceScoringModelModel(Base, WorkspaceScopedMixin, TimestampMixin, AuditMixin):
    """**Customer-authored configuration**, not derived intelligence.

    Immutable and versioned: a new model is a new row naming the one it
    supersedes. It cannot be regenerated from anything, so a rebuild that
    dropped it would destroy customer data (migration 0013).

    There is no `posture` column, deliberately. Posture is Signora's, and
    the absence of the column is what makes that structural rather than
    advisory.
    """

    __tablename__ = "workspace_scoring_model"
    __table_args__ = (
        UniqueConstraint("workspace_id", "version", name="uq_scoring_model_version"),
        CheckConstraint("version > 0", name="ck_scoring_model_version_positive"),
    )

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    overrides: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    supersedes: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("workspace_scoring_model.id", ondelete="SET NULL"),
        nullable=True,
    )


class BuyingScoreModel(Base, WorkspaceScopedMixin, TimestampMixin, AuditMixin):
    """Derived intelligence — a projection over signals, and immutable.

    There are deliberately **no account attribute columns**. A score is not
    an alternative representation of account state, and a row carrying a
    name or an industry would become a de facto account record that
    consumers read instead of the intelligence it summarizes.
    """

    __tablename__ = "buying_score"
    __table_args__ = (
        CheckConstraint("value >= 0 AND value <= 100", name="ck_buying_score_range"),
        CheckConstraint("ceiling > 0", name="ck_buying_score_ceiling_positive"),
        CheckConstraint(
            "valid_until IS NULL OR valid_until >= computed_at",
            name="ck_buying_score_validity_ordered",
        ),
        CheckConstraint(
            "NOT contested OR array_length(dissenting_signal_ids, 1) >= 1",
            name="ck_buying_score_dissent_is_named",
        ),
    )

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True)
    entity_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("entity.id", ondelete="CASCADE")
    )
    value: Mapped[int] = mapped_column(Integer, nullable=False)
    trend: Mapped[str] = mapped_column(String(16), nullable=False)
    delta: Mapped[int] = mapped_column(Integer, nullable=False)
    ledger: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, nullable=False)
    ceiling: Mapped[int] = mapped_column(Integer, nullable=False)
    contested: Mapped[bool] = mapped_column(Boolean, nullable=False)
    dissenting_signal_ids: Mapped[list[UUID]] = mapped_column(
        ARRAY(PGUUID(as_uuid=True)), nullable=False, default=list
    )
    computed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    valid_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    basis_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    trigger: Mapped[str] = mapped_column(String(32), nullable=False)
    scoring_model_version: Mapped[int] = mapped_column(Integer, nullable=False)
    model_artifact_version: Mapped[int] = mapped_column(Integer, nullable=False)
    profile_version: Mapped[int] = mapped_column(Integer, nullable=False)
    payload_version: Mapped[int] = mapped_column(Integer, nullable=False)
    supersedes: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("buying_score.id", ondelete="SET NULL"), nullable=True
    )
