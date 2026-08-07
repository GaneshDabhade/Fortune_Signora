"""The coordination source is stale only when its *content* has changed.

[B-134](../../docs/BUGS.md), found by QE. `infra/coordination.py --check` could
never return `0`: `render()` stamped `generated_from` with `HEAD`, so
regenerating recorded the current commit, committing the file moved `HEAD`, and
the next comparison re-rendered a different stamp. **The file recorded a value
that writing the file invalidated.**

⚠️ **I reported the instrument clean the cycle before QE found this.** It was —
for the minutes between regenerating and committing, which is the only window I
ever ran it in. QE ran it on a detached checkout with nothing stale, which is
the honest steady state, and there it failed every time. **Running a check only
where it passes is not running it**, and that is the finding this file exists to
keep fixed.

[B-135](../../docs/BUGS.md) is why it exists at all: 285 lines of governance
tooling shipped with no tests, and B-134 is precisely the defect a test would
have caught on the first run.

**Every case below is fixed text, never the live `coordination.toml`.**
Asserting that the real published source is current would pass today and pass
identically with `_content` deleted — the Decorative Logic `CLAUDE.md` §2 names.
The rows that separate a correct implementation from the broken one are written
out here instead.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]


def _load_coordination() -> ModuleType:
    path = REPO_ROOT / "infra" / "coordination.py"
    spec = importlib.util.spec_from_file_location("coordination", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    # `@dataclass(slots=True)` resolves annotations through
    # `sys.modules[cls.__module__]`, so register before the body executes.
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


coordination = _load_coordination()

#: A source with one lane block and one task. **Two `[meta]` stamps differ and
#: nothing else does** — which is exactly the state the repository is in one
#: commit after the file was written.
_PUBLISHED = """\
# THE CANONICAL COORDINATION SOURCE — generated, never hand-edited.

[meta]
generator      = "infra/coordination.py"
generated_from = "aaaaaaa"
task_count     = 1

[lane.Lane_A]
current            = "TASK-478"
claimable          = 1

[[task]]
id            = "TASK-478"
state         = "ASSIGNED"
"""

_REGENERATED_SAME_CONTENT = _PUBLISHED.replace("aaaaaaa", "bbbbbbb")
_REGENERATED_NEW_CONTENT = _PUBLISHED.replace('current            = "TASK-478"', 'current            = "TASK-450"')


def test_a_changed_stamp_alone_is_not_staleness() -> None:
    """**The whole of B-134.** Provenance moved; not one task or metric did."""
    assert coordination._content(_PUBLISHED) == coordination._content(
        _REGENERATED_SAME_CONTENT
    )


def test_a_changed_lane_pipeline_is_staleness() -> None:
    """⛔ The check must still fail on the thing it exists to catch.

    Without this, `_content` returning a constant would satisfy the test above
    and the check would be a guard that cannot fail (`CLAUDE.md` §2).
    """
    assert coordination._content(_PUBLISHED) != coordination._content(
        _REGENERATED_NEW_CONTENT
    )


def test_content_survives_a_source_with_no_lane_block() -> None:
    """A source that never reached a lane block is compared whole.

    ⚠️ `_content` splits on `\\n[lane.`; the fallback matters because a
    generator run that produced no lanes must not silently compare equal to
    every other such run.
    """
    a = "[meta]\ngenerated_from = \"aaaaaaa\"\n"
    b = "[meta]\ngenerated_from = \"bbbbbbb\"\n"
    assert coordination._content(a) != coordination._content(b)


@pytest.mark.parametrize(
    ("declared", "ahead", "expected"),
    [
        ("`IN VALIDATION` — Lane A, 2026-08-06", 0, True),
        ("`VERIFIED` — QE", 0, True),
        ("`CERTIFIED` — QE", 0, True),
        # ⛔ Someone is holding it right now. Not delivered.
        ("`CLAIMED` — Lane A", 0, False),
        ("`IN PROGRESS` — Lane A", 0, False),
        ("`READY` — Lane C", 0, False),
        # ⚡ The branch is what stops a declaration being taken at its word.
        ("`IN VALIDATION` — Lane A", 3, False),
    ],
)
def test_delivered_reads_the_branch_not_only_the_declaration(
    declared: str, ahead: int, expected: bool
) -> None:
    """A predecessor is handed over only if its lane has nothing outstanding.

    [C-427](../../docs/LANE_COORDINATION.md): twenty-two rows sat `SEQUENCED`
    behind predecessors already on `main`, because the only state that would
    have moved them is `VERIFIED` and that is QE's alone.

    ⛔ **The first version of `_delivered` asked `git log origin/main
    --grep=TASK-nnn`** — which matches every commit that *mentions* an id,
    including the one that wrote the row, so every task ever discussed read as
    delivered. **[B-101](../../docs/BUGS.md)'s class inside the function
    written to end it.** These rows are what separate the two implementations.
    """
    row = coordination.Task(
        id="TASK-449",
        title="predecessor",
        state=coordination.IN_FLIGHT,
        declared=declared,
        lane="Lane A",
        depends_on=[],
    )
    assert (
        coordination._delivered("TASK-449", {"TASK-449": row}, {"Lane A": ahead})
        is expected
    )


def test_a_predecessor_absent_from_the_graph_is_delivered() -> None:
    """`DONE`, `DISPOSED` and `PROMOTED` are dropped before the walk.

    So absence means closed, and a successor must not wait on a row nobody
    can find.
    """
    assert coordination._delivered("TASK-001", {}, {"Lane A": 0}) is True


def test_the_pipeline_is_ordered_by_leverage_not_by_identifier() -> None:
    """⚡ Every claimable row sits at depth 0, so the tiebreak decided the order.

    Sorting by `(critical_path, id)` told Lane A to start `TASK-441`, which
    releases nothing, ahead of `TASK-478`, which releases three rows — because
    441 < 478. **A queue ordered by identifier is not an ordering.**
    """

    # ⛔ **`-> Any`, not `-> coordination.Task` — B-138.** `coordination` is
    # loaded through `importlib`, so it is a `ModuleType` and mypy has no static
    # symbol behind the dot. **Attribute access on it is `Any` and fine; an
    # annotation is a name lookup and fails.** Every other reference in this
    # file is the former, which is why this was the only red line in 811.
    def row(task_id: str, unblocks: list[str]) -> Any:
        return coordination.Task(
            id=task_id,
            title=task_id,
            state=coordination.ASSIGNED,
            declared="`READY`",
            lane="Lane A",
            depends_on=[],
            unblocks=unblocks,
        )

    rows = [row("TASK-441", []), row("TASK-478", ["a", "b", "c"]), row("TASK-450", ["a"])]
    ordered = sorted(rows, key=lambda r: (-len(r.unblocks), r.critical_path, r.id))
    assert [r.id for r in ordered] == ["TASK-478", "TASK-450", "TASK-441"]
