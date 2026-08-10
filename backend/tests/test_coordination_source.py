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
from datetime import datetime
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
    assert [
        r.id for r in coordination.premature_releases([held, released], frozenset())
    ] == ["TASK-458"]


def test_premature_releases_is_silent_on_a_correct_release() -> None:
    """⛔ A guard that always fires is as useless as one that cannot.

    ⚠️ **This case is [B-144](../../docs/BUGS.md)'s detector and it did its
    job.** It began failing on a tree that had certified green, with nothing in
    the repository changed — `premature_releases` called `_outstanding_rows()`
    internally, which greps lane branches for task ids, and **another lane
    typed `TASK-432` in a commit body.** ⛔ **Never repair a failure here by
    loosening the assertion: a gate that answers differently on two clones is
    the defect, and this is what notices.**
    """
    done = coordination.Task(
        id="TASK-432", title="p", state=coordination.IN_FLIGHT,
        declared="IN VALIDATION", lane="Lane A", depends_on=[],
    )
    released = coordination.Task(
        id="TASK-444", title="r", state=coordination.ASSIGNED,
        declared="READY", lane="Lane A", depends_on=["TASK-432"],
    )
    assert coordination.premature_releases([done, released], frozenset()) == []


def test_the_release_guards_are_pure_functions_of_their_arguments() -> None:
    """⛔ A certification gate must answer the same way on every clone.

    **[B-144](../../docs/BUGS.md), found by QE.** `_delivered` was hoisted for
    exactly this reason ([B-139](../../docs/BUGS.md)) and **the hidden input
    moved up one frame and stayed in the call path**: all three of these called
    `_outstanding_rows()` internally, so their answers depended on which refs
    the running clone had fetched and on what other lanes had typed in a commit
    message. **`origin/main` went green to red with the tree unchanged.**

    ⚡ **This asserts the property, not the repair** — the same rows with two
    different worlds must give two different answers, and the *only* thing that
    may move the answer is an argument. **It covers all three siblings**,
    because fixing only the one a test caught is how the input moved frames the
    first time.
    """
    done = coordination.Task(
        id="TASK-432", title="p", state=coordination.IN_FLIGHT,
        declared="IN VALIDATION", lane="Lane A", depends_on=[],
    )
    released = coordination.Task(
        id="TASK-444", title="r", state=coordination.ASSIGNED,
        declared="READY", lane="Lane A", depends_on=["TASK-432"],
    )
    rows = [done, released]

    # Nothing outstanding: the predecessor is handed over, so the release stands.
    assert coordination.premature_releases(rows, frozenset()) == []
    assert coordination.premature_releases(rows, frozenset()) == []
    # ⚡ Only the argument moves it — this is the world that used to arrive
    # through `git cherry` on whichever refs the machine happened to hold.
    assert [
        r.id for r in coordination.premature_releases(rows, frozenset({"TASK-432"}))
    ] == ["TASK-444"]

    parked = coordination.Task(
        id="TASK-445", title="s", state=coordination.SEQUENCED,
        declared="SEQUENCED", lane="Lane A", depends_on=["TASK-432"],
    )
    seq = [done, parked]
    assert [r.id for r in coordination.stale_sequencing(seq, frozenset())] == ["TASK-445"]
    assert coordination.stale_sequencing(seq, frozenset({"TASK-432"})) == []

    # `blocked_on_integration` reads the same world and took it the same way.
    assert coordination.blocked_on_integration(seq, "Lane A", frozenset()) == []
    assert [
        r.id
        for r in coordination.blocked_on_integration(seq, "Lane A", frozenset({"TASK-432"}))
    ] == ["TASK-445"]


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


