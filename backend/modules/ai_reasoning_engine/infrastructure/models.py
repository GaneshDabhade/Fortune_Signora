"""The SQLAlchemy model for `ai_reasoning`.

One table, holding a **materialized AI artifact** — the fifth data category.
Not derived intelligence (rebuildable), not customer configuration
(irreplaceable), not workflow state (unreproducible), not operational history
(the platform's account of its own behaviour): the conclusion a customer was
actually shown, with the evidence, support and limits that accompanied it.

Immutable. `signora_app` holds `SELECT`, `INSERT` and `DELETE` but **no
`UPDATE` grant** (migration 0017), so the absence of an update method here is
not the only thing stopping an edit.

**No foreign key points anywhere**, matching `ai_inference` and
`ai_narration`. `originating_buying_score_id` is a plain UUID: a reference to
`buying_score` would tie a customer-visible row's lifetime to pipeline data
with a different retention story, and would make the artifact undeletable when
a workspace is erased.

`support_level` and `contested` are **write-only query surface**, and the
repository deliberately never reads them back — see `SqlDecisionPackageRepository`.
"""

from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy import Boolean, CheckConstraint, Integer, String, Text
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from signora_platform.db.base import AuditMixin, Base, TimestampMixin, WorkspaceScopedMixin


class AIReasoningModel(Base, WorkspaceScopedMixin, TimestampMixin, AuditMixin):
    """One Decision Package: fifteen parts, three of which a model authored."""

    __tablename__ = "ai_reasoning"
    __table_args__ = (
        CheckConstraint("prompt_version > 0", name="ck_ai_reasoning_prompt_version_positive"),
        CheckConstraint("catalog_version > 0", name="ck_ai_reasoning_catalog_version_positive"),
        CheckConstraint(
            "length(trim(subject_kind)) > 0", name="ck_ai_reasoning_subject_is_addressed"
        ),
        CheckConstraint(
            "array_length(supporting_evidence, 1) >= 1", name="ck_ai_reasoning_cites_evidence"
        ),
        CheckConstraint(
            "array_length(limitations, 1) >= 1 AND array_length(suggested_validation, 1) >= 1",
            name="ck_ai_reasoning_states_its_limits",
        ),
        CheckConstraint(
            "NOT contested OR jsonb_array_length(support -> 'dissenting') IS NOT NULL "
            "OR (support ->> 'dissenting_signals')::int >= 1",
            name="ck_ai_reasoning_contested_names_its_dissent",
        ),
    )

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True)
    correlation_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)

    subject_kind: Mapped[str] = mapped_column(String(64), nullable=False)
    subject_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)

    # ---- the three parts a model authored, each a grounded statement
    summary: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    proposition: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    stated_reasoning: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, nullable=False)

    # ---- derived from facts the pipeline already owns
    supporting_evidence: Mapped[list[str]] = mapped_column(ARRAY(String(128)), nullable=False)
    #: The complete `SupportBasis`. **The authoritative representation** — a
    #: stored level alone would be the opaque score this design refuses.
    support: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    #: Derived from `support`, written for operator queries, **never read
    #: back**. See the repository.
    support_level: Mapped[str] = mapped_column(String(16), nullable=False)
    contested: Mapped[bool] = mapped_column(Boolean, nullable=False)
    temporal: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    alternative_readings: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, nullable=False)

    # ---- snapshotted from the signal catalog, with the version it came from
    limitations: Mapped[list[str]] = mapped_column(ARRAY(Text), nullable=False)
    suggested_validation: Mapped[list[str]] = mapped_column(ARRAY(Text), nullable=False)
    catalog_version: Mapped[int] = mapped_column(Integer, nullable=False)

    # ---- provenance, complete and denormalized
    prompt_name: Mapped[str] = mapped_column(String(128), nullable=False)
    prompt_version: Mapped[int] = mapped_column(Integer, nullable=False)
    prompt_fingerprint: Mapped[str] = mapped_column(String(64), nullable=False)
    model: Mapped[str] = mapped_column(String(128), nullable=False)
    vendor: Mapped[str] = mapped_column(String(32), nullable=False)
    evidence_digest: Mapped[str] = mapped_column(String(64), nullable=False)
    inference_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    #: Referenced, never copied: a buying score is immutable, so every
    #: temporal answer stays recoverable from this id forever.
    originating_buying_score_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)

    payload_version: Mapped[int] = mapped_column(Integer, nullable=False)
