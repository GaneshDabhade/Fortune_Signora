"""A `VERIFIED` defect cannot be reopened by a rebase without the promotion refusing.

`verified_regressions` protects QE-written states in `BACKLOG.md`. It reads
`BUGS.md` **not at all** — `grep -c 'docs/BUGS.md"'` against
`infra/certification-guard.py` returned `0` when [B-197](../../docs/BUGS.md) was
filed. So a rebase could carry a `VERIFIED` defect back to `OPEN` and the
promotion would print **`PASS`** beside it: truthfully, about the other register.

⚡ **It is [B-232](../../docs/BUGS.md) one register over**, and the same repair —
**read the authoritative cell, never the prose around it.** `registers.bug_rows`
already does that, and `BugRow.state` already takes the *first* state token,
because *"`FIXED` — **`VERIFIED` is QE's to set**"* contains both words
([B-101](../../docs/BUGS.md)).

⚠️ **The fix as first written could not run at all.** It called `bug_rows`
without importing it, so the promotion path raised `NameError` rather than
checking anything. It survived unnoticed because QE promotes through the guard's
single-argument form and `_promote` was never exercised — **an unreachable defect
in a gate, which is the shape [B-434](../../docs/BUGS.md) had one file over.**

Every case below is fixed text, never the live register. Asserting that today's
`BUGS.md` reports nothing would pass identically with the whole check deleted —
the Decorative Logic `CLAUDE.md` §2 names. **Three of these must FIRE.**
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]

#: One row, one severity, one status — the smallest register that still parses.
#: The state is interpolated so a case changes exactly one thing.
ROW = """### B-900 · a fixture

| | |
|---|---|
| **Severity** | 🟠 |
| **Status** | {state} |

"""

VERIFIED = ROW.format(state="✅ **`VERIFIED`** — QE, 2026-08-14")


def _load_guard() -> ModuleType:
    path = REPO_ROOT / "infra" / "certification-guard.py"
    spec = importlib.util.spec_from_file_location("certification_guard_under_test", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules["certification_guard_under_test"] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def guard() -> ModuleType:
    return _load_guard()


def test_the_function_can_be_called_at_all(guard: ModuleType) -> None:
    """⛔ **The regression this file exists for first.**

    The original fix called `bug_rows` without importing it. **Loading the module
    succeeded** — the name is only resolved when the function runs — so nothing
    detected it until the promotion path was exercised. **This asserts the call,
    not the import**, because the import is one way to satisfy it and the caller
    does not care which.
    """
    assert guard.verified_bug_regressions(VERIFIED, VERIFIED) == []


REOPENED = [
    pytest.param("🔵 **`OPEN`**", "OPEN", id="reopened-to-OPEN"),
    pytest.param("**`FIXING`** — the lane", "FIXING", id="downgraded-to-FIXING"),
    pytest.param("**`FIXED`** — the lane, awaiting QE", "FIXED", id="downgraded-to-FIXED"),
]


@pytest.mark.parametrize(("state", "expected"), REOPENED)
def test_a_verified_defect_that_loses_its_state_is_reported(
    guard: ModuleType, state: str, expected: str
) -> None:
    assert guard.verified_bug_regressions(VERIFIED, ROW.format(state=state)) == [
        ("B-900", expected)
    ]


def test_a_verified_row_that_disappears_is_reported_as_ABSENT(guard: ModuleType) -> None:
    """⚠️ **A row leaving the register counts.**

    Deleting a `VERIFIED` row hides a closed defect exactly as thoroughly as
    reopening it, and **a rebase that drops a row is how B-168 happened.**
    """
    other = ROW.replace("B-900", "B-901").format(state="🔵 **`OPEN`**")
    assert guard.verified_bug_regressions(VERIFIED, other) == [("B-900", "ABSENT")]


def test_an_unchanged_register_reports_nothing(guard: ModuleType) -> None:
    assert guard.verified_bug_regressions(VERIFIED, VERIFIED) == []


def test_commentary_after_the_state_token_does_not_count_as_a_change(
    guard: ModuleType,
) -> None:
    """📁 **B-101's rule, inherited rather than re-implemented.**

    The register writes *"`FIXED` — **`VERIFIED` is QE's to set**"*, so a cell
    naming a later state has not reached it. **`BugRow.state` takes the FIRST
    token**, and this asserts that this function inherits that reading rather
    than substring-matching a second time.
    """
    wordy = ROW.format(state="✅ **`VERIFIED`** — QE, and the row mentions OPEN and FIXED in prose")
    assert guard.verified_bug_regressions(VERIFIED, wordy) == []


def test_a_row_that_was_never_verified_is_not_watched(guard: ModuleType) -> None:
    """**Only QE-written states are protected.** `FIXED` is the lane's to set and
    unset; watching it here would refuse promotions for ordinary lane work."""
    was_fixed = ROW.format(state="**`FIXED`** — the lane")
    assert guard.verified_bug_regressions(was_fixed, ROW.format(state="🔵 **`OPEN`**")) == []


def test_the_live_register_parses_and_holds_verified_rows(guard: ModuleType) -> None:
    """Guards the fixture itself.

    ⛔ **If `bug_rows` silently returned nothing, every case above would pass and
    the check would be inert.** This asserts the parser reaches the real register
    and finds states there — **without asserting a count, which would fail on the
    next promotion for the wrong reason.**
    """
    import subprocess

    text = subprocess.run(
        ["git", "show", "origin/main:docs/BUGS.md"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    ).stdout
    if not text:
        pytest.skip("origin/main not reachable in this clone")
    rows = guard.bug_rows(text)
    assert len(rows) > 100, "the register should hold far more than a hundred rows"
    assert any(row.state == "VERIFIED" for row in rows), "no VERIFIED row found to protect"
