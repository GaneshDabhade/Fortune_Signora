"""commercial_profile: icp_declaration

Revision ID: 0020
Revises: 0019
Create Date: 2026-08-01

**The third table in the platform that cannot be regenerated from anything**,
after `signal_profile` and `product_catalog`. It holds a statement a customer
made about who buys what they sell, and it needs the operational treatment
derived tables do not: a pipeline rebuild regenerates everything through
buying scores and **must not touch it**.

Immutable on the same terms as `product_catalog`: `signora_app` holds
`SELECT`, `INSERT` and `DELETE` but **not `UPDATE`**. A revision is a new row
naming the one it supersedes.

**`DELETE` is granted deliberately** — erasability is a property of the
tenancy model, not of what a row means. A table the app role cannot delete
from is a workspace that cannot be erased. Protecting the history is an
application concern, enforced by the absent `UPDATE` grant and a repository
that offers no delete.

**Its own table rather than a column on `product_catalog`.** They are separate
aggregates versioned independently: sharing a row would mint an ideal-customer
version every time somebody corrected a product's spelling, and an audit
history nobody can read is the thing versioning exists to prevent.

**Currency is `MAX(version)`**, so `uq_icp_declaration_version` is the
concurrency control: two callers who both read version 3 both try to insert
version 4, and the second is refused by the constraint rather than silently
winning.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0020"
down_revision: str | None = "0019"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None

APP_ROLE = "signora_app"
TABLE = "icp_declaration"


def upgrade() -> None:
    op.create_table(
        TABLE,
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("version", sa.Integer(), nullable=False),
        # JSONB because a declaration is read whole and never queried field by
        # field. **Nothing joins on a product id inside it**: resolving one is
        # the reader's job, and a relational shape here would invite the query
        # that matched companies — which this module must never do.
        sa.Column("profiles", postgresql.JSONB(), nullable=False),
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
        sa.UniqueConstraint("workspace_id", "version", name="uq_icp_declaration_version"),
        sa.CheckConstraint("version > 0", name="ck_icp_declaration_version_positive"),
    )
    op.create_index("ix_icp_declaration_workspace_id", TABLE, ["workspace_id"])

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
