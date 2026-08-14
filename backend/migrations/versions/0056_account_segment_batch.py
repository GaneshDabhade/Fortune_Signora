"""commercial_profile: what one bulk *Add to segment* asked for, and what it added

Revision ID: 0056
Revises: 0055
Create Date: 2026-08-14

**[TASK-1479](../../../docs/BACKLOG.md) slice ⓶b.** **`0052` is this table for
tags and `0054` for owner assignments; this is the third and they are
deliberately one shape** — one capability, three operations, one record.

### ⛔ Why the module keeps its own row rather than trusting the event

📁 *Events carry identity; ports carry payload.* The applied event names a
`batch_id` and nothing else is read from it, **so a replayed event cannot
apply a selection somebody has since changed.**

### 🔴 `added` is nullable and the null is load-bearing

| | |
|---|---|
| `NULL` | **Not applied.** Nothing has happened; the reversal has nothing to undo |
| `[]` | **Applied, and every selected account was already in the segment** |
| populated | **Applied**, and the reversal removes exactly these |

⚠️ **Collapsing `NULL` and `[]` would make *"never approved"* and *"approved
and changed nothing"* the same row**, and only the first is still waiting for
somebody.

### ⚡ The reversal removes `added` and never `requested`

🔴 **This is the defect the two slices before it both hit.** An account
curated into *Board reporting set* in June and then caught in an August bulk
add **must still be in it after the customer presses *take it back***. **The
inverse is derived from what changed, never from what was asked** — so
`requested` is kept for the confirmation and the record, and the reversal may
not read it.

### Reversible

`downgrade()` drops the table. **Lossless only while nothing has been
written.**
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0056"
down_revision: str | None = "0055"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None

BATCH = "account_segment_batch"
APP_ROLE = "signora_app"

_SCOPE = "workspace_id = NULLIF(current_setting('app.workspace_id', true), '')::uuid"


def upgrade() -> None:
    op.create_table(
        BATCH,
        # **The `action_batch` id, and this module's own key.** One row per
        # batch, so a second `record` for one batch is refused by the schema.
        sa.Column("batch_id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("workspace_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("segment_id", postgresql.UUID(as_uuid=True), nullable=False),
        # What the customer selected, before anything ran.
        sa.Column("requested", postgresql.JSONB(), nullable=False),
        # **What was actually added.** ⛔ **Nullable, and the null says *not
        # applied*** rather than *applied and added nobody*.
        sa.Column("added", postgresql.JSONB(), nullable=True),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")
        ),
        # **Cascades with the segment.** A batch that added accounts to a
        # segment that no longer exists has nothing left to describe, and
        # nothing left to reverse.
        sa.ForeignKeyConstraint(
            ["segment_id"], ["account_segment.segment_id"], ondelete="CASCADE"
        ),
    )
    op.create_index(f"ix_{BATCH}_workspace", BATCH, ["workspace_id"])

    op.execute(f"ALTER TABLE {BATCH} ENABLE ROW LEVEL SECURITY")
    op.execute(f"ALTER TABLE {BATCH} FORCE ROW LEVEL SECURITY")
    op.execute(f"CREATE POLICY {BATCH}_select ON {BATCH} FOR SELECT USING ({_SCOPE})")
    op.execute(f"CREATE POLICY {BATCH}_insert ON {BATCH} FOR INSERT WITH CHECK ({_SCOPE})")
    # **`UPDATE` for one field and one transition**: `added` is written when the
    # batch applies.
    op.execute(
        f"CREATE POLICY {BATCH}_update ON {BATCH} "
        f"FOR UPDATE USING ({_SCOPE}) WITH CHECK ({_SCOPE})"
    )
    op.execute(f"CREATE POLICY {BATCH}_delete ON {BATCH} FOR DELETE USING ({_SCOPE})")
    op.execute(f"GRANT SELECT, INSERT, UPDATE, DELETE ON {BATCH} TO {APP_ROLE}")


def downgrade() -> None:
    op.drop_index(f"ix_{BATCH}_workspace", table_name=BATCH)
    op.drop_table(BATCH)