def test_the_published_source_never_reads_the_clock() -> None:
    """⛔ Two regenerations of one commit must produce one file.

    **[B-145](../../docs/BUGS.md), found by QE.** `_blocked_days` measured
    against `datetime.now()` and the result was baked into the published
    source, so **`coordination.py --check` went red roughly every 2.4 hours
    without a single planning fact changing.** ⚠️ **A check that goes red on
    its own is one lanes learn to read past**, and that is the whole cost — the
    numbers themselves were never wrong.

    ⚡ **The same class as [B-144](../../docs/BUGS.md) in this same module, one
    day apart**: an input that moves the output without being part of the
    declared contract (`CLAUDE.md` §2, *hidden inputs are architecture
    defects*). **B-144 was a clone read mid-function; this was a clock read
    mid-function.**

    **Asserted by making the clock explode rather than by comparing two runs**,
    because two runs a second apart agree even when the defect is present —
    which is exactly why this survived until a lane polled hours later.
    """

    class Exploding(datetime):
        @classmethod
        def now(cls, tz: object = None) -> "Exploding":  # noqa: ARG003
            raise AssertionError(
                "datetime.now() reached during generation — the clock is an input again"
            )

    original = getattr(coordination, "datetime")
    setattr(coordination, "datetime", Exploding)
    try:
        rows = coordination.tasks()
        assert rows, "the fixture is empty — the assertion would pass vacuously"
        coordination.render(rows)
    finally:
        setattr(coordination, "datetime", original)


# ── a trigger steward is an owner, never an executor ────────────────────────


_STEWARD_BODY = (
    "| ⚡ **Trigger steward** | **Lane C — Product Office**, inherited with "
    "[TASK-411](#task-411), whose slices 4–5 are its trigger. ⛔ **This is not "
    "a module assignment and does not become one.** |"
)


def test_a_startable_row_takes_no_lane_from_a_trigger_steward() -> None:
    """⛔ D-135 gave the steward an *owner*'s job, and this read it as an executor's.

    **`TASK-412`, measured on 2026-08-10, not foreseen.** Its Module cell is
    absent — the boundary is deferred by [D-042] — so resolution fell to the
    steward and the published ref offered **Product Office** a row whose own
    Change Budget is 🟢 `modules/ai_platform/**`. ⛔ `modules.toml` settles
    `ai_platform` on Lane A and §20e forbids Lane C to implement it, **while
    `queues/lane-a.toml` queued the same row to Lane A**: one row, two
    documents, opposite owners — the C-213 class this ref exists to end.

    ⚡ **`backlog` is the array §20e step 4 tells a lane to select from**, so a
    steward reaching it is not a label a lane can ignore.
    """
    assert coordination._lane_for("", _STEWARD_BODY, {}, "READY") is None


def test_a_parked_row_still_takes_its_steward() -> None:
    """✅ The half D-135 actually asked for, which the fix must not remove.

    *"Every task should have an owner even if it cannot yet have an executor."*
    **`TASK-411` is `SEQUENCED`** — no lane can claim it, so naming its steward
    assigns nobody work and somebody still watches the trigger. **A fix that
    silenced this one would trade one defect for the one D-135 closed.**
    """
    assert coordination._lane_for("", _STEWARD_BODY, {}, "SEQUENCED") == "Lane C"


def test_a_named_module_still_beats_a_steward_on_a_startable_row() -> None:
    """⚡ The withholding is scoped to rows with *no other evidence*.

    A row that names its module resolves through `modules.toml` exactly as
    before — **this must not make every startable row ownerless**, which is the
    obvious way to over-apply the fix and would empty both lanes' backlogs.
    """
    owners = {"ai_platform": "Lane A"}
    assert coordination._lane_for("`ai_platform`", _STEWARD_BODY, owners, "READY") == "Lane A"


def test_a_startable_row_with_no_lane_reads_as_waiting_architecture() -> None:
    """✅ Withholding the steward loses no information — it tells the truth.

    `_classify` already renders a startable row with no lane as
    `WAITING ARCHITECTURE`, which is what a deliberately-deferred module
    boundary **is**. ⛔ The row does not vanish from the projection; it stops
    being advertised as claimable by a lane that may not build it.
    """
    assert coordination._classify("READY", "", None) == coordination.WAITING_ARCHITECTURE
    assert coordination._classify("READY", "", "Lane A") == coordination.ASSIGNED


# ── a notice may answer a blocker on this lane's own row ───────────────────


