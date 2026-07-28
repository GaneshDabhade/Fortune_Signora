"""SQLAlchemy models for Provider Normalization."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from signora_platform.db.base import AuditMixin, Base, TimestampMixin, WorkspaceScopedMixin


class ClaimModel(Base, WorkspaceScopedMixin, TimestampMixin, AuditMixin):
    """Immutable. The application role holds no UPDATE grant (migration
    0008), so an attempted overwrite fails with a permission error."""

    __tablename__ = "claim"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True)
    raw_record_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("raw_provider_record.id", ondelete="CASCADE")
    )
    provider: Mapped[str] = mapped_column(String(64), nullable=False)
    attribute: Mapped[str] = mapped_column(String(64), nullable=False)
    claim_domain: Mapped[str] = mapped_column(String(32), nullable=False)
    value: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    subject_external_id: Mapped[str] = mapped_column(String(512), nullable=False)
    subject_domain: Mapped[str | None] = mapped_column(String(255), nullable=True)
    subject_legal_name: Mapped[str | None] = mapped_column(String(512), nullable=True)
    mapper_version: Mapped[str] = mapped_column(String(32), nullable=False)
    payload_provenance: Mapped[str] = mapped_column(String(64), nullable=False)


class NormalizationOutcomeModel(Base, WorkspaceScopedMixin, TimestampMixin, AuditMixin):
    __tablename__ = "normalization_outcome"
    __table_args__ = (
        UniqueConstraint(
            "raw_record_id", "mapper_version", name="uq_normalization_outcome_attempt"
        ),
    )

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True)
    raw_record_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("raw_provider_record.id", ondelete="CASCADE")
    )
    provider: Mapped[str] = mapped_column(String(64), nullable=False)
    mapper_version: Mapped[str] = mapped_column(String(32), nullable=False)
    claim_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    rejections: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, nullable=False, default=list)
    ignored_fields: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list)
