"""auth: dedicated schema for Better Auth tables

Revision ID: 0005
Revises: 0004
Create Date: 2026-07-28

Creates the ``auth`` schema Better Auth owns, per the approved M1.2
decision: authentication data stays isolated while operational complexity
stays low (one PostgreSQL instance to run, back up, and monitor).

**This migration creates the schema and nothing inside it.** Better Auth
owns its own table definitions and migrates them itself; Alembic managing
those tables would mean two migration systems with overlapping authority
over the same objects, and an upgrade to Better Auth would silently
conflict with our migration history.

The application role is deliberately granted nothing here. The Python tier
verifies JWTs and never reads authentication data (ADR-0026); a grant would
make the boundary a matter of discipline rather than of permissions.
"""

from collections.abc import Sequence

from alembic import op

revision: str = "0005"
down_revision: str | None = "0004"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None

AUTH_SCHEMA = "auth"
AUTH_ROLE = "signora_auth"


def upgrade() -> None:
    op.execute(f"CREATE SCHEMA IF NOT EXISTS {AUTH_SCHEMA}")

    # A role distinct from signora_app: the auth tier and the API tier have
    # disjoint data needs, and a shared role would let a compromise of one
    # read the other's tables.
    op.execute(
        f"""
        DO $$
        BEGIN
          IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = '{AUTH_ROLE}') THEN
            CREATE ROLE {AUTH_ROLE} NOLOGIN;
          END IF;
        END
        $$
        """
    )
    op.execute(f"ALTER ROLE {AUTH_ROLE} NOBYPASSRLS")
    op.execute(f"GRANT USAGE, CREATE ON SCHEMA {AUTH_SCHEMA} TO {AUTH_ROLE}")
    op.execute(
        f"ALTER DEFAULT PRIVILEGES IN SCHEMA {AUTH_SCHEMA} "
        f"GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO {AUTH_ROLE}"
    )

    # Explicitly deny the application role any access to authentication data.
    op.execute(f"REVOKE ALL ON SCHEMA {AUTH_SCHEMA} FROM signora_app")


def downgrade() -> None:
    op.execute(f"DROP SCHEMA IF EXISTS {AUTH_SCHEMA} CASCADE")
    # The role is not dropped: it may own objects in other databases, and
    # dropping a role that still owns anything fails confusingly.
