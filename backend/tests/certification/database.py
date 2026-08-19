"""**Certification provisions its own database and destroys it afterwards.**

RE-03. *Repository Health · **Configuration Safety**.*

**The last hand-typed correctness requirement in the pipeline.** Until now the
suite resolved its target from `SIGNORA_TEST_APP_DATABASE_URL` — and if the
shell that launched `make certify` did not export it, the run silently measured
the **shared** `signora` database instead. Nothing said so. It certified
correctly at that setting every time it was tried, which is precisely what makes
it dangerous.

### The evidence, machine-written rather than argued

A certification attempt on 2026-08-03 recorded its own environment before the
first gate, and the record read:

    "test_database": "(unset — defaults to shared)"

That is [B-022](../../../docs/BUGS.md) observed rather than predicted, and it is
the same class as [B-106](../../../docs/BUGS.md): **a gate whose result depends
on the shell it was launched from.** The repository's own standard says
`CLAUDE.md` §2 — *hidden inputs are architecture defects*, because they make the
same declared inputs produce different results, which defeats replay and
regression testing. **In a certification gate it is worse**: the run that
certifies and the run that reproduces it are then measuring different things,
and the record cannot tell you which.

### What this removes

> **The workstation may affect execution speed. It must never affect execution
> correctness.**

A disposable database makes that true for the one dimension it was still false
for. After this, `make certify` produces the same measurement whether the
operator's shell exports anything or not — and a developer's own database is
untouched, because certification never looks at it.

### Why a fresh database rather than a fresh schema

**Migrations are the thing being certified.** `0002` creates the least-privileged
`signora_app` role and its grants; RLS policies are attached per table by the
migrations that create them. Running the chain against an empty database proves
the chain works from nothing — which a schema reset inside an existing database
does not, because it inherits grants somebody else applied.

### What it deliberately does not do

**It does not touch `make smoke` or `make dr`.** Those build their own stack with
their own PostgreSQL inside a compose project, and are already isolated. This is
only about the suite's database.

**It does not run outside certification.** `make test` still uses whatever the
developer configured, because a developer wants their data to persist between
runs and certification never does.
"""

from __future__ import annotations

import asyncio
import os
import re
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Final

import asyncpg

#: The runtime identity the suite connects as. **Never the owner**: a service
#: connected as the owner is exempt from RLS on every table it touches, which
#: would make the tenancy invariants pass vacuously.
APP_ROLE: Final = "signora_app"
APP_PASSWORD: Final = "signora_app_local_dev"

#: 🔴 **`ADMIN` and `_HOST` were `localhost:5432` literals — [B-1028](../../../docs/BUGS.md).**
#:
#: **`5432` is slot 0, which is human review's** (`RUNNING.md` allocates
#: `5432 + 100n`). So **every certification run this repository has ever
#: performed created and dropped its disposable database on the reviewer's
#: server**, not on the lane's — and when human review is *not* running,
#: `make certify` cannot create a database at all.
#:
#: ⛔ **No default.** Guessing a host is what produced the defect, and
#: `signora_platform/settings.py` already refuses a missing database URL for
#: the same reason. **The Makefile passes this to every gate; a run that
#: reaches here without it was started some other way and must say so rather
#: than reach for slot 0.**
_ADMIN_URL_VARIABLE: Final = "SIGNORA_TEST_ADMIN_DATABASE_URL"


def _host() -> str:
    """`host:port` of the server disposable databases are created on."""
    url = os.environ.get(_ADMIN_URL_VARIABLE)
    if not url:
        raise RuntimeError(
            f"{_ADMIN_URL_VARIABLE} is not set, so there is no server to create a "
            "disposable database on. It has NO default: `localhost:5432` is slot "
            "0 — human review's — and defaulting to it is B-1028. `make certify` "
            "and `make test` both set this from the lane's own allocation."
        )
    match = re.search(r"@([^/@]+)/", url)
    if not match:
        raise RuntimeError(f"{_ADMIN_URL_VARIABLE} names no host: {url!r}")
    return match.group(1)


def admin_dsn() -> str:
    """Where a disposable database is created. **The admin identity**, because
    `CREATE DATABASE` is owner-only — and the same identity migrations run under
    (`CLAUDE.md` §8: schema changes execute only under the migration identity).

    **`postgres`, the maintenance database**, because `CREATE DATABASE` cannot
    run from inside the database being created or dropped.
    """
    return f"postgresql://signora:signora@{_host()}/postgres"


@dataclass(frozen=True, slots=True)
class Disposable:
    """The two URLs a certification run hands to its subprocesses."""

    name: str
    app_url: str
    admin_url: str

    @property
    def environment(self) -> dict[str, str]:
        """What every gate in the run inherits.

        **Three variables, not two.** `SIGNORA_DATABASE_URL` is Alembic's own
        contract — `migrations/env.py` reads `os.environ` directly and cannot see
        a `Settings` object — and omitting it is exactly how
        [B-106](../../../docs/BUGS.md) happened.
        """
        return {
            "SIGNORA_TEST_APP_DATABASE_URL": self.app_url,
            "SIGNORA_TEST_ADMIN_DATABASE_URL": self.admin_url,
            "SIGNORA_DATABASE_URL": self.admin_url,
        }


def _valid(name: str) -> str:
    """A database name that cannot be anything but a database name.

    **`CREATE DATABASE` takes no parameters** — the identifier is interpolated,
    so the only safe input is one that has been proven to contain nothing else.
    A commit SHA satisfies this trivially; asserting it means a future caller
    passing something else fails here rather than somewhere more interesting.
    """
    if not re.fullmatch(r"[a-z0-9_]{1,60}", name):
        raise ValueError(f"'{name}' is not a safe database identifier")
    return name


async def _execute(statement: str) -> None:
    connection = await asyncpg.connect(admin_dsn())
    try:
        await connection.execute(statement)
    finally:
        await connection.close()


async def _drop(name: str) -> None:
    """Remove the database, disconnecting anything still attached.

    **`WITH (FORCE)` is not optional here.** A gate that failed mid-run can leave
    a pooled connection open, and `DROP DATABASE` refuses while one exists — so
    without it a single failed certification would leave a database behind and
    block the next run at the same commit.
    """
    await _execute(f'DROP DATABASE IF EXISTS "{name}" WITH (FORCE)')


@contextmanager
def disposable(name: str) -> Iterator[Disposable]:
    """Create a database for this run, and destroy it however the run ends.

    **Dropped in a `finally`, deliberately.** A certification that fails is
    exactly the run most likely to leave residue, and residue from a failed run
    is what makes the *next* run unreproducible — the failure mode this exists to
    remove, reintroduced one level up.
    """
    safe = _valid(name)
    asyncio.run(_drop(safe))
    asyncio.run(_execute(f'CREATE DATABASE "{safe}"'))
    try:
        yield Disposable(
            name=safe,
            app_url=f"postgresql+asyncpg://{APP_ROLE}:{APP_PASSWORD}@{_host()}/{safe}",
            admin_url=f"postgresql+asyncpg://signora:signora@{_host()}/{safe}",
        )
    finally:
        asyncio.run(_drop(safe))


def name_for(commit: str) -> str:
    """`signora_certify_<12 hex>` — identified by what it is certifying.

    **Not a random name.** A run that hangs and is killed leaves a database
    whose name says which commit it belonged to, and the next run at that commit
    drops it before creating its own. A UUID would leave an orphan nobody could
    attribute.
    """
    return f"signora_certify_{commit[:12].lower()}"
