"""provider_platform: what declaration this workspace has been synced against

Revision ID: 0028
Revises: 0027
Create Date: 2026-08-02

**One row per workspace, holding one integer.**
[ADR-0036](../../docs/architecture/adr/0036-target-account-contract.md) §7:
idempotency on `event_id` handles redelivery and does **not** handle ordering.
Two declarations in quick succession are two workspace-level events, and per-
entity ordering does not order them against each other — so a handler for
version 5 running after version 6's would sync a list one revision stale.

Provider Platform therefore **ignores an event older than the version it has
already acted on**, and this table is where "already acted on" lives. The
comparison is local by design: no coordination, no lock, no reading of another
module's tables.

**Why it cannot be derived.** The obvious alternative is to infer the version
from the watermarks — but a declaration that only *removes* an account creates
no watermark, and PP-03 deliberately leaves removed accounts' watermarks in
place. Two declarations can therefore leave the watermark set identical, which
makes the version unrecoverable from it. A stored integer is the least powerful
author that can get this right.

**Not `UPDATE`-free, and that is correct.** This is not a historical record —
it is *current position*, the same category as `provider_watermark`, which is
also updated in place. What happened is recorded by `provider_sync` and the
outbox; this row only ever answers *where are we now*.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0028"
down_revision: str | None = "0027"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None

APP_ROLE = "signora_app"
TABLE = "target_sync_state"


def upgrade() -> None:
    op.create_table(
        TABLE,
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("workspace_id", postgresql.UUID(as_uuid=True), nullable=False),
        # The declaration this workspace's target accounts were last
        # synchronised against. Never decreases.
        sa.Column("declaration_version", sa.Integer(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False
        ),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True), nullable=False),
        # One row per workspace: this answers a single question about the
        # workspace, and a second row would be a second answer to it.
        sa.UniqueConstraint("workspace_id", name="uq_target_sync_state_workspace"),
    )
    op.create_index(f"ix_{TABLE}_workspace_id", TABLE, ["workspace_id"])

    op.execute(f"GRANT SELECT, INSERT, UPDATE ON {TABLE} TO {APP_ROLE}")
    op.execute(f"ALTER TABLE {TABLE} ENABLE ROW LEVEL SECURITY")
    # FORCE matters separately from ENABLE: without it the table's owner is
    # exempt from its own policies.
    op.execute(f"ALTER TABLE {TABLE} FORCE ROW LEVEL SECURITY")
    # NULLIF so a missing GUC coerces to NULL and the predicate fails closed,
    # rather than raising on ''::uuid.
    op.execute(
        f"""
        CREATE POLICY {TABLE}_select ON {TABLE} FOR SELECT
          USING (workspace_id = NULLIF(current_setting('app.workspace_id', true), '')::uuid)
        """
    )
    op.execute(
        f"""
        CREATE POLICY {TABLE}_insert ON {TABLE} FOR INSERT
          WITH CHECK (workspace_id = NULLIF(current_setting('app.workspace_id', true), '')::uuid)
        """
    )
    op.execute(
        f"""
        CREATE POLICY {TABLE}_update ON {TABLE} FOR UPDATE
          USING (workspace_id = NULLIF(current_setting('app.workspace_id', true), '')::uuid)
          WITH CHECK (workspace_id = NULLIF(current_setting('app.workspace_id', true), '')::uuid)
        """
    )


def downgrade() -> None:
    op.execute(f"REVOKE ALL ON {TABLE} FROM {APP_ROLE}")
    op.drop_index(f"ix_{TABLE}_workspace_id", table_name=TABLE)
    op.drop_table(TABLE)
