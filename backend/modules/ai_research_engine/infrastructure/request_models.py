"""SQLAlchemy models for a research request and its history.

Kept apart from `models.py` because the tables are apart for a reason: those
three record what a run *produced* and are written once; these two record that
somebody *asked*, and accumulate. Migration `0021` carries the full reasoning.

Append-only throughout: `signora_app` holds `SELECT`, `INSERT` and `DELETE` and
**no `UPDATE` grant** on either, so a status that could be quietly rewritten is
refused by the database and not only by the absence of a method.

`entity_id` is repeated on the state row so the partial in-flight unique index
can be per-account without a join. It is written once, from the request, and
neither row is ever updated — so the copy cannot drift.
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from signora_platform.db.base import AuditMixin, Base, TimestampMixin, WorkspaceScopedMixin


class ResearchRequestModel(Base, WorkspaceScopedMixin, TimestampMixin, AuditMixin):
    """A person asked for research on one account. Workflow state."""

    __tablename__ = "research_request"
    __table_args__ = (
        UniqueConstraint(
            "workspace_id", "entity_id", "generation", name="uq_research_request_generation"
        ),
        CheckConstraint("generation >= 0", name="ck_research_request_generation_non_negative"),
    )

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True)
    entity_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    opportunity_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    requested_by: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    requested_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    generation: Mapped[int] = mapped_column(Integer, nullable=False)


class ResearchRequestStateModel(Base, WorkspaceScopedMixin, TimestampMixin, AuditMixin):
    """A complete statement of where a request stands. Never a delta."""

    __tablename__ = "research_request_state"
    __table_args__ = (
        UniqueConstraint("request_id", "sequence", name="uq_research_request_state_sequence"),
        CheckConstraint("sequence >= 0", name="ck_research_request_state_sequence_non_negative"),
        CheckConstraint(
            "status IN ('requested', 'running', 'completed', 'nothing_to_research', 'failed')",
            name="ck_research_request_state_known_status",
        ),
        CheckConstraint(
            "(status = 'completed') = (task_id IS NOT NULL)",
            name="ck_research_request_state_completed_names_its_artifact",
        ),
        CheckConstraint(
            "(status = 'failed') = (detail IS NOT NULL AND length(trim(detail)) > 0)",
            name="ck_research_request_state_failure_states_why",
        ),
    )

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True)
    request_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("research_request.id", ondelete="CASCADE"), nullable=False
    )
    entity_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    sequence: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    task_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), nullable=True)
    detail: Mapped[str | None] = mapped_column(Text, nullable=True)
