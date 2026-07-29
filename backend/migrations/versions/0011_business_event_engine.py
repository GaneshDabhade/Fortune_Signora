"""business_event_engine: business_event

Revision ID: 0011
Revises: 0010
Create Date: 2026-07-29

One workspace-owned table with forced RLS and its full policy set in this
same revision.

**Business events are durable history, and the database enforces it.**
`signora_app` holds `SELECT`, `INSERT`, and `DELETE` but **not `UPDATE`** —
a phenomenon that extends or a conclusion that is corrected produces a new
event naming the one it replaces, never an edit. Future intelligence
modules are expected to reason over complete historical sequences, which
requires the sequence to exist.

`DELETE` is granted because business events are entirely *derived*:
dropping and rebuilding them from observations is the rollback for a bad
rule, and replaying under two taxonomy versions is how a threshold change
is evaluated before it ships.

**There is deliberately no priority, score, urgency, or rank column.** The
module answers "why is this business-relevant?" — how important the
account is, whether Sales should engage, and how likely a purchase is
belong to the Signal Engine and everything after it
(docs/architecture/24-business-event-engine.md).
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0011"
down_revision: str | None = "0010"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None

APP_ROLE = "signora_app"
TABLE = "business_event"


def upgrade() -> None:
    op.create_table(
        TABLE,
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("workspace_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("entity_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("type_key", sa.String(64), nullable=False),
        sa.Column("domain", sa.String(32), nullable=False),
        # When it happened in the customer's business. Timeline orders on
        # this, never on detected_at, or a backfill renders as a wall of
        # activity on its ingestion day.
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("window_start", sa.DateTime(timezone=True), nullable=False),
        sa.Column("window_end", sa.DateTime(timezone=True), nullable=False),
        sa.Column("detected_at", sa.DateTime(timezone=True), nullable=False),
        # The sentence a customer reads, rendered by the rule from `facts`,
        # so the words and the numbers cannot diverge.
        sa.Column("summary", sa.String(512), nullable=False),
        sa.Column("facts", postgresql.JSONB(), nullable=False),
        sa.Column(
            "evidence_observation_ids",
            postgresql.ARRAY(postgresql.UUID(as_uuid=True)),
            nullable=False,
        ),
        # Which providers' series independently reached this conclusion. A
        # count of agreement, never a weight — combining provider values
        # into a synthetic truth is what the pipeline refuses.
        sa.Column("corroborating_providers", postgresql.ARRAY(sa.String(64)), nullable=False),
        # The meaning in force when this was detected. Without it a replay
        # under a new version is incomparable to what came before.
        sa.Column("taxonomy_version", sa.Integer(), nullable=False),
        # The wire shape, versioned separately so tuning a threshold never
        # breaks a consumer contract.
        sa.Column("payload_version", sa.Integer(), nullable=False),
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
        sa.ForeignKeyConstraint(["supersedes"], ["business_event.id"], ondelete="SET NULL"),
        # Citation, never subsumption. An event with no evidence is an
        # assertion, and the chain back to raw provider payloads is what
        # separates intelligence from a guess.
        sa.CheckConstraint(
            "array_length(evidence_observation_ids, 1) >= 1",
            name="ck_business_event_cites_evidence",
        ),
        # Every conclusion is *according to* someone.
        sa.CheckConstraint(
            "array_length(corroborating_providers, 1) >= 1",
            name="ck_business_event_names_a_provider",
        ),
        sa.CheckConstraint("window_end >= window_start", name="ck_business_event_window_ordered"),
    )

    op.create_index("ix_business_event_workspace_id", TABLE, ["workspace_id"])
    op.create_index("ix_business_event_entity", TABLE, ["workspace_id", "entity_id", "occurred_at"])
    op.create_index("ix_business_event_timeline", TABLE, ["workspace_id", "occurred_at"])
    # Per-type detection rate is the operational metric that reveals a rule
    # which has silently stopped firing — "no events" is otherwise
    # indistinguishable from "nothing happened".
    op.create_index("ix_business_event_type", TABLE, ["workspace_id", "type_key"])
    op.create_index("ix_business_event_supersedes", TABLE, ["supersedes"])
    op.create_index(
        "ix_business_event_evidence",
        TABLE,
        ["evidence_observation_ids"],
        postgresql_using="gin",
    )

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

    # Durable history: SELECT, INSERT, DELETE — deliberately no UPDATE.
    op.execute(f"GRANT SELECT, INSERT, DELETE ON {TABLE} TO {APP_ROLE}")


def downgrade() -> None:
    op.execute(f"REVOKE ALL ON {TABLE} FROM {APP_ROLE}")
    op.drop_table(TABLE)
