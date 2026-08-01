"""commercial_profile: product_catalog

Revision ID: 0019
Revises: 0018
Create Date: 2026-08-01

**The second table in the platform that cannot be regenerated from
anything.** `signal_profile` was the first. Both hold a statement a customer
made about their own business, and both need the operational treatment
derived tables do not: a pipeline rebuild regenerates everything through
buying scores and **must not touch either**.

Immutable: `signora_app` holds `SELECT`, `INSERT` and `DELETE` but **not
`UPDATE`**. A revision is a new row naming the one it supersedes. An edited
catalog would make every future citation of a product unresolvable — *"which
product did you mean?"* would have no answer, because the answer changed
underneath it.

**`DELETE` is granted, and the first draft of this migration withheld it.**
The Security Invariants refused that within a minute, and were right:
*erasability is a property of the tenancy model, not of what a row means* — a
table the app role cannot delete from is a workspace that cannot be erased,
which is a retention defect on every table it owns. Protecting the audit
history is an **application** concern, and it is enforced where it belongs:
the repository offers no delete method, and no `UPDATE` grant exists at all.

**Currency is `MAX(version)`, not a partial index on `supersedes IS NULL`.**
On an immutable table the *new* row is the one that names its predecessor, so
a null `supersedes` marks the **first** version permanently. `signal_profile`
carries a partial index built on the opposite assumption; the defect is
latent there only because nothing has ever written a second version. Here
`uq_product_catalog_version` does the same job correctly: two callers who
both read version 3 both try to insert version 4, and the second is refused
by the constraint rather than silently winning.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0019"
down_revision: str | None = "0018"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None

APP_ROLE = "signora_app"
TABLE = "product_catalog"


def upgrade() -> None:
    op.create_table(
        TABLE,
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        # Monotonic per workspace. Everything declared later cites it, and
        # without it a historical declaration cannot be explained.
        sa.Column("version", sa.Integer(), nullable=False),
        # JSONB because a catalog is read whole and never queried field by
        # field — the same reasoning as `signal_profile.entries`. Each entry
        # carries a stable product id that survives every revision of the
        # list containing it.
        sa.Column("products", postgresql.JSONB(), nullable=False),
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
        # The concurrency control. Not decoration: it is what turns two
        # simultaneous saves into one refusal rather than one silent loss.
        sa.UniqueConstraint("workspace_id", "version", name="uq_product_catalog_version"),
        sa.CheckConstraint("version > 0", name="ck_product_catalog_version_positive"),
    )
    op.create_index("ix_product_catalog_workspace_id", TABLE, ["workspace_id"])

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
