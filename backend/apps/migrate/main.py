"""Migration runner — the only process permitted to change schema.

Run as a discrete release step, never from inside a running service:

    python -m apps.migrate.main

Two properties this entry point exists to guarantee, neither of which
``alembic upgrade head`` provides on its own.

**It is safe to run concurrently.** Deployments start replicas in parallel,
and a rollback may start a new task while an old one is still shutting
down. Two Alembic processes racing on the same database produce partially
applied migrations and a version table that agrees with neither. A
PostgreSQL advisory lock serialises them: the first proceeds, the rest wait
and then find nothing to do.

**It refuses to run under a runtime identity.** Migrations execute only
under the migration identity (CLAUDE.md §8). Enforcing that here rather
than trusting the deployment configuration means a mistake in a task
definition fails loudly at the migration step instead of silently granting
the application role the ability to alter schema.
"""

import asyncio
import os
import sys
from typing import Final

from alembic import command
from alembic.config import Config
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from signora_platform.observability import configure_logging, get_logger
from signora_platform.settings import Settings, get_settings

logger = get_logger(__name__)

# Arbitrary but fixed: any constant works provided every migration runner
# uses the same one. Derived from nothing, so it cannot collide with a lock
# taken by application code that happened to pick a "meaningful" number.
MIGRATION_LOCK_ID: Final = 8_274_591_003_112

# Roles that must never apply a migration. The check is by role name rather
# than by privilege because a role could hold DDL privileges transiently;
# the intent is that *these identities* are not the migration identity,
# whatever they are currently permitted to do.
RUNTIME_ROLES: Final = frozenset({"signora_app", "signora_auth", "signora_relay"})


class MigrationIdentityError(RuntimeError):
    """The runner is connected as a role that must not apply migrations."""


async def _verify_migration_identity(settings: Settings) -> str:
    engine = create_async_engine(str(settings.database_url), poolclass=None)
    try:
        async with engine.connect() as conn:
            role = str((await conn.execute(text("SELECT current_user"))).scalar_one())
    finally:
        await engine.dispose()

    if role in RUNTIME_ROLES:
        raise MigrationIdentityError(
            f"Refusing to migrate as '{role}'. Schema changes execute only under the "
            "migration identity; runtime services must never hold the ability to "
            "apply one (CLAUDE.md §8). Set SIGNORA_DATABASE_URL to the migration "
            "credential for this step."
        )
    return role


async def _run_with_lock(settings: Settings) -> None:
    """Hold an advisory lock for the duration of the upgrade.

    Session-scoped rather than transaction-scoped: Alembic runs each
    migration in its own transaction, so a transaction-scoped lock would be
    released between them and admit a second runner mid-sequence.
    """
    engine = create_async_engine(str(settings.database_url))
    try:
        async with engine.connect() as conn:
            acquired = (
                await conn.execute(
                    text("SELECT pg_try_advisory_lock(:lock_id)"), {"lock_id": MIGRATION_LOCK_ID}
                )
            ).scalar_one()

            if not acquired:
                logger.info(
                    "waiting for concurrent migration runner to finish",
                    extra={"lock_id": MIGRATION_LOCK_ID},
                )
                await conn.execute(
                    text("SELECT pg_advisory_lock(:lock_id)"), {"lock_id": MIGRATION_LOCK_ID}
                )

            try:
                # Alembic is synchronous and opens its own connection. That
                # is fine and deliberate: the lock is held on *this*
                # connection for the whole upgrade, which is what serialises
                # concurrent runners.
                await asyncio.to_thread(_upgrade_to_head)
            finally:
                await conn.execute(
                    text("SELECT pg_advisory_unlock(:lock_id)"), {"lock_id": MIGRATION_LOCK_ID}
                )
    finally:
        await engine.dispose()


def _upgrade_to_head() -> None:
    config = Config("alembic.ini")
    command.upgrade(config, "head")


async def run() -> None:
    settings = get_settings()
    configure_logging(level=settings.log_level)
    # Tells migrations/env.py not to replace the logging configuration just
    # established. Without it Alembic's fileConfig takes over the root
    # logger at WARNING and the completion line below never prints.
    os.environ["SIGNORA_LOGGING_CONFIGURED"] = "1"

    role = await _verify_migration_identity(settings)
    logger.info("applying migrations", extra={"role": role})

    await _run_with_lock(settings)

    logger.info("migrations applied", extra={"role": role})


def main() -> int:
    try:
        asyncio.run(run())
    except MigrationIdentityError as exc:
        # Logged as an error and returned as a non-zero exit rather than a
        # traceback: this is a configuration mistake with a specific fix,
        # and a stack trace would bury it.
        logger.error("migration refused", extra={"reason": str(exc)})
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
