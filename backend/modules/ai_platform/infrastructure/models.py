"""SQLAlchemy models for the AI Platform.

Two tables, holding two different kinds of thing. `ai_inference` is
**operational history** — what happened on a model call. `ai_narration` is a
**materialized AI artifact** — what the platform produced and a customer may
read.

**Neither carries a foreign key into the pipeline, and neither names its
vocabulary.** No opportunity id, no entity id, no score: `ai_inference`
records nothing about what a call was *for*, and `ai_narration` addresses its
subject with the module's own `kind`/`id` pair. A foreign key would have been
the quiet way to make the substrate unextractable at the database whatever
the import graph said (migrations 0015 and 0016).
"""

from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy import CheckConstraint, Integer, String
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from signora_platform.db.base import AuditMixin, Base, TimestampMixin, WorkspaceScopedMixin


class AIInferenceModel(Base, WorkspaceScopedMixin, TimestampMixin, AuditMixin):
    """One row per model call, written on **every** outcome.

    Immutable: `signora_app` holds no `UPDATE` grant. An operational record
    that can be edited is not a record, and the ungrounded rate read from an
    editable table would be a number nobody could defend.
    """

    __tablename__ = "ai_inference"
    __table_args__ = (
        CheckConstraint("prompt_version > 0", name="ck_ai_inference_prompt_version_positive"),
        CheckConstraint(
            "input_tokens >= 0 AND output_tokens >= 0 AND latency_ms >= 0 AND retries >= 0",
            name="ck_ai_inference_usage_non_negative",
        ),
        CheckConstraint(
            "outcome <> 'ok' OR (vendor IS NOT NULL AND served_model IS NOT NULL)",
            name="ck_ai_inference_success_names_its_source",
        ),
        CheckConstraint(
            "(outcome = 'ok') = (detail IS NULL)",
            name="ck_ai_inference_failure_states_a_reason",
        ),
    )

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True)
    correlation_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)

    prompt_name: Mapped[str] = mapped_column(String(128), nullable=False)
    prompt_version: Mapped[int] = mapped_column(Integer, nullable=False)
    prompt_fingerprint: Mapped[str] = mapped_column(String(64), nullable=False)

    requested_model: Mapped[str] = mapped_column(String(128), nullable=False)
    served_model: Mapped[str | None] = mapped_column(String(128), nullable=True)
    vendor: Mapped[str | None] = mapped_column(String(32), nullable=True)

    evidence_digest: Mapped[str] = mapped_column(String(64), nullable=False)
    evidence_refs: Mapped[list[str]] = mapped_column(ARRAY(String(128)), nullable=False)

    outcome: Mapped[str] = mapped_column(String(16), nullable=False)
    input_tokens: Mapped[int] = mapped_column(Integer, nullable=False)
    output_tokens: Mapped[int] = mapped_column(Integer, nullable=False)
    latency_ms: Mapped[int] = mapped_column(Integer, nullable=False)
    retries: Mapped[int] = mapped_column(Integer, nullable=False)
    detail: Mapped[str | None] = mapped_column(String(1024), nullable=True)


class AINarrationModel(Base, WorkspaceScopedMixin, TimestampMixin, AuditMixin):
    """A **materialized AI artifact** — the fifth data category.

    Not derived intelligence, not configuration, not workflow, not
    operational history: a grounded explanation deliberately persisted for
    auditability, user experience and provenance.

    Immutable. `signora_app` holds no `UPDATE` grant, because the row records
    what the platform actually produced at one moment — editing it would
    destroy the only record of what a customer was shown (migration 0016).

    Provenance is denormalized on purpose, so the row answers *which evidence
    · which prompt · which model · which inference · when* without a join.
    """

    __tablename__ = "ai_narration"
    __table_args__ = (
        CheckConstraint("prompt_version > 0", name="ck_ai_narration_prompt_version_positive"),
        CheckConstraint(
            "length(trim(subject_kind)) > 0", name="ck_ai_narration_subject_is_addressed"
        ),
        CheckConstraint(
            "jsonb_typeof(statements) = 'array' AND jsonb_array_length(statements) > 0",
            name="ck_ai_narration_says_something",
        ),
        CheckConstraint(
            "array_length(evidence_refs, 1) >= 1", name="ck_ai_narration_cites_evidence"
        ),
    )

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True)
    correlation_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)

    subject_kind: Mapped[str] = mapped_column(String(64), nullable=False)
    subject_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)

    prompt_name: Mapped[str] = mapped_column(String(128), nullable=False)
    prompt_version: Mapped[int] = mapped_column(Integer, nullable=False)
    prompt_fingerprint: Mapped[str] = mapped_column(String(64), nullable=False)
    model: Mapped[str] = mapped_column(String(128), nullable=False)
    vendor: Mapped[str] = mapped_column(String(32), nullable=False)

    evidence_digest: Mapped[str] = mapped_column(String(64), nullable=False)
    evidence_refs: Mapped[list[str]] = mapped_column(ARRAY(String(128)), nullable=False)

    #: No foreign key: operational history and a customer-visible artifact
    #: have different lifetimes, and a narration must not become unreadable
    #: because the row describing how it was produced aged out.
    inference_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)

    statements: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, nullable=False)
    payload_version: Mapped[int] = mapped_column(Integer, nullable=False)
