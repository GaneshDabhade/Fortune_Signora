"""commercial_profile: commercial_focus

Revision ID: 0024
Revises: 0023
Create Date: 2026-08-01

**The fifth table in the platform that cannot be regenerated from anything**,
after `signal_profile`, `product_catalog`, `icp_declaration` and
`buying_committee`. It holds a statement about what the customer is selling
right now, and a pipeline rebuild must leave it untouched.

Immutable on the established terms: `signora_app` holds `SELECT`, `INSERT` and
`DELETE` but **not `UPDATE`**. `DELETE` is granted deliberately — erasability
is a property of the tenancy model, not of what a row means.

**No ordinal column, deliberately.** The roadmap calls this capability
*business priorities* and a priority invites a rank; a stored rank here is the
column a future consumer multiplies by something, in the module furthest from
any evidence that would justify it. A product is in focus or it is not, and
the module's structural invariant refuses the word outright.

**Its own table**, and this one changes fastest of the four: a catalog moves
quarterly, an ideal customer rarely, a focus every planning cycle. One shared
version would fill three audit histories with a fourth thing's changes.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0024"
down_revision: str | None = "0023"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None

APP_ROLE = "signora_app"
TABLE = "commercial_focus"


def upgrade() -> None:
    op.create_table(
        TABLE,
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("version", sa.Integer(), nullable=False),
        # JSONB because the list is read whole and never queried element by
        # element. **Nothing joins on a product id inside it** — resolving one
        # is the reader's job.
        sa.Column("products", postgresql.JSONB(), nullable=False),
        sa.Column("objective", sa.Text(), nullable=False, server_default=""),
        sa.Column("supersedes", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("workspace_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(["supersedes"], [f"{TABLE}.id"], ondelete="SET NULL"),
        sa.UniqueConstraint("workspace_id", "version", name="uq_commercial_focus_version"),
        sa.CheckConstraint("version > 0", name="ck_commercial_focus_version_positive"),
    )
    op.create_index("ix_commercial_focus_workspace_id", TABLE, ["workspace_id"])

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
    op.drop_table(TABLE)
