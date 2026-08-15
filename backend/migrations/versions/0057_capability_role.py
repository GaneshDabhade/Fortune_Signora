"""workspace_tenancy: named capability roles, and who holds one

Revision ID: 0057
Revises: 0056
Create Date: 2026-08-15

**[TASK-1479](../../../docs/BACKLOG.md) slice ⓸**, on
[ADR-0410](../../../docs/architecture/adr/0410-authorization-capability-layer.md):
*"Use a capability/permission layer ABOVE the existing `WorkspaceRole` enum."*

### ⛔ What is NOT here, and it is the largest thing

**The role's CONTENTS.** 📁 ADR-0410 §2: *"Existing authorization/RBAC/Casbin
architecture must remain the implementation authority… Do not create a second
independent authorization model."*

⚡ **The grants are `policy.csv` rows keyed on `role_key`** — the registry every
lane already extends. ⛔ **A `capability` table here would be that second
model**, and it would drift from the file the enforcer actually reads.

### 🔴 `role_key` is stored, and it is what reaches Casbin

**`capability_role.name` is what a customer sees; `role_key` is the subject
handed to `Authorizer.is_allowed`.** ⚡ **Namespaced `cap:` by the domain**, so
a capability role can never collide with a membership role — **not the ones
that exist today, which a reserved list handles, but the ones that do not yet.**

⚠️ **Unique on `(workspace_id, role_key)` rather than on the name**, because
`Analyst` and `analyst` are one role to the person who typed them, and the
folded form is what decides.

### ⚡ At most one capability role per person, and the primary key says so

📁 **ADR-0410 §3 calls *"Effective permissions"* the resolved answer for a
person** — **one answer.** `(workspace_id, user_id)` as the primary key makes a
second assignment unrepresentable rather than merely refused.

⛔ **`role_id` is nullable and the null is the ordinary state**: everyone holds
no capability role until somebody assigns one, which is how ADR-0410 §5's
*"every current OWNER and every current MEMBER keeps exactly the authority it
has today"* is true by construction.

### ⚠️ `ON DELETE RESTRICT`, not `CASCADE`, and the difference is a security one

**Deleting a role that people still hold would silently return every one of
them to their membership role** — 📁 which for an owner assigned a narrow
`Analyst` is a **widening**, and *"no endpoint's authorization weakens"* has a
mirror: **no person's authority should widen because a row went away.**

⛔ **So the database refuses**, and un-assigning is something a person does
deliberately.

### Reversible

`downgrade()` drops both tables, assignment first. **Lossless only while
nothing has been written** — true of any new table, and stated rather than
implied.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0057"
down_revision: str | None = "0056"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None

ROLE = "capability_role"
ASSIGNMENT = "capability_assignment"
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
        op.execute(
            f"CREATE POLICY {table}_update ON {table} "
            f"FOR UPDATE USING ({_SCOPE}) WITH CHECK ({_SCOPE})"
        )
    op.execute(f"CREATE POLICY {table}_delete ON {table} FOR DELETE USING ({_SCOPE})")
    grants = "SELECT, INSERT, UPDATE, DELETE" if updatable else "SELECT, INSERT, DELETE"
    op.execute(f"GRANT {grants} ON {table} TO {APP_ROLE}")


def upgrade() -> None:
    op.create_table(
        ROLE,
        sa.Column("role_id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("workspace_id", postgresql.UUID(as_uuid=True), nullable=False),
        # What the customer typed, shown exactly as typed.
        sa.Column("name", sa.String(40), nullable=False),
        # **The subject Casbin is asked about.** ⛔ Never rendered.
        sa.Column("role_key", sa.String(48), nullable=False),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")
        ),
    )
    op.create_index(f"ix_{ROLE}_key", ROLE, ["workspace_id", "role_key"], unique=True)

    op.create_table(
        ASSIGNMENT,
        # ⚡ **`(workspace_id, user_id)` is the key**, so a second capability
        # role for one person is unrepresentable rather than refused.
        sa.Column("workspace_id", postgresql.UUID(as_uuid=True), primary_key=True),
        # ⛔ **No foreign key to a user**: identity is Better Auth's and lives in
        # the Next.js tier (ADR-0026). What has to be true is that they are a
        # MEMBER of this workspace, which only `membership` can answer.
        sa.Column("user_id", postgresql.UUID(as_uuid=True), primary_key=True),
        # ⛔ **Nullable, and the null is the ordinary state** — no capability
        # role, which is where everyone starts and where *"change back"* lands.
        sa.Column("role_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")
        ),
        # ⚠️ **RESTRICT rather than CASCADE**, and it is a security choice:
        # deleting a role people hold would silently return each of them to
        # their membership role, which for an owner holding a narrow role is a
        # WIDENING. See the module docstring.
        sa.ForeignKeyConstraint(
            ["role_id"], [f"{ROLE}.role_id"], ondelete="RESTRICT"
        ),
    )
    op.create_index(f"ix_{ASSIGNMENT}_role", ASSIGNMENT, ["workspace_id", "role_id"])

    _tenant_policies(ROLE, updatable=True)
    # ⚡ **`UPDATE` granted**: *"Change to Analyst"* and *"change back"* are both
    # edits to the one row a person has, rather than a new row each time.
    _tenant_policies(ASSIGNMENT, updatable=True)


def downgrade() -> None:
    op.drop_index(f"ix_{ASSIGNMENT}_role", table_name=ASSIGNMENT)
    op.drop_table(ASSIGNMENT)
    op.drop_index(f"ix_{ROLE}_key", table_name=ROLE)
    op.drop_table(ROLE)
