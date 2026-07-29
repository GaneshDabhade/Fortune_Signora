"""Integration tests for the migration runner.

The runner exists to guarantee two things ``alembic upgrade head`` does not:
that concurrent invocations cannot corrupt the schema, and that a runtime
identity cannot apply a migration. Both are asserted against a real
PostgreSQL, because both are properties of the database rather than of the
Python.
"""

import asyncio

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from apps.migrate.main import (
    MIGRATION_LOCK_ID,
    MigrationIdentityError,
    _run_with_lock,
    _verify_migration_identity,
    main,
)
from signora_platform.settings import Settings
from tests.conftest import DEFAULT_ADMIN_DATABASE_URL, DEFAULT_APP_DATABASE_URL

pytestmark = pytest.mark.integration


def _settings(database_url: str) -> Settings:
    return Settings(
        environment="test",
        database_url=database_url,
        jwt_public_key="placeholder",
        jwt_issuer="https://auth.signora.test",
        jwt_audience="signora-api-test",
    )


class TestIdentityEnforcement:
    async def test_accepts_the_migration_identity(self) -> None:
        role = await _verify_migration_identity(_settings(DEFAULT_ADMIN_DATABASE_URL))

        assert role == "signora"

    async def test_refuses_the_application_identity(self) -> None:
        """A task definition that hands the runner the application
        credential must fail at the migration step, not silently grant the
        application role the ability to alter schema."""
        with pytest.raises(MigrationIdentityError) as exc_info:
            await _verify_migration_identity(_settings(DEFAULT_APP_DATABASE_URL))

        assert "signora_app" in str(exc_info.value)

    async def test_refusal_names_the_fix(self) -> None:
        """The message is the whole value of failing here rather than on a
        permission error three migrations in."""
        with pytest.raises(MigrationIdentityError) as exc_info:
            await _verify_migration_identity(_settings(DEFAULT_APP_DATABASE_URL))

        message = str(exc_info.value)
        assert "SIGNORA_DATABASE_URL" in message
        assert "migration identity" in message

    def test_exits_non_zero_rather_than_raising(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """A configuration mistake should produce an actionable log line and
        a failed release step, not a traceback that buries the reason."""
        monkeypatch.setenv("SIGNORA_DATABASE_URL", DEFAULT_APP_DATABASE_URL)
        monkeypatch.setenv("SIGNORA_JWT_PUBLIC_KEY", "placeholder")
        monkeypatch.setenv("SIGNORA_JWT_ISSUER", "https://auth.signora.test")
        monkeypatch.setenv("SIGNORA_JWT_AUDIENCE", "signora-api-test")
        from signora_platform.settings import get_settings

        get_settings.cache_clear()

        try:
            assert main() == 2
        finally:
            get_settings.cache_clear()


class TestConcurrencySafety:
    async def test_a_second_runner_waits_rather_than_racing(
        self, admin_engine: AsyncEngine
    ) -> None:
        """Deployments start replicas in parallel. Two Alembic processes on
        one database produce partially applied migrations and a version
        table that agrees with neither.

        The test holds the lock and asserts the runner *blocks* — rather
        than starting the runner and probing, which races: against an
        already-migrated database the upgrade is a near-instant no-op and
        the probe arrives after the lock is released. Holding it here makes
        the timing deterministic.
        """
        settings = _settings(DEFAULT_ADMIN_DATABASE_URL)

        async with admin_engine.connect() as holder:
            acquired = (
                await holder.execute(
                    text("SELECT pg_try_advisory_lock(:lock_id)"),
                    {"lock_id": MIGRATION_LOCK_ID},
                )
            ).scalar_one()
            assert acquired, "test could not take the lock it needs to hold"

            runner = asyncio.create_task(_run_with_lock(settings))
            await asyncio.sleep(1.0)

            assert not runner.done(), (
                "the runner proceeded while another process held the migration "
                "lock — concurrent deployments would race on the schema"
            )

            await holder.execute(
                text("SELECT pg_advisory_unlock(:lock_id)"), {"lock_id": MIGRATION_LOCK_ID}
            )

        # Once the lock is free the runner must finish on its own.
        await asyncio.wait_for(runner, timeout=60)

    async def test_the_lock_is_released_afterwards(
        self, admin_session_factory: async_sessionmaker[AsyncSession]
    ) -> None:
        """A lock leaked on a pooled connection would block every subsequent
        deployment, with no error to explain why."""
        await _run_with_lock(_settings(DEFAULT_ADMIN_DATABASE_URL))

        async with admin_session_factory() as session, session.begin():
            acquired = (
                await session.execute(
                    text("SELECT pg_try_advisory_lock(:lock_id)"), {"lock_id": MIGRATION_LOCK_ID}
                )
            ).scalar_one()
            if acquired:
                await session.execute(
                    text("SELECT pg_advisory_unlock(:lock_id)"), {"lock_id": MIGRATION_LOCK_ID}
                )

        assert acquired is True

    async def test_the_schema_is_at_head_afterwards(
        self, admin_session_factory: async_sessionmaker[AsyncSession]
    ) -> None:
        await _run_with_lock(_settings(DEFAULT_ADMIN_DATABASE_URL))

        async with admin_session_factory() as session, session.begin():
            version = (
                await session.execute(text("SELECT version_num FROM alembic_version"))
            ).scalar_one()

        assert version == "0010"
