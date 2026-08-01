"""commercial_profile: buying_committee

Revision ID: 0022
Revises: 0021
Create Date: 2026-08-01

**The fourth table in the platform that cannot be regenerated from anything**,
after `signal_profile`, `product_catalog` and `icp_declaration`.

**Renumbered 0021 -> 0022 during the rebase onto `integration`**, where Lane
A's `research_request` had already taken 0021. Alembic's chain is linear by
rule (`CLAUDE.md` §20e), and the lane that rebases is the one that renumbers. It holds a
statement a customer made about how a purchase gets decided inside the
companies they sell to, and it needs the operational treatment derived tables
do not: a pipeline rebuild must leave it untouched.

Immutable on the established terms: `signora_app` holds `SELECT`, `INSERT` and
`DELETE` but **not `UPDATE`**. A revision is a new row naming the one it
supersedes. `DELETE` is granted deliberately — erasability is a property of
the tenancy model, not of what a row means, and a table the app role cannot
delete from is a workspace that cannot be erased.

**A third table rather than a column on `icp_declaration`**, and the reason is
the one that separated the first two: a committee and an ideal customer change
on different days. Somebody adds a security reviewer without touching who the
product is for, and one shared version would put both changes into an audit
history that could no longer answer *what changed*.

**No person is named in it.** A committee is a template of roles; person
entities are deferred platform-wide, and the JSONB holds job titles the
customer typed, never individuals.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0022"
down_revision: str | None = "0021"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None

APP_ROLE = "signora_app"
TABLE = "buying_committee"


def upgrade() -> None:
    op.create_table(
        TABLE,
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("version", sa.Integer(), nullable=False),
        # JSONB because a declaration is read whole and never queried field by
        # field. **Nothing joins on a product id or a role inside it** —
        # a relational shape here would invite the query that matched a person
        # to a seat, which this module must never do.
        sa.Column("committees", postgresql.JSONB(), nullable=False),
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
        sa.UniqueConstraint("workspace_id", "version", name="uq_buying_committee_version"),
        sa.CheckConstraint("version > 0", name="ck_buying_committee_version_positive"),
    )
    op.create_index("ix_buying_committee_workspace_id", TABLE, ["workspace_id"])

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
