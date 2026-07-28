"""signora_platform/event_bus: outbox_event table

Revision ID: 0000
Revises:
Create Date: 2026-07-28

Owned by signora_platform/event_bus, not any single module — the transactional
outbox is shared infrastructure every module's EventPublisher writes to.
Deliberately has no Row-Level Security: it is never queried on behalf of an
end user, and the future relay process must be able to sweep events across
every workspace (docs/architecture/06-events.md).
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0000"
down_revision: str | None = None
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "outbox_event",
        sa.Column("event_id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("event_type", sa.String(255), nullable=False),
        sa.Column("event_version", sa.Integer(), nullable=False),
        sa.Column("workspace_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("producer_module", sa.String(255), nullable=False),
        sa.Column("correlation_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("causation_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("payload", postgresql.JSONB(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("relayed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_outbox_event_event_type", "outbox_event", ["event_type"])
    op.create_index("ix_outbox_event_workspace_id", "outbox_event", ["workspace_id"])
    op.create_index("ix_outbox_event_correlation_id", "outbox_event", ["correlation_id"])
    # The relay's core query will be "pending events, oldest first" — a
    # partial index on relayed_at IS NULL keeps that cheap regardless of how
    # large the (append-only, rarely-pruned) table grows.
    op.create_index(
        "ix_outbox_event_pending",
        "outbox_event",
        ["created_at"],
        postgresql_where=sa.text("relayed_at IS NULL"),
    )


def downgrade() -> None:
    op.drop_index("ix_outbox_event_pending", table_name="outbox_event")
    op.drop_index("ix_outbox_event_correlation_id", table_name="outbox_event")
    op.drop_index("ix_outbox_event_workspace_id", table_name="outbox_event")
    op.drop_index("ix_outbox_event_event_type", table_name="outbox_event")
    op.drop_table("outbox_event")
