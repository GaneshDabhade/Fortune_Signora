"""platform/event_bus: dispatch tables (processed_event, dead_letter_event)

Revision ID: 0004
Revises: 0003
Create Date: 2026-07-28

Adds the two tables the dispatch layer needs, plus relay bookkeeping columns
on ``outbox_event``.

``processed_event`` makes consumer idempotency a property of the event bus
rather than a discipline each of thirteen modules must implement correctly.
Delivery is at-least-once, so a handler can legitimately be invoked twice;
the dispatcher writes here inside the handler's own transaction, and a
primary-key conflict means "already done".

``dead_letter_event`` retains the full envelope rather than referencing
``outbox_event``, because the outbox may eventually be pruned while a dead
letter must remain independently replayable long afterwards.

Neither table is RLS-protected. Both are system infrastructure — never
queried on behalf of an end user, never exposed through an API, and swept
across every workspace by the relay, which RLS scoping would prevent. Same
reasoning as ``outbox_event`` (docs/architecture/11-tenancy.md).
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0004"
down_revision: str | None = "0003"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None

APP_ROLE = "signora_app"


def upgrade() -> None:
    op.create_table(
        "processed_event",
        sa.Column("consumer_name", sa.String(255), nullable=False),
        sa.Column("event_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=False),
        # Composite key, not event_id alone: several consumers subscribe to
        # the same event and each must process it exactly once independently.
        sa.PrimaryKeyConstraint("consumer_name", "event_id"),
    )

    op.create_table(
        "dead_letter_event",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("consumer_name", sa.String(255), nullable=False),
        sa.Column("event_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("event_type", sa.String(255), nullable=False),
        sa.Column("event_version", sa.Integer(), nullable=False),
        sa.Column("workspace_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("producer_module", sa.String(255), nullable=False),
        sa.Column("correlation_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("causation_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("payload", postgresql.JSONB(), nullable=False),
        sa.Column("attempts", sa.Integer(), nullable=False),
        sa.Column("failure_reason", sa.Text(), nullable=False),
        sa.Column("failed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("replayed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_dead_letter_event_consumer_name", "dead_letter_event", ["consumer_name"])
    op.create_index("ix_dead_letter_event_event_id", "dead_letter_event", ["event_id"])
    op.create_index("ix_dead_letter_event_event_type", "dead_letter_event", ["event_type"])
    op.create_index("ix_dead_letter_event_workspace_id", "dead_letter_event", ["workspace_id"])
    op.create_index("ix_dead_letter_event_correlation_id", "dead_letter_event", ["correlation_id"])
    # Operators overwhelmingly query "what is still dead", so the un-replayed
    # subset gets its own partial index rather than scanning history.
    op.create_index(
        "ix_dead_letter_event_unreplayed",
        "dead_letter_event",
        ["failed_at"],
        postgresql_where=sa.text("replayed_at IS NULL"),
    )

    op.add_column(
        "outbox_event",
        sa.Column("relay_attempts", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "outbox_event", sa.Column("relay_failed_at", sa.DateTime(timezone=True), nullable=True)
    )

    for table in ("processed_event", "dead_letter_event"):
        op.execute(f"GRANT SELECT, INSERT, UPDATE, DELETE ON {table} TO {APP_ROLE}")


def downgrade() -> None:
    op.execute(f"REVOKE ALL ON dead_letter_event FROM {APP_ROLE}")
    op.execute(f"REVOKE ALL ON processed_event FROM {APP_ROLE}")

    op.drop_column("outbox_event", "relay_failed_at")
    op.drop_column("outbox_event", "relay_attempts")

    op.drop_index("ix_dead_letter_event_unreplayed", table_name="dead_letter_event")
    op.drop_index("ix_dead_letter_event_correlation_id", table_name="dead_letter_event")
    op.drop_index("ix_dead_letter_event_workspace_id", table_name="dead_letter_event")
    op.drop_index("ix_dead_letter_event_event_type", table_name="dead_letter_event")
    op.drop_index("ix_dead_letter_event_event_id", table_name="dead_letter_event")
    op.drop_index("ix_dead_letter_event_consumer_name", table_name="dead_letter_event")
    op.drop_table("dead_letter_event")
    op.drop_table("processed_event")
