"""A blocking gate stops promotion, and a status word in prose is not a status.

**[D-228](../../docs/DECISION_REGISTER.md), the product owner**, after QE
promoted while a gate was firing and after that gate turned out to be wrong.

Two defects, one ruling:

* **[B-168](../../docs/BUGS.md)** matched the *word* `VERIFIED` anywhere in a
  removed line, so a `READY` cell whose prose cited a verified row read as a
  regression. **Measured then: 12 `VERIFIED` status cells before, 12 after, no
  row changed.**
* **[B-142](../../docs/BUGS.md)'s class** — the check and the promotion sat in
  one command block with no gate between them. ⛔ *"A check whose output nobody
  is forced to read is a log line, not a gate."*

**Every case below is fixed text.** A test asserting against the live
`BACKLOG.md` would pass today and pass identically with the fix reverted.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType

REPO_ROOT = Path(__file__).resolve().parents[2]


def _load_guard() -> ModuleType:
    """`infra/certification-guard.py`, registered before execution — its
    `@dataclass(slots=True)` resolves annotations through `sys.modules`."""
    path = REPO_ROOT / "infra" / "certification-guard.py"
    spec = importlib.util.spec_from_file_location("certification_guard", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


guard = _load_guard()


def _row(task: str, status: str, extra: str = "") -> str:
    return (
        f"### {task} · a title\n\n"
        "| | |\n|---|---|\n"
        f"| **Status** | {status} |\n"
        f"{extra}"
        "\n"
    )


class TestProseCannotBecomeAStatus:
    """⛔ B-168's false positive, asserted directly."""

    def test_a_reference_to_another_rows_verified_state_is_not_this_rows_state(self) -> None:
        text = _row(
            "TASK-1",
            "✅ **`READY` — Lane C.** ✅ **Released: [TASK-1408] is `VERIFIED` "
            "and promoted at `e72b6af0`.**",
        )

        assert guard.backlog_states(text) == {"TASK-1": "READY"}

    def test_the_exact_cell_that_produced_the_false_positive_reports_no_regression(self) -> None:
        """⚡ The measured case: the row moved `SEQUENCED` -> `READY` and its
        prose names a verified row. **No `VERIFIED` state is lost.**"""
        before = _row("TASK-1", "⏸️ **`SEQUENCED`** — the shell does not exist yet")
        after = _row(
            "TASK-1",
            "✅ **`READY` — Lane C.** ✅ **[TASK-1408] is `VERIFIED` and promoted.**",
        )

        assert guard.verified_regressions(before, after) == []

    def test_a_status_word_in_a_title_or_a_note_is_ignored(self) -> None:
        text = (
            "### TASK-2 · why TASK-9 is VERIFIED and this one is not\n\n"
            "| | |\n|---|---|\n"
            "| **Status** | ✅ **`CLAIMED` — Lane A** |\n"
            "| **Evidence** | it was `VERIFIED` at `abc1234`, see the note |\n"
            "| **Reference** | `VERIFIED` rows are QE's |\n"
        )

        assert guard.backlog_states(text) == {"TASK-2": "CLAIMED"}


class TestARealRegressionStillFires:
    def test_verified_becoming_in_validation_is_reported(self) -> None:
        before = _row("TASK-3", "✅ **`VERIFIED` — QE**, at `1874df08`")
        after = _row("TASK-3", "✅ **`IN VALIDATION` — Lane A**")

        assert guard.verified_regressions(before, after) == [("TASK-3", "IN VALIDATION")]

    def test_a_verified_row_that_disappears_entirely_is_reported(self) -> None:
        before = _row("TASK-4", "✅ **`VERIFIED` — QE**")

        assert guard.verified_regressions(before, "") == [("TASK-4", "ABSENT")]

    def test_the_three_occurrences_that_prompted_b_168_would_now_be_caught(self) -> None:
        """⚡ TASK-1435 and TASK-1436, reverted by a clean rebase and promoted."""
        before = _row("TASK-1435", "✅ **`VERIFIED` — QE**") + _row(
            "TASK-1436", "✅ **`VERIFIED` (the capability) — QE**"
        )
        after = _row("TASK-1435", "✅ **`IN VALIDATION` — Lane A**") + _row(
            "TASK-1436", "🟣 **`IN VALIDATION` (the capability)** · ⏸️ **`BLOCKED`**"
        )

        assert guard.verified_regressions(before, after) == [
            ("TASK-1435", "IN VALIDATION"),
            ("TASK-1436", "IN VALIDATION"),
        ]


