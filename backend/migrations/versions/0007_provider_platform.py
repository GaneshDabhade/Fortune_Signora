"""provider_platform: sync, watermark, and raw record tables

Revision ID: 0007
Revises: 0006
Create Date: 2026-07-28

Three workspace-owned tables, each with `FORCE ROW LEVEL SECURITY` and its
policies **in this same revision** — a table created now and secured later
is a table that was unprotected in between (CLAUDE.md §8).

Policies use the `SECURITY DEFINER` membership predicate established in
migration 0003, so RLS is self-sufficient rather than dependent on the
application having scoped the session correctly.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0007"
down_revision: str | None = "0006"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None

APP_ROLE = "signora_app"
TABLES = ("provider_sync", "provider_watermark", "raw_provider_record")


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
        "provider_sync",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("provider", sa.String(64), nullable=False),
        sa.Column("capability", sa.String(64), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("records_received", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("pages_fetched", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("failure_kind", sa.String(32), nullable=True),
        sa.Column("failure_message", sa.String(1024), nullable=True),
        *_audit_columns(),
    )
    op.create_index("ix_provider_sync_workspace_id", "provider_sync", ["workspace_id"])
    op.create_index("ix_provider_sync_provider", "provider_sync", ["provider"])
    op.create_index("ix_provider_sync_status", "provider_sync", ["status"])

    op.create_table(
        "provider_watermark",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("provider", sa.String(64), nullable=False),
        sa.Column("capability", sa.String(64), nullable=False),
        sa.Column("position", sa.DateTime(timezone=True), nullable=True),
        *_audit_columns(),
        sa.UniqueConstraint(
            "workspace_id", "provider", "capability", name="uq_provider_watermark_scope"
        ),
    )
    op.create_index("ix_provider_watermark_workspace_id", "provider_watermark", ["workspace_id"])

    op.create_table(
        "raw_provider_record",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("sync_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("provider", sa.String(64), nullable=False),
        sa.Column("capability", sa.String(64), nullable=False),
        sa.Column("external_id", sa.String(512), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("payload", postgresql.JSONB(), nullable=False),
        *_audit_columns(),
        sa.ForeignKeyConstraint(["sync_id"], ["provider_sync.id"], ondelete="CASCADE"),
        # Deduplication identity. A provider legitimately reports the same
        # subject at different times, so occurred_at is part of the key —
        # collapsing those would erase the history the pipeline reads.
        sa.UniqueConstraint(
            "workspace_id",
            "provider",
            "external_id",
            "occurred_at",
            name="uq_raw_provider_record_identity",
        ),
    )
    op.create_index("ix_raw_provider_record_workspace_id", "raw_provider_record", ["workspace_id"])
    op.create_index("ix_raw_provider_record_provider", "raw_provider_record", ["provider"])
    op.create_index("ix_raw_provider_record_occurred_at", "raw_provider_record", ["occurred_at"])

    for table in TABLES:
        op.execute(f"GRANT SELECT, INSERT, UPDATE, DELETE ON {table} TO {APP_ROLE}")
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
        # FORCE matters separately from ENABLE: without it the table's owner
        # is exempt from its own policies.
        op.execute(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY")
        # NULLIF so a missing GUC coerces to NULL and the predicate fails
        # closed, rather than raising on ''::uuid.
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
            CREATE POLICY {table}_update ON {table} FOR UPDATE
              USING (workspace_id = NULLIF(current_setting('app.workspace_id', true), '')::uuid)
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


def downgrade() -> None:
    for table in reversed(TABLES):
        op.execute(f"REVOKE ALL ON {table} FROM {APP_ROLE}")
    op.drop_table("raw_provider_record")
    op.drop_table("provider_watermark")
    op.drop_table("provider_sync")