def _notice_for(tmp_path: Path, body: str, lane: str, reachable: set[str]) -> str:
    """Run `_notice` against a substituted notices file, not the real one."""
    f = tmp_path / "notices.toml"
    f.write_text(f'["{lane}"]\nnotice = """{body}"""\n')
    original = getattr(coordination, "NOTICES")
    setattr(coordination, "NOTICES", f)
    try:
        return str(coordination._notice(lane, reachable))
    finally:
        setattr(coordination, "NOTICES", original)


def test_a_notice_may_name_this_lanes_own_integrated_row(tmp_path: Path) -> None:
    """⚡ Answering a blocker is what a notice is FOR — measured 2026-08-10.

    **`reachable` was the lane's `backlog` array**, which is `ASSIGNED and
    on_integration`, **so a notice could not name a row the lane was BLOCKED
    on.** 🔴 Lane A raised `C-269` against `TASK-1439`, released the claim, and
    this office's answer was withheld **for naming the row Lane A had itself
    asked about** — the one case neither of B-221's recorded causes covers.
    """
    body = "C-269 answered — TASK-1439's entry set needs a ruling; its structure does not."
    out = _notice_for(tmp_path, body, "Lane A", {"TASK-1439"})
    assert "WITHHELD" not in out
    assert "TASK-1439" in out


def test_an_unintegrated_row_is_still_refused(tmp_path: Path) -> None:
    """⛔ B-221's first cause, and the widening must not reopen it.

    *"`backlog` is computed from what is SYNCHRONIZED, the notice from what was
    AUTHORED."* **A row this office has only authored is absent from the
    reachable set and must still be refused**, which is why the notice written
    on 2026-08-10 names the `/accounts` row by description rather than by id.
    """
    body = "A row is opened for the missing index — TASK-1457 — and sequenced."
    out = _notice_for(tmp_path, body, "Lane A", {"TASK-1439"})
    assert "WITHHELD" in out
    assert "TASK-1457" in out


def test_another_lanes_row_is_still_refused(tmp_path: Path) -> None:
    """⛔ B-221's second cause, which mattered more than the first.

    *"`TASK-1431` is `platform_foundation`, Lane C's own module, and the notice
    told Lane A it was yours today"* — **this office handing its own work to
    another lane on the one channel that bypasses QE.** The reachable set is
    per-lane, so a row outside it is refused however integrated it is.
    """
    out = _notice_for(tmp_path, "TASK-1431 is worth a look.", "Lane A", {"TASK-1439"})
    assert "WITHHELD" in out


def test_a_notice_still_may_not_assert_a_state(tmp_path: Path) -> None:
    """⛔ B-216 is independent of the widening and must survive it.

    A notice may now name this lane's blocked row; it still may not say what
    the state IS. **Only `BACKLOG.md` may**, and the widening deliberately did
    not touch the banned-word check that enforces it.
    """
    out = _notice_for(tmp_path, "TASK-1439 is BLOCKED, so take another.", "Lane A", {"TASK-1439"})
    assert "WITHHELD" in out
    assert "state" in out.lower()


def test_render_publishes_a_notice_naming_a_blocked_row_of_that_lane(tmp_path: Path) -> None:
    """🔴 The CALL SITE, and the first version of these tests missed it.

    **`_notice` was always correct given a reachable set.** What changed on
    2026-08-10 is *which set `render` passes it* — it passed the lane's
    `backlog` array, which excludes blocked rows. ⚡ **Testing `_notice`
    directly cannot see that**, and the first three tests here passed with the
    fix reverted: **decorative, by the repository's own definition** (§2).

    This goes through `render`, so reverting the call site turns it red.
    """
    blocked = coordination.Task(
        id="TASK-1439", title="the rail", state=coordination.BLOCKED,
        declared="BLOCKED", lane="Lane A", depends_on=[], on_integration=True,
    )
    f = tmp_path / "notices.toml"
    f.write_text('["Lane A"]\nnotice = """C-269 answered — TASK-1439\'s entry set needs a ruling."""\n')
    original = getattr(coordination, "NOTICES")
    setattr(coordination, "NOTICES", f)
    try:
        out = coordination.render([blocked])
    finally:
        setattr(coordination, "NOTICES", original)
    assert "WITHHELD" not in out, "a lane's own blocked row was refused by its own notice"
    assert "TASK-1439" in out
