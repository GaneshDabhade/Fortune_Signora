"""SQLAlchemy models for the AI Research Engine's three tables.

**Three tables because there are three data categories**, not three types —
`research_task` is operational history, `research_finding` is derived
intelligence rebuildable from the rows it cites, and `research_synthesis` is a
materialized AI artifact. Migration `0018` carries the full reasoning.

Immutable throughout: `signora_app` holds `SELECT`, `INSERT` and `DELETE` and
**no `UPDATE` grant** on any of them, so the absence of an update method in the
repository is not the only thing preventing an edit.

**No foreign key points anywhere**, including `task_id`. A finding's identity
excludes its task, so `task_id` records the run that *first* derived it — a
cascade would erase facts a later run also produced, and a restrict would make
operational history undeletable while any derivation survived.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import CheckConstraint, DateTime, Integer, String
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from signora_platform.db.base import AuditMixin, Base, TimestampMixin, WorkspaceScopedMixin


class ResearchTaskModel(Base, WorkspaceScopedMixin, TimestampMixin, AuditMixin):
    """One act of researching an account. Operational history, not knowledge."""

    __tablename__ = "research_task"
    __table_args__ = (
        CheckConstraint(
            "length(trim(subject_kind)) > 0", name="ck_research_task_subject_is_addressed"
        ),
    )

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True)
    correlation_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    subject_kind: Mapped[str] = mapped_column(String(64), nullable=False)
    subject_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    opportunity_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    requested_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class ResearchFindingModel(Base, WorkspaceScopedMixin, TimestampMixin, AuditMixin):
    """One comparison's result. **Derived, and addressed by its content.**"""

    __tablename__ = "research_finding"
    __table_args__ = (
        CheckConstraint(
            "length(trim(derivation)) > 0", name="ck_research_finding_names_its_derivation"
        ),
        CheckConstraint(
            "derivation_version > 0", name="ck_research_finding_derivation_version_positive"
        ),
        CheckConstraint(
            "payload_version > 0", name="ck_research_finding_payload_version_positive"
        ),
        # `cardinality`, not `array_length`: the latter returns NULL for an
        # empty array and a CHECK fails only on FALSE, so the obvious spelling
        # accepts exactly the case it was written to reject. See
        # docs/architecture/36-empty-array-checks.md.
        CheckConstraint("cardinality(cited) >= 1", name="ck_research_finding_cites_evidence"),
        CheckConstraint(
            "jsonb_typeof(attributes) = 'array' AND jsonb_array_length(attributes) >= 1",
            name="ck_research_finding_states_something",
        ),
    )

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True)
    task_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    subject_kind: Mapped[str] = mapped_column(String(64), nullable=False)
    subject_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    derivation: Mapped[str] = mapped_column(String(128), nullable=False)
    derivation_version: Mapped[int] = mapped_column(Integer, nullable=False)
    #: `[{"name": ..., "type": ..., "value": ...}]`, in canonical order. Typed
    #: rather than rendered, because a value's type is part of its meaning and
    #: a comparison over text would make `1` and `"1"` equal by accident.
    attributes: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, nullable=False)
    cited: Mapped[list[str]] = mapped_column(ARRAY(String(128)), nullable=False)
    payload_version: Mapped[int] = mapped_column(Integer, nullable=False)


class ResearchSynthesisModel(Base, WorkspaceScopedMixin, TimestampMixin, AuditMixin):
    """What the model made of the findings. A materialized AI artifact."""

    __tablename__ = "research_synthesis"
    __table_args__ = (
        CheckConstraint(
            "prompt_version > 0", name="ck_research_synthesis_prompt_version_positive"
        ),
        CheckConstraint(
            "payload_version > 0", name="ck_research_synthesis_payload_version_positive"
        ),
        CheckConstraint(
            "jsonb_typeof(statements) = 'array' AND jsonb_array_length(statements) >= 1",
            name="ck_research_synthesis_says_something",
        ),
        CheckConstraint(
            "cardinality(finding_ids) >= 1", name="ck_research_synthesis_rests_on_findings"
        ),
    )

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True)
    task_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    statements: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, nullable=False)
    finding_ids: Mapped[list[UUID]] = mapped_column(ARRAY(PGUUID(as_uuid=True)), nullable=False)

    prompt_name: Mapped[str] = mapped_column(String(128), nullable=False)
    prompt_version: Mapped[int] = mapped_column(Integer, nullable=False)
    prompt_fingerprint: Mapped[str] = mapped_column(String(64), nullable=False)
    model: Mapped[str] = mapped_column(String(128), nullable=False)
    #: Provenance only. Nothing in this module branches on it.
    vendor: Mapped[str] = mapped_column(String(32), nullable=False)
    evidence_digest: Mapped[str] = mapped_column(String(64), nullable=False)
    inference_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    payload_version: Mapped[int] = mapped_column(Integer, nullable=False)
