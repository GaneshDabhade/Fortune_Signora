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
from pathlib import Path

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

# ⚡ **The suite declares its own environment, and it is `test`.**
#
# 📁 [ADR-0412](../../docs/architecture/adr/0412-environment-and-secret-safe-logging.md)
# §2 makes `SIGNORA_ENVIRONMENT` required, and until this line the suite had
# no answer of its own — it inherited whatever `.env` happened to say.
# **Measured: not one of the 36 `Settings(...)` constructions passed it**, so
# every test silently believed it was `local`. The right answer, by accident.
#
# ⛔ **Set rather than `setdefault`, unlike the value above it.** A shell that
# exported `SIGNORA_ENVIRONMENT` would otherwise decide whether the suite
# thinks it is production — **a safety class inherited from ambient state is
# the hidden input [§2](../../CLAUDE.md) forbids**, and a test run's
# environment is not a matter of configuration. A test that needs another
# environment constructs `Settings(environment=...)` explicitly, and several do.
os.environ["SIGNORA_ENVIRONMENT"] = "test"

# The target database, resolved **once, here**, from the environment.
#
# **This is what makes two development lanes possible** (CLAUDE.md §20e).
# These were plain constants, and `SIGNORA_TEST_APP_DATABASE_URL` was read
# only by the two fixtures below — so every API integration test, which
# constructs `Settings(database_url=DEFAULT_APP_DATABASE_URL)` directly,
# ignored the override and went to the shared database regardless. Two lanes
# running `pytest` at the same time would have truncated each other's rows
# mid-run, producing failures neither could reproduce.
#
# Reading the environment at the constant means all twelve call sites
# inherit the isolation without knowing it exists.
DEFAULT_APP_DATABASE_URL = os.environ.get(
    "SIGNORA_TEST_APP_DATABASE_URL",
    "postgresql+asyncpg://signora_app:signora_app_local_dev@localhost:5432/signora",
)
DEFAULT_ADMIN_DATABASE_URL = os.environ.get(
    "SIGNORA_TEST_ADMIN_DATABASE_URL",
    "postgresql+asyncpg://signora:signora@localhost:5432/signora",
)


@pytest.fixture(scope="session")
async def app_engine() -> AsyncIterator[AsyncEngine]:
    engine = create_async_engine(DEFAULT_APP_DATABASE_URL)
    try:
        yield engine
    finally:
        await engine.dispose()


@pytest.fixture(scope="session")
async def admin_engine() -> AsyncIterator[AsyncEngine]:
    engine = create_async_engine(DEFAULT_ADMIN_DATABASE_URL)
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
    _refuse_human_reviews_database()


#: Human review's database, derived rather than written down. `infra/` is not on
#: the test path, so this reads the values `environments.py` computes for the
#: `review` environment and falls back to the literal pair only if that import
#: is impossible — an absent registry must not silently disable the guard.
def _human_review_target() -> tuple[str, str]:
    try:
        import importlib.util
        import sys as _sys

        path = Path(__file__).resolve().parents[2] / "infra" / "environments.py"
        spec = importlib.util.spec_from_file_location("_signora_environments", path)
        if spec and spec.loader:
            module = importlib.util.module_from_spec(spec)
            _sys.modules["_signora_environments"] = module
            spec.loader.exec_module(module)
            review = next(e for e in module.ENVIRONMENTS if e.name == "review")
            return str(review.postgres_port), str(review.database)
    except Exception:  # noqa: BLE001 - a missing registry must not disable the guard
        pass
    return "5432", "signora"


def _refuse_human_reviews_database() -> None:
    """Refuse to truncate the database a person is reviewing the product in.

    ⛔ **[B-270](../../docs/BUGS.md).** The consent guard above asks *"do you
    consent to truncation?"* and **never** *"which database?"* — and the answer
    to the first was correctly **yes** every time. `make test` supplied the
    consent flag with no database variable, so a shell without `SIGNORA_TEST_*`
    fell through `DEFAULT_APP_DATABASE_URL` to human review's database and
    emptied it. **No mistake was required: new shell, documented gate, slot 0
    gone.** Lane A hit it exactly that way.

    ⚡ **This is keyed on the DATABASE, not on the cluster, and that distinction
    is load-bearing.** `make certify` creates a disposable `signora_certify_<sha>`
    **on `localhost:5432`** — slot 0's cluster — because
    `tests/certification/database.py` pins `_HOST` there. **A port-based refusal
    would break every certification run**, which is why the pair is checked and
    not the port alone.

    ✅ **`ALLOW_SLOT_0=1` is the same escape `refuse-slot-0` uses in the
    `Makefile`**, deliberately one vocabulary rather than two: the environment
    genuinely cannot distinguish a reviewer from a lane, so the human says which.
    """
    if os.environ.get("ALLOW_SLOT_0") == "1":
        return
    port, database = _human_review_target()
    for variable in ("SIGNORA_TEST_APP_DATABASE_URL", "SIGNORA_TEST_ADMIN_DATABASE_URL"):
        url = os.environ.get(variable) or (
            DEFAULT_APP_DATABASE_URL
            if variable.endswith("APP_DATABASE_URL")
            else DEFAULT_ADMIN_DATABASE_URL
        )
        if url.endswith(f":{port}/{database}"):
            raise RuntimeError(
                f"REFUSED — {variable} points at localhost:{port}/{database}, "
                "which is human review's database. This suite truncates every "
                "table after each test (B-270).\n\n"
                "  Derive your own environment instead of quoting one:\n"
                "    eval \"$(python3 infra/environments.py --exports)\"\n\n"
                "  If you are deliberately targeting slot 0, set ALLOW_SLOT_0=1."
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
