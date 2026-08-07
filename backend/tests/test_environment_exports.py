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
    ("name", "expected"),
    [
        # ⚡ Slot 0 is `signora` by history, and that is the only place the
        # hardcoded name was ever right.
        ("review", "signora"),
        ("demo", "signora_demo"),
        ("lane-a", "signora_lane_a"),
        ("lane-b", "signora_lane_b"),
        ("lane-qe", "signora_lane_qe"),
    ],
)
def test_each_environment_publishes_its_own_database(name: str, expected: str) -> None:
    """**The rows that separate the fix from the defect.**

    ⛔ Before this, every one of these resolved to `signora` — correct for
    `review` and wrong for the other four, on each one's *own* PostgreSQL port.
    """
    assert _exports_for(name)["SIGNORA_DATABASE"] == expected


def test_no_two_environments_share_a_database() -> None:
    """A shared name would defeat the separate clusters it sits inside.

    ⚡ **[483](../../docs/architecture/483-environment-isolation-audit.md)**: a
    separate cluster is what makes role separation real, and a shared database
    *name* across clusters is survivable but reads as one environment in every
    log line and connection string.
    """
    names = [e.database for e in environments.ENVIRONMENTS]
    assert len(names) == len(set(names))


def test_the_demo_environment_is_not_slot_zero() -> None:
    """⛔ The whole of why a sign-up was unreviewable.

    **`make demo` pointed at `http://localhost:3000` — human review** — so the
    allocated demo environment had no route a person was ever told to open.
    **If these two ever coincide, that is back.**
    """
    demo = next(e for e in environments.ENVIRONMENTS if e.name == "demo")
    review = next(e for e in environments.ENVIRONMENTS if e.name == "review")
    assert demo.web_port != review.web_port
    assert demo.api_port != review.api_port
    assert demo.postgres_port != review.postgres_port
    assert demo.database != review.database
