"""Something happened and one person should be told — [TASK-495](../../../docs/BACKLOG.md).

**The half [TASK-480](../../../docs/BACKLOG.md) could not build.** Migration
`0058` records what a person has READ; nothing published a notification, so the
badge counted an empty set and the bell had nothing to open. ⚡ **This is what
it reads.**

## 🔴 One recipient per row, and that is the tenancy narrowing

📁 **492 §0, quoted on [D-239](../../../docs/DECISION_REGISTER.md)**: *"a
NARROWING of tenant-owned, never a parallel to it. `workspace_id` stays
non-nullable and every existing guarantee still applies. One predicate is
added."*

⛔ **There is no `recipient_ids` array and no workspace-wide row.** ⚡ **Telling
five people is five rows** — each independently readable, ignorable and
countable, ✅ **which is what a per-person badge is.** 📁 A shared row would make
read state a workspace fact, which is D-239's own exclusion.

## 🔴 The asymmetry: a colleague may WRITE one, only the recipient may READ it

⚠️ **This is the one place this table departs from `notification_read`
(`0058`), and it is deliberate rather than an oversight.**

⛔ **`0058`'s policies are `workspace AND user` on all three verbs, because a
person marks their OWN read.** ⚡ **A notification is written FOR somebody
else** — a mention is one colleague addressing another, and the research agent
addresses whoever asked. **An INSERT policy requiring
`recipient_id = current_setting('app.user_id')` would make it impossible to
notify anybody but yourself**, which is every case.

✅ **So INSERT is workspace-scoped and SELECT is workspace AND recipient.**
🔴 **The guarantee this table exists to hold lives entirely on the READ side**:
⛔ *one person's notifications are not another's to see* — and that predicate is
in the policy, in the query, and asserted in
`tests/security_invariants/test_notification_isolates_colleagues.py`.

## ⛔ No UPDATE — and DELETE, which is a different question

📁 [§2](../../../CLAUDE.md), *immutability is the default for anything that
records a fact*. ⚡ **A notification says something happened**; ⛔ **correcting
the summary of a nudge somebody already read would change what they were told
AFTER they were told it**, so there is no `UPDATE` grant and no `UPDATE` policy.

⚠️ **This first shipped with no `DELETE` either, and the Security Invariant
suite refused it.** 📁 `test_tenancy_policy.py`, on every immutable tenant
table: *"Erasability is a property of the TENANCY model, not of what a row
means: a workspace that cannot be deleted is a retention problem on every table
it owns, immutable or not."*

⛔ **The reasoning that withheld it confused two questions.** ⚡ ***Dismissing* a
notification is a read** — recorded next door in `notification_read`, which is
why the two tables are separate — **and that is a product decision.**
✅ **Erasing a workspace is a tenancy obligation**, and every tenant-owned table
owes it.

🔴 **So the DELETE policy is workspace-scoped, mirroring INSERT rather than
SELECT.** ⛔ **A recipient-scoped DELETE would mean nobody could erase a
departing colleague's notifications** — the retention case, unreachable by
construction.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0059"
down_revision: str | None = "0058"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

APP_ROLE = "signora_app"
TABLE = "notification"

_WORKSPACE = "workspace_id = NULLIF(current_setting('app.workspace_id', true), '')::uuid"
#: 🔴 **The narrowing, and it is on the READ side only** — see the module
#: docstring: a notification is written for somebody other than its author.
_RECIPIENT = "recipient_id = NULLIF(current_setting('app.user_id', true), '')::uuid"
_READ_SCOPE = f"{_WORKSPACE} AND {_RECIPIENT}"


def upgrade() -> None:
    op.create_table(
        TABLE,
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "workspace_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("workspace.id", ondelete="CASCADE"),
            nullable=False,
        ),
        # ⚡ **Exactly one person.** ⛔ **No array, no null, no broadcast row.**
        sa.Column("recipient_id", postgresql.UUID(as_uuid=True), nullable=False),
        # 📁 The panel's tabs. ⛔ **`all` is deliberately not a value** — it is
        # the absence of a filter, never a third kind of notification.
        sa.Column("category", sa.String(length=32), nullable=False),
        # ⚡ **Who or what acted.** 📁 `actor_kind` carries the design's
        # *intelligence hue* as a domain fact rather than a rendering hint:
        # *"a generated nudge never reads as a colleague's request."*
        sa.Column("actor_kind", sa.String(length=16), nullable=False),
        # 🔴 **Both nullable, and exactly one is set** — the domain refuses the
        # other three combinations and this table cannot express that.
        #
        # ⛔ **There is deliberately NO `actor_display_name`.** 📁
        # **[C-203](../../../docs/LANE_COORDINATION.md) is `DEFERRED` and
        # architectural**: *"Nothing in the product can render a person's
        # name"*, and its impact line names notifications. **A column here
        # would have answered it by accident**, in the table least entitled to
        # — 📁 37: the same question *"appears in Timeline, comments, audit
        # history, AI attribution, notifications, mentions and assignments."*
        sa.Column("actor_person_id", postgresql.UUID(as_uuid=True), nullable=True),
        # ⚡ **An agent's name is the PLATFORM's** — it has no Better Auth
        # identity to resolve, so naming one needs nobody's answer.
        sa.Column("actor_agent_name", sa.String(length=200), nullable=True),
        # ⚡ **Which record.** 📁 Identity only — ⛔ **no cached title**: a
        # notification holding an account's name would show one that changed
        # last week.
        sa.Column("subject_kind", sa.String(length=64), nullable=False),
        sa.Column("subject_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        # 🔴 **What is expected of the reader** — the Definition of Done's
        # fourth thing, and the one a notification system usually omits.
        sa.Column("expectation", sa.Text(), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    # ⚡ **The panel's only query**: *this person's notifications, newest
    # first.* ⛔ **Leading with the pair every read filters on** before it
    # orders — the same shape `ix_notification_read_person` takes next door.
    op.create_index(
        f"ix_{TABLE}_recipient",
        TABLE,
        ["workspace_id", "recipient_id", sa.text("occurred_at DESC")],
    )

    op.execute(f"ALTER TABLE {TABLE} ENABLE ROW LEVEL SECURITY")
    op.execute(f"ALTER TABLE {TABLE} FORCE ROW LEVEL SECURITY")
    # ⛔ **No UPDATE** — §2: a notification records that something happened,
    # and there is nothing about one to amend. ✅ **DELETE is granted and is a
    # different question**: erasability is a property of the tenancy model, not
    # of what a row means (`test_tenancy_policy.py`).
    op.execute(f"GRANT SELECT, INSERT, DELETE ON {TABLE} TO {APP_ROLE}")

    # 🔴 **The guarantee.** ⛔ **A colleague's notification is invisible even to
    # a query that forgot to filter by recipient.**
    op.execute(f"CREATE POLICY {TABLE}_select ON {TABLE} FOR SELECT USING ({_READ_SCOPE})")
    # ⚡ **Workspace-scoped, deliberately.** 📁 See the module docstring: a
    # recipient predicate here would permit notifying nobody but yourself.
    op.execute(f"CREATE POLICY {TABLE}_insert ON {TABLE} FOR INSERT WITH CHECK ({_WORKSPACE})")
    # ⚡ **Workspace-scoped like INSERT, not recipient-scoped like SELECT.**
    # ⛔ **Deletion here is RETENTION, never *dismiss*** — a recipient predicate
    # would leave a departing colleague's rows erasable by nobody.
    op.execute(f"CREATE POLICY {TABLE}_delete ON {TABLE} FOR DELETE USING ({_WORKSPACE})")


def downgrade() -> None:
    op.execute(f"DROP POLICY IF EXISTS {TABLE}_delete ON {TABLE}")
    op.execute(f"DROP POLICY IF EXISTS {TABLE}_insert ON {TABLE}")
    op.execute(f"DROP POLICY IF EXISTS {TABLE}_select ON {TABLE}")
    op.drop_index(f"ix_{TABLE}_recipient", table_name=TABLE)
    op.drop_table(TABLE)
