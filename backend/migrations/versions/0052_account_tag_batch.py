"""commercial_profile: what a tag batch asked for, and what it changed

Revision ID: 0052
Revises: 0051
Create Date: 2026-08-13

**The row a consumer of the Action Batch is forced to hold** —
[TASK-466](../../../docs/BACKLOG.md).

📁 `ActionBatchView` publishes ***"`item_count` and not the items… what each
item *means* belongs to the domain that proposed it"***. ⚡ **So the Action
Batch knows a batch covers forty-one things and nothing about what they are**,
and this table is where `commercial_profile` keeps its half.

### 🔴 Two lists, and the second is the one that makes reversal possible

* **`requested`** — the accounts the customer selected. **What was asked.**
* **`changed`** — the accounts that did not already carry the tag and now do.
  ⛔ **`NULL` until the batch applies**, which is a different fact from an
  empty list: *not yet applied* versus *applied and changed nothing*.

⚡ **A reversal reads `changed` and never `requested`.** 📁 If three of the
forty-one were tagged in June, taking the batch back must leave those three —
**they were not this batch's doing**, and stripping them destroys a fact the
customer authored and never asked to undo.

### ⚠️ Why the accounts are JSONB rather than a child table

**They are read and written whole, and nothing joins on one.** 📁 The same
reasoning `target_account_list.accounts` and `icp_declaration.profiles` each
record. ⛔ **A child table would invite the query that asks *"which batches
touched this account?"***, which is the timeline's question and not this
module's.

### Reversible

`downgrade()` drops the table. **Lossless only while nothing has been
written** — true of any new table, and stated rather than implied.

### ⚠️ Corrected 2026-08-14 — the `NULL` above is a Python `None`, not a SQL `NULL`

🔴 **[B-269](../../../docs/BUGS.md).** The three states this docstring
tabulates are true through the ORM and **were not true to SQL**: SQLAlchemy's
default for a JSON column stores Python `None` as the JSON value `null`, so
`changed IS NULL` matched nothing. ✅ **Fixed at the model with
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

revision: str = "0052"
down_revision: str | None = "0051"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None

BATCH = "account_tag_batch"
APP_ROLE = "signora_app"

_SCOPE = "workspace_id = NULLIF(current_setting('app.workspace_id', true), '')::uuid"


def upgrade() -> None:
    op.create_table(
        BATCH,
        # ⛔ **No foreign key to `action_batch`**, and the omission is the
        # module boundary: the lifecycle is another module's aggregate, and a
        # constraint across it would make this schema depend on theirs (§5).
        sa.Column("batch_id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("workspace_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "tag_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("account_tag.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("requested", postgresql.JSONB(), nullable=False),
        # ⚡ **Nullable, and the null is load-bearing.** `NULL` is *not yet
        # applied*; `[]` is *applied and changed nothing*, which happens when
        # every selected account already carried the tag.
        sa.Column("changed", postgresql.JSONB(), nullable=True),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=False),
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
    )
    op.create_index(f"ix_{BATCH}_workspace", BATCH, ["workspace_id"])
    op.execute(f"ALTER TABLE {BATCH} ENABLE ROW LEVEL SECURITY")
    op.execute(f"ALTER TABLE {BATCH} FORCE ROW LEVEL SECURITY")
    op.execute(f"CREATE POLICY {BATCH}_select ON {BATCH} FOR SELECT USING ({_SCOPE})")
    op.execute(f"CREATE POLICY {BATCH}_insert ON {BATCH} FOR INSERT WITH CHECK ({_SCOPE})")
    # ⚡ **`USING` and `WITH CHECK` both**, so a row cannot be updated out of
    # the workspace it belongs to — the half an `UPDATE` policy loses if only
    # `USING` is given.
    op.execute(
        f"CREATE POLICY {BATCH}_update ON {BATCH} "
        f"FOR UPDATE USING ({_SCOPE}) WITH CHECK ({_SCOPE})"
    )
    op.execute(f"CREATE POLICY {BATCH}_delete ON {BATCH} FOR DELETE USING ({_SCOPE})")
    # ⚠️ **`UPDATE` is granted, and only for one transition**: `changed` moves
    # from `NULL` to a list when the batch applies. **Nothing else on this row
    # is ever edited**, and a second `UPDATE` would be a batch rewriting what
    # it asked for after the fact.
    op.execute(f"GRANT SELECT, INSERT, UPDATE, DELETE ON {BATCH} TO {APP_ROLE}")


def downgrade() -> None:
    op.drop_table(BATCH)
