"""SQLAlchemy models for the Knowledge Graph."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from signora_platform.db.base import AuditMixin, Base, TimestampMixin, WorkspaceScopedMixin


class EntityModel(Base, WorkspaceScopedMixin, TimestampMixin, AuditMixin):
    """An identity, not a record.

    There is deliberately no `name`, `domain`, or `industry` column: those
    are claims, and a column here would immediately disagree with them
    (AC-28).
    """

    __tablename__ = "entity"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True)
    kind: Mapped[str] = mapped_column(String(32), nullable=False)


class ResolutionDecisionModel(Base, WorkspaceScopedMixin, TimestampMixin, AuditMixin):
    """Immutable. The application role holds no UPDATE grant (migration
    0009), so a correction must be a new row naming its predecessor."""

    __tablename__ = "resolution_decision"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True)
    provider: Mapped[str] = mapped_column(String(64), nullable=False)
    provider_external_id: Mapped[str] = mapped_column(String(512), nullable=False)
    outcome: Mapped[str] = mapped_column(String(32), nullable=False)
    reasons: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, nullable=False, default=list)
    entity_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("entity.id", ondelete="CASCADE"), nullable=True
    )
    candidate_entity_ids: Mapped[list[UUID]] = mapped_column(
        ARRAY(PGUUID(as_uuid=True)), nullable=False, default=list
    )
    evidence_claim_ids: Mapped[list[UUID]] = mapped_column(
        ARRAY(PGUUID(as_uuid=True)), nullable=False, default=list
    )
    decided_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    supersedes: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("resolution_decision.id", ondelete="SET NULL"),
        nullable=True,
    )


class IdentityBindingModel(Base, WorkspaceScopedMixin, TimestampMixin, AuditMixin):
    __tablename__ = "identity_binding"
    __table_args__ = (
        CheckConstraint(
            "state <> 'ambiguous' OR entity_id IS NULL",
            name="ck_identity_binding_ambiguous_binds_nothing",
        ),
    )

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True)
    provider: Mapped[str] = mapped_column(String(64), nullable=False)
    provider_external_id: Mapped[str] = mapped_column(String(512), nullable=False)
    state: Mapped[str] = mapped_column(String(32), nullable=False)
    entity_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("entity.id", ondelete="CASCADE"), nullable=True
    )
    decision_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("resolution_decision.id", ondelete="CASCADE")
    )
    domain: Mapped[str | None] = mapped_column(String(255), nullable=True)
    legal_name: Mapped[str | None] = mapped_column(String(512), nullable=True)
    country: Mapped[str | None] = mapped_column(String(64), nullable=True)
    superseded_by: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("identity_binding.id", ondelete="SET NULL"), nullable=True
    )


class RelationshipModel(Base, WorkspaceScopedMixin, TimestampMixin, AuditMixin):
    __tablename__ = "relationship"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True)
    kind: Mapped[str] = mapped_column(String(64), nullable=False)
    source_entity_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("entity.id", ondelete="CASCADE")
    )
    target_entity_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("entity.id", ondelete="CASCADE")
    )
    valid_from: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    valid_to: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    evidence_claim_ids: Mapped[list[UUID]] = mapped_column(
        ARRAY(PGUUID(as_uuid=True)), nullable=False, default=list
    )
    superseded_by: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("relationship.id", ondelete="SET NULL"), nullable=True
    )
