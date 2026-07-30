"""ai_platform: ai_narration

Revision ID: 0016
Revises: 0015
Create Date: 2026-07-30

**A fifth kind of data, ratified 2026-07-30: a materialized AI artifact.**

The platform now holds five distinct categories, and this is not any of the
other four. It is not *derived intelligence* (rebuildable — regeneration is
the rollback for a bad mapper), not *customer configuration* (irreplaceable
and declarative), not *workflow state* (the record of work a human
performed), and not *operational history* (`ai_inference`, the platform's
account of its own behaviour). It is **a grounded explanation deliberately
persisted for auditability, user experience and provenance**.

**Immutable, and for a reason specific to this category.** A stored narration
records *what the platform actually produced at that moment* — against that
prompt, that model, that evidence. Prompt evolution or better evidence
produces a **new** narration; editing one would destroy the only record of
what a customer was actually shown, and silently invalidate every evaluation
and audit that cites it. `signora_app` holds `SELECT`, `INSERT` and `DELETE`
but **not `UPDATE`**, as every table since 0008.

**Provenance is denormalized on purpose.** Prompt name, version and
fingerprint, model, vendor, evidence digest and the full ref list are all
stored on the row, so it answers *which evidence · which prompt · which model
· which inference · when* **without reconstruction** (CLAUDE.md §17).

`inference_id` is a plain UUID with an index and **deliberately no foreign
key** to `ai_inference`. The two have different lifetimes: operational
history is a candidate for retention pruning, and a customer-visible artifact
must not become unreadable because a row describing how it was produced aged
out. The denormalized columns are what keep the narration self-describing
when that happens.

**The subject is addressed in the module's own vocabulary**, `subject_kind` +
`subject_id` — the `EvidenceRef` shape, split into columns so it is
queryable. An `entity_id` column would put the pipeline's vocabulary into the
substrate's schema, which is the same mistake `ai_inference` avoids by
carrying no foreign key at all.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0016"
down_revision: str | None = "0015"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None

APP_ROLE = "signora_app"
TABLES = ("ai_narration",)


def _audit_columns() -> list[sa.Column]:
    return [
        sa.Column("workspace_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True), nullable=False),
    ]


def upgrade() -> None:
    op.create_table(
        "ai_narration",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("correlation_id", postgresql.UUID(as_uuid=True), nullable=False),
        # What this narration is about, in the AI Platform's own addressing
        # vocabulary rather than the pipeline's.
        sa.Column("subject_kind", sa.String(64), nullable=False),
        sa.Column("subject_id", postgresql.UUID(as_uuid=True), nullable=False),
        # Provenance, complete and denormalized. See the module docstring.
        sa.Column("prompt_name", sa.String(128), nullable=False),
        sa.Column("prompt_version", sa.Integer(), nullable=False),
        sa.Column("prompt_fingerprint", sa.String(64), nullable=False),
        sa.Column("model", sa.String(128), nullable=False),
        sa.Column("vendor", sa.String(32), nullable=False),
        sa.Column("evidence_digest", sa.String(64), nullable=False),
        sa.Column(
            "evidence_refs", postgresql.ARRAY(sa.String(128)), nullable=False, server_default="{}"
        ),
        # The operational record of the call that produced this. No FK: see
        # the module docstring on differing lifetimes.
        sa.Column("inference_id", postgresql.UUID(as_uuid=True), nullable=False),
        # The artifact itself: an ordered list of `{text, evidence[]}`. JSONB
        # because a narration is read whole and never queried sentence by
        # sentence — and because the statement, not the paragraph, is the unit
        # grounding operates on, so the structure must survive storage.
        sa.Column("statements", postgresql.JSONB(), nullable=False),
        sa.Column("payload_version", sa.Integer(), nullable=False),
        *_audit_columns(),
        sa.CheckConstraint("prompt_version > 0", name="ck_ai_narration_prompt_version_positive"),
        sa.CheckConstraint(
            "length(trim(subject_kind)) > 0", name="ck_ai_narration_subject_is_addressed"
        ),
        # **A narration that says nothing is not an artifact.** An empty
        # statement list would be a row asserting the platform produced an
        # explanation while holding none, and it would pass every grounding
        # check vacuously.
        sa.CheckConstraint(
            "jsonb_typeof(statements) = 'array' AND jsonb_array_length(statements) > 0",
            name="ck_ai_narration_says_something",
        ),
        # Every narration cites something. Grounding already refuses an
        # uncited statement; this is the same guarantee at rest, so a row that
        # arrived by any other path cannot claim to be grounded.
        sa.CheckConstraint(
            "array_length(evidence_refs, 1) >= 1", name="ck_ai_narration_cites_evidence"
        ),
    )
    op.create_index("ix_ai_narration_workspace_id", "ai_narration", ["workspace_id"])
    # The current narration for a subject: the most recent one. Narrations
    # accumulate rather than being replaced, so "latest" is a query and never
    # a mutable column.
    op.create_index(
        "ix_ai_narration_subject",
        "ai_narration",
        ["workspace_id", "subject_kind", "subject_id", sa.text("created_at DESC")],
    )
    # Tracing one pipeline run through the artifact it produced (CLAUDE.md §17).
    op.create_index(
        "ix_ai_narration_correlation", "ai_narration", ["workspace_id", "correlation_id"]
    )
    op.create_index("ix_ai_narration_inference", "ai_narration", ["inference_id"])

    for table in TABLES:
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
        op.execute(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY")
        op.execute(
            f"""
            CREATE POLICY {table}_select ON {table} FOR SELECT
              USING (workspace_id = NULLIF(current_setting('app.workspace_id', true), '')::uuid)
            """
        )
        op.execute(
            f"""
            CREATE POLICY {table}_insert ON {table} FOR INSERT
              WITH CHECK (
                workspace_id = NULLIF(current_setting('app.workspace_id', true), '')::uuid
              )
            """
        )
        op.execute(
            f"""
            CREATE POLICY {table}_delete ON {table} FOR DELETE
              USING (workspace_id = NULLIF(current_setting('app.workspace_id', true), '')::uuid)
            """
        )
        op.execute(f"GRANT SELECT, INSERT, DELETE ON {table} TO {APP_ROLE}")


def downgrade() -> None:
    for table in TABLES:
        op.execute(f"REVOKE ALL ON {table} FROM {APP_ROLE}")
    op.drop_table("ai_narration")
