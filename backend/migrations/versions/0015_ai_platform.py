"""ai_platform: ai_inference

Revision ID: 0015
Revises: 0014
Create Date: 2026-07-30

**One table, and it introduces a fourth kind of data.** Everything before
this is derived intelligence (rebuildable), customer configuration
(irreplaceable), or workflow state (unreproducible). `ai_inference` is an
**operational record**: what happened when Signora called a model. It is not
intelligence, nobody configures it, and no human authored it — it is the
platform's account of its own behaviour, and it is the only place the
ungrounded rate can be read from.

**The row that matters most is a failed one.** A table recording only
successes cannot report a failure rate, so every outcome is written —
`ok`, `schema_invalid`, `ungrounded`, `transient`, `permanent`. That column
is what makes AC-9 (the AI evaluation gate) measurable in production rather
than only in the harness, and it is how risk R-10 stops being an open risk
and becomes a number.

**No foreign key points anywhere.** The AI Platform is a substrate: its
`domain/` and `application/` know nothing of opportunities, scores or
signals, and its schema must not know either. A reference to `opportunity`
here would put pipeline knowledge in the substrate's own table and make the
module unextractable at the database, whatever the import graph said.

**No currency column exists, and none may be added** (AC-72). Tokens,
latency and retries are facts that stay true; a price is a contract term
that changes without the code changing. Pricing is applied at reporting
time over these rows, so a rate change re-prices history correctly instead
of leaving a stratum priced at a rate nobody remembers.

Immutable, like every table since 0008: `signora_app` holds `SELECT`,
`INSERT` and `DELETE` but **not `UPDATE`**. An operational record that can
be edited is not a record. `DELETE` remains because every tenant-owned
table must be erasable when a workspace is — retention is a property of the
tenancy model, not of what the row means.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0015"
down_revision: str | None = "0014"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None

APP_ROLE = "signora_app"
TABLES = ("ai_inference",)


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
        "ai_inference",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("correlation_id", postgresql.UUID(as_uuid=True), nullable=False),
        # Which prompt, and *which text* — not merely which number. Two rows
        # claiming version 1 with different fingerprints came from different
        # prompts, and a released version that changed is precisely the
        # failure the fingerprint exists to make visible (AC-70).
        sa.Column("prompt_name", sa.String(128), nullable=False),
        sa.Column("prompt_version", sa.Integer(), nullable=False),
        sa.Column("prompt_fingerprint", sa.String(64), nullable=False),
        # What was asked for, and what answered. Not always the same: a tag
        # may resolve to a specific build, and "the model changed underneath
        # us" is otherwise indistinguishable from "the prompt got worse".
        sa.Column("requested_model", sa.String(128), nullable=False),
        sa.Column("served_model", sa.String(128), nullable=True),
        # Provenance, never a decision input. Nothing outside an adapter may
        # branch on this column's value (CLAUDE.md §10, vendor neutrality).
        # NULL when no vendor was reached — a request rejected before
        # provider resolution has no vendor, and naming one would put a false
        # lead in the first place an engineer looks.
        sa.Column("vendor", sa.String(32), nullable=True),
        # The reproducible half of the input. With `prompt_fingerprint` this
        # is enough to reconstruct exactly what the model saw, which is why
        # the rendered prompt text is deliberately *not* stored: R-05
        # (prompt data classification) is an open escalation requiring legal
        # input, and this design routes around needing it resolved rather
        # than pretending a coding session may decide it.
        sa.Column("evidence_digest", sa.String(64), nullable=False),
        sa.Column(
            "evidence_refs",
            postgresql.ARRAY(sa.String(128)),
            nullable=False,
            server_default="{}",
        ),
        # ok · schema_invalid · ungrounded · transient · permanent.
        #
        # Deliberately no CHECK enumerating those five. `InferenceOutcome` is
        # the authoritative representation, and a SQL list of the same strings
        # would be a synchronised second copy that silently goes stale — the
        # same reason `stage` and `qualification` carry none.
        sa.Column("outcome", sa.String(16), nullable=False),
        sa.Column("input_tokens", sa.Integer(), nullable=False),
        sa.Column("output_tokens", sa.Integer(), nullable=False),
        sa.Column("latency_ms", sa.Integer(), nullable=False),
        # Retries *this platform* performed, not the adapter's own. A rising
        # value is the earliest visible sign of a rate-limit problem — visible
        # here long before it is visible on an invoice (R-01).
        sa.Column("retries", sa.Integer(), nullable=False, server_default="0"),
        # Why it failed, bounded. The bound is load-bearing rather than
        # decorative: a grounding report quotes short excerpts of the model's
        # own output, and without a ceiling this column is how the untriaged
        # blob of text the design avoids would accumulate anyway. The writer
        # truncates to fit, because a recording failure caused by the size of
        # a failure message would lose the row that mattered most.
        sa.Column("detail", sa.String(1024), nullable=True),
        *_audit_columns(),
        sa.CheckConstraint("prompt_version > 0", name="ck_ai_inference_prompt_version_positive"),
        sa.CheckConstraint(
            "input_tokens >= 0 AND output_tokens >= 0 AND latency_ms >= 0 AND retries >= 0",
            name="ck_ai_inference_usage_non_negative",
        ),
        # **Provenance is complete on every success** (AC-69). Output that
        # arrived from nobody, or from a vendor that never named what served
        # it, is a row whose result cannot be attributed — and an inference
        # nobody can attribute is not evidence of anything.
        sa.CheckConstraint(
            "outcome <> 'ok' OR (vendor IS NOT NULL AND served_model IS NOT NULL)",
            name="ck_ai_inference_success_names_its_source",
        ),
        # A failure always says why; a success never carries a reason to
        # explain. Both halves matter: a failed row with no detail is an
        # incident with no first line, and a successful row carrying one
        # means something was swallowed.
        sa.CheckConstraint(
            "(outcome = 'ok') = (detail IS NULL)",
            name="ck_ai_inference_failure_states_a_reason",
        ),
    )
    op.create_index("ix_ai_inference_workspace_id", "ai_inference", ["workspace_id"])
    # The question this table exists to answer: what proportion of calls in
    # this workspace came back ungrounded, and is it moving (AC-9, R-10).
    op.create_index(
        "ix_ai_inference_outcome", "ai_inference", ["workspace_id", "outcome", "created_at"]
    )
    # End-to-end tracing of one pipeline run through the model call it made.
    # `correlation_id` propagation is the primary debugging tool for the async
    # pipeline and is not optional plumbing (CLAUDE.md §17).
    op.create_index(
        "ix_ai_inference_correlation", "ai_inference", ["workspace_id", "correlation_id"]
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
    op.drop_table("ai_inference")
