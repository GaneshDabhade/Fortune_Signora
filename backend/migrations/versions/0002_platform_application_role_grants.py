"""platform: least-privilege application role and grants

Revision ID: 0002
Revises: 0001
Create Date: 2026-07-28

PostgreSQL superusers (and any role holding BYPASSRLS) ignore Row-Level
Security entirely — even on tables declared FORCE ROW LEVEL SECURITY. An
application that connects as a superuser therefore has *no* tenant
isolation, regardless of how carefully its policies are written.

This migration creates the non-superuser role the application connects as,
and grants it exactly the table privileges it needs and nothing more
(docs/architecture/10-security.md, least privilege). The role is created
NOLOGIN with no password here: credentials are issued by infrastructure
provisioning (AWS Secrets Manager per ADR-0022) or, for local development,
by infra/postgres-init/01-app-role.sql — a migration must never contain
credentials.

Adding a new table to any module requires granting that table to
signora_app in the same migration that creates it, or the application will
fail closed with a permission error.
"""

from collections.abc import Sequence

from alembic import op

revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None

APP_ROLE = "signora_app"

TENANT_TABLES = ("workspace", "membership")
INFRASTRUCTURE_TABLES = ("outbox_event",)


def upgrade() -> None:
    op.execute(
        f"""
        DO $$
        BEGIN
          IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = '{APP_ROLE}') THEN
            CREATE ROLE {APP_ROLE} NOLOGIN;
          END IF;
        END
        $$
        """
    )

    # Explicitly assert the role can never bypass RLS, even if a future
    # provisioning change grants it elevated attributes by accident.
    op.execute(f"ALTER ROLE {APP_ROLE} NOBYPASSRLS")

    op.execute(f"GRANT USAGE ON SCHEMA public TO {APP_ROLE}")

    for table in (*TENANT_TABLES, *INFRASTRUCTURE_TABLES):
        op.execute(f"GRANT SELECT, INSERT, UPDATE, DELETE ON {table} TO {APP_ROLE}")

    # Alembic's own bookkeeping table: read-only for the application role.
    # Schema changes are applied by a separate, privileged migration
    # identity, never by the running application.
    op.execute(f"GRANT SELECT ON alembic_version TO {APP_ROLE}")


def downgrade() -> None:
    for table in (*TENANT_TABLES, *INFRASTRUCTURE_TABLES):
        op.execute(f"REVOKE ALL ON {table} FROM {APP_ROLE}")
    op.execute(f"REVOKE SELECT ON alembic_version FROM {APP_ROLE}")
    op.execute(f"REVOKE USAGE ON SCHEMA public FROM {APP_ROLE}")
    # The role itself is deliberately not dropped: it may own grants in
    # other databases or be referenced by provisioning state.
