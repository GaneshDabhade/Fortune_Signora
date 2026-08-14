"""commercial_profile: a named, saved grouping of accounts, and who is in it

Revision ID: 0055
Revises: 0054
Create Date: 2026-08-14

**[TASK-1479](../../../docs/BACKLOG.md) slice ⓶b** — the third and last of
[ADR-0411](../../../docs/architecture/adr/0411-customer-organized-account-metadata.md)'s
capabilities. **`0051` is the same pair of shapes for tags and this mirrors it
deliberately**: a named thing, and a row per account that has it.

### 🔴 Two tables, because a segment outlives its membership

⛔ **A segment with nobody in it is a real thing** — a customer names *"Board
reporting set"* before curating it — **so membership cannot be the segment.**
📁 The same reason `account_tag` and `account_tag_assignment` are two tables:
**deleting the last member must not delete the list.**

### ⚡ Uniqueness is on the FOLDED name, and the display is not folded

**`ix_account_segment_name` is unique over `(workspace_id, name_key)`.**
`name_key` is the casefolded, whitespace-collapsed form the domain computes;
`name` is what the customer typed and what the panel shows. ⛔ **Without the
folded column the constraint would have to be `lower(name)`, which is not the
rule** — `lower("STRASSE")` and `lower("straße")` differ where the customer
means one segment, and `casefold` is the function that does not.

⚠️ **Stored rather than computed in a generated column** so the database and
the domain cannot disagree about what folding means: **there is one
implementation, in `account_tag.fold`, and this column is its output.**

### ⛔ No `rule` column, and its absence is the decision

📁 **The design draws two kinds of segment — `Dynamic` (*"recalculates
hourly"*) and `Static` (*"manually curated"*).** ⚡ **Only the enumerated kind
is built** ([C-1511](../../../docs/LANE_COORDINATION.md)), and **a nullable
`rule` column would be a half-built predicate engine sitting in the schema
inviting somebody to finish it** — with four of the five drawn rules naming
facts that have no source anywhere in `backend/modules/`.

### Reversible

`downgrade()` drops both tables, membership first. **Lossless only while
nothing has been written** — true of any new table, and stated rather than
implied.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0055"
down_revision: str | None = "0054"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None

SEGMENT = "account_segment"
MEMBER = "account_segment_member"
APP_ROLE = "signora_app"

_SCOPE = "workspace_id = NULLIF(current_setting('app.workspace_id', true), '')::uuid"


def _tenant_policies(table: str, *, updatable: bool) -> None:
    """RLS on, forced, and one policy per verb.

    **Forced as well as enabled**: without `FORCE`, the table owner bypasses
    every policy, and migrations run as the owner (§8).
    """
    op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
    op.execute(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY")
    op.execute(f"CREATE POLICY {table}_select ON {table} FOR SELECT USING ({_SCOPE})")
    op.execute(f"CREATE POLICY {table}_insert ON {table} FOR INSERT WITH CHECK ({_SCOPE})")
    if updatable:
        # `USING` and `WITH CHECK` both, so a row cannot be updated out of the
        # workspace it belongs to.
        op.execute(
            f"CREATE POLICY {table}_update ON {table} "
            f"FOR UPDATE USING ({_SCOPE}) WITH CHECK ({_SCOPE})"
        )
    op.execute(f"CREATE POLICY {table}_delete ON {table} FOR DELETE USING ({_SCOPE})")
    grants = "SELECT, INSERT, UPDATE, DELETE" if updatable else "SELECT, INSERT, DELETE"
    op.execute(f"GRANT {grants} ON {table} TO {APP_ROLE}")


def upgrade() -> None:
    op.create_table(
        SEGMENT,
        sa.Column("segment_id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("workspace_id", postgresql.UUID(as_uuid=True), nullable=False),
        # What the customer typed, shown exactly as typed.
        sa.Column("name", sa.String(60), nullable=False),
        # **What uniqueness is decided on** — `account_tag.fold`'s output, and
        # never rendered.
        sa.Column("name_key", sa.String(60), nullable=False),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")
        ),
    )
    op.create_index(
        f"ix_{SEGMENT}_name", SEGMENT, ["workspace_id", "name_key"], unique=True
    )

    op.create_table(
        MEMBER,
        # **The account is not a foreign key**, and that is deliberate: an
        # account is `knowledge_graph`'s and this module never joins into it.
        # A reference across a module boundary enforced by the database is a
        # dependency the import contract cannot see.
        sa.Column("segment_id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("account_id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("workspace_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("added_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "added_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")
        ),
        # **Cascades from the segment, and only from it.** Deleting a segment
        # deletes its membership; nothing else here deletes a segment.
        sa.ForeignKeyConstraint(
            ["segment_id"], [f"{SEGMENT}.segment_id"], ondelete="CASCADE"
        ),
    )
    op.create_index(f"ix_{MEMBER}_workspace", MEMBER, ["workspace_id"])
    # **The index the Companies table reads through**: "which segments is each
    # of these forty accounts in?" is one query over this, not forty.
    op.create_index(f"ix_{MEMBER}_account", MEMBER, ["workspace_id", "account_id"])

    _tenant_policies(SEGMENT, updatable=True)
    # ⛔ **No `UPDATE` on membership, and none is needed.** An account is in a
    # segment or it is not; there is no field on this row a customer can
    # change. **A grant nobody uses is a grant somebody later relies on.**
    _tenant_policies(MEMBER, updatable=False)


def downgrade() -> None:
    op.drop_index(f"ix_{MEMBER}_account", table_name=MEMBER)
    op.drop_index(f"ix_{MEMBER}_workspace", table_name=MEMBER)
    op.drop_table(MEMBER)
    op.drop_index(f"ix_{SEGMENT}_name", table_name=SEGMENT)
    op.drop_table(SEGMENT)
