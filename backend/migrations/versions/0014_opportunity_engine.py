"""opportunity_engine: opportunity, opportunity_state, workspace_opportunity_policy

Revision ID: 0014
Revises: 0013
Create Date: 2026-07-29

**The first workflow tables in the platform**, and they introduce a third
category of data. Everything before this is either *derived intelligence*
(rebuildable — regeneration is the rollback for a bad mapper or rule) or
*customer configuration* (declarative, and irreplaceable). These are
**workflow state**: the accumulated record of work a human performed, which
nothing reproduces.

The operational consequence belongs in the runbook, not only in code: a
pipeline rebuild regenerates derived intelligence and **must not touch
these tables**. Losing configuration means a customer re-enters their
preferences; losing workflow means a seller's pipeline disappears.

All three are immutable — `signora_app` holds `SELECT`, `INSERT`, and
`DELETE` but **not `UPDATE`**, exactly as every table since 0008. Workflow
did not require an exception:

* `opportunity` is written once. Its identity never moves, which matters
  because it is the first object in this platform a *human* tracks by
  identity — and which M13's CRM integration will hold a reference to.
* `opportunity_state` is append-only, each row a **complete** statement of
  workflow state rather than a delta. The status *is* the audit log rather
  than something kept beside it, so the two cannot drift.
* `workspace_opportunity_policy` is versioned and superseded; an edited
  policy would make every historical opportunity unexplainable.

**There is deliberately no current-score column on `opportunity`.** It
cites the score that caused it to exist and reads everything else live. A
workflow table caching derived intelligence would be a second, stale copy
of the pipeline's output (docs/architecture/27-opportunity-engine.md).
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0014"
down_revision: str | None = "0013"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None

APP_ROLE = "signora_app"
TABLES = ("workspace_opportunity_policy", "opportunity", "opportunity_state")


def _audit_columns() -> list[sa.Column]:
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


def upgrade() -> None:
    op.create_table(
        "workspace_opportunity_policy",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("version", sa.Integer(), nullable=False),
        # The policy document: minimum score, whether contested qualifies,
        # whether Signora may open opportunities unprompted. JSONB because
        # a policy is read whole and never queried field by field.
        sa.Column("policy", postgresql.JSONB(), nullable=False),
        sa.Column("supersedes", postgresql.UUID(as_uuid=True), nullable=True),
        *_audit_columns(),
        sa.ForeignKeyConstraint(
            ["supersedes"], ["workspace_opportunity_policy.id"], ondelete="SET NULL"
        ),
        sa.UniqueConstraint("workspace_id", "version", name="uq_opportunity_policy_version"),
        sa.CheckConstraint("version > 0", name="ck_opportunity_policy_version_positive"),
    )
    op.create_index(
        "ix_opportunity_policy_workspace_id", "workspace_opportunity_policy", ["workspace_id"]
    )
    # One *current* policy per workspace. The constraint is what stops two
    # concurrent configuration writes leaving a workspace with two live
    # qualification rules and no way to say which applied.
    op.create_index(
        "uq_opportunity_policy_current",
        "workspace_opportunity_policy",
        ["workspace_id"],
        unique=True,
        postgresql_where=sa.text("supersedes IS NULL"),
    )

    op.create_table(
        "opportunity",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("entity_id", postgresql.UUID(as_uuid=True), nullable=False),
        # How many opportunities this entity has had before. Part of the
        # unique key below, so two concurrent qualifications conflict rather
        # than both opening one.
        sa.Column("generation", sa.Integer(), nullable=False),
        # The score that caused this to exist. Readable forever, because
        # buying scores are immutable — the explanation chain does not break
        # when the score is later superseded.
        sa.Column("originating_buying_score_id", postgresql.UUID(as_uuid=True), nullable=False),
        # A historical fact, never a cache of a current value.
        sa.Column("score_at_creation", sa.Integer(), nullable=False),
        sa.Column("contested_at_creation", sa.Boolean(), nullable=False),
        sa.Column("qualification", sa.String(16), nullable=False),
        sa.Column("policy_version", sa.Integer(), nullable=False),
        sa.Column("payload_version", sa.Integer(), nullable=False),
        *_audit_columns(),
        sa.ForeignKeyConstraint(["entity_id"], ["entity.id"], ondelete="CASCADE"),
        # RESTRICT, not CASCADE: a buying score must never be deletable out
        # from under the opportunity that cites it. Workflow is the thing
        # here that cannot be regenerated.
        sa.ForeignKeyConstraint(
            ["originating_buying_score_id"], ["buying_score.id"], ondelete="RESTRICT"
        ),
        sa.UniqueConstraint(
            "workspace_id", "entity_id", "generation", name="uq_opportunity_generation"
        ),
        sa.CheckConstraint("generation >= 0", name="ck_opportunity_generation_non_negative"),
        sa.CheckConstraint(
            "score_at_creation >= 0 AND score_at_creation <= 100",
            name="ck_opportunity_score_range",
        ),
    )
    op.create_index("ix_opportunity_workspace_id", "opportunity", ["workspace_id"])
    op.create_index("ix_opportunity_entity", "opportunity", ["workspace_id", "entity_id"])
    op.create_index(
        "ix_opportunity_originating_score", "opportunity", ["originating_buying_score_id"]
    )

    op.create_table(
        "opportunity_state",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("opportunity_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("sequence", sa.Integer(), nullable=False),
        sa.Column("stage", sa.String(16), nullable=False),
        sa.Column("owner_id", postgresql.UUID(as_uuid=True), nullable=True),
        # NULL only for the opening TRACKING row — the one state Signora may
        # author. Every stage beyond it names the person who decided it.
        sa.Column("actor_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("reason", sa.String(512), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        *_audit_columns(),
        sa.ForeignKeyConstraint(["opportunity_id"], ["opportunity.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("opportunity_id", "sequence", name="uq_opportunity_state_sequence"),
        sa.CheckConstraint("sequence >= 0", name="ck_opportunity_state_sequence_non_negative"),
        # **Intelligence suggests; humans commit.** The machine may author
        # exactly one stage, and the database is what makes that structural
        # rather than advisory.
        sa.CheckConstraint(
            "actor_id IS NOT NULL OR stage = 'tracking'",
            name="ck_opportunity_state_only_tracking_is_machine_authored",
        ),
        sa.CheckConstraint("length(trim(reason)) > 0", name="ck_opportunity_state_has_reason"),
    )
    op.create_index("ix_opportunity_state_workspace_id", "opportunity_state", ["workspace_id"])
    # The current state: the highest sequence per opportunity.
    op.create_index(
        "ix_opportunity_state_current",
        "opportunity_state",
        ["opportunity_id", sa.text("sequence DESC")],
    )
    op.create_index("ix_opportunity_state_owner", "opportunity_state", ["workspace_id", "owner_id"])

    for table in TABLES:
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
        op.execute(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY")
        op.execute(
            f"""
            CREATE POLICY {table}_select ON {table} FOR SELECT
              USING (workspace_id = NULLIF(current_setting('app.workspace_id', true), '')::uuid)
            """
        )
        op.execute(
            f"""
            CREATE POLICY {table}_insert ON {table} FOR INSERT
              WITH CHECK (
                workspace_id = NULLIF(current_setting('app.workspace_id', true), '')::uuid
              )
            """
        )
        op.execute(
            f"""
            CREATE POLICY {table}_delete ON {table} FOR DELETE
              USING (workspace_id = NULLIF(current_setting('app.workspace_id', true), '')::uuid)
            """
        )
        op.execute(f"GRANT SELECT, INSERT, DELETE ON {table} TO {APP_ROLE}")


def downgrade() -> None:
    for table in TABLES:
        op.execute(f"REVOKE ALL ON {table} FROM {APP_ROLE}")
    op.drop_table("opportunity_state")
    op.drop_table("opportunity")
    op.drop_table("workspace_opportunity_policy")
