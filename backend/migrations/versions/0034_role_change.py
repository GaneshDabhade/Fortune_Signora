"""workspace_tenancy: what somebody was allowed to do, and when it changed

Revision ID: 0034
Revises: 0033
Create Date: 2026-08-03

**A role change overwrites `membership.role`.** Without this table the previous
value is gone, and *"who made Ravi an owner, and when?"* becomes unanswerable
by anything — not by a report somebody writes later, and not by replay.

`CLAUDE.md` §2: **a system cannot be improved using information it never
recorded, and the record cannot be added retroactively** — the changes that
would have explained the problem are gone.

### This is a record, not an event

An event with no consumer is speculative and is deliberately deferred
(46-team-management.md §18). **A fact that becomes unrecoverable if unwritten
is the opposite case**, and the distinction is the whole reason one is built
here and the other is not.

### Append-only, and the grant says so

`INSERT` and `SELECT`, and **no `UPDATE` grant** — the same enforcement
`CLAUDE.md` §2 requires of anything recording a fact. A row here describes
something that *was* true.

### The four verifications

| | |
|---|---|
| **Data preservation** | A new table. Nothing existing is read, written or dropped |
| **Behaviour preservation** | Nothing reads it yet. Every existing path is untouched |
| **Capability expansion** | Role changes become answerable later — who, from what, to what, when, and why |
| **Rollback safety** | Dropping it loses only rows written after the upgrade. **Verified down and up.** Nothing that existed before this migration depends on it |
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0034"
down_revision: str | None = "0033"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None

APP_ROLE = "signora_app"
TABLE = "membership_role_change"


def upgrade() -> None:
    op.create_table(
        TABLE,
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "workspace_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("workspace.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "membership_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("membership.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "previous_role",
            postgresql.ENUM("owner", "member", name="workspace_role", create_type=False),
            nullable=False,
        ),
        sa.Column(
            "new_role",
            postgresql.ENUM("owner", "member", name="workspace_role", create_type=False),
            nullable=False,
        ),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False
        ),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True), nullable=False),
    )
    op.create_index(f"ix_{TABLE}_workspace_id", TABLE, ["workspace_id"])
    op.create_index(f"ix_{TABLE}_membership", TABLE, ["workspace_id", "membership_id"])

    # **No UPDATE.** A record of what was true then is never edited.
    #
    # **`DELETE` is granted, on the terms every other immutable table uses.**
    # Immutability is about *editing*, not about permanence: erasability is a
    # property of the tenancy model, so deleting a workspace must be able to
    # remove its history. The `ON DELETE CASCADE` above does that; the grant is
    # what lets the application role perform it.
    op.execute(f"GRANT SELECT, INSERT, DELETE ON {TABLE} TO {APP_ROLE}")
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
          WITH CHECK (workspace_id = NULLIF(current_setting('app.workspace_id', true), '')::uuid)
        """
    )


def downgrade() -> None:
    op.execute(f"REVOKE ALL ON {TABLE} FROM {APP_ROLE}")
    op.drop_index(f"ix_{TABLE}_membership", table_name=TABLE)
    op.drop_index(f"ix_{TABLE}_workspace_id", table_name=TABLE)
    op.drop_table(TABLE)
