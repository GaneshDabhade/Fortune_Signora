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

# The worker entry point resolves its ARQ configuration at import — ARQ
# reads `WorkerSettings.redis_settings` as a value and dereferences it
# immediately, so it cannot be deferred behind a callable. Importing
# `apps.worker.main` therefore requires a complete Settings, exactly as the
# running worker does.
#
# Placeholders only, and only if the environment has not already supplied
# real ones. Tests that care about JWT behaviour build their own Settings
# with an ephemeral key pair; these exist so importing the module does not
# fail on configuration it will never use.
os.environ.setdefault("SIGNORA_JWT_PUBLIC_KEY", "test-placeholder-not-a-key")
os.environ.setdefault("SIGNORA_JWT_ISSUER", "https://auth.signora.test")
os.environ.setdefault("SIGNORA_JWT_AUDIENCE", "signora-api-test")

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


@pytest.fixture
def admin_session_factory(admin_engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    """Session factory for platform infrastructure that legitimately spans
    workspaces — the outbox relay and dead-letter handling.

    These operate on system tables (``outbox_event``, ``processed_event``,
    ``dead_letter_event``) which carry no RLS by design: the relay must
    sweep every workspace's events, which tenant scoping would prevent.
    Using the app-role factory here would work today but would silently
    break the moment those tables gained RLS, so the distinction is made
    explicit.
    """
    return async_sessionmaker(admin_engine, expire_on_commit=False)


@pytest.fixture(scope="session", autouse=True)
async def require_explicit_consent_to_truncate() -> None:
    """Refuse to run against a database that has not opted in to being wiped.

    ``clean_database`` truncates every table after each test. That is
    correct for a test database and catastrophic for any other — and the
    M1.3A/M1.3B checklists both call for running the Security Invariants
    against a *deployed* stack, which points this suite at real data.

    Found the hard way: running the invariants against the local production
    stack emptied it mid-way through the disaster-recovery script, so the
    ordering and reconciliation checks that followed passed against empty
    tables. A destructive default plus an innocent-looking invocation is a
    bad combination; opting in explicitly costs one environment variable.
    """
    if os.environ.get("SIGNORA_ALLOW_DESTRUCTIVE_TESTS") != "1":
        raise RuntimeError(
            "This suite TRUNCATES every table after each test. Set "
            "SIGNORA_ALLOW_DESTRUCTIVE_TESTS=1 to confirm the target database "
            "is disposable. Never set it against a database holding data you "
            "want to keep."
        )


@pytest.fixture(autouse=True)
async def clean_database(admin_engine: AsyncEngine) -> AsyncIterator[None]:
    yield
    async with admin_engine.begin() as conn:
        await conn.execute(
            text(
                "TRUNCATE membership, workspace, outbox_event, "
                "processed_event, dead_letter_event CASCADE"
            )
        )
