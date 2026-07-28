"""provider_normalization: claim and normalization_outcome

Revision ID: 0008
Revises: 0007
Create Date: 2026-07-28

Two workspace-owned tables with forced RLS and full policy sets in this
same revision.

**Claims are immutable, and the database enforces it.** `signora_app` is
granted `SELECT` and `INSERT` on `claim` but **not `UPDATE`** — new
information is a new claim, never an overwrite. Immutability guarded only
by convention is immutability that lasts until the first inconvenient
deadline; here an attempted update fails with a permission error.

`DELETE` is granted because claims are *derived* data: they can be dropped
and regenerated from raw records, which is the rollback path for a broken
mapper. That is deliberate and different from mutation — a regenerated
claim is a new claim, not an edited one.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0008"
down_revision: str | None = "0007"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None

APP_ROLE = "signora_app"
TABLES = ("claim", "normalization_outcome")


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
        "claim",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("raw_record_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("provider", sa.String(64), nullable=False),
        sa.Column("attribute", sa.String(64), nullable=False),
        sa.Column("claim_domain", sa.String(32), nullable=False),
        # Value shape varies by attribute, so it is stored as JSONB and
        # typed at the domain boundary rather than by a column per
        # attribute — which would make adding one a schema migration.
        sa.Column("value", postgresql.JSONB(), nullable=False),
        sa.Column("observed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("subject_external_id", sa.String(512), nullable=False),
        sa.Column("subject_domain", sa.String(255), nullable=True),
        sa.Column("subject_legal_name", sa.String(512), nullable=True),
        sa.Column("mapper_version", sa.String(32), nullable=False),
        sa.Column("payload_provenance", sa.String(64), nullable=False),
        *_audit_columns(),
        sa.ForeignKeyConstraint(["raw_record_id"], ["raw_provider_record.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_claim_workspace_id", "claim", ["workspace_id"])
    op.create_index("ix_claim_attribute", "claim", ["attribute"])
    op.create_index("ix_claim_observed_at", "claim", ["observed_at"])
    op.create_index("ix_claim_subject_domain", "claim", ["subject_domain"])
    op.create_index("ix_claim_raw_record_id", "claim", ["raw_record_id"])

    op.create_table(
        "normalization_outcome",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("raw_record_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("provider", sa.String(64), nullable=False),
        sa.Column("mapper_version", sa.String(32), nullable=False),
        sa.Column("claim_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("rejections", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("ignored_fields", postgresql.JSONB(), nullable=False, server_default="[]"),
        *_audit_columns(),
        sa.ForeignKeyConstraint(["raw_record_id"], ["raw_provider_record.id"], ondelete="CASCADE"),
        # One outcome per record per mapper version. A re-run with the same
        # mapper is idempotent; a re-run after a mapper fix produces a new
        # row, so the improvement is visible as a diff rather than an
        # overwrite.
        sa.UniqueConstraint(
            "raw_record_id", "mapper_version", name="uq_normalization_outcome_attempt"
        ),
    )
    op.create_index(
        "ix_normalization_outcome_workspace_id", "normalization_outcome", ["workspace_id"]
    )
    op.create_index("ix_normalization_outcome_provider", "normalization_outcome", ["provider"])

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

    # Claims are immutable: SELECT, INSERT, DELETE — deliberately no UPDATE.
    # An attempted overwrite fails with a permission error rather than
    # succeeding quietly, which is what makes the invariant real.
    op.execute(f"GRANT SELECT, INSERT, DELETE ON claim TO {APP_ROLE}")

    # Outcomes carry no evidence and are re-derivable, so they may be
    # updated — but the unique constraint means a re-run under a *new*
    # mapper version inserts rather than replaces, preserving the history
    # of what each version produced.
    op.execute(f"GRANT SELECT, INSERT, UPDATE, DELETE ON normalization_outcome TO {APP_ROLE}")
    op.execute(
        """
        CREATE POLICY normalization_outcome_update ON normalization_outcome FOR UPDATE
          USING (workspace_id = NULLIF(current_setting('app.workspace_id', true), '')::uuid)
          WITH CHECK (
            workspace_id = NULLIF(current_setting('app.workspace_id', true), '')::uuid
          )
        """
    )


def downgrade() -> None:
    for table in reversed(TABLES):
        op.execute(f"REVOKE ALL ON {table} FROM {APP_ROLE}")
    op.drop_table("normalization_outcome")
    op.drop_table("claim")
