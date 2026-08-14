"""commercial_profile: who owns an account, and who looks after it

Revision ID: 0053
Revises: 0052
Create Date: 2026-08-14

**The second of ADR-0411's three capabilities** — [TASK-1479](../../../docs/BACKLOG.md)
slice ⓶, against [ADR-0411](../../../docs/architecture/adr/0411-customer-organized-account-metadata.md).
Tags shipped at `0051`; this is Account Owner and CSM.

### ⛔ `member_user_id`, and no name column anywhere

📁 The ruling: *"A reference to a workspace **member**, not free text. A person
who leaves must not leave a dangling string — the reference is what makes
removal answerable."*

⚠️ **And no foreign key to a membership table**, for the reason `account_id`
carries none: a constraint here would make this module's migration depend on
another bounded context's table shape. **The application verifies membership
through `WorkspaceQueryPort` before it writes**, which is the check that can
actually be made — a foreign key would prove the *user* exists, never that
they are a member of *this* workspace.

### ⚡ `(workspace_id, account_id, role)` is the primary key

**So a second owner is refused by the schema rather than by a query somebody
remembers to write.** 📁 [§2](../../../CLAUDE.md), *prefer a violation that is
unrepresentable over one that is merely discouraged.*

### ⚠️ `UPDATE` is granted, and `0051`'s reasoning is why

📁 `0051` records that the grant *"differs because the concept differs"* — an
ICP is versioned and cited, a tag is a label on the customer's own filing.
**An assignment is the second kind.** Reassigning an account is a correction to
who is responsible, not a published statement, and **versioning it would keep a
history nobody would cite** while making every reassignment a two-row write.

⛔ **What replaces the history is the batch record**, which `0052` already
holds: *who was reassigned, from whom, by which approved batch* is answerable
there, where it is actually asked.

### Reversible

`downgrade()` drops the table. **Lossless only while nothing has been
written** — true of any new table, and stated rather than implied.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0053"
down_revision: str | None = "0052"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None

ASSIGNMENT = "account_assignment"
APP_ROLE = "signora_app"

_SCOPE = "workspace_id = NULLIF(current_setting('app.workspace_id', true), '')::uuid"


def upgrade() -> None:
    op.create_table(
        ASSIGNMENT,
        sa.Column("workspace_id", postgresql.UUID(as_uuid=True), nullable=False),
        # The Knowledge Graph's account. **Carried, never constrained** — the
        # same boundary `account_tag_assignment` and `affiliation` both keep.
        sa.Column("account_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("role", sa.String(8), nullable=False),
        sa.Column("member_user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.PrimaryKeyConstraint("workspace_id", "account_id", "role"),
        # **The closed role set, in the database.** The domain refuses an
        # unapproved role and so does this — a role arriving through a direct
        # write would be scope entering where no application code runs.
        sa.CheckConstraint("role IN ('owner', 'csm')", name="ck_account_assignment_role"),
    )
    # **Who owns what** is the account-side question the primary key already
    # serves. This index serves the other direction — *"which accounts does
    # this person hold?"* — which is what a leaver's reassignment needs.
    op.create_index(
        f"ix_{ASSIGNMENT}_member", ASSIGNMENT, ["workspace_id", "member_user_id"]
    )

    op.execute(f"ALTER TABLE {ASSIGNMENT} ENABLE ROW LEVEL SECURITY")
    op.execute(f"ALTER TABLE {ASSIGNMENT} FORCE ROW LEVEL SECURITY")
    op.execute(
        f"CREATE POLICY {ASSIGNMENT}_select ON {ASSIGNMENT} FOR SELECT USING ({_SCOPE})"
    )
    op.execute(
        f"CREATE POLICY {ASSIGNMENT}_insert ON {ASSIGNMENT} FOR INSERT WITH CHECK ({_SCOPE})"
    )
    # `USING` and `WITH CHECK` both, so a row cannot be updated OUT of the
    # workspace it belongs to — the half an `UPDATE` policy loses if only
    # `USING` is given.
    op.execute(
        f"CREATE POLICY {ASSIGNMENT}_update ON {ASSIGNMENT} "
        f"FOR UPDATE USING ({_SCOPE}) WITH CHECK ({_SCOPE})"
    )
    op.execute(
        f"CREATE POLICY {ASSIGNMENT}_delete ON {ASSIGNMENT} FOR DELETE USING ({_SCOPE})"
    )
    op.execute(f"GRANT SELECT, INSERT, UPDATE, DELETE ON {ASSIGNMENT} TO {APP_ROLE}")


def downgrade() -> None:
    op.drop_index(f"ix_{ASSIGNMENT}_member", table_name=ASSIGNMENT)
    op.drop_table(ASSIGNMENT)
