"""buying_score_engine: buying_score, workspace_scoring_model

Revision ID: 0013
Revises: 0012
Create Date: 2026-07-29

Two workspace-owned tables with forced RLS and their full policy sets in
this same revision, and — as in 0012 — they are **not the same kind of
data**.

`buying_score` is derived intelligence: it can be dropped and rebuilt from
signals, which is the rollback for a bad weighting and the mechanism behind
current replay.

**`workspace_scoring_model` is customer-authored configuration.** It is the
second thing in the platform that cannot be regenerated from anything — a
statement a customer makes about how much attention each hypothesis earns.
A rebuild that discarded it would destroy customer data, not derived data.

Both are immutable: `signora_app` holds `SELECT`, `INSERT`, and `DELETE`
but **not `UPDATE`**. A recomputed score is a new row naming the one it
replaces, so what a customer was shown in March survives being shown
something different in April — which is what makes `trend` a fact about
history rather than a guess.

**There are deliberately no account attributes on `buying_score`** — no
name, no domain, no industry, nothing copied from the Knowledge Graph. A
score is a projection over signals, never an alternative representation of
account state, and a row that grew those columns would become a de facto
account record within a year. Enforced by a Security Invariant, not left to
review (docs/architecture/26-buying-score-engine.md).
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0013"
down_revision: str | None = "0012"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None

APP_ROLE = "signora_app"
TABLES = ("workspace_scoring_model", "buying_score")


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
        "workspace_scoring_model",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        # Monotonic per workspace. A score records this, and without it a
        # historical score cannot be explained.
        sa.Column("version", sa.Integer(), nullable=False),
        # What the workspace changed: weights, multipliers, bands, ceiling.
        # JSONB because a model is read whole and never queried field by
        # field. Posture is deliberately absent — it is Signora's, and there
        # is no column here through which a workspace could invert it.
        sa.Column("overrides", postgresql.JSONB(), nullable=False),
        sa.Column("supersedes", postgresql.UUID(as_uuid=True), nullable=True),
        *_audit_columns(),
        sa.ForeignKeyConstraint(
            ["supersedes"], ["workspace_scoring_model.id"], ondelete="SET NULL"
        ),
        sa.UniqueConstraint("workspace_id", "version", name="uq_scoring_model_version"),
        sa.CheckConstraint("version > 0", name="ck_scoring_model_version_positive"),
    )
    op.create_index(
        "ix_scoring_model_workspace_id", "workspace_scoring_model", ["workspace_id"]
    )
    # One *current* model per workspace. The constraint is what stops two
    # concurrent configuration writes leaving a workspace with two live
    # weightings and no way to say which applied.
    op.create_index(
        "uq_scoring_model_current",
        "workspace_scoring_model",
        ["workspace_id"],
        unique=True,
        postgresql_where=sa.text("supersedes IS NULL"),
    )

    op.create_table(
        "buying_score",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("entity_id", postgresql.UUID(as_uuid=True), nullable=False),
        # 0-100. Not a probability and not a prediction: an ordering of
        # commercial attention, normalized against a declared ceiling.
        sa.Column("value", sa.Integer(), nullable=False),
        sa.Column("trend", sa.String(16), nullable=False),
        sa.Column("delta", sa.Integer(), nullable=False),
        # The authoritative explanation. Every other column is derived from
        # it, and the score reproduces from it exactly.
        sa.Column("ledger", postgresql.JSONB(), nullable=False),
        sa.Column("ceiling", sa.Integer(), nullable=False),
        # Opposing readings both live. Never reduces the score: a
        # fought-over account warrants more attention, not average attention.
        sa.Column("contested", sa.Boolean(), nullable=False),
        sa.Column(
            "dissenting_signal_ids",
            postgresql.ARRAY(postgresql.UUID(as_uuid=True)),
            nullable=False,
            server_default="{}",
        ),
        sa.Column("computed_at", sa.DateTime(timezone=True), nullable=False),
        # Until when the stored value is *exactly* correct — not merely
        # recent. NULL means nothing is contributing, so nothing changes
        # without a new signal, and a new signal publishes an event.
        sa.Column("valid_until", sa.DateTime(timezone=True), nullable=True),
        # The evidence-derived moment the ledger's composition last changed.
        sa.Column("basis_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("trigger", sa.String(32), nullable=False),
        sa.Column("scoring_model_version", sa.Integer(), nullable=False),
        sa.Column("model_artifact_version", sa.Integer(), nullable=False),
        sa.Column("profile_version", sa.Integer(), nullable=False),
        sa.Column("payload_version", sa.Integer(), nullable=False),
        sa.Column("supersedes", postgresql.UUID(as_uuid=True), nullable=True),
        *_audit_columns(),
        sa.ForeignKeyConstraint(["entity_id"], ["entity.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["supersedes"], ["buying_score.id"], ondelete="SET NULL"),
        sa.CheckConstraint("value >= 0 AND value <= 100", name="ck_buying_score_range"),
        sa.CheckConstraint("ceiling > 0", name="ck_buying_score_ceiling_positive"),
        sa.CheckConstraint(
            "valid_until IS NULL OR valid_until >= computed_at",
            name="ck_buying_score_validity_ordered",
        ),
        # Contradiction is named, never merely counted. A contested score
        # with no dissent recorded would tell a consumer that something
        # disagrees while withholding what.
        sa.CheckConstraint(
            "NOT contested OR array_length(dissenting_signal_ids, 1) >= 1",
            name="ck_buying_score_dissent_is_named",
        ),
    )
    op.create_index("ix_buying_score_workspace_id", "buying_score", ["workspace_id"])
    op.create_index(
        "ix_buying_score_entity", "buying_score", ["workspace_id", "entity_id", "computed_at"]
    )
    op.create_index("ix_buying_score_supersedes", "buying_score", ["supersedes"])
    # The staleness sweep: which scores have passed the moment their own
    # arithmetic changes. Partial, because a superseded score is history and
    # is never re-scored.
    op.create_index(
        "ix_buying_score_stale",
        "buying_score",
        ["valid_until"],
        postgresql_where=sa.text("valid_until IS NOT NULL"),
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
    op.drop_table("buying_score")
    op.drop_table("workspace_scoring_model")
