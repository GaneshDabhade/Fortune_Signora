"""Certification measures a database it created, not one it found.

RE-03. The suite resolved its target from `SIGNORA_TEST_APP_DATABASE_URL`, so a
run launched from a shell that did not export it **silently measured the shared
`signora` database** — and certified correctly at that setting every time it was
tried, which is what made it dangerous rather than obvious.

The evidence is machine-written. A certification attempt on 2026-08-03 recorded
its own environment before the first gate:

    "test_database": "(unset — defaults to shared)"

That is [B-022](../../../docs/BUGS.md) observed rather than predicted.

**These tests use a real PostgreSQL**, because the property is a property of the
database — that `CREATE DATABASE` and `DROP DATABASE … WITH (FORCE)` behave as
assumed — and a fake would prove only that the fake was written to agree.
"""

from __future__ import annotations

import asyncio

import asyncpg
import pytest

from tests.certification import database as disposable_database

pytestmark = pytest.mark.integration


def test_the_name_identifies_what_is_being_certified() -> None:
    """**Not a random name.** A run that hangs and is killed leaves a database
    whose name says which commit it belonged to, and the next run at that commit
    drops it before creating its own. A UUID leaves an orphan nobody can
    attribute to anything."""
    assert disposable_database.name_for("08226e541959" + "0" * 28) == "signora_certify_08226e541959"
    assert disposable_database.name_for("ABCDEF123456") == "signora_certify_abcdef123456"


@pytest.mark.parametrize(
    "unsafe",
    ['signora"; DROP DATABASE signora; --', "signora certify", "signora-certify", "", "x" * 61],
)
def test_an_unsafe_identifier_is_refused(unsafe: str) -> None:
    """**`CREATE DATABASE` takes no parameters.**

    The identifier is interpolated into the statement, so the only safe input is
    one proven to contain nothing else. Every caller today passes a commit SHA
    and satisfies this trivially — which is exactly when a validator stops being
    exercised, so it is asserted here instead.
    """
    with pytest.raises(ValueError, match="not a safe database identifier"):
        disposable_database._valid(unsafe)


def _exists(name: str) -> bool:
    """Whether the server has this database.

    **Synchronous, like the caller.** `disposable()` uses `asyncio.run` because
    its caller — `tests/certification/__main__.py` — is a synchronous entry
    point. An `async def` test runs inside a loop already, so it cannot call it;
    making `disposable()` loop-aware would be adding production complexity to
    suit a test, which is backwards.
    """

    async def query() -> bool:
        connection = await asyncpg.connect(disposable_database.admin_dsn())
        try:
            return bool(
                await connection.fetchval("SELECT 1 FROM pg_database WHERE datname = $1", name)
            )
        finally:
            await connection.close()

    return asyncio.run(query())


def test_it_creates_and_then_destroys() -> None:
    """The property, against a real server.

    **The `finally` matters more than the create.** A certification that fails is
    the run most likely to leave residue, and residue from a failed run is what
    makes the *next* run unreproducible — the failure mode this exists to remove,
    reintroduced one level up.
    """
    name = "signora_certify_selftest01"
    assert not _exists(name), "a previous run left this behind"

    with disposable_database.disposable(name) as target:
        assert _exists(name)
        assert target.name == name
        assert name in target.app_url and name in target.admin_url

    assert not _exists(name), "the database survived the context manager"


def test_it_is_destroyed_even_when_the_run_fails() -> None:
    """**A failing certification must not poison the next one.**

    Without this, one failed run would leave a database behind and the next run
    at the same commit would fail to create it — turning a single failure into a
    permanently stuck pipeline.
    """
    name = "signora_certify_selftest02"

    with pytest.raises(RuntimeError, match="a gate failed"):
        with disposable_database.disposable(name):
            assert _exists(name)
            raise RuntimeError("a gate failed")

    assert not _exists(name), "a failed run left its database behind"


def test_the_app_url_never_uses_the_owner_identity() -> None:
    """**A service connected as the owner is exempt from RLS on every table.**

    That would make the tenancy Security Invariants pass vacuously — 360 tests
    asserting isolation against a role that cannot be isolated. The distinction
    is `CLAUDE.md` §8, and it is the one thing about these URLs that must never
    be convenient.
    """
    target = disposable_database.Disposable(
        name="signora_certify_x",
        app_url=f"postgresql+asyncpg://{disposable_database.APP_ROLE}:p@h/db",
        admin_url="postgresql+asyncpg://signora:signora@h/db",
    )
    assert "signora_app:" in target.app_url
    assert "://signora:" not in target.app_url


def test_alembic_receives_its_url_too() -> None:
    """**Three variables, not two.**

    `migrations/env.py` reads `os.environ["SIGNORA_DATABASE_URL"]` directly — it
    cannot see a `Settings` object — so a run that set only the two test URLs
    would migrate whatever the shell pointed at while testing the disposable
    database. That is [B-106](../../../docs/BUGS.md) with the numbers changed.
    """
    target = disposable_database.Disposable(
        name="signora_certify_x", app_url="app", admin_url="admin"
    )
    assert target.environment == {
        "SIGNORA_TEST_APP_DATABASE_URL": "app",
        "SIGNORA_TEST_ADMIN_DATABASE_URL": "admin",
        "SIGNORA_DATABASE_URL": "admin",
    }
