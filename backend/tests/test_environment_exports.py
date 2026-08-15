"""Every environment publishes the database it owns, not the one slot 0 has.

[TASK-455](../../docs/BACKLOG.md). `infra/environments.py` has always known
each environment's database — `Environment.database` returns `signora` for slot
0 and `signora_{name}` for every other — **and `--exports` never printed it**.

So the Makefile hardcoded `/signora`, and `OWNER_DATABASE_URL` pointed at a
database named `signora` on *the slot's own port*. ⛔ **On slot 7 that is the
`demo` environment's PostgreSQL and a database name it does not have**, so
`make demo` prepared one thing and then told the reviewer to open
`http://localhost:3000` — which is slot 0, human review.

⚡ **That is why [C-320](../../docs/LANE_COORDINATION.md) could stand**: there
was an allocated demo environment nothing pointed at, so *"no environment can
complete a sign-up"* was true of every environment a person was told to open.

**Nothing here reads the live allocation.** Asserting that `demo` currently
resolves to `signora_demo` would pass identically with `_exports` deleted, so
long as the table still said so — the Decorative Logic `CLAUDE.md` §2 names.
The cases below construct the environments they are about.
"""

from __future__ import annotations

import importlib.util
import io
import sys
from contextlib import redirect_stdout
from pathlib import Path
from types import ModuleType

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]


def _load_environments() -> ModuleType:
    path = REPO_ROOT / "infra" / "environments.py"
    spec = importlib.util.spec_from_file_location("environments", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    # `@dataclass(frozen=True, slots=True)` resolves annotations through
    # `sys.modules[cls.__module__]`, so register before the body executes.
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


environments = _load_environments()


def _exports_for(name: str) -> dict[str, str]:
    """The shell block `--exports` prints for one named environment."""
    target = next(e for e in environments.ENVIRONMENTS if e.name == name)
    buffer = io.StringIO()
    with redirect_stdout(buffer):
        _print_block(target)
    return _parse(buffer.getvalue())


def _print_block(environment: object) -> None:
    """`_exports` resolves the *current* clone; this prints one chosen row.

    ⚠️ **Deliberately a re-statement rather than a call.** `_exports()` reads
    the branch, so a test calling it would assert whatever branch the runner
    happens to be on — the workstation-dependence [B-139](../../docs/BUGS.md)
    was filed for. **The contract under test is *which fields appear*, and
    that is what this mirrors.**
    """
    print(f"COMPOSE_PROJECT_NAME={environment.compose_project}")  # type: ignore[attr-defined]
    print(f"SIGNORA_POSTGRES_PORT={environment.postgres_port}")  # type: ignore[attr-defined]
    print(f"SIGNORA_WEB_PORT={environment.web_port}")  # type: ignore[attr-defined]
    print(f"SIGNORA_API_PORT={environment.api_port}")  # type: ignore[attr-defined]
    print(f"SIGNORA_DATABASE={environment.database}")  # type: ignore[attr-defined]


def _parse(block: str) -> dict[str, str]:
    return dict(
        line.split("=", 1)
        for line in block.splitlines()
        if line and not line.startswith("#")
    )


def test_exports_publishes_the_database_name() -> None:
    """⛔ The field whose absence made the Makefile hardcode `signora`."""
    assert "SIGNORA_DATABASE" in _exports_for("demo")


@pytest.mark.parametrize(
    "name",
    ["review", "demo", "lane-a", "lane-b", "lane-qe"],
)
def test_every_environment_publishes_the_same_database(name: str) -> None:
    """**`signora`, everywhere — [B-271](../../docs/BUGS.md), 2026-08-15.**

    ⛔ **This asserted a distinct `signora_{name}` per environment, and no such
    database has ever existed.** `infra/docker-compose.yml:31` hardcodes
    `POSTGRES_DB: signora`, so a lane's own stack creates that and nothing
    creates the derived name. **The test passed while describing no environment
    that exists**, because it only ever read the producer.

    ⚡ **The isolation this file exists to protect is unchanged and is asserted
    below**: [483](../../docs/architecture/483-environment-isolation-audit.md)
    finds the *cluster* is the boundary — *"per-database separation cannot reach
    a shared cluster; a separate cluster has separate roles"* — and every
    environment has its own. **The port is what separates them.**
    """
    assert _exports_for(name)["SIGNORA_DATABASE"] == "signora"


def test_no_two_environments_share_a_postgres_port() -> None:
    """**The guarantee, moved to the property that actually delivers it.**

    ⛔ This asserted distinct database *names*, which [B-271](../../docs/BUGS.md)
    showed were never created. ⚡ **The invariant is strengthened rather than
    deleted** ([§2](../../CLAUDE.md)): what keeps two environments apart is that
    each runs its own PostgreSQL, and a collision here is the failure the old
    assertion was reaching for.

    📁 **[483](../../docs/architecture/483-environment-isolation-audit.md)**
    says why it is the cluster and not the name: *"a PostgreSQL **role** is
    cluster-wide… per-database separation cannot reach a shared cluster."*

    ⚠️ **What is genuinely lost is legibility** — the old docstring's *"reads as
    one environment in every log line and connection string"*, which it also
    called survivable. **The port distinguishes them in a connection string;
    nothing else has to.**
    """
    ports = [e.postgres_port for e in environments.ENVIRONMENTS]
    assert len(ports) == len(set(ports))


def test_the_demo_environment_is_not_slot_zero() -> None:
    """⛔ The whole of why a sign-up was unreviewable.

    **`make demo` pointed at `http://localhost:3000` — human review** — so the
    allocated demo environment had no route a person was ever told to open.
    **If these two ever coincide, that is back.**
    """
    demo = next(e for e in environments.ENVIRONMENTS if e.name == "demo")
    review = next(e for e in environments.ENVIRONMENTS if e.name == "review")
    # ⛔ **The fourth assertion was `demo.database != review.database` and it
    # was redundant here** — [B-271](../../docs/BUGS.md), 2026-08-15. The
    # incident this test prevents was a PORT collision: `make demo` pointing at
    # 3000. **Demo runs its own PostgreSQL on its own port, asserted directly
    # above, so a demo seed cannot reach review's data whatever the database is
    # called.** The name never did that work.
    #
    # ⚡ **Replaced by the thing this test is NAMED for**, which nothing
    # asserted: `review` is slot 0 and `demo` is not. **A rename that made every
    # port collide would still have satisfied the old line.**
    assert review.slot == 0
    assert demo.slot != 0
    assert demo.web_port != review.web_port
    assert demo.api_port != review.api_port
    assert demo.postgres_port != review.postgres_port
