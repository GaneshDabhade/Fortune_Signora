"""action_batch: action_batch and action_batch_transition

Revision ID: 0042
Revises: 0041
Create Date: 2026-08-07

**Slice 3 of six** ([455 §5](../../../docs/architecture/455-context-definitions-r02-r03.md)),
ratified by
[ADR-0405](../../../docs/architecture/adr/0405-an-action-is-approved-before-it-is-effective.md).

### Why two tables rather than one with a status column

**An approval that can be edited is an approval nobody can cite** (§2). A
single table carrying `state`, `applied_at` and `reversal` would need `UPDATE`
on every one of them — and the rows most worth editing are always the
inconvenient ones. So the identity is written once and **never touched again**,
and every subsequent lifecycle event is a new row.

**The current state is derived from the transitions**, and there is no column
holding it: §2, *truth has exactly one authoritative representation; everything
else derives from it.* A stored `state` beside the log is two representations of
one fact, and the log is the one an audit cites.

> **The precedent is `opportunity_state`** (migration 0014), which this copies
> deliberately rather than inventing a second shape for the same problem:
> *"append-only, each row a **complete** statement of workflow state rather than
> a delta. The status **is** the audit log rather than something kept beside
> it, so the two cannot drift."*

### ⛔ Neither table carries `UPDATE`, and no exception is argued here

`affiliation` in 0040 **is** an exception and argues itself at length — closing
an interval moves `ended_on` exactly once and touches nothing else. **Nothing
in this context has that shape.** Every transition here is a fact about a
moment, and a fact about a moment is never corrected in place.

### There is deliberately no `is_settled` column

**The reversible window is a predicate, never a state** (ADR-0405 §2), computed
by `has_settled` in the domain. Storing it would be two representations of one
fact *and* would need a scheduler to flip it —
[P-B](../../../docs/DOMAIN_DISCOVERY_REGISTER.md) exists to refuse exactly that.
`reversible_for` is stored because it is *declared* at proposal; whether it has
elapsed is computed at read time from it and `applied_at`.

### `actor_id` is nullable on exactly one transition, and the database says so

**`applied` is the only lifecycle event with no actor.** Application is
performed by the consuming domain on the authority of the approval already
recorded, so inventing a second actor there would attribute the write to
whoever happened to flush it. The domain expresses this by `applied_on` taking
no `actor_id`; the check constraint makes it **structural rather than a
convention somebody remembers** — the same device `opportunity_state` uses for
*"intelligence suggests; humans commit."*

### No foreign key leaves this context

`workspace_id` is carried, not constrained, exactly as everywhere. The batch
holds a `name` and an `item_count` and **nothing identifying what the items
are** — this context coordinates lifecycle and never learns business semantics
([D-126](../../../docs/DECISION_REGISTER.md)).
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0042"
down_revision: str | None = "0041"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None

APP_ROLE = "signora_app"
BATCH = "action_batch"
TRANSITION = "action_batch_transition"

# The five lifecycle events, and they are the five verbs the aggregate already
# has methods for. Constrained in the database as well as in the domain so a
# row nothing in Python wrote is still refused.
TRANSITIONS = ("approved", "rejected", "withdrawn", "applied", "reversed")

# The one transition with no actor. Named once here and used by both the
# CHECK constraint and the comment above it.
UNATTRIBUTED = "applied"


def _audit_columns() -> list[sa.Column]:  # type: ignore[type-arg]
    return [
        sa.Column("workspace_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True), nullable=False),
    ]


def _tenancy(table: str) -> None:
    """`SELECT`, `INSERT`, `DELETE` — and never `UPDATE`.

    `DELETE` is granted on the same erasability grounds as every immutable
    table since 0008: being able to remove a workspace's data is a tenancy
    property, and withholding it would make a deletion request unservable.
    """
    op.execute(f"GRANT SELECT, INSERT, DELETE ON {table} TO {APP_ROLE}")
    op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
    op.execute(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY")
    tenant = "workspace_id = NULLIF(current_setting('app.workspace_id', true), '')::uuid"
    op.execute(f"CREATE POLICY {table}_select ON {table} FOR SELECT USING ({tenant})")
    op.execute(f"CREATE POLICY {table}_insert ON {table} FOR INSERT WITH CHECK ({tenant})")
    op.execute(f"CREATE POLICY {table}_delete ON {table} FOR DELETE USING ({tenant})")
    # **No UPDATE policy, because there is no UPDATE grant.** Both are withheld
    # rather than one: a policy without a grant is decorative, and a grant
    # without a policy is a tenancy hole.


def upgrade() -> None:
    op.create_table(
        BATCH,
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        # What the customer called it. Their words — a history reads as a
        # record of decisions rather than a list of identifiers.
        sa.Column("name", sa.String(length=200), nullable=False),
        # A count, never the payload. What each item *means* belongs to the
        # domain that proposed it.
        sa.Column("item_count", sa.Integer(), nullable=False),
        sa.Column("proposed_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("proposed_at", sa.DateTime(timezone=True), nullable=False),
        # Declared at proposal, and `NULL` means **reversal was never offered**
        # — a different answer from *expired*, and a customer is told them
        # differently.
        sa.Column("reversible_for", sa.Interval(), nullable=True),
        *_audit_columns(),
        sa.CheckConstraint("length(trim(name)) > 0", name=f"ck_{BATCH}_has_a_name"),
        sa.CheckConstraint("item_count >= 1", name=f"ck_{BATCH}_covers_something"),
        # `None` says reversal was never offered; a non-positive interval says
        # nothing at all, and the domain refuses it for the same reason.
        sa.CheckConstraint(
            "reversible_for IS NULL OR reversible_for > interval '0'",
            name=f"ck_{BATCH}_window_is_a_window",
        ),
    )
    op.create_index(f"ix_{BATCH}_workspace_id", BATCH, ["workspace_id"])
    _tenancy(BATCH)

    op.create_table(
        TRANSITION,
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "batch_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey(f"{BATCH}.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("sequence", sa.Integer(), nullable=False),
        sa.Column("transition", sa.String(length=16), nullable=False),
        # NULL only for `applied` — see the constraint below.
        sa.Column("actor_id", postgresql.UUID(as_uuid=True), nullable=True),
        # When it happened, never when it was written.
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        *_audit_columns(),
        sa.UniqueConstraint("batch_id", "sequence", name=f"uq_{TRANSITION}_sequence"),
        sa.CheckConstraint("sequence >= 0", name=f"ck_{TRANSITION}_sequence_non_negative"),
        sa.CheckConstraint(
            " OR ".join(f"transition = '{t}'" for t in TRANSITIONS),
            name=f"ck_{TRANSITION}_is_a_known_transition",
        ),
        # **Application is the one event with no actor**, on the authority of
        # the approval already recorded. Structural, so a row written by
        # anything other than this module is still refused.
        sa.CheckConstraint(
            f"actor_id IS NOT NULL OR transition = '{UNATTRIBUTED}'",
            name=f"ck_{TRANSITION}_only_application_is_unattributed",
        ),
    )
    op.create_index(f"ix_{TRANSITION}_workspace_id", TRANSITION, ["workspace_id"])
    # The one query reconstruction makes: *"this batch's transitions, in
    # order."* Ascending, because the aggregate is rebuilt by replaying them
    # from the beginning rather than by reading the latest.
    op.create_index(f"ix_{TRANSITION}_replay", TRANSITION, ["batch_id", "sequence"])
    _tenancy(TRANSITION)


def downgrade() -> None:
    op.execute(f"REVOKE ALL ON {TRANSITION} FROM {APP_ROLE}")
    op.drop_table(TRANSITION)
    op.execute(f"REVOKE ALL ON {BATCH} FROM {APP_ROLE}")
    op.drop_table(BATCH)
