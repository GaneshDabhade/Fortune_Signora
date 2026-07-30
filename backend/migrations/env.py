"""Alembic environment.

Runs migrations against the async engine, reading ``SIGNORA_DATABASE_URL``
from the environment directly rather than through ``Settings``.

**The value supplied here is deliberately not the application's.** The same
variable name carries a different identity per process: the migration step
connects as the owner, the API and workers as ``signora_app`` (CLAUDE.md §8,
infra/docker-compose.prod.yml). A runtime service connected as the owner is
exempt from Row-Level Security on every table it touches, so the separation
is the tenancy model rather than a deployment preference.

Corrected 2026-07-30: this file previously described itself as using
``get_settings()`` and asserted "no separate migration-specific database
configuration". It reads ``os.environ`` and the configuration is separate on
purpose — the claim inverted a security property.

**Migrations here are hand-authored, and autogenerate is not used.** Every
revision states its own RLS policies, grants and constraints — none of which
autogenerate can produce, and all of which are the point. ``target_metadata``
is supplied because Alembic's API asks for it, not because anything compares
it against the live schema.

That is why only the platform's own models are imported below: the seven
business modules' models are deliberately absent, and adding a module's
import here would create a maintenance obligation with no consumer. The
schema's authoritative representation is the migration history, and a
module's SQLAlchemy models derive from it rather than the reverse.

Corrected 2026-07-30: this file previously claimed every module's models
must be imported here. Seven modules never were, and nothing broke — which
is what a rule with no consumer looks like from the outside.
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
