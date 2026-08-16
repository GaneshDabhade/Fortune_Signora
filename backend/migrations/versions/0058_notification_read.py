"""A person has read a notification — [TASK-480](../../../docs/BACKLOG.md).

**[D-239](../../../docs/DECISION_REGISTER.md), product owner**: `workspace_tenancy`
owns per-person, per-workspace notification state. ⛔ **No new module, no ADR,
no abstraction** — ⚡ *"we are not building a notification platform."*

## 🔴 Person-scoped, and it is the second table of its class

📁 **`person_preferences` (migration `0044`) is the precedent and this follows
it exactly** — 492 §0:

> ***"A third tenancy class … a NARROWING of tenant-owned, never a parallel to
> it. `workspace_id` stays non-nullable and every existing guarantee still
> applies. One predicate is added."***

⚡ **So all four policies carry `workspace_id AND user_id`**, and the
repository filters by both again — 📁 [§8](../../../CLAUDE.md),
*defense-in-depth*, which the person predicate earns for the same reason the
tenant one does.

## ⛔ A read is recorded; an unread is an absence

⚠️ **There is no `read` boolean and no row per recipient per delivery.** ⚡ **A
workspace of 200 people receiving 50 notifications would otherwise hold 10,000
rows describing INACTION.** ✅ **The badge count is derived from these rows,
never stored beside them** ([§2](../../../CLAUDE.md)).

## ⛔ And no foreign key to a notification

📁 **Notifications are [ADR-0017](../../../docs/architecture/adr/0017-notifications.md)'s
and [TASK-495](../../../docs/BACKLOG.md) builds them.** ⚡ **A constraint here
would make this table wait for one that does not exist** — and the row is
meaningless without its notification either way, which is a product concern
rather than a referential one.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0058"
down_revision: str | None = "0057"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

APP_ROLE = "signora_app"
TABLE = "notification_read"

_WORKSPACE = "workspace_id = NULLIF(current_setting('app.workspace_id', true), '')::uuid"
#: ⚡ **The narrowing** — 492 §0, and the same predicate `person_preferences` added.
_PERSON = "user_id = NULLIF(current_setting('app.user_id', true), '')::uuid"
_SCOPE = f"{_WORKSPACE} AND {_PERSON}"


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
        sa.Column("notification_id", postgresql.UUID(as_uuid=True), nullable=False),
        # ⚡ **The database owns the timestamp** — §2, the least powerful author.
        sa.Column(
            "read_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        # ⛔ **The key IS the idempotency.** ⚡ Marking a notification read twice
        # is something a customer does by double-clicking, and it must not be
        # an error — the repository upserts and the second write changes nothing.
        sa.PrimaryKeyConstraint("workspace_id", "user_id", "notification_id"),
    )

    # ⚡ **Counting unread is the hot path**, and it asks *"which of these ids
    # has this person NOT read"* — so the index leads with the pair every query
    # filters on before it looks at a notification at all.
    op.create_index(
        f"ix_{TABLE}_person",
        TABLE,
        ["workspace_id", "user_id"],
    )

    op.execute(f"ALTER TABLE {TABLE} ENABLE ROW LEVEL SECURITY")
    op.execute(f"ALTER TABLE {TABLE} FORCE ROW LEVEL SECURITY")
    op.execute(f"GRANT SELECT, INSERT, DELETE ON {TABLE} TO {APP_ROLE}")

    op.execute(f"CREATE POLICY {TABLE}_select ON {TABLE} FOR SELECT USING ({_SCOPE})")
    op.execute(f"CREATE POLICY {TABLE}_insert ON {TABLE} FOR INSERT WITH CHECK ({_SCOPE})")
    # ⛔ **No UPDATE grant and no UPDATE policy.** ⚡ **A read is a record of
    # something that happened** (§2, immutability) — **there is nothing about
    # one to amend**, and `mark as unread` is a DELETE if the product ever asks
    # for it rather than an edit to when it was read.
    op.execute(f"CREATE POLICY {TABLE}_delete ON {TABLE} FOR DELETE USING ({_SCOPE})")


def downgrade() -> None:
    op.execute(f"DROP POLICY IF EXISTS {TABLE}_delete ON {TABLE}")
    op.execute(f"DROP POLICY IF EXISTS {TABLE}_insert ON {TABLE}")
    op.execute(f"DROP POLICY IF EXISTS {TABLE}_select ON {TABLE}")
    op.drop_index(f"ix_{TABLE}_person", table_name=TABLE)
    op.drop_table(TABLE)
