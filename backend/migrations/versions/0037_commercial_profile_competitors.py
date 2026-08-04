"""commercial_profile: declared_competitors

Revision ID: 0037
Revises: 0036
Create Date: 2026-08-04

**The sixth declaration, and the first that is about a risk.** The catalog says
what a customer sells, the ideal customer says who buys it, the committee says
who has to agree, the focus says which of it matters now, the target accounts
say who to watch — and this says who else is in the room.

**The fact the pipeline was missing, not the mechanism.**
`business_event_engine` has emitted `TECHNOLOGY_ADOPTED` and
`TECHNOLOGY_RETIRED` since M4, and two signals already consume them. What no
provider can report is *which of those technologies the customer is losing
deals to* — that is knowledge only the customer has, and this holds their
answer.

**Another table that cannot be regenerated from anything.** A pipeline rebuild
replays every provider payload and every conclusion drawn from it, and **must
not invent the list that made one of those technologies matter.**

Immutable on the established terms: `signora_app` holds `SELECT`, `INSERT` and
`DELETE` but **not `UPDATE`**. `DELETE` is granted deliberately — erasability
is a property of the tenancy model, not of what a row means.

**No weight, no threat level, no rank, and no column that could become one.**
`commercial_profile` records and evaluates nobody. What a `competitor_entry`
signal contributes to a score is a weight in `scoring_model@1.json`, a reviewed
artifact with a content hash that a diff can argue with — which is the least
powerful author capable of getting it right.

**No stored name normalisation either.** The name is what the customer typed,
and matching it to a technology is the Knowledge Graph's work.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0037"
down_revision: str | None = "0036"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None

APP_ROLE = "signora_app"
TABLE = "declared_competitors"


def upgrade() -> None:
    op.create_table(
        TABLE,
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("version", sa.Integer(), nullable=False),
        # JSONB, read whole, like every declaration in this module. **Nothing
        # joins on a name inside it** — matching "Salesforce" to a technology
        # is the Knowledge Graph's work, and a relational shape here would
        # invite somebody to do it in the wrong module.
        sa.Column("competitors", postgresql.JSONB(), nullable=False),
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
        sa.UniqueConstraint("workspace_id", "version", name="uq_declared_competitors_version"),
        sa.CheckConstraint("version > 0", name="ck_declared_competitors_version_positive"),
    )
    op.create_index("ix_declared_competitors_workspace_id", TABLE, ["workspace_id"])

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
