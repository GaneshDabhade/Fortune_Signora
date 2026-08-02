"""integrations: connected_account, integration_grant

Revision ID: 0027
Revises: 0026
Create Date: 2026-08-02

**The customer's own systems, as opposed to Signora's suppliers.** That
distinction is ratified in `04-modules.md` and is why these tables are not
Provider Platform's: a connection exists before synchronization, while paused,
after revocation, and even if synchronization never happens.

**Mutable, unlike most tables here, and deliberately.** A connection is a live
relationship rather than a record of something that was true, so `UPDATE` is
granted — versioning it would make *"is Salesforce connected?"* a query over
history. What happened *to* a connection belongs to the event log; what it *is*
belongs here.

**`integration_grant` holds no secret material.** `secret_ref` points at a
`SecretStore`; the token never enters a table that is backed up, replicated and
readable by anybody with database access. The vault
([ADR-0022](../../docs/architecture/adr/0022-devops-infrastructure-and-deployment-topology.md))
arrives at M14.5 behind that port and changes nothing here.

**`integration` is a `String`, not an enum.** A closed vocabulary cannot admit a
partner-published or customer-written connector, and that is the first
assumption an ecosystem breaks.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0027"
down_revision: str | None = "0026"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None

ACCOUNTS = "connected_account"
GRANTS = "integration_grant"
APP_ROLE = "signora_app"


def _rls(table: str, *, updatable: bool) -> None:
    op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
    op.execute(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY")
    scope = "workspace_id = NULLIF(current_setting('app.workspace_id', true), '')::uuid"
    op.execute(f"CREATE POLICY {table}_select ON {table} FOR SELECT USING ({scope})")
    op.execute(f"CREATE POLICY {table}_insert ON {table} FOR INSERT WITH CHECK ({scope})")
    op.execute(f"CREATE POLICY {table}_delete ON {table} FOR DELETE USING ({scope})")
    grants = "SELECT, INSERT, DELETE"
    if updatable:
        op.execute(
            f"CREATE POLICY {table}_update ON {table} FOR UPDATE "
            f"USING ({scope}) WITH CHECK ({scope})"
        )
        grants = "SELECT, INSERT, UPDATE, DELETE"
    op.execute(f"GRANT {grants} ON {table} TO {APP_ROLE}")


def upgrade() -> None:
    op.create_table(
        ACCOUNTS,
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("workspace_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("integration", sa.String(64), nullable=False),
        sa.Column("external_account_id", sa.String(255), nullable=False),
        sa.Column("endpoint", sa.String(512), nullable=True),
        sa.Column("label", sa.String(128), nullable=False),
        sa.Column("state", sa.String(32), nullable=False),
        sa.Column("connected_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True), nullable=False),
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
        sa.UniqueConstraint(
            "workspace_id",
            "integration",
            "external_account_id",
            name="uq_connected_account_identity",
        ),
    )
    op.create_index(
        "ix_connected_account_workspace", ACCOUNTS, ["workspace_id", "integration"]
    )

    op.create_table(
        GRANTS,
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("workspace_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "connected_account_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey(f"{ACCOUNTS}.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("secret_ref", sa.String(255), nullable=False),
        sa.Column("scopes", postgresql.ARRAY(sa.String), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("refreshable", sa.Boolean, nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True), nullable=False),
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
        "ix_integration_grant_account",
        GRANTS,
        ["workspace_id", "connected_account_id", "revoked_at"],
    )

    # Both updatable: a connection's state and a grant's revocation are facts
    # about *now*, and the history of how they got there is the event log's.
    _rls(ACCOUNTS, updatable=True)
    _rls(GRANTS, updatable=True)


def downgrade() -> None:
    op.execute(f"REVOKE ALL ON {GRANTS} FROM {APP_ROLE}")
    op.execute(f"REVOKE ALL ON {ACCOUNTS} FROM {APP_ROLE}")
    op.drop_index("ix_integration_grant_account", table_name=GRANTS)
    op.drop_table(GRANTS)
    op.drop_index("ix_connected_account_workspace", table_name=ACCOUNTS)
    op.drop_table(ACCOUNTS)
