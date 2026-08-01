"""commercial_profile: target_account_list

Revision ID: 0025
Revises: 0024
Create Date: 2026-08-01

**The table that finally gives the pipeline an input.** `RunProviderSync` has
taken a `subject: str` since M2.1 and nothing has ever supplied one; every
company the platform has processed arrived from a seeder. This holds the
customer's own answer to *which companies*.

**The sixth table that cannot be regenerated from anything**, and the one
whose loss would be worst: a pipeline rebuild replays every provider payload
and every conclusion drawn from it, and **must not invent the list that asked
for them**. Losing it does not lose derived intelligence — it loses the
customer's instructions.

Immutable on the established terms: `signora_app` holds `SELECT`, `INSERT` and
`DELETE` but **not `UPDATE`**. `DELETE` is granted deliberately — erasability
is a property of the tenancy model, not of what a row means.

**No synchronization state, deliberately.** No watermark, no last-fetched, no
provider, no cadence, no status. Every one of those is Provider Platform's and
lives in its own tables; a column here would be this module holding a fact
about synchronization, which [ADR-0036](../../docs/architecture/adr/0036-target-account-contract.md)
makes permanently not its own.

**No stored name normalisation either.** The name is what the customer typed.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0025"
down_revision: str | None = "0024"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None

APP_ROLE = "signora_app"
TABLE = "target_account_list"


def upgrade() -> None:
    op.create_table(
        TABLE,
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("version", sa.Integer(), nullable=False),
        # JSONB, read whole, like every declaration in this module. **Nothing
        # joins on a name inside it** — matching a name to a company is the
        # Knowledge Graph's work, and a relational shape here would invite
        # somebody to do it in the wrong module.
        sa.Column("accounts", postgresql.JSONB(), nullable=False),
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
        sa.UniqueConstraint("workspace_id", "version", name="uq_target_account_list_version"),
        sa.CheckConstraint("version > 0", name="ck_target_account_list_version_positive"),
    )
    op.create_index("ix_target_account_list_workspace_id", TABLE, ["workspace_id"])

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
