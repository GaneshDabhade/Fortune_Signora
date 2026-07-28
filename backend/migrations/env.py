"""Alembic environment.

Runs migrations against the async engine, using the exact same
``signora_signora_platform.settings.get_settings()`` configuration the application uses —
there is no separate migration-specific database configuration to drift out
of sync with the app.

Every module's ORM models must be imported here (even though nothing else
in this file references them by name) so their tables are registered on
``Base.metadata`` before autogenerate compares it against the live schema.
"""

import asyncio
import os
from logging.config import fileConfig

from alembic import context
from sqlalchemy import Connection, pool
from sqlalchemy.ext.asyncio import async_engine_from_config

# ruff: noqa: E402 -- models must be imported (above) before Base.metadata is read (below)
from modules.workspace_tenancy.infrastructure.models import (  # noqa: F401
    MembershipModel,
    WorkspaceModel,
)
from signora_platform.db.base import Base
from signora_platform.event_bus.models import (  # noqa: F401
    DeadLetterEventModel,
    ProcessedEventModel,
)
from signora_platform.event_bus.outbox_model import OutboxEventModel  # noqa: F401


def _database_url() -> str:
    url = os.environ.get("SIGNORA_DATABASE_URL")
    if not url:
        raise RuntimeError("SIGNORA_DATABASE_URL must be set to run migrations.")
    return url


config = context.config

# Alembic's fileConfig replaces the root logger — a console handler at
# WARNING, in plain text. Run from the Alembic CLI that is exactly right.
# Run from `apps.migrate.main`, it discards the runner's own INFO lines
# (including "migrations applied", which is what an operator greps for to
# confirm the release step succeeded) and splits one release step across two
# log formats.
#
# So the two configurations are made mutually exclusive rather than left to
# whichever runs last. The runner sets this variable before importing
# Alembic; nothing else does.
if config.config_file_name is not None and not os.environ.get("SIGNORA_LOGGING_CONFIGURED"):
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    context.configure(
        url=_database_url(),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def _do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    configuration = config.get_section(config.config_ini_section) or {}
    configuration["sqlalchemy.url"] = _database_url()
    connectable = async_engine_from_config(
        configuration, prefix="sqlalchemy.", poolclass=pool.NullPool
    )

    async with connectable.connect() as connection:
        await connection.run_sync(_do_run_migrations)

    await connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
