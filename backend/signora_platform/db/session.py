"""Async engine/session factory and the Row-Level Security context helpers.

Per docs/architecture/11-tenancy.md, every unit of work (FastAPI request or
ARQ job) must establish ``app.user_id`` (and, except during workspace
creation, ``app.workspace_id``) as transaction-local Postgres settings
*before* issuing any query against RLS-protected tables. This module is the
single place that happens — no module's infrastructure layer sets these
directly.

``set_config(..., true)`` is used instead of ``SET LOCAL ... = :param``
because PostgreSQL's ``SET`` family of statements does not accept bound
parameters over the extended query protocol; ``set_config`` is a regular
function call and does, which avoids string-interpolating caller-supplied
values into SQL text.
"""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from signora_platform.settings import Settings

_SET_USER_CONTEXT = text("SELECT set_config('app.user_id', :user_id, true)")
_SET_WORKSPACE_CONTEXT = text("SELECT set_config('app.workspace_id', :workspace_id, true)")


def create_engine(settings: Settings) -> AsyncEngine:
    return create_async_engine(
        str(settings.database_url),
        pool_size=settings.database_pool_size,
        max_overflow=settings.database_pool_max_overflow,
        pool_pre_ping=True,
    )


def create_relay_engine(settings: Settings) -> AsyncEngine:
    """Engine for the outbox relay, under the `signora_relay` identity.

    The relay is the only runtime process permitted to read platform
    infrastructure tables, which span every workspace. Falling back to
    `database_url` keeps a single-role local setup working, but the caller
    is expected to say so out loud — silently running the relay as the
    application role would reinstate exactly the cross-workspace read path
    migration 0006 closed.
    """
    url = settings.relay_database_url or settings.database_url
    return create_async_engine(
        str(url),
        # The relay is a single lightweight process running one batch loop;
        # it does not need the API's pool.
        pool_size=2,
        max_overflow=1,
        pool_pre_ping=True,
    )


def create_session_factory(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(engine, expire_on_commit=False)


async def set_workspace_context(session: AsyncSession, workspace_id: UUID) -> None:
    """Set ``app.workspace_id`` for the remainder of the current transaction.

    Used by ``CreateWorkspaceUseCase`` immediately after a new workspace row
    is inserted, so the founding membership row can be inserted under normal
    RLS (see the workspace-creation bootstrap pattern in
    docs/architecture/11-tenancy.md).
    """
    await session.execute(_SET_WORKSPACE_CONTEXT, {"workspace_id": str(workspace_id)})


@asynccontextmanager
async def user_scoped_session(
    session_factory: async_sessionmaker[AsyncSession], *, user_id: UUID
) -> AsyncIterator[AsyncSession]:
    """Open a transaction scoped only to an authenticated user, with no
    workspace context yet. The only legitimate use is workspace creation —
    every other unit of work must use ``tenant_scoped_session`` instead.
    """
    async with session_factory() as session, session.begin():
        await session.execute(_SET_USER_CONTEXT, {"user_id": str(user_id)})
        yield session


@asynccontextmanager
async def tenant_scoped_session(
    session_factory: async_sessionmaker[AsyncSession], *, workspace_id: UUID, user_id: UUID
) -> AsyncIterator[AsyncSession]:
    """Open a transaction scoped to both the authenticated user and the
    workspace being operated on. This is the default entry point for every
    unit of work except workspace creation.
    """
    async with session_factory() as session, session.begin():
        await session.execute(_SET_USER_CONTEXT, {"user_id": str(user_id)})
        await session.execute(_SET_WORKSPACE_CONTEXT, {"workspace_id": str(workspace_id)})
        yield session
