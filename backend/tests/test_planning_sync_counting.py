"""A planning correction is a commit carrying the trailer — not any commit.

**The defect these were written from.** `pipeline-dashboard.py` computed
``git rev-list --count origin/integration..HEAD`` and rendered the total under
the heading **"Planning not on integration"** with a target of ``0``. It counted
every commit on whatever branch happened to be checked out, so five `infra/` bug
fixes reported as a 🔴 against the Product Office — and standing on
``integration`` would have reported ``0`` however much planning was waiting on
somebody's branch.

⛔ **Both errors at once: it over-reports work that is not planning, and it
under-reports planning that is not on this branch.**

⚡ **[D-136](../../docs/DECISION_REGISTER.md) already defined the answer** — a
planning correction carries ``Planning-Sync: required`` as a commit trailer, and
`state-check.py` matches exactly that. The dashboard had invented a second,
different meaning for the same words, which is what `registers.py` exists to
prevent: *"`state-check.py` and `kpi.py` both need to answer 'is this bug
blocking?', and they answered it differently."* **Same file, same principle, one
metric later.**
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

_SPEC = importlib.util.spec_from_file_location(
    "registers", Path(__file__).resolve().parents[2] / "infra" / "registers.py"
)
assert _SPEC is not None and _SPEC.loader is not None
registers = importlib.util.module_from_spec(_SPEC)
# `@dataclass` resolves annotations through `sys.modules[cls.__module__]`, so
# the module must be registered before its body executes — the same trap
# `test_bug_row_state.py` documents, and loading it by hand walked into it.
sys.modules["registers"] = registers
_SPEC.loader.exec_module(registers)


ORDINARY = """B-439 — doc-drift blamed a lane for another lane's promoted work

The default range was the bare string `integration..HEAD`.

Budget: green infra/doc-drift.py
"""

PLANNING = """C-422 — TASK-440's account table has no read

The row is not buildable as written.

Planning-Sync: required
"""

# 🔴 **The case a bare-word grep gets wrong, and it is not hypothetical.**
# This is the shape of the commit that FIXED the counting: it discusses the
# convention in prose and carries no trailer.
PROSE_ONLY = """B-440 — the planning counter counted every commit on the branch

Same reasoning §20e already applies to Planning-Sync: a check that fails on
something its own lane cannot fix teaches people to ignore it.
"""

# 🔴 **The case a FULL-STRING substring match gets wrong — measured, not
# imagined.** This is B-440's own fix commit, and `state-check` reported it as
# an unsynchronized planning correction eight minutes after it was written
# ([B-442](../../docs/BUGS.md)). **A repository whose commits explain their own
# conventions will always contain prose that quotes them.**
QUOTES_THE_TRAILER = """B-440 — the planning counter counted every commit on the branch

D-136 defines a planning correction as a commit carrying `Planning-Sync:
required`, and state-check.py matches exactly that.

Budget: green infra/pipeline-dashboard.py
"""

# ⚠️ **Indented, because a quoted trailer is usually quoted in a code block.**
INDENTED_QUOTE = """Notes on the convention

    Planning-Sync: required

is what a planning correction carries.
"""


class TestOnlyTheTrailerCounts:
    def test_an_ordinary_commit_is_not_a_planning_correction(self) -> None:
        """✅ **The defect, inverted.** Five bug fixes are five bug fixes."""
        assert registers.planning_sync_commits(ORDINARY) == 0

    def test_a_trailer_is_counted(self) -> None:
        assert registers.planning_sync_commits(PLANNING) == 1

    def test_prose_mentioning_the_convention_is_not_counted(self) -> None:
        """🔴 **The subtle half, and a bare-word grep fails it.**

        ⚠️ **`git log --grep="Planning-Sync"` matches this**, because the commit
        that repaired the counter explains the convention it was getting wrong.
        ⛔ **A tool that measured planning debt with a bare grep would count its
        own fix as debt** — which is why the constant is the FULL trailer and
        why this test exists rather than a comment saying so.
        """
        assert registers.planning_sync_commits(PROSE_ONLY) == 0

    def test_prose_QUOTING_the_full_trailer_is_not_counted(self) -> None:
        """🔴 **The one that shipped, and it was caught by its own commit.**

        ⛔ **Rejecting the bare word was not enough.** B-440's fix matched the
        full string *anywhere in the message*, and B-440's own commit quotes it
        while explaining D-136 — so `state-check` reported that commit as an
        unsynchronized planning correction **eight minutes after it was
        written** ([B-442](../../docs/BUGS.md)).

        ⚡ **A git trailer is `Key: value` at the START OF A LINE**, and
        anchoring there is what separates *using* a convention from *writing
        about* one. 📁 **A repository whose commits explain their own
        conventions will always contain both.**
        """
        assert registers.planning_sync_commits(QUOTES_THE_TRAILER) == 0

    def test_an_indented_quotation_is_not_counted(self) -> None:
        """⚠️ **The shape a quoted trailer usually takes** — a code block."""
        assert registers.planning_sync_commits(INDENTED_QUOTE) == 0

    def test_a_mixed_log_counts_only_the_planning_ones(self) -> None:
        """⚡ **The realistic input**: `git log --format=%B` over a range."""
        log = "\n".join(
            [ORDINARY, PLANNING, PROSE_ONLY, QUOTES_THE_TRAILER, PLANNING]
        )

        assert registers.planning_sync_commits(log) == 2

    def test_an_empty_range_is_zero_rather_than_an_error(self) -> None:
        """✅ **The ordinary state**, and it must be quiet.

        A lane with nothing unsynced is the resting position; a counter that
        raised or returned `None` here would make every caller guard for it.
        """
        assert registers.planning_sync_commits("") == 0
