"""commercial_profile: what one bulk owner change asked for, and what it moved

Revision ID: 0054
Revises: 0053
Create Date: 2026-08-14

**[TASK-1479](../../../docs/BACKLOG.md) slice ⓶**, the batch half of
[ADR-0411](../../../docs/architecture/adr/0411-customer-organized-account-metadata.md)'s
Owner/CSM. **`0052` is the same table for tags and this mirrors it
deliberately** — one capability, two operations, one shape.

### ⛔ Why the module keeps its own row rather than trusting the event

📁 *Events carry identity; ports carry payload.* The applied event names a
`batch_id` and nothing else is read from it, **so a replayed event cannot
apply a selection somebody has since changed.**

### 🔴 `moved` is nullable and the null is load-bearing

**Three states, and a consumer can tell them apart:**

| | |
|---|---|
| `NULL` | **Not applied.** Nothing has happened; the reversal has nothing to undo |
| `[]` | **Applied, and every account already had that member.** The batch ran and moved nobody |
| populated | **Applied**, and the reversal restores exactly these |

⚠️ **Collapsing `NULL` and `[]` would make *"never approved"* and *"approved
and changed nothing"* the same row**, and only the first is still waiting for
somebody.

### ⚡ `assigned_to` is stored, and it is what makes the reversal safe

**The reversal is conditional on the batch's own value still being in place** —
📁 three defects found by QE and fixed at `935cbbd5`: an assignment made since,
a second reversal, and an account the batch no longer held. **The condition
cannot be recomputed later, so it is recorded here.**

### Reversible

`downgrade()` drops the table. **Lossless only while nothing has been
written** — true of any new table, and stated rather than implied.

### ⚠️ Corrected 2026-08-14 — the `NULL` above is a Python `None`, not a SQL `NULL`

🔴 **[B-269](../../../docs/BUGS.md).** The three states this docstring
tabulates are true through the ORM and **were not true to SQL**: SQLAlchemy's
default for a JSON column stores Python `None` as the JSON value `null`, so
`moved IS NULL` matched nothing. ✅ **Fixed at the model with
`JSONB(none_as_null=True)`** — no migration, no backfill, and every row
already written still decodes to `None`.

⚠️ **The sentence above is kept rather than rewritten**, because it states the
intent correctly and **a lane arriving cold should see that the promise and
the storage once disagreed** ([§2](../../../CLAUDE.md)).
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0054"
down_revision: str | None = "0053"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None

BATCH = "account_assignment_batch"
APP_ROLE = "signora_app"

_SCOPE = "workspace_id = NULLIF(current_setting('app.workspace_id', true), '')::uuid"


def upgrade() -> None:
    op.create_table(
        BATCH,
        # **The `action_batch` id, and this module's own key.** One row per
        # batch, so a second `record` for one batch is refused by the schema.
        sa.Column("batch_id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("workspace_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("role", sa.String(8), nullable=False),
        sa.Column("member_user_id", postgresql.UUID(as_uuid=True), nullable=False),
        # What the customer selected, before anything ran.
        sa.Column("requested", postgresql.JSONB(), nullable=False),
        # **What actually moved, with who held it before** — `[account, prior]`
        # pairs, `prior` null where nobody did. ⛔ **Nullable, and the null says
        # *not applied*** rather than *applied and moved nobody*.
        sa.Column("moved", postgresql.JSONB(), nullable=True),
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
        sa.CheckConstraint(
            "role IN ('owner', 'csm')", name="ck_account_assignment_batch_role"
        ),
    )
    op.create_index(f"ix_{BATCH}_workspace", BATCH, ["workspace_id"])

    op.execute(f"ALTER TABLE {BATCH} ENABLE ROW LEVEL SECURITY")
    op.execute(f"ALTER TABLE {BATCH} FORCE ROW LEVEL SECURITY")
    op.execute(f"CREATE POLICY {BATCH}_select ON {BATCH} FOR SELECT USING ({_SCOPE})")
    op.execute(f"CREATE POLICY {BATCH}_insert ON {BATCH} FOR INSERT WITH CHECK ({_SCOPE})")
    # **`UPDATE` for one field and one transition**: `moved` is written when the
    # batch applies. `USING` and `WITH CHECK` both, so a row cannot be updated
    # out of the workspace it belongs to.
    op.execute(
        f"CREATE POLICY {BATCH}_update ON {BATCH} "
        f"FOR UPDATE USING ({_SCOPE}) WITH CHECK ({_SCOPE})"
    )
    op.execute(f"CREATE POLICY {BATCH}_delete ON {BATCH} FOR DELETE USING ({_SCOPE})")
    op.execute(f"GRANT SELECT, INSERT, UPDATE, DELETE ON {BATCH} TO {APP_ROLE}")


def downgrade() -> None:
    op.drop_index(f"ix_{BATCH}_workspace", table_name=BATCH)
    op.drop_table(BATCH)
