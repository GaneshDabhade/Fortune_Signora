"""signal_engine: signal, signal_profile

Revision ID: 0012
Revises: 0011
Create Date: 2026-07-29

Two workspace-owned tables with forced RLS and their full policy sets in
this same revision — and they are **not the same kind of data**.

`signal` is derived intelligence: it can be dropped and rebuilt from
business events, which is the rollback for a bad rule and the mechanism
behind current replay.

**`signal_profile` is customer-authored configuration.** It is the first
thing in the platform that cannot be regenerated from anything — a
statement a customer makes about their own commercial position — and it
needs the operational rigour that implies. A rebuild that discarded it
would destroy customer data, not derived data.

Both are immutable: `signora_app` holds `SELECT`, `INSERT`, and `DELETE`
but **not `UPDATE`**. For signals, a hypothesis that gains evidence becomes
a new signal naming the one it replaces. For profiles, an edit in place
would make every historical signal unexplainable — *"why was I told
this?"* would have no answer, because the reason changed underneath it.

**There is deliberately no score, priority, likelihood, or rank column on
`signal`.** The module answers "why might this matter to this customer?";
how much it matters is the Buying Score Engine's question
(docs/architecture/25-signal-engine.md).
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0012"
down_revision: str | None = "0011"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None

APP_ROLE = "signora_app"
TABLES = ("signal_profile", "signal")


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
        "signal_profile",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        # Monotonic per workspace. A signal records this, and without it a
        # historical signal cannot be explained.
        sa.Column("version", sa.Integer(), nullable=False),
        # The entries themselves: which types are relevant, how centrally,
        # and any tuning within catalog-declared semantics. JSONB because a
        # profile is read whole and never queried field-by-field.
        sa.Column("entries", postgresql.JSONB(), nullable=False),
        sa.Column("supersedes", postgresql.UUID(as_uuid=True), nullable=True),
        *_audit_columns(),
        sa.ForeignKeyConstraint(["supersedes"], ["signal_profile.id"], ondelete="SET NULL"),
        sa.UniqueConstraint("workspace_id", "version", name="uq_signal_profile_version"),
        sa.CheckConstraint("version > 0", name="ck_signal_profile_version_positive"),
    )
    op.create_index("ix_signal_profile_workspace_id", "signal_profile", ["workspace_id"])
    # One *current* profile per workspace. The constraint is what stops two
    # concurrent configuration writes leaving a workspace with two live
    # interpretations and no way to say which applied.
    op.create_index(
        "uq_signal_profile_current",
        "signal_profile",
        ["workspace_id"],
        unique=True,
        postgresql_where=sa.text("supersedes IS NULL"),
    )

    op.create_table(
        "signal",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("entity_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("signal_type", sa.String(64), nullable=False),
        # A category, never a number. The Buying Score Engine maps these to
        # weights in its own configuration, which is where propensity lives.
        sa.Column("relevance", sa.String(16), nullable=False),
        # When the underlying business events happened. Timeline orders on
        # this, never on generated_at.
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("window_start", sa.DateTime(timezone=True), nullable=False),
        sa.Column("window_end", sa.DateTime(timezone=True), nullable=False),
        sa.Column("generated_at", sa.DateTime(timezone=True), nullable=False),
        # A hypothesis has a shelf life. A derived date, not a weight.
        sa.Column("relevant_until", sa.DateTime(timezone=True), nullable=False),
        # Two halves: why this matters here, and what it rests on.
        sa.Column("rationale", sa.String(1024), nullable=False),
        sa.Column(
            "contributing_event_ids",
            postgresql.ARRAY(postgresql.UUID(as_uuid=True)),
            nullable=False,
        ),
        sa.Column("contributing_event_types", postgresql.ARRAY(sa.String(64)), nullable=False),
        # A composite enriches; it never replaces. Constituents are stored
        # in their own right and named here.
        sa.Column(
            "constituent_signal_ids",
            postgresql.ARRAY(postgresql.UUID(as_uuid=True)),
            nullable=False,
            server_default="{}",
        ),
        sa.Column("catalog_version", sa.Integer(), nullable=False),
        sa.Column("profile_version", sa.Integer(), nullable=False),
        sa.Column("payload_version", sa.Integer(), nullable=False),
        sa.Column("supersedes", postgresql.UUID(as_uuid=True), nullable=True),
        *_audit_columns(),
        sa.ForeignKeyConstraint(["entity_id"], ["entity.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["supersedes"], ["signal.id"], ondelete="SET NULL"),
        # A hypothesis with no evidence is an opinion. The chain back to raw
        # provider payloads is what makes it otherwise.
        sa.CheckConstraint(
            "array_length(contributing_event_ids, 1) >= 1",
            name="ck_signal_cites_business_events",
        ),
        sa.CheckConstraint(
            "array_length(contributing_event_types, 1) >= 1",
            name="ck_signal_names_event_types",
        ),
        # `IGNORED` means the hypothesis is not held here at all — a signal
        # carrying it would be one the workspace explicitly does not want.
        sa.CheckConstraint("relevance <> 'ignored'", name="ck_signal_relevance_is_held"),
        sa.CheckConstraint("window_end >= window_start", name="ck_signal_window_ordered"),
        sa.CheckConstraint("relevant_until >= occurred_at", name="ck_signal_shelf_life_ordered"),
    )
    op.create_index("ix_signal_workspace_id", "signal", ["workspace_id"])
    op.create_index("ix_signal_entity", "signal", ["workspace_id", "entity_id", "occurred_at"])
    op.create_index("ix_signal_timeline", "signal", ["workspace_id", "occurred_at"])
    op.create_index("ix_signal_type", "signal", ["workspace_id", "signal_type"])
    # The live set: which hypotheses are still current for this workspace.
    op.create_index("ix_signal_relevant_until", "signal", ["workspace_id", "relevant_until"])
    op.create_index("ix_signal_supersedes", "signal", ["supersedes"])
    op.create_index(
        "ix_signal_contributing_events",
        "signal",
        ["contributing_event_ids"],
        postgresql_using="gin",
    )

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
    op.drop_table("signal")
    op.drop_table("signal_profile")
