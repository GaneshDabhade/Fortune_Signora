"""SQLAlchemy models for the AI Platform.

One table. It records what happened on a model call and nothing about what
the call was *for* — no opportunity id, no entity id, no score. The
substrate does not learn the pipeline's vocabulary at the database any more
than it does in ``domain/``, and a foreign key would have been the quiet way
to lose that (migration 0015).
"""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import CheckConstraint, Integer, String
from sqlalchemy.dialects.postgresql import ARRAY
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
