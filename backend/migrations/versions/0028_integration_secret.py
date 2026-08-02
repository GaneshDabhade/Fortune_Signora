"""integrations: integration_secret

Revision ID: 0028
Revises: 0027
Create Date: 2026-08-02

**Where a customer's credential actually lives, until a vault exists.**
`13-integrations.md` puts per-workspace grants in AWS Secrets Manager and
`M14.5` provisions it three milestones from here, so the material lives in its
own table behind the same `SecretStore` port the vault will implement.

**Encrypted at rest, not merely separated.** A token in a plain column is a
token in every backup, every replica and every engineer's `psql` session. The
key is injected as configuration and never defaulted.

**Its own table rather than a column on `integration_grant`.** The grant is
lifecycle — read on every connections screen, listed and counted. Material is
read only when a call is about to be made. Separating them keeps ciphertext out
of the common query, and makes the eventual move to a vault a dropped table
rather than a column migrated out of a hot aggregate.

**No `UPDATE` grant.** Rotating a credential writes a new `secret_ref` and
leaves the old one to be purged; editing material in place would make the
previous value unrecoverable at exactly the moment a rotation is being
diagnosed.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0028"
down_revision: str | None = "0027"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None

TABLE = "integration_secret"
APP_ROLE = "signora_app"


def upgrade() -> None:
    op.create_table(
        TABLE,
        sa.Column("secret_ref", sa.String(255), primary_key=True),
        sa.Column("workspace_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "connected_account_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("connected_account.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("kind", sa.String(32), nullable=False),
        sa.Column("ciphertext", postgresql.BYTEA, nullable=False),
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
    op.create_index(
        "ix_integration_secret_account", TABLE, ["workspace_id", "connected_account_id"]
    )

    op.execute(f"ALTER TABLE {TABLE} ENABLE ROW LEVEL SECURITY")
    op.execute(f"ALTER TABLE {TABLE} FORCE ROW LEVEL SECURITY")
    scope = "workspace_id = NULLIF(current_setting('app.workspace_id', true), '')::uuid"
    op.execute(f"CREATE POLICY {TABLE}_select ON {TABLE} FOR SELECT USING ({scope})")
    op.execute(f"CREATE POLICY {TABLE}_insert ON {TABLE} FOR INSERT WITH CHECK ({scope})")
    op.execute(f"CREATE POLICY {TABLE}_delete ON {TABLE} FOR DELETE USING ({scope})")
    # No UPDATE: a rotation is a new ref, never an edit.
    op.execute(f"GRANT SELECT, INSERT, DELETE ON {TABLE} TO {APP_ROLE}")


def downgrade() -> None:
    op.execute(f"REVOKE ALL ON {TABLE} FROM {APP_ROLE}")
    op.drop_index("ix_integration_secret_account", table_name=TABLE)
    op.drop_table(TABLE)
