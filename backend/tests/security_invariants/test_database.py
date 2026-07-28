"""Invariants: each tier holds a credential that can do its job and nothing
more.

Three roles, three jobs (docs/architecture/11-tenancy.md):

* the **owner** migrates and is never used by a running service;
* **signora_app** runs the API and workers, and cannot alter schema or read
  authentication data;
* **signora_auth** runs Better Auth, and cannot read application data.

These are asserted as *relationships*, not one role at a time. Both roles
were individually correct in M1.2 while the frontend still connected as the
owner, which made the revoke inert — the isolation existed in the migration
and nowhere else.
"""

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

pytestmark = pytest.mark.integration

APP_ROLE = "signora_app"
AUTH_ROLE = "signora_auth"
AUTH_SCHEMA = "auth"


class TestRuntimeRoleCannotMigrate:
    """Schema changes execute only under the migration identity. A runtime
    service that can alter schema turns any application-code vulnerability
    into a database-structure vulnerability."""

    async def test_the_runtime_role_cannot_create_a_table(self, app_engine: AsyncEngine) -> None:
        async with app_engine.connect() as conn, conn.begin():
            with pytest.raises(Exception) as exc_info:
                await conn.execute(text("CREATE TABLE invariant_probe (id int)"))

        assert "permission denied" in str(exc_info.value).lower()

    async def test_the_runtime_role_cannot_alter_an_existing_table(
        self, app_engine: AsyncEngine
    ) -> None:
        async with app_engine.connect() as conn, conn.begin():
            with pytest.raises(Exception) as exc_info:
                await conn.execute(text("ALTER TABLE workspace ADD COLUMN probe int"))

        assert "must be owner" in str(exc_info.value).lower()

    async def test_the_runtime_role_cannot_drop_a_table(self, app_engine: AsyncEngine) -> None:
        async with app_engine.connect() as conn, conn.begin():
            with pytest.raises(Exception) as exc_info:
                await conn.execute(text("DROP TABLE membership"))

        assert "must be owner" in str(exc_info.value).lower()

    async def test_the_runtime_role_cannot_rewrite_migration_history(
        self, app_engine: AsyncEngine
    ) -> None:
        """It may read ``alembic_version`` — the application reports the
        schema version it is running against — but a service able to write
        it could make a half-migrated database look fully migrated."""
        async with app_engine.connect() as conn, conn.begin():
            await conn.execute(text("SELECT version_num FROM alembic_version"))

        async with app_engine.connect() as conn, conn.begin():
            with pytest.raises(Exception) as exc_info:
                await conn.execute(text("UPDATE alembic_version SET version_num = '0000'"))

        assert "permission denied" in str(exc_info.value).lower()

    async def test_the_runtime_role_cannot_escalate_its_own_privileges(
        self, app_engine: AsyncEngine
    ) -> None:
        """The escape hatch that would render every other test here moot."""
        async with app_engine.connect() as conn, conn.begin():
            with pytest.raises(Exception) as exc_info:
                await conn.execute(text(f"ALTER ROLE {APP_ROLE} BYPASSRLS"))

        assert "permission denied" in str(exc_info.value).lower()


class TestTierCredentialsAreDisjoint:
    async def test_the_runtime_role_cannot_reach_the_auth_schema(
        self, admin_session_factory: async_sessionmaker[AsyncSession]
    ) -> None:
        """Authentication data is unreachable from the API tier by
        permission, not merely by the absence of code that reads it."""
        async with admin_session_factory() as session, session.begin():
            can_use = (
                await session.execute(
                    text(f"SELECT has_schema_privilege('{APP_ROLE}', '{AUTH_SCHEMA}', 'USAGE')")
                )
            ).scalar_one()

        assert can_use is False

    async def test_the_auth_role_cannot_reach_application_tables(
        self, admin_session_factory: async_sessionmaker[AsyncSession]
    ) -> None:
        """The converse: a compromise of the frontend tier must not yield
        workspace data.

        ``pg_class`` rather than ``information_schema.tables`` — the latter
        is filtered to objects the *querying* role can see, which is not the
        question being asked.
        """
        async with admin_session_factory() as session, session.begin():
            reachable = (
                (
                    await session.execute(
                        text(
                            f"""
                            SELECT c.relname FROM pg_class c
                            JOIN pg_namespace n ON n.oid = c.relnamespace
                            WHERE n.nspname = 'public' AND c.relkind = 'r'
                              AND has_table_privilege('{AUTH_ROLE}', c.oid, 'SELECT')
                            ORDER BY c.relname
                            """
                        )
                    )
                )
                .scalars()
                .all()
            )

        assert list(reachable) == [], f"{AUTH_ROLE} can read application tables: {reachable}"

    async def test_neither_runtime_role_can_bypass_row_level_security(
        self, admin_session_factory: async_sessionmaker[AsyncSession]
    ) -> None:
        """A superuser or ``BYPASSRLS`` role ignores every policy in this
        codebase, *including* on tables declared ``FORCE ROW LEVEL
        SECURITY``. If this fails, every isolation assertion in the suite
        passes vacuously."""
        async with admin_session_factory() as session, session.begin():
            roles = (
                await session.execute(
                    text(
                        "SELECT rolname, rolsuper, rolbypassrls FROM pg_roles "
                        f"WHERE rolname IN ('{APP_ROLE}', '{AUTH_ROLE}') ORDER BY rolname"
                    )
                )
            ).all()

        assert len(roles) == 2, f"both tier roles must exist; found {roles}"
        for name, is_superuser, bypasses_rls in roles:
            assert not is_superuser, f"{name} is a superuser and ignores RLS"
            assert not bypasses_rls, f"{name} holds BYPASSRLS and ignores RLS"

    async def test_the_running_application_is_not_connected_as_the_owner(
        self, app_role_name: str
    ) -> None:
        """The M1.2 defect, stated directly: a tier connecting as the owner
        makes every grant and revoke above decorative."""
        assert app_role_name == APP_ROLE
