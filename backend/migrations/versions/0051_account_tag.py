"""commercial_profile: a customer's own labels, and which accounts wear them

Revision ID: 0051
Revises: 0050
Create Date: 2026-08-13

**The first of ADR-0411's three capabilities** — [TASK-466](../../../docs/BACKLOG.md),
against [ADR-0411](../../../docs/architecture/adr/0411-customer-organized-account-metadata.md).

Two tables, and each answers a question the other must not:

* **`account_tag`** — the workspace's vocabulary. **Identity, and the label is
  not it.** A rename is an `UPDATE` to `name` and every account keeps the tag,
  which is the difference between renaming a label and replacing one.
* **`account_tag_assignment`** — which accounts wear which tag. **A join row
  and nothing else**, so removing a tag from an account is a `DELETE` rather
  than a state column somebody has to remember to read.

### ⚠️ `UPDATE` is granted here, and the earlier tables in this module refuse it

📁 `0031` says *"no `UPDATE` grant anywhere… granting one would make
immutability a convention rather than a permission"* — **and that is right for
an ICP, which is versioned and cited.** ⛔ **A tag is neither.** A customer who
renames *At risk* to *Churn risk* is correcting a label on their own filing,
not publishing a new statement, and **versioning it would keep a history
nobody would ever cite** while making the rename a write of four rows.

⚡ **So the grant differs because the concept differs**, and the difference is
recorded here rather than discovered as an inconsistency.

### 🔴 Uniqueness is enforced on the fold, in the database

**A unique index over `(workspace_id, lower(name))`** — because two chips a
customer cannot tell apart, filtering differently, is a defect they would
report, and a rule kept only in the application is a rule two concurrent
requests can both pass. 📁 The domain folds with `casefold`; **Postgres has no
`casefold`, so the index uses `lower`**, which agrees with it on everything a
customer types and differs only where the domain is *stricter*.

⚠️ **That asymmetry is deliberate and is the safe direction**: the domain
refuses a pair the index would have allowed, so the index never has to reject
something the application already accepted.

### Reversible

`downgrade()` drops both tables. **Lossless only while nothing has been
written** — which is true of any new table and is stated rather than implied.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0051"
down_revision: str | None = "0050"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None

TAG = "account_tag"
ASSIGNMENT = "account_tag_assignment"
APP_ROLE = "signora_app"

_SCOPE = "workspace_id = NULLIF(current_setting('app.workspace_id', true), '')::uuid"


def _tenant_rls(table: str, *, updatable: bool) -> None:
    op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
    op.execute(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY")
    op.execute(f"CREATE POLICY {table}_select ON {table} FOR SELECT USING ({_SCOPE})")
    op.execute(f"CREATE POLICY {table}_insert ON {table} FOR INSERT WITH CHECK ({_SCOPE})")
    op.execute(f"CREATE POLICY {table}_delete ON {table} FOR DELETE USING ({_SCOPE})")
    grants = "SELECT, INSERT, DELETE"
    if updatable:
        # `USING` and `WITH CHECK` both, so a row cannot be updated OUT of the
        # workspace it belongs to — the half an `UPDATE` policy loses if only
        # `USING` is given.
        op.execute(
            f"CREATE POLICY {table}_update ON {table} "
            f"FOR UPDATE USING ({_SCOPE}) WITH CHECK ({_SCOPE})"
        )
        grants = "SELECT, INSERT, UPDATE, DELETE"
    op.execute(f"GRANT {grants} ON {table} TO {APP_ROLE}")


def upgrade() -> None:
    op.create_table(
        TAG,
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("workspace_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(40), nullable=False),
        # The design's four chip tones. Stored as the token the stylesheet
        # already uses, so the screen renders it without a mapping table.
        sa.Column("tone", sa.String(8), nullable=False),
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
    )
    op.create_index(f"ix_{TAG}_workspace", TAG, ["workspace_id"])
    op.execute(
        f"CREATE UNIQUE INDEX uq_{TAG}_workspace_name ON {TAG} (workspace_id, lower(name))"
    )
    _tenant_rls(TAG, updatable=True)

    op.create_table(
        ASSIGNMENT,
        sa.Column("workspace_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "tag_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey(f"{TAG}.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        # ⛔ **No foreign key to an account**, and the omission matches
        # `icp_segment_product`'s: the entity lives in `knowledge_graph`, and a
        # constraint across a module boundary would make one module's schema
        # depend on another's (§5).
        sa.Column("account_id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )
    # ⚡ **Account first.** The screen's hot read is *"the tags on these forty
    # rows"*, never *"the accounts wearing this tag"*, and a composite index
    # only helps the query whose leading column it starts with.
    op.create_index(
        f"ix_{ASSIGNMENT}_account", ASSIGNMENT, ["workspace_id", "account_id"]
    )
    _tenant_rls(ASSIGNMENT, updatable=False)


def downgrade() -> None:
    op.drop_table(ASSIGNMENT)
    op.drop_table(TAG)
