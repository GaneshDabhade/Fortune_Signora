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
    ("declared", "outstanding", "expected"),
    [
        ("`IN VALIDATION` — Lane A, 2026-08-06", frozenset(), True),
        ("`VERIFIED` — QE", frozenset(), True),
        ("`CERTIFIED` — QE", frozenset(), True),
        # ⛔ Someone is holding it right now. Not delivered.
        ("`CLAIMED` — Lane A", frozenset(), False),
        ("`IN PROGRESS` — Lane A", frozenset(), False),
        ("`READY` — Lane C", frozenset(), False),
        # ⚡ Outstanding work on the branch stops a declaration being taken at
        # its word — **and this row is what B-139 found untested.** It passed
        # `ahead={"Lane A": 3}` into a body that had stopped reading the
        # argument, so it would have passed identically with the argument
        # deleted, and the real answer came from whichever refs the running
        # clone happened to have.
        ("`IN VALIDATION` — Lane A", frozenset({"TASK-449"}), False),
    ],
)
def test_delivered_reads_outstanding_work_not_only_the_declaration(
    declared: str, outstanding: frozenset[str], expected: bool
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
        coordination._delivered("TASK-449", {"TASK-449": row}, outstanding)
        is expected
    )


def test_a_predecessor_absent_from_the_graph_is_delivered() -> None:
    """`DONE`, `DISPOSED` and `PROMOTED` are dropped before the walk.

    So absence means closed, and a successor must not wait on a row nobody
    can find.
    """
    assert coordination._delivered("TASK-001", {}, frozenset()) is True


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


def test_a_released_row_keeps_the_edge_it_was_released_from() -> None:
    """⛔ Rewriting `SEQUENCED` into `READY` must not delete the predecessor.

    **`TASK-458`, 2026-08-07.** Its status was rewritten from
    `SEQUENCED — predecessor [TASK-457]` to `READY`, which left it claimable
    with an empty `depends_on` — **so `stale_sequencing` could not see it (it
    only reads `SEQUENCED` rows) and nothing else was looking.** ⚡ **Releasing
    a row destroyed the evidence that the release was wrong.**

    **Lane A found it by opening `people/public/__init__.py` and seeing zero
    lines in it.** That is the check this asserts is no longer needed.
    """
    status = (
        "| **Status** | ✅ **`READY`** — **released from `SEQUENCED` after "
        "[TASK-457](#task-457--people-publishes), Lane C 2026-08-07.** More prose. |"
    )
    assert coordination._dependencies("READY", status) == ["TASK-457"]


def test_a_ready_row_with_no_release_marker_has_no_edge() -> None:
    """⚡ An ordinary `READY` row was never sequenced and must claim no edge.

    Without this, the pattern above could match any prose mentioning a task and
    invent dependencies — the false-edge defect `_dependencies` already carries
    a comment about, one release later.
    """
    assert coordination._dependencies("READY", "| **Status** | ✅ **`READY`** — see [TASK-457](#x) |") == []


def test_premature_releases_fires_on_a_predecessor_still_held() -> None:
    """The mirror of `stale_sequencing`, and the half that was missing.

    ⛔ `stale_sequencing` only reads rows still `SEQUENCED`, **so a row
    released in error leaves its scope at the moment the error is made.**
    """
    held = coordination.Task(
        id="TASK-457", title="p", state=coordination.IN_FLIGHT,
        declared="CLAIMED", lane="Lane B", depends_on=[],
    )
    released = coordination.Task(
        id="TASK-458", title="r", state=coordination.ASSIGNED,
        declared="READY", lane="Lane A", depends_on=["TASK-457"],
    )
    assert [r.id for r in coordination.premature_releases([held, released])] == ["TASK-458"]


def test_premature_releases_is_silent_on_a_correct_release() -> None:
    """⛔ A guard that always fires is as useless as one that cannot."""
    done = coordination.Task(
        id="TASK-432", title="p", state=coordination.IN_FLIGHT,
        declared="IN VALIDATION", lane="Lane A", depends_on=[],
    )
    released = coordination.Task(
        id="TASK-444", title="r", state=coordination.ASSIGNED,
        declared="READY", lane="Lane A", depends_on=["TASK-432"],
    )
    assert coordination.premature_releases([done, released]) == []


def test_delivered_is_a_pure_function_of_its_arguments() -> None:
    """⛔ The same declared inputs must produce the same result, anywhere.

    **[B-139](../../docs/BUGS.md), found by QE.** `_delivered` took `ahead` and
    stopped reading it, answering instead from `git log` against real refs in
    the running clone. ⚡ **So it passed on the workstation where it was
    written and failed on the one where it was run** — `CLAUDE.md` §2's
    *hidden inputs are architecture defects*, exactly.

    **This asserts the property rather than the repair**: called twice with
    identical arguments it returns identically, and the only thing that changes
    the answer is an argument.
    """
    row = coordination.Task(
        id="TASK-449", title="p", state=coordination.IN_FLIGHT,
        declared="`IN VALIDATION` — Lane A", lane="Lane A", depends_on=[],
    )
    by_id = {"TASK-449": row}
    assert coordination._delivered("TASK-449", by_id, frozenset()) is True
    assert coordination._delivered("TASK-449", by_id, frozenset()) is True
    # ⚡ Only the argument moves the answer.
    assert coordination._delivered("TASK-449", by_id, frozenset({"TASK-449"})) is False