class TestValidRowsKeepPassing:
    def test_an_unchanged_verified_row_is_not_a_regression(self) -> None:
        text = _row("TASK-5", "✅ **`VERIFIED` — QE**, at `abc1234`")

        assert guard.verified_regressions(text, text) == []

    def test_a_row_with_no_status_cell_contributes_nothing_rather_than_guessing(self) -> None:
        """⛔ [B-169](../../docs/BUGS.md) — four rows carried their state inside
        the Module cell. **Absent must read as absent, never as a default.**"""
        text = "### TASK-6 · a title\n\n| | |\n|---|---|\n| **Module** | `x` · **Status** `SEQUENCED` |\n"

        assert guard.backlog_states(text) == {}

    def test_progressing_forward_from_verified_is_not_a_regression(self) -> None:
        before = _row("TASK-7", "✅ **`VERIFIED` — QE**")
        after = _row("TASK-7", "✅ **`PROMOTED` — QE**")

        assert guard.verified_regressions(before, after) == [("TASK-7", "PROMOTED")]


def _load_coordination() -> ModuleType:
    path = REPO_ROOT / "infra" / "coordination.py"
    spec = importlib.util.spec_from_file_location("coordination_mod", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


coordination = _load_coordination()


class TestTheLatestLifecycleStateWins:
    """⛔ **[B-163](../../docs/BUGS.md), corrected under
    [D-228](../../docs/DECISION_REGISTER.md)** — *"a stale coordination state
    must not stop a legitimately progressing implementation lane."*

    `_integration_states` reconciles two refs by lifecycle rank, so the rank
    table **is** the reconciliation. A wrong rank is a wrong answer about which
    ref is newer.
    """

    def _resolve(self, a: str, b: str) -> str:
        rank = coordination._LIFECYCLE
        return a if rank.get(a, 0) > rank.get(b, 0) else b

    def test_in_validation_beats_the_older_claimed(self) -> None:
        """⚡ The case D-228 names: `integration` says `CLAIMED`, the lane has
        legitimately progressed. **The newer state wins.**"""
        assert self._resolve("IN VALIDATION", "CLAIMED") == "IN VALIDATION"

    def test_claimed_beats_the_older_ready(self) -> None:
        assert self._resolve("CLAIMED", "READY") == "CLAIMED"

    def test_changes_requested_beats_in_validation(self) -> None:
        """🔴 **The one non-monotonic transition, and the defect.** §20e places
        `CHANGES REQUESTED` AFTER `IN VALIDATION` — QE returned the slice. Ranked
        below, a returned row read as still waiting on QE and the lane could not
        see it had to act."""
        assert self._resolve("CHANGES REQUESTED", "IN VALIDATION") == "CHANGES REQUESTED"

    def test_verified_still_outranks_changes_requested(self) -> None:
        """⛔ **The reverse case, so the fix does not let a stale return
        override a later verification.**"""
        assert self._resolve("VERIFIED", "CHANGES REQUESTED") == "VERIFIED"

    def test_a_stale_earlier_state_never_overrides_a_later_one(self) -> None:
        order = ["READY", "CLAIMED", "IN PROGRESS", "IN VALIDATION",
                 "CHANGES REQUESTED", "VERIFIED", "CERTIFIED", "PROMOTED", "DONE"]
        for index, later in enumerate(order):
            for earlier in order[:index]:
                assert self._resolve(later, earlier) == later, f"{earlier} beat {later}"

    def test_every_state_the_backlog_uses_has_a_rank(self) -> None:
        """⚠️ **An unranked state scores 0 and loses to everything** — silently."""
        for state in ("READY", "SEQUENCED", "BLOCKED", "WAITING", "CLAIMED",
                      "IN PROGRESS", "IN VALIDATION", "CHANGES REQUESTED",
                      "VERIFIED", "CERTIFIED", "PROMOTED", "DONE"):
            assert coordination._LIFECYCLE.get(state, 0) > 0, state
