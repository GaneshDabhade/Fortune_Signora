"""Shared fixtures for integration tests.

Two connections are used, deliberately mirroring production reality:

* ``app_engine`` — connects as ``signora_app``, the least-privilege,
  non-superuser role the application itself uses. All code under test runs
  through this. Connecting as a superuser here would silently bypass
  Row-Level Security and make every isolation assertion pass vacuously.
* ``admin_engine`` — connects as the owning/migration role, used only for
  test setup and teardown (truncating between tests), which the app role is
  correctly forbidden from doing.
"""

import os
from collections.abc import AsyncIterator

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

DEFAULT_APP_DATABASE_URL = (
    "postgresql+asyncpg://signora_app:signora_app_local_dev@localhost:5432/signora"
)
DEFAULT_ADMIN_DATABASE_URL = "postgresql+asyncpg://signora:signora@localhost:5432/signora"


@pytest.fixture(scope="session")
async def app_engine() -> AsyncIterator[AsyncEngine]:
    url = os.environ.get("SIGNORA_TEST_APP_DATABASE_URL", DEFAULT_APP_DATABASE_URL)
    engine = create_async_engine(url)
    try:
        yield engine
    finally:
        await engine.dispose()


@pytest.fixture(scope="session")
async def admin_engine() -> AsyncIterator[AsyncEngine]:
    url = os.environ.get("SIGNORA_TEST_ADMIN_DATABASE_URL", DEFAULT_ADMIN_DATABASE_URL)
    engine = create_async_engine(url)
    try:
        yield engine
    finally:
        await engine.dispose()


@pytest.fixture(scope="session", autouse=True)
async def verify_app_role_is_rls_bound(app_engine: AsyncEngine) -> None:
    """Fail the suite loudly if it is pointed at a connection that bypasses
    RLS — every isolation test would otherwise pass for the wrong reason.
    """
    async with app_engine.connect() as conn:
        result = await conn.execute(
            text("SELECT rolsuper OR rolbypassrls FROM pg_roles WHERE rolname = current_user")
        )
        bypasses_rls = result.scalar_one()
    assert not bypasses_rls, (
        "Integration tests must connect as a non-superuser role without BYPASSRLS; "
        "otherwise Row-Level Security is not enforced and isolation assertions are vacuous."
    )


@pytest.fixture
def session_factory(app_engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(app_engine, expire_on_commit=False)


@pytest.fixture(autouse=True)
async def clean_database(admin_engine: AsyncEngine) -> AsyncIterator[None]:
    yield
    async with admin_engine.begin() as conn:
        await conn.execute(text("TRUNCATE membership, workspace, outbox_event CASCADE"))
