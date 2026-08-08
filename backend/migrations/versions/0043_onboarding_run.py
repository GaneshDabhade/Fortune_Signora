"""workspace_tenancy: what a person confirmed on their way in

Revision ID: 0043
Revises: 0042
Create Date: 2026-08-08

**[TASK-469] · Workflow 8**, against `docs/design-snapshot/screens/Fortune
Signora Onboarding.dc.html` ([D-138]: the snapshot is the implementation
authority). The row names this table as *"this row's backend slice"* — the
one capability Workflow 8 has that nothing in the repository already answers.

### Every answer column is nullable, and that is the design

> ***"The workspace exists at step 2… an abandoned onboarding still produces a
> customer."***

**Only the workspace step is required, and it is not stored here** — by the
time a run exists the workspace does, and `workspace_id` is what points at it.
⛔ **A `NOT NULL` industry would make the person who left at step 3
unwritable**, which is the exact opposite of what *skippable* means.

### Provenance is per answer, not per row

The design requires *"every inferred value marked as inferred and
correctable"*. **One shared provenance column would be wrong for three of the
four company facts the moment somebody corrected any one of them**, so each
answer carries its own.

### No `features` column

**Goals imply features deterministically** (*"Three outcomes map
deterministically onto modules, so the feature-preferences step
disappears"*), so the aggregate derives them and nothing stores them —
[`CLAUDE.md` §2], *truth has exactly one authoritative representation*. **A
stored copy is the one that disagrees** the first time the mapping changes,
and a customer would then see a home page built from a rule the product no
longer holds.

### `UPDATE` is granted, and the reason differs from `saved_view`'s

**Autosave is an update.** *"Every step saves on advance and on blur"* — a run
is a thing still in progress rather than a record of what was true, so
revising it is a change to its present state. ⚠️ **`membership_role_change` is
append-only for the opposite reason**, and the two are not in tension: one
records history, this one records a work in progress.

### The four verifications

| | |
|---|---|
| **Data preservation** | A new table. Nothing existing is read, written or
  dropped, and no existing row is touched |
| **Behaviour preservation** | Nothing reads it before [TASK-469]'s own
  endpoints. Every existing path is untouched |
| **Capability expansion** | A person can leave onboarding at any point and
  come back to what they had already confirmed |
| **Rollback safety** | Dropping it loses only runs written after the upgrade;
  **the workspaces those runs refined survive**, which is the same property
  that makes skipping safe. **Verified down and up** |

[TASK-469]: ../../../docs/BACKLOG.md
[D-138]: ../../../docs/DECISION_REGISTER.md
[`CLAUDE.md` §2]: ../../../CLAUDE.md
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0043"
down_revision: str | None = "0042"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None

APP_ROLE = "signora_app"
TABLE = "onboarding_run"

#: Long enough for an IANA zone (`America/Argentina/ComodRivadavia` is 34) with
#: room, and bounded so the column cannot become a note.
_TIMEZONE_LENGTH = 64
_PROVENANCE_LENGTH = 16


def upgrade() -> None:
    op.create_table(
        TABLE,
        sa.Column(
            "workspace_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("workspace.id", ondelete="CASCADE"),
            nullable=False,
        ),
        # **Composite primary key.** A workspace has many members and each
        # arrives once, so *(workspace, person)* is the identity — and it is
        # what stops a second member resuming the first member's run.
        sa.Column("person_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("current_step", sa.String(length=16), nullable=False),
        sa.Column(
            "completed_steps",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
        sa.Column("industry", sa.String(length=64), nullable=True),
        sa.Column("industry_provenance", sa.String(length=_PROVENANCE_LENGTH), nullable=True),
        sa.Column("company_size", sa.String(length=16), nullable=True),
        sa.Column("company_size_provenance", sa.String(length=_PROVENANCE_LENGTH), nullable=True),
        sa.Column("region", sa.String(length=32), nullable=True),
        sa.Column("region_provenance", sa.String(length=_PROVENANCE_LENGTH), nullable=True),
        sa.Column("timezone", sa.String(length=_TIMEZONE_LENGTH), nullable=True),
        sa.Column("timezone_provenance", sa.String(length=_PROVENANCE_LENGTH), nullable=True),
        sa.Column("role", sa.String(length=32), nullable=True),
        sa.Column("role_provenance", sa.String(length=_PROVENANCE_LENGTH), nullable=True),
        sa.Column("team_size", sa.Integer(), nullable=True),
        sa.Column("team_size_provenance", sa.String(length=_PROVENANCE_LENGTH), nullable=True),
        sa.Column(
            "goals",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("skipped_at", sa.DateTime(timezone=True), nullable=True),
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
        sa.PrimaryKeyConstraint("workspace_id", "person_id"),
    )
    # **`team_size` is bounded in the database as well as in the aggregate.**
    # The domain refuses it and this refuses it too — a rule kept only in code
    # is a rule a future writer can miss, and the range is what makes a team
    # size comparable to anything.
    op.create_check_constraint(
        f"ck_{TABLE}_team_size_range",
        TABLE,
        "team_size IS NULL OR (team_size >= 1 AND team_size <= 10000)",
    )
    # ⛔ **Three, in the database.** *"The fourth selection is disabled, not
    # silently ignored"* — the screen disables, the aggregate refuses, and this
    # is what holds if anything ever writes here without going through either.
    op.create_check_constraint(
        f"ck_{TABLE}_goal_limit",
        TABLE,
        "jsonb_array_length(goals) <= 3",
    )

    # `UPDATE` is granted: autosave is an update. See the note above on why
    # this differs from `membership_role_change`.
    op.execute(f"GRANT SELECT, INSERT, UPDATE, DELETE ON {TABLE} TO {APP_ROLE}")
    op.execute(f"ALTER TABLE {TABLE} ENABLE ROW LEVEL SECURITY")
    # **`FORCE` matters separately**: without it the table's owner is exempt
    # from its own policies (docs/architecture/11-tenancy.md).
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
    # **Both halves.** `USING` decides which rows are visible to update;
    # `WITH CHECK` decides what they may become. Omitting the second would let
    # an autosave move a run into another workspace.
    op.execute(
        f"""
        CREATE POLICY {TABLE}_update ON {TABLE} FOR UPDATE
          USING (workspace_id = NULLIF(current_setting('app.workspace_id', true), '')::uuid)
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
    op.drop_constraint(f"ck_{TABLE}_goal_limit", TABLE, type_="check")
    op.drop_constraint(f"ck_{TABLE}_team_size_range", TABLE, type_="check")
    op.drop_table(TABLE)
