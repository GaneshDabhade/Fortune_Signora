"""SQLAlchemy models for the Opportunity Engine."""

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
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from signora_platform.db.base import AuditMixin, Base, TimestampMixin, WorkspaceScopedMixin


class WorkspaceOpportunityPolicyModel(Base, WorkspaceScopedMixin, TimestampMixin, AuditMixin):
    """**Customer-authored configuration**, not derived intelligence.

    Immutable and versioned: a new policy is a new row naming the one it
    supersedes. Every opportunity records the version that qualified it, so
    an edited policy would make history unexplainable (migration 0014).
    """

    __tablename__ = "workspace_opportunity_policy"
    __table_args__ = (
        UniqueConstraint("workspace_id", "version", name="uq_opportunity_policy_version"),
        CheckConstraint("version > 0", name="ck_opportunity_policy_version_positive"),
    )

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    policy: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    supersedes: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("workspace_opportunity_policy.id", ondelete="SET NULL"),
        nullable=True,
    )


class OpportunityModel(Base, WorkspaceScopedMixin, TimestampMixin, AuditMixin):
    """**Workflow state** — the third category of platform data.

    Not derived intelligence and not configuration: the accumulated record
    of work a human performed, which nothing reproduces. A pipeline rebuild
    regenerates intelligence and must not touch this table.

    Written once and never updated. There is deliberately **no current-score
    column**: the opportunity cites the score that caused it to exist and
    reads everything else live, so no stale copy of the pipeline's output
    accumulates here.
    """

    __tablename__ = "opportunity"
    __table_args__ = (
        UniqueConstraint(
            "workspace_id", "entity_id", "generation", name="uq_opportunity_generation"
        ),
        CheckConstraint("generation >= 0", name="ck_opportunity_generation_non_negative"),
        CheckConstraint(
            "score_at_creation >= 0 AND score_at_creation <= 100",
            name="ck_opportunity_score_range",
        ),
    )

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True)
    entity_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("entity.id", ondelete="CASCADE")
    )
    generation: Mapped[int] = mapped_column(Integer, nullable=False)
    originating_buying_score_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("buying_score.id", ondelete="RESTRICT"), nullable=False
    )
    score_at_creation: Mapped[int] = mapped_column(Integer, nullable=False)
    contested_at_creation: Mapped[bool] = mapped_column(Boolean, nullable=False)
    qualification: Mapped[str] = mapped_column(String(16), nullable=False)
    policy_version: Mapped[int] = mapped_column(Integer, nullable=False)
    payload_version: Mapped[int] = mapped_column(Integer, nullable=False)


class OpportunityStateModel(Base, WorkspaceScopedMixin, TimestampMixin, AuditMixin):
    """Append-only workflow history. **Never rewritten.**

    Each row is a *complete* statement of workflow state rather than a
    delta, so the current state is one row and the status **is** the audit
    log rather than something kept beside it.
    """

    __tablename__ = "opportunity_state"
    __table_args__ = (
        UniqueConstraint("opportunity_id", "sequence", name="uq_opportunity_state_sequence"),
        CheckConstraint("sequence >= 0", name="ck_opportunity_state_sequence_non_negative"),
        # Intelligence suggests; humans commit. The machine may author
        # exactly one stage, and the database makes that structural.
        CheckConstraint(
            "actor_id IS NOT NULL OR stage = 'tracking'",
            name="ck_opportunity_state_only_tracking_is_machine_authored",
        ),
        CheckConstraint("length(trim(reason)) > 0", name="ck_opportunity_state_has_reason"),
    )

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True)
    opportunity_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("opportunity.id", ondelete="CASCADE")
    )
    sequence: Mapped[int] = mapped_column(Integer, nullable=False)
    stage: Mapped[str] = mapped_column(String(16), nullable=False)
    owner_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), nullable=True)
    actor_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), nullable=True)
    reason: Mapped[str] = mapped_column(String(512), nullable=False)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
