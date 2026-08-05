"""signal_engine: signal_resolution

Revision ID: 0039
Revises: 0038
Create Date: 2026-08-05

**A signal is raised today and never resolved.** The approved Signal Center is
*"a triage queue, not a notification list"* — every signal ends in a decision,
and *"nothing is deleted: every resolution is auditable."* This is that
decision.

**A separate table rather than columns on `signal`, and that is the design.**
The signal records what Signora concluded from evidence at a moment. A person
disagreeing with it later has not changed what was concluded, so a resolution
*refers* to a signal and never edits one. The acceptance criterion *"resolution
never mutates the signal or its evidence"* is therefore a property of the
schema: there is no writable path from here to `signal`, and `signal` has held
no `UPDATE` grant since migration 0012 in any case.

**Shaped after `opportunity_state` (migration 0013).** That table is this
concept one level up — an append-only, human-authored decision carrying an
explicit `actor_id` and its own `occurred_at` rather than leaning on the audit
columns. `opportunity_engine` also already owns the dismissal vocabulary:
`DISMISSED` means *"we should not have been shown this"* and is deliberately
distinct from `CLOSED_LOST` — one is feedback about Signora's judgement, the
other is a sales outcome. **A signal-level dismissal is that same feedback
about a smaller unit, so the vocabulary is reused and not redefined.**

**The one difference from `opportunity_state` is stricter, not looser.** That
table permits exactly one machine-authored stage and its constraint says so.
**No outcome here may be authored by Signora**, so `actor_id` is `NOT NULL`
with no exemption at all.

**Four payload columns, not a JSONB blob.** Each is a fact something reads:
`snoozed_until` is compared against `now()` to bring a signal back, and a blob
would make the queue's central predicate unindexable. The equivalence
constraints — `(outcome = 'dismissed') = (dismissal_reason IS NOT NULL)` — are
written in both directions on purpose: a dismissal cannot omit its reason, and
an `actioned` row cannot smuggle one in. The domain types make the omission
*unconstructable*; this makes it *unstorable*, which is what the second writer
will eventually need.

**No `resolved` boolean on `signal` and no status column anywhere.** Whether a
signal has left the queue is derived from the outcome; a stored copy would be a
second representation of a fact this table already carries, and the two would
eventually disagree (`CLAUDE.md` §2).

Immutable on the established terms: `signora_app` holds `SELECT`, `INSERT` and
`DELETE` but **not `UPDATE`**. Changing your mind is a new row naming the one
it supersedes, so a dismissal somebody regretted cannot quietly cease to exist.
`DELETE` is granted deliberately — erasability is a property of the tenancy
model, not of what a row means.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0039"
down_revision: str | None = "0038"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None

APP_ROLE = "signora_app"
TABLE = "signal_resolution"


def upgrade() -> None:
    op.create_table(
        TABLE,
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "signal_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("signal.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("outcome", sa.String(length=16), nullable=False),
        sa.Column("assigned_to", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("snoozed_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column("dismissal_reason", sa.String(length=500), nullable=True),
        # Never nullable. Every outcome here is a human judgement.
        sa.Column("actor_id", postgresql.UUID(as_uuid=True), nullable=False),
        # When the person decided — distinct from `created_at`, which is when
        # the row reached the database. The snooze compares against this one.
        sa.Column("recorded_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("supersedes", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("payload_version", sa.Integer(), nullable=False),
        sa.Column("workspace_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(["supersedes"], [f"{TABLE}.id"], ondelete="SET NULL"),
        sa.CheckConstraint(
            "outcome IN ('actioned', 'assigned', 'snoozed', 'dismissed')",
            name=f"ck_{TABLE}_outcome_known",
        ),
        sa.CheckConstraint(
            "(outcome = 'assigned') = (assigned_to IS NOT NULL)",
            name=f"ck_{TABLE}_assignment_names_somebody",
        ),
        sa.CheckConstraint(
            "(outcome = 'snoozed') = (snoozed_until IS NOT NULL)",
            name=f"ck_{TABLE}_snooze_states_a_time",
        ),
        sa.CheckConstraint(
            "(outcome = 'dismissed') = (dismissal_reason IS NOT NULL)",
            name=f"ck_{TABLE}_dismissal_gives_a_reason",
        ),
        sa.CheckConstraint(
            "dismissal_reason IS NULL OR length(trim(dismissal_reason)) > 0",
            name=f"ck_{TABLE}_reason_is_not_blank",
        ),
        sa.CheckConstraint(
            "snoozed_until IS NULL OR snoozed_until > recorded_at",
            name=f"ck_{TABLE}_snooze_is_not_already_over",
        ),
    )
    op.create_index(f"ix_{TABLE}_workspace_id", TABLE, ["workspace_id"])
    # The queue reads a workspace's resolutions for a set of signals. Every
    # other access path goes through this pair.
    op.create_index(f"ix_{TABLE}_signal", TABLE, ["workspace_id", "signal_id"])

    # **No UPDATE.** Changing your mind is a new row naming the one it
    # supersedes, so the history of how the queue reached its current state
    # stays readable. `DELETE` is granted on the terms every other immutable
    # table uses: erasability is a property of the tenancy model, and the
    # `ON DELETE CASCADE` above is what removes a workspace's history with it.
    op.execute(f"GRANT SELECT, INSERT, DELETE ON {TABLE} TO {APP_ROLE}")
    op.execute(f"ALTER TABLE {TABLE} ENABLE ROW LEVEL SECURITY")
    op.execute(f"ALTER TABLE {TABLE} FORCE ROW LEVEL SECURITY")
    op.execute(
        f"""
        CREATE POLICY {TABLE}_select ON {TABLE} FOR SELECT
          USING (workspace_id = NULLIF(current_setting('app.workspace_id', true), '')::uuid)
        """
    )
    op.execute(
        f"""
        CREATE POLICY {TABLE}_insert ON {TABLE} FOR INSERT
          WITH CHECK (workspace_id = NULLIF(current_setting('app.workspace_id', true), '')::uuid)
        """
    )
    op.execute(
        f"""
        CREATE POLICY {TABLE}_delete ON {TABLE} FOR DELETE
          USING (workspace_id = NULLIF(current_setting('app.workspace_id', true), '')::uuid)
        """
    )


def downgrade() -> None:
    op.execute(f"REVOKE ALL ON {TABLE} FROM {APP_ROLE}")
    op.drop_table(TABLE)
