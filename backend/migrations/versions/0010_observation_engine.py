"""observation_engine: observation

Revision ID: 0010
Revises: 0009
Create Date: 2026-07-29

One workspace-owned table with forced RLS and its full policy set in this
same revision.

**Observations are immutable, and the database enforces it.** `signora_app`
holds `SELECT`, `INSERT`, and `DELETE` but **not `UPDATE`** — a
late-arriving claim produces a *finer* observation naming the coarser one
it refines, never an edit. That is also why the supersession pointer points
backwards: a forward `superseded_by` would have to be written onto the
older row, which the missing grant makes impossible.

`DELETE` is granted because observations are entirely *derived*: dropping
and rebuilding them from claims is the rollback for a bad derivation rule,
and the reason claims are stored rather than streamed.

The primary key is **deterministic** (a UUIDv5 over the observed facts), so
deduplication is a primary-key conflict rather than a code path. Re-running
derivation over the same evidence is a no-op no matter how many times an
event is redelivered.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0010"
down_revision: str | None = "0009"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None

APP_ROLE = "signora_app"
TABLE = "observation"


def upgrade() -> None:
    op.create_table(
        TABLE,
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("workspace_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("entity_id", postgresql.UUID(as_uuid=True), nullable=False),
        # An observation is always *according to someone*. Dropping this is
        # how provider disagreement becomes phantom change.
        sa.Column("provider", sa.String(64), nullable=False),
        sa.Column("attribute", sa.String(64), nullable=False),
        sa.Column("kind", sa.String(32), nullable=False),
        # NULL exactly when the observation is an occurrence: there is
        # genuinely nothing it moved from, and a placeholder would be a
        # value nobody observed.
        sa.Column("previous_value", postgresql.JSONB(), nullable=True),
        sa.Column("current_value", postgresql.JSONB(), nullable=False),
        sa.Column("direction", sa.String(16), nullable=False),
        # Arithmetic delta for counts only. Never a score, never normalized,
        # never comparable across attributes.
        sa.Column("magnitude", sa.Numeric(), nullable=True),
        sa.Column("observed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("previous_observed_at", sa.DateTime(timezone=True), nullable=True),
        # When Signora learned it — deliberately distinct from `created_at`.
        # The gap from `observed_at` is reporting lag, which downstream
        # reasons about; `created_at` is row audit.
        sa.Column("recorded_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "evidence_claim_ids",
            postgresql.ARRAY(postgresql.UUID(as_uuid=True)),
            nullable=False,
        ),
        sa.Column("supersedes", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(["entity_id"], ["entity.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["supersedes"], ["observation.id"], ondelete="SET NULL"),
        # Every observation cites the evidence that produced it. A zero-length
        # array would be an orphan, and an orphan observation looks like
        # knowledge without being traceable to any (AC-32).
        sa.CheckConstraint(
            "array_length(evidence_claim_ids, 1) >= 1",
            name="ck_observation_cites_evidence",
        ),
        # A value change must bound the window it occurred within; an
        # occurrence has nothing to have moved from. Both halves enforced
        # here so no write path can produce a half-formed observation.
        sa.CheckConstraint(
            "(kind = 'value_changed' AND previous_observed_at IS NOT NULL)"
            " OR (kind = 'occurrence_observed' AND previous_value IS NULL"
            " AND previous_observed_at IS NULL)",
            name="ck_observation_shape_matches_kind",
        ),
    )

    op.create_index("ix_observation_workspace_id", TABLE, ["workspace_id"])
    op.create_index(
        "ix_observation_entity", TABLE, ["workspace_id", "entity_id", "attribute", "observed_at"]
    )
    # Timeline reads in observed_at order, never recorded_at — otherwise a
    # backfill renders as a wall of activity on the day it was ingested.
    op.create_index("ix_observation_timeline", TABLE, ["workspace_id", "observed_at"])
    op.create_index("ix_observation_supersedes", TABLE, ["supersedes"])

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

    # Immutable: SELECT, INSERT, DELETE — deliberately no UPDATE.
    op.execute(f"GRANT SELECT, INSERT, DELETE ON {TABLE} TO {APP_ROLE}")


def downgrade() -> None:
    op.execute(f"REVOKE ALL ON {TABLE} FROM {APP_ROLE}")
    op.drop_table(TABLE)
