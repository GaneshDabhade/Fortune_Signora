"""ai_reasoning_engine: ai_reasoning

Revision ID: 0017
Revises: 0016
Create Date: 2026-07-30

The **Decision Package** — a materialized AI artifact, the fifth data
category, and the first row in the platform a customer will read in order to
*disagree* with Signora rather than merely to learn from it.

**Its own table, not a discriminator on `ai_narration`.** The two have
different shapes and different consumers — the Recommendation Engine and the
Revenue Intelligence Platform read reasoning; nothing reads narration yet —
and a shared table with a `kind` column would be one representation serving
two truths.

**Immutable, like every table since 0008.** `signora_app` holds `SELECT`,
`INSERT` and `DELETE` but **not `UPDATE`**. A package records what a customer
was actually shown; a better conclusion is a new package naming a later score.

**Two storage rules, and the difference is the design (ADR-0030).**

*Catalog content is snapshotted.* `limitations` and `suggested_validation`
are stored with the `catalog_version` they came from, because a reviewed
artifact changes by version and a package holding only a reference would
silently change what it appears to have said.

*Immutable history is referenced.* `originating_buying_score_id` is a plain
UUID and everything temporal is recoverable from it forever, because a buying
score is never edited. Copying it would duplicate a fact that cannot drift.

**No foreign key points anywhere**, for the same reason as `ai_inference` and
`ai_narration`: a reference to `buying_score` would make the artifact
undeletable when a workspace is erased, and would tie a customer-visible row's
lifetime to operational data with a different retention story.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0017"
down_revision: str | None = "0016"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None

APP_ROLE = "signora_app"
TABLES = ("ai_reasoning",)


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
        "ai_reasoning",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("correlation_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("subject_kind", sa.String(64), nullable=False),
        sa.Column("subject_id", postgresql.UUID(as_uuid=True), nullable=False),
        # ---- the three parts a model authored, each a grounded statement
        sa.Column("summary", postgresql.JSONB(), nullable=False),
        sa.Column("proposition", postgresql.JSONB(), nullable=False),
        sa.Column("stated_reasoning", postgresql.JSONB(), nullable=False),
        # ---- derived from facts the pipeline already owns
        sa.Column(
            "supporting_evidence", postgresql.ARRAY(sa.String(128)), nullable=False
        ),
        # The support *basis*, not merely its level: a customer must be able
        # to see why Support reads as it does, and a stored level alone would
        # be the opaque score this design refuses.
        sa.Column("support", postgresql.JSONB(), nullable=False),
        sa.Column("support_level", sa.String(16), nullable=False),
        sa.Column("contested", sa.Boolean(), nullable=False),
        sa.Column("temporal", postgresql.JSONB(), nullable=False),
        sa.Column("alternative_readings", postgresql.JSONB(), nullable=False),
        # ---- snapshotted from the signal catalog, with its version
        sa.Column("limitations", postgresql.ARRAY(sa.Text()), nullable=False),
        sa.Column("suggested_validation", postgresql.ARRAY(sa.Text()), nullable=False),
        sa.Column("catalog_version", sa.Integer(), nullable=False),
        # ---- provenance, complete and denormalized
        sa.Column("prompt_name", sa.String(128), nullable=False),
        sa.Column("prompt_version", sa.Integer(), nullable=False),
        sa.Column("prompt_fingerprint", sa.String(64), nullable=False),
        sa.Column("model", sa.String(128), nullable=False),
        sa.Column("vendor", sa.String(32), nullable=False),
        sa.Column("evidence_digest", sa.String(64), nullable=False),
        sa.Column("inference_id", postgresql.UUID(as_uuid=True), nullable=False),
        # Referenced, never copied: a buying score is immutable, so every
        # temporal answer stays recoverable from this id alone.
        sa.Column(
            "originating_buying_score_id", postgresql.UUID(as_uuid=True), nullable=False
        ),
        sa.Column("payload_version", sa.Integer(), nullable=False),
        *_audit_columns(),
        sa.CheckConstraint("prompt_version > 0", name="ck_ai_reasoning_prompt_version_positive"),
        sa.CheckConstraint("catalog_version > 0", name="ck_ai_reasoning_catalog_version_positive"),
        sa.CheckConstraint(
            "length(trim(subject_kind)) > 0", name="ck_ai_reasoning_subject_is_addressed"
        ),
        # **A conclusion that cites nothing is not a conclusion.** Grounding
        # refuses an uncited statement in flight; this is the same guarantee
        # at rest, so a row arriving by any other path cannot claim to be
        # grounded.
        sa.CheckConstraint(
            "array_length(supporting_evidence, 1) >= 1", name="ck_ai_reasoning_cites_evidence"
        ),
        # **The catalog was consulted.** Both are required in the signal
        # catalog, so an empty one here means the package was composed without
        # it — and a customer would be shown a conclusion with no stated
        # limits and no way to check it.
        sa.CheckConstraint(
            "array_length(limitations, 1) >= 1 "
            "AND array_length(suggested_validation, 1) >= 1",
            name="ck_ai_reasoning_states_its_limits",
        ),
        # **Contradiction survives to the last stage.** The Buying Score
        # Engine preserves dissent through six stages precisely so it is not
        # netted away here.
        sa.CheckConstraint(
            "NOT contested OR jsonb_array_length(support -> 'dissenting') IS NOT NULL "
            "OR (support ->> 'dissenting_signals')::int >= 1",
            name="ck_ai_reasoning_contested_names_its_dissent",
        ),
    )
    op.create_index("ix_ai_reasoning_workspace_id", "ai_reasoning", ["workspace_id"])
    # The current package for a subject: the most recent. Packages accumulate;
    # "latest" is a query, never a mutable column that could disagree.
    op.create_index(
        "ix_ai_reasoning_subject",
        "ai_reasoning",
        ["workspace_id", "subject_kind", "subject_id", sa.text("created_at DESC")],
    )
    op.create_index(
        "ix_ai_reasoning_correlation", "ai_reasoning", ["workspace_id", "correlation_id"]
    )
    op.create_index("ix_ai_reasoning_inference", "ai_reasoning", ["inference_id"])
    op.create_index(
        "ix_ai_reasoning_score", "ai_reasoning", ["originating_buying_score_id"]
    )

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
    op.drop_table("ai_reasoning")
