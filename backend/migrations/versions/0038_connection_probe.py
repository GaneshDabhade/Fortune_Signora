"""integrations: connection_probe

Revision ID: 0038
Revises: 0037
Create Date: 2026-08-04

**Every other answer the Connection Center gives is derived from records.** A
grant exists, it has not expired, the state is `CONNECTED` — and none of that
is evidence the credential still works. The commonest integration failure is a
token that authenticates perfectly and has lost a permission, and no column
anywhere can see it.

**This table holds the only thing that can: what happened when the platform
actually tried.** Health is then derived from these rows and never stored — a
`health` column would be wrong the moment a credential was revoked without
anybody writing to it, which is the defect the derivation exists to avoid.

**Immutable, because a probe is a record of a moment.** `signora_app` holds
`SELECT`, `INSERT` and `DELETE` but **not `UPDATE`**: a probe is never
corrected, and a later one supersedes it by being later. `DELETE` is granted on
the established terms — erasability is a property of the tenancy model, not of
what a row means.

**No credential material, no vendor payload, no response body.** `detail` is
the adapter's own message about the failure and nothing else (§16). A table
that recorded what the vendor said would be a table that eventually recorded a
token in an error string.

**No counter, no streak column, no `consecutive_failures`.** Two consecutive
failures is a reading of these rows, and storing the reading beside the facts
is the duplicated truth §2 refuses — the two disagree the first time a row is
inserted by anything that forgot to increment.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0038"
down_revision: str | None = "0037"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None

APP_ROLE = "signora_app"
TABLE = "connection_probe"


def upgrade() -> None:
    op.create_table(
        TABLE,
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("connected_account_id", postgresql.UUID(as_uuid=True), nullable=False),
        # The classification, as text rather than a native enum: adding a
        # result the vendor taxonomy grows is then a deployment of code, not a
        # migration that has to run before it.
        sa.Column("result", sa.Text(), nullable=False),
        sa.Column("detail", sa.Text(), nullable=True),
        # **When the platform tried**, supplied by the caller rather than
        # defaulted by the database. Unlike a `created_at`, this is a fact
        # about the attempt and a replay must be able to state it.
        sa.Column("probed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("workspace_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        # **Present and never advanced**, exactly as on `timeline_entry`.
        # `TimestampMixin` is required on every table, and there is no `UPDATE`
        # grant for anything to advance it with — so it permanently equals
        # `created_at`, which is the honest reading of a row that is written
        # once. Diverging from the convention for one table would cost more
        # than the redundant column does.
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["connected_account_id"], ["connected_account.id"], ondelete="CASCADE"
        ),
    )
    # The only read this table serves: the newest probes for one connection.
    # Descending, because *"is it working now?"* is asked of the newest rows
    # and never of the oldest.
    op.create_index(
        "ix_connection_probe_recent",
        TABLE,
        ["workspace_id", "connected_account_id", sa.text("probed_at DESC")],
    )

    op.execute(f"ALTER TABLE {TABLE} ENABLE ROW LEVEL SECURITY")
    op.execute(f"ALTER TABLE {TABLE} FORCE ROW LEVEL SECURITY")
    op.execute(
        f"""
        CREATE POLICY {TABLE}_select ON {TABLE} FOR SELECT
          USING (workspace_id = NULLIF(current_setting('app.workspace_id', true), '')::uuid)
        """
    )
    op.execute(
        f"""
        CREATE POLICY {TABLE}_insert ON {TABLE} FOR INSERT
          WITH CHECK (
            workspace_id = NULLIF(current_setting('app.workspace_id', true), '')::uuid
          )
        """
    )
    op.execute(
        f"""
        CREATE POLICY {TABLE}_delete ON {TABLE} FOR DELETE
          USING (workspace_id = NULLIF(current_setting('app.workspace_id', true), '')::uuid)
        """
    )
    op.execute(f"GRANT SELECT, INSERT, DELETE ON {TABLE} TO {APP_ROLE}")


def downgrade() -> None:
    op.execute(f"REVOKE ALL ON {TABLE} FROM {APP_ROLE}")
    op.drop_index("ix_connection_probe_recent", table_name=TABLE)
    op.drop_table(TABLE)
