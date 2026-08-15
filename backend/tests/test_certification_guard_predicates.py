"""The promotion guard asks two questions about a certification record, not one.

⛔ **[B-435](../../docs/BUGS.md).** `_satisfied()` was a **second implementation**
of the certification predicate whose docstring claimed parity it did not have —
*"Derived exactly as `CertificationRun.satisfied` derives it."* It checked four
of the package's five conditions. **The missing one was whether every member of
`REQUIRED_GATES` actually ran**, which is the condition the product owner changed
on 2026-08-15 when `frontend-suite` and `eslint` were added.

⚠️ **The obvious repair — make `_satisfied` strict — is wrong, and QE's first
reason for saying so was ALSO wrong.** Today's eight-gate set leaves **2** of 230
records satisfied, and QE wrote that an audit using it would refuse 209 commits
on `main`. ⛔ **Fire-tested: it does not.** `--audit-main` accepts *an ancestor of
a certified commit on `main`*, and a certified commit near the tip vouches for
everything behind it — the audit still reports the guarantee holding.

⚡ **The actual hazard is the window.** `certified_all` is **empty** whenever no
stored record satisfies the current set — precisely the state between widening
`REQUIRED_GATES` and the first run under it. **With nothing to be an ancestor of,
every non-Closeout commit on `main` becomes a violation at once.** A historical
audit whose verdict depends on a gate added this morning is not a historical
audit. **And independently, the product owner ruled it**: *"the records remain
historical records under the gate set that existed at the time."*

**So the repair is two named predicates rather than one silent one:**

| | asks | required-gate check |
|---|---|---|
| `_satisfied` | *did this run's recorded gates pass?* — **about the past** | ⛔ no, deliberately |
| `_promotable` | *may this be promoted NOW?* — **about today** | ✅ yes |

⚠️ **Every case below is a fabricated record, never the live manifest.** Asserting
that today's records behave would pass identically with both predicates deleted —
the Decorative Logic `CLAUDE.md` §2 names. **Six of these must FIRE.**
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]


def _load_guard() -> ModuleType:
    path = REPO_ROOT / "infra" / "certification-guard.py"
    spec = importlib.util.spec_from_file_location("certification_guard_predicates", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules["certification_guard_predicates"] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def guard() -> ModuleType:
    return _load_guard()


def _record(guard: ModuleType, **overrides: Any) -> dict[str, object]:
    """A record that passes everything, so a case changes exactly one thing.

    ⚡ **The gate list is built FROM `REQUIRED_GATES`, never written out.**
    A literal list here would be a fourth copy of the registry
    ([B-1001](../../docs/BUGS.md)) and — worse — it would stop tracking the set
    the moment the product owner changes it, so the day a gate is added this
    fixture would silently start testing the old world.
    """
    base: dict[str, object] = {
        "commit": "0" * 40,
        "tree_clean": True,
        "coverage": 99.0,
        "gates": [{"name": name, "passed": True} for name in sorted(guard.REQUIRED_GATES)],
        "scenarios": [{"name": "a scenario", "passed": True}],
    }
    base.update(overrides)
    return base


def test_a_complete_record_satisfies_both(guard: ModuleType) -> None:
    run = _record(guard)
    assert guard._satisfied(run) == (True, [])
    assert guard._promotable(run) == (True, [])


# ── The condition B-435 found missing ────────────────────────────────────────


def test_a_missing_required_gate_is_not_promotable(guard: ModuleType) -> None:
    """⛔ **The regression this file exists for.**

    📁 [B-122](../../docs/BUGS.md)'s scenario exactly: `frontend-suite` was absent
    from 228 runs and **absence was never a failure here**, so every one of them
    was promotable.
    """
    dropped = sorted(guard.REQUIRED_GATES)[0]
    run = _record(
        guard,
        gates=[{"name": n, "passed": True} for n in sorted(guard.REQUIRED_GATES) if n != dropped],
    )
    promotable, failures = guard._promotable(run)
    assert not promotable
    assert f"required gate '{dropped}' did not run" in failures


def test_the_same_record_still_satisfies_the_historical_question(guard: ModuleType) -> None:
    """🔴 **The case that protects `main`, and it must never be "fixed".**

    ⚠️ **The reason is not the one QE first wrote.** Making `_satisfied` strict
    does **not** break today's audit — the ancestor rule absorbs the old records,
    and that was measured rather than assumed after being asserted wrongly.

    ⛔ **It breaks the audit in the window where no record yet satisfies the new
    set** — between a widening and its first passing run — because `certified_all`
    is empty, nothing is an ancestor of anything, and **every non-Closeout commit
    on `main` is reported as a violation simultaneously.** A future session
    tempted to unify the two predicates fails here first, and this docstring is
    why it should not.
    """
    dropped = sorted(guard.REQUIRED_GATES)[0]
    run = _record(
        guard,
        gates=[{"name": n, "passed": True} for n in sorted(guard.REQUIRED_GATES) if n != dropped],
    )
    assert guard._satisfied(run) == (True, [])


def test_the_two_predicates_differ_only_on_required_gate_presence(guard: ModuleType) -> None:
    """**States the design as an assertion rather than as prose.**

    If a future change makes them differ on anything else, the difference should
    have been named — and this fails until it is.
    """
    dropped = sorted(guard.REQUIRED_GATES)[0]
    run = _record(
        guard,
        gates=[{"name": n, "passed": True} for n in sorted(guard.REQUIRED_GATES) if n != dropped],
    )
    extra = set(guard._promotable(run)[1]) - set(guard._satisfied(run)[1])
    assert extra == {f"required gate '{dropped}' did not run"}


# ── Absence is not a pass ────────────────────────────────────────────────────


MALFORMED = [
    pytest.param({"gates": None}, id="no-gates-key-at-all"),
    pytest.param({"gates": []}, id="gates-present-but-empty"),
    pytest.param({"gates": {"pytest": True}}, id="gates-is-a-dict-not-a-list"),
    pytest.param({"gates": "pytest"}, id="gates-is-a-string"),
    pytest.param({"scenarios": None}, id="no-scenarios-key-at-all"),
]


@pytest.mark.parametrize("override", MALFORMED)
def test_a_malformed_record_is_refused_rather_than_read_as_empty(
    guard: ModuleType, override: dict[str, object]
) -> None:
    """⛔ **`run.get("gates") or []` is what this replaces, and the `or []` WAS the
    defect** — a gateless record iterated zero times, produced zero failures, and
    **absence read as success.**

    📁 The empty-array class `36-empty-array-checks.md` found in nine CHECK
    constraints, and `REQUIRED_GATES`' own comment names it: *"a run recording no
    gates at all would otherwise satisfy 'every gate passed' vacuously."*
    **The package defended against it; this file did not.**

    ⚠️ **`gates: []` is in this list on purpose.** It is well-formed JSON and
    still means *nothing was measured* — `_satisfied` reads it as zero passing
    gates, so only `_promotable` catches it, which is the correct division: an
    empty record is historically uninformative but must never be promotable.

    ⚡ **Fire-tested, and the result named which case is load-bearing.** Restoring
    `or []` in `_entries` turns **only `no-scenarios-key-at-all`** red: the four
    `gates` cases are caught a second time by `_promotable`'s required-gate check,
    so they do not isolate `_entries`. ⛔ **`scenarios` has no such backstop —
    there is no `REQUIRED_SCENARIOS` — so `_entries` is the only thing standing
    between a record with no scenarios and a clean pass.** **That is the case to
    keep if this list is ever trimmed**, and it is the least obvious one.
    """
    run = _record(guard, **override)
    assert not guard._promotable(run)[0]


def test_a_non_object_entry_is_reported_not_skipped(guard: ModuleType) -> None:
    """A list holding a string is refused, not quietly filtered to the good ones.

    **Silently dropping it would make a truncated record indistinguishable from a
    complete one**, which is the same failure as `or []` wearing a tidier coat.
    """
    run = _record(guard, gates=[{"name": "pytest", "passed": True}, "eslint"])
    satisfied, failures = guard._satisfied(run)
    assert not satisfied
    assert any("not objects" in f for f in failures)


# ── The constants are imported, never restated ───────────────────────────────


def test_the_coverage_floor_comes_from_the_package(guard: ModuleType) -> None:
    """⛔ **The guard used to hardcode `95.0`.**

    📁 [B-1001](../../docs/BUGS.md)'s class: *"the copy is never wrong when
    written; it is wrong the first time the registry grows."* This asserts the
    **identity** of the constant rather than its current value — a test written
    against `95.0` would itself become the copy.
    """
    from tests.certification.record import MINIMUM_COVERAGE

    assert guard.MINIMUM_COVERAGE is MINIMUM_COVERAGE
    run = _record(guard, coverage=MINIMUM_COVERAGE - 0.01)
    satisfied, failures = guard._satisfied(run)
    assert not satisfied
    assert any(str(MINIMUM_COVERAGE) in f for f in failures)


def test_the_required_gate_set_comes_from_the_package(guard: ModuleType) -> None:
    """The guard must not hold its own idea of which gates are required.

    **A widening ruled by the product owner has to reach the promotion gate in
    the same act**, or the two disagree about what CERTIFIED means — which is
    what B-435 found.
    """
    from tests.certification.record import REQUIRED_GATES

    assert guard.REQUIRED_GATES is REQUIRED_GATES


def test_a_run_at_exactly_the_floor_passes(guard: ModuleType) -> None:
    """The boundary is `<`, not `<=`. Cycle 231 certified at 95.12% against a
    95.0 floor, and an off-by-one here would have refused a legitimate cycle."""
    from tests.certification.record import MINIMUM_COVERAGE

    assert guard._satisfied(_record(guard, coverage=MINIMUM_COVERAGE)) == (True, [])
