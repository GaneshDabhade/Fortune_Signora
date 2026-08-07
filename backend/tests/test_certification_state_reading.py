"""`state-check` must read the last run that **certified**, never the last run.

The manifest records every *attempt*. A failed one is evidence about a commit
and is never deleted — `CLAUDE.md` §2 forbids rewriting a record of what was
true then. So the final entry is routinely a run that did not certify, and
three findings downstream describe the repository's certification state from
whatever `_latest_certification()` returns.

**B-137 is what that cost.** Cycle 87's `smoke` gate failed; the entry was
written with `passed: false`; `state-check` then reported *"`4d37ede` is
certified and is NOT on `main`. The cycle stopped after certification"* — when
certification was the thing that had stopped. `certification-guard.py` was
right throughout and refused the promotion. **Only the advisory view was
inverted, which is the more dangerous half: a refusal is read once, an advisory
is what a session reasons from.**

**Every manifest below is constructed.** A test asserting the live manifest
reads correctly would pass today and pass identically with the fix reverted —
the Decorative Logic §2 names.
"""

from __future__ import annotations

import importlib.util
import json
from collections.abc import Callable
from pathlib import Path
from types import ModuleType

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]


def _load_state_check() -> ModuleType:
    """Import `infra/state-check.py`, whose filename is not a Python identifier."""
    path = REPO_ROOT / "infra" / "state-check.py"
    spec = importlib.util.spec_from_file_location("state_check", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


state_check = _load_state_check()


def _run(commit: str, *, passed: bool = True, coverage: float = 95.3) -> dict[str, object]:
    return {
        "commit": commit,
        "certified_at": f"2026-08-07T00:00:0{len(commit) % 10}+00:00",
        "coverage": coverage,
        "gates": [{"name": "smoke", "passed": passed, "detail": "24 stages"}],
        "scenarios": [{"name": "baseline@1", "passed": True, "detail": "190"}],
        "tree_clean": True,
    }


Manifest = Callable[..., None]


@pytest.fixture
def manifest(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Manifest:
    """Redirect only the manifest path. `REPO_ROOT` stays real, so the predicate
    under test is `certification-guard.py`'s own — not a stub agreeing with
    itself."""

    def write(*runs: dict[str, object]) -> None:
        path = tmp_path / "manifest.json"
        path.write_text(json.dumps({"runs": list(runs)}))
        monkeypatch.setattr(state_check, "MANIFEST", path)

    return write


class TestTheLastRunIsNotTheLastCertification:
    def test_a_failed_run_after_a_passing_one_is_skipped(self, manifest: Manifest) -> None:
        manifest(_run("aaaaaaa"), _run("bbbbbbb", passed=False))

        found = state_check._latest_certification()

        assert found is not None
        assert found["commit"] == "aaaaaaa"

    def test_the_newest_passing_run_wins_when_several_pass(self, manifest: Manifest) -> None:
        manifest(_run("aaaaaaa"), _run("bbbbbbb"), _run("ccccccc", passed=False))

        found = state_check._latest_certification()

        assert found is not None
        assert found["commit"] == "bbbbbbb"

    def test_no_passing_run_is_no_certification_not_the_last_failure(
        self, manifest: Manifest
    ) -> None:
        """⛔ The case that matters most. Returning the last *failure* here is
        what produced B-137's inverted finding."""
        manifest(_run("aaaaaaa", passed=False), _run("bbbbbbb", passed=False))

        assert state_check._latest_certification() is None

    def test_an_empty_manifest_is_no_certification(self, manifest: Manifest) -> None:
        manifest()

        assert state_check._latest_certification() is None

    def test_an_absent_manifest_is_no_certification(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(state_check, "MANIFEST", tmp_path / "nothing.json")

        assert state_check._latest_certification() is None


class TestThePredicateIsTheGuardsAndNotACopy:
    """§2 — one authoritative representation. A second copy of *"did this run
    certify?"* is a second answer, and only one of them gates a promotion."""

    def test_a_failing_scenario_is_not_certified(self) -> None:
        run = _run("aaaaaaa")
        run["scenarios"] = [{"name": "baseline@1", "passed": False, "detail": ""}]

        assert state_check._satisfied(run) is False

    def test_a_dirty_tree_is_not_certified(self) -> None:
        run = _run("aaaaaaa")
        run["tree_clean"] = False

        assert state_check._satisfied(run) is False

    def test_coverage_below_the_floor_is_not_certified(self) -> None:
        assert state_check._satisfied(_run("aaaaaaa", coverage=94.9)) is False

    def test_a_run_with_every_gate_green_is_certified(self) -> None:
        assert state_check._satisfied(_run("aaaaaaa")) is True

    def test_it_delegates_rather_than_deciding(self) -> None:
        """The guard is the authority, so the two must agree on the same run —
        including on the failures this file does not enumerate."""
        guard = _load_guard()
        for run in (
            _run("aaaaaaa"),
            _run("bbbbbbb", passed=False),
            _run("ccccccc", coverage=10.0),
        ):
            expected, _ = guard._satisfied(run)

            assert state_check._satisfied(run) is bool(expected)


def _load_guard() -> ModuleType:
    """`infra/certification-guard.py`, registered in `sys.modules` **before**
    execution — its `@dataclass(slots=True)` resolves annotations through
    `sys.modules[cls.__module__]` while the class body runs."""
    import sys

    path = REPO_ROOT / "infra" / "certification-guard.py"
    spec = importlib.util.spec_from_file_location("certification_guard", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module
