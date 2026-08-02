"""timeline: timeline_entry

Revision ID: 0026
Revises: 0025
Create Date: 2026-08-02

**The pipeline's account of itself.** Every module upstream has already made its
judgement; this table restates those facts in time order and adds no opinion.

**Derived intelligence, not customer configuration.** Every row is projected
from an event whose source of truth is another module's table, so losing this
table loses no fact — it loses an index over facts that still exist. That is the
opposite of `target_account_list` (migration `0025`), which holds the customer's
own instructions and can be regenerated from nothing.

Immutable on the established terms: `signora_app` holds `SELECT`, `INSERT` and
`DELETE` but **not `UPDATE`**. A correction to a projected entry is a new entry.
`DELETE` is granted deliberately — erasability is a property of the tenancy
model, not a statement about what a row means.

**`event_id` is unique, and that is the idempotency guarantee stated where it
can fail loudly.** The primary key is derived from `event_id`, so a redelivered
event already conflicts; the constraint says the same thing about the value the
guarantee is actually about, so a future change to the id scheme cannot weaken
it silently.

**No `created_by`/`updated_by`.** A projection row has no actor — nobody did
this. Filling an audit column with a system UUID would invent an author.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0026"
down_revision: str | None = "0025"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None

TABLE = "timeline_entry"
APP_ROLE = "signora_app"


def upgrade() -> None:
    op.create_table(
        TABLE,
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("workspace_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "entity_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("entity.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("kind", sa.String(32), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("event_id", postgresql.UUID(as_uuid=True), nullable=False, unique=True),
        sa.Column("source_module", sa.String(64), nullable=False),
        sa.Column("source_ref", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "detail",
            postgresql.JSONB,
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )

    # The one query the module exists to serve, made total by `id`: two entries
    # can share `occurred_at`, and a cursor over a non-total order drops or
    # repeats rows at a page boundary.
    op.create_index(
        "ix_timeline_entry_feed",
        TABLE,
        ["workspace_id", "entity_id", "occurred_at", "id"],
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
          WITH CHECK (
            workspace_id = NULLIF(current_setting('app.workspace_id', true), '')::uuid
          )
        """
    )
    op.execute(
        f"""
        CREATE POLICY {TABLE}_delete ON {TABLE} FOR DELETE
          USING (workspace_id = NULLIF(current_setting('app.workspace_id', true), '')::uuid)
        """
    )
    op.execute(f"GRANT SELECT, INSERT, DELETE ON {TABLE} TO {APP_ROLE}")


def downgrade() -> None:
    op.execute(f"REVOKE ALL ON {TABLE} FROM {APP_ROLE}")
    op.drop_index("ix_timeline_entry_feed", table_name=TABLE)
    op.drop_table(TABLE)
