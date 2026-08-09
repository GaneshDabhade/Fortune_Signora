"""security_event: one append-only record every module writes to

Revision ID: 0046
Revises: 0045
Create Date: 2026-08-09

**[TASK-492](../../../docs/BACKLOG.md)**, on
[493 §5](../../../docs/architecture/493-security-platform-architecture.md) and
[496 §3](../../../docs/architecture/496-security-architecture-blueprint.md).

### Why this is first, and why it cannot be added later

**It is the only capability on 493's roadmap whose data cannot be recovered
retroactively.** [§2](../../../CLAUDE.md): *"a system cannot be improved using
information it never recorded, and the record cannot be added retroactively —
the runs that would have explained the problem are gone."* **Workflow 1 is
producing authentication facts on `main` today and nothing records them**, and
every hour that stays true is an hour of history that does not exist.

### It is an account-activity stream, not a security log

**A security-only log means building the second one later** (493 §5).
Compliance, support and the customer's own timeline all read the same facts,
and a stream scoped to *security* would be re-derived the first time a customer
asked *"what happened to my account?"* — which is the same question with a
different reader.

### 🔴 The two-identity rule, and it is in the schema rather than the convention

**Every event carries `subject_id` AND `acting_for`, both non-nullable, from
this migration** (496 §3).

> **A line naming only the agent cannot answer *who authorised this*. A line
> naming only the human is a lie whenever an agent acted.**

**Both columns non-nullable from the first migration is the whole point** —
retrofitting an attribution column is how audit history becomes *"everything
before March has no actor"*, and that gap is permanent. When a person acts
directly the two are equal, and the row says so explicitly rather than by a
`NULL` a reader has to interpret.

### ⛔ Append-only, by the grant and the policies rather than by care

**This copies `action_batch` (0042) deliberately** rather than inventing a
second shape for the same problem, which itself copied `opportunity_state`
(0014). `SELECT`, `INSERT`, `DELETE` — **and never `UPDATE`.**

**`DELETE` is granted on the same erasability grounds as every immutable table
since 0008**: being able to remove a workspace's data is a tenancy property,
and withholding it would make a deletion request unservable.

**No `UPDATE` policy, because there is no `UPDATE` grant.** Both are withheld
rather than one — a policy without a grant is decorative, and a grant without a
policy is a tenancy hole.

### `occurred_at` is the fact's time and `created_at` is the row's

**They are different questions and both are worth keeping.** A sign-in happened
at a moment; the row recording it was written at another, and under a retry or
a replay those can differ by minutes. **Collapsing them would make the stream
unable to answer either reliably** — [§2](../../../CLAUDE.md)'s least-powerful-
author rule puts `created_at` on the database (`DEFAULT now()`, uninventable)
and `occurred_at` on the caller, which is the only thing that knows.

### No foreign key leaves this context

`workspace_id` is carried, not constrained, exactly as everywhere. **And
`subject_id` carries no foreign key to `membership` deliberately**: a security
event about somebody whose membership was later deleted must survive that
deletion, or the stream loses precisely the rows an investigation wants.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0046"
down_revision: str | None = "0045"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None

APP_ROLE = "signora_app"
TABLE = "security_event"


def _tenancy(table: str) -> None:
    """`SELECT`, `INSERT`, `DELETE` — and never `UPDATE`.

    Identical to `action_batch`'s in 0042, deliberately: two append-only
    tables with two different tenancy shapes is how one of them ends up wrong.
    """
    op.execute(f"GRANT SELECT, INSERT, DELETE ON {table} TO {APP_ROLE}")
    op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
    op.execute(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY")
    tenant = "workspace_id = NULLIF(current_setting('app.workspace_id', true), '')::uuid"
    op.execute(f"CREATE POLICY {table}_select ON {table} FOR SELECT USING ({tenant})")
    op.execute(f"CREATE POLICY {table}_insert ON {table} FOR INSERT WITH CHECK ({tenant})")
    op.execute(f"CREATE POLICY {table}_delete ON {table} FOR DELETE USING ({tenant})")
    # **No UPDATE policy, because there is no UPDATE grant.** Both withheld
    # rather than one: a policy without a grant is decorative, and a grant
    # without a policy is a tenancy hole.


def upgrade() -> None:
    op.create_table(
        TABLE,
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("workspace_id", postgresql.UUID(as_uuid=True), nullable=False),
        # **What happened, in this context's vocabulary.** A string rather than
        # a native enum: every module publishes into this stream, and a new
        # event kind must not require a migration on a type every module's
        # inserts depend on. The domain constrains the value; the database
        # constrains that it is present and short.
        sa.Column("kind", sa.String(length=80), nullable=False),
        # 🔴 **The two-identity rule, and both are non-nullable.** `subject_id`
        # is who the event is ABOUT; `acting_for` is on whose authority it
        # happened. Equal when a person acts directly, and the row says so
        # rather than leaving a NULL for a reader to interpret.
        sa.Column("subject_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("acting_for", postgresql.UUID(as_uuid=True), nullable=False),
        # When the FACT happened, supplied by whoever knows. Distinct from
        # `created_at` below, which is when the ROW was written.
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        # **Context, never payload.** Whatever the producing module needs to
        # make its own line readable — an address a link was sent to, a role
        # that changed. ⛔ Never a credential, never a token, never a password
        # (§13, §16): this table is read by support and by compliance.
        sa.Column(
            "detail",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        # `DEFAULT now()` — the database owns it because it cannot be mistaken
        # (§2, the least powerful author capable of producing it correctly).
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    # **The read every consumer makes**: one workspace's activity, most recent
    # first. 493 §5 names login history, audit, compliance and the customer's
    # own timeline, and all four ask that same question.
    op.create_index(
        f"ix_{TABLE}_workspace_recent",
        TABLE,
        ["workspace_id", sa.text("occurred_at DESC")],
    )
    # **And the second read: everything about one person.** A support call
    # starts with a name, not with a date range.
    op.create_index(f"ix_{TABLE}_subject", TABLE, ["workspace_id", "subject_id"])
    _tenancy(TABLE)


def downgrade() -> None:
    op.execute(f"REVOKE ALL ON {TABLE} FROM {APP_ROLE}")
    op.drop_table(TABLE)
