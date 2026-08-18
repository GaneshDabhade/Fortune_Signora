"""recently viewed records — Session Continuity tier 4

**📁 `Fortune Signora Session Continuity.dc.html`, tier 4 · work context.**
Its preserved facts are *"active AI thread, in-flight agent run reference, last
search query, last workspace, **recently viewed records**"*, and `D-01` fixes
the medium: *"four tiers, one medium each — URL, sessionStorage,
IndexedDB-plus-server, **server**."* **Tier 4 is the server, so it is a table.**

**📁 What Home does with it** — `Fortune Signora Home.dc.html` §04:
*"Pick up where you left off · `card.recents` · last five records touched ·
context, never urgent."* ⛔ **Home stores nothing of its own** — its own
reconciliation says so — **so the fact lives here and Home reads it.**

## 🔴 "Touched" is *viewed*, and that is not this lane's decision

⚠️ **Home says *"touched"* and never defines it.** ✅ **Session Continuity
does**: the tier-4 fact is *"recently **viewed** records"*, and its restore rule
names the same list — *"silent where it only informs a list **(recents)**"*.

## ⚡ One row per person per record, not an append-only log

**The primary key is `(workspace, person, entity)`, so viewing a record twice
updates `viewed_at` rather than appending.** 📁 The design asks for *"the last
five **records**"* — ⛔ **an append-only log would answer with the same account
five times** for somebody who opened it five times this morning, which is the
one thing the card must not do. **It also bounds the table by the number of
records a person has opened rather than by how often.**

## ⛔ `viewed_at` is not `updated_at`

**`updated_at` is audit metadata written by the mixin**; `viewed_at` is the fact
the card orders by. **Reading the audit column instead would work today and
break the first time a backfill or a column change touched a row.**

## 📁 Retention is 30 days, and it is configuration

**Session Continuity state 14**: *"tier 3 kept 7 days… **tier 4 kept 30 days**"*,
and its `U-01` — owner **Legal + Security** — says *"implement 7 and 30 as
configuration"* because retention may be constrained by the DPA. ⚡ **So the
window is applied at the read as a configured value, not frozen into the
schema.**
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0064"
down_revision: str | None = "0063"
branch_labels: None = None
depends_on: None = None

APP_ROLE = "signora_app"
TABLE = "recently_viewed"

#: The tenant predicate every table in this schema carries.
_WORKSPACE = "workspace_id = NULLIF(current_setting('app.workspace_id', true), '')::uuid"
#: 📁 **492 §0's narrowing.** A person's recents are theirs; the workspace half
#: alone would make one colleague's reading history readable by another.
_PERSON = "user_id = NULLIF(current_setting('app.user_id', true), '')::uuid"
_SCOPE = f"{_WORKSPACE} AND {_PERSON}"

#: 📁 The record kinds the design names in its own example — *"Vantage
#: Logistics"*, *"EMEA enterprise pipeline"*, *"Norvell Energy research"*.
#: ⛔ **Bounded in the database as well as at the edge**, the same habit
#: `person_preferences` follows: a kind nothing can open is a dead row.
_KINDS = "('account', 'report', 'research')"


def upgrade() -> None:
    op.create_table(
        TABLE,
        sa.Column(
            "workspace_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("workspace.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("entity_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("entity_kind", sa.String(length=32), nullable=False),
        # ⚡ **The fact the card orders by**, distinct from the audit columns.
        sa.Column("viewed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True), nullable=False),
        # **One row per person per record** — see the header.
        sa.PrimaryKeyConstraint("workspace_id", "user_id", "entity_id"),
    )
    op.create_check_constraint(
        f"ck_{TABLE}_entity_kind", TABLE, f"entity_kind IN {_KINDS}"
    )
    # ⚡ **The card's only query**: this person's rows, newest first, limit five.
    op.create_index(
        f"ix_{TABLE}_recent",
        TABLE,
        ["workspace_id", "user_id", sa.text("viewed_at DESC")],
    )

    op.execute(f"GRANT SELECT, INSERT, UPDATE, DELETE ON {TABLE} TO {APP_ROLE}")
    op.execute(f"ALTER TABLE {TABLE} ENABLE ROW LEVEL SECURITY")
    # **`FORCE` separately**: without it the owner is exempt from its own
    # policies (docs/architecture/11-tenancy.md).
    op.execute(f"ALTER TABLE {TABLE} FORCE ROW LEVEL SECURITY")

    # 🔴 **Both predicates on every policy**, including `WITH CHECK` on UPDATE —
    # ⛔ omitting it would let a write move a row onto another person.
    op.execute(f"CREATE POLICY {TABLE}_select ON {TABLE} FOR SELECT USING ({_SCOPE})")
    op.execute(f"CREATE POLICY {TABLE}_insert ON {TABLE} FOR INSERT WITH CHECK ({_SCOPE})")
    op.execute(
        f"CREATE POLICY {TABLE}_update ON {TABLE} FOR UPDATE "
        f"USING ({_SCOPE}) WITH CHECK ({_SCOPE})"
    )
    op.execute(f"CREATE POLICY {TABLE}_delete ON {TABLE} FOR DELETE USING ({_SCOPE})")


def downgrade() -> None:
    op.execute(f"REVOKE ALL ON {TABLE} FROM {APP_ROLE}")
    op.drop_index(f"ix_{TABLE}_recent", table_name=TABLE)
    op.drop_constraint(f"ck_{TABLE}_entity_kind", TABLE, type_="check")
    op.drop_table(TABLE)
