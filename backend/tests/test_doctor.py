"""**A doctor that repairs is a doctor nobody can trust to report.**

TASK-410's acceptance names two properties, and both are here: *"a test that
the composite fails when any component fails"* and *"that it repairs nothing"*.

The second is the one worth a test. `state-check.py` refuses to repair because
*"every inconsistency it finds has more than one correct resolution… and
choosing between them is a governance decision, not a script's"* — and a
composite that ran the same tools in their *fixing* modes would make that
decision silently, on behalf of every tool it wraps.

**The property is checkable because repair is a flag.** `workstation.py` repairs
by default and reports under `--check`; `--force` regenerates a key pair and
invalidates every live session. So the test is not a mood — it reads the command
table and asserts what is in it.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture(scope="module")
def doctor() -> ModuleType:
    spec = importlib.util.spec_from_file_location("doctor", REPO_ROOT / "infra" / "doctor.py")
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules["doctor"] = module
    spec.loader.exec_module(module)
    return module


def test_it_repairs_nothing(doctor: ModuleType) -> None:
    """**No check may carry a flag that changes the repository.**

    `--force` invalidates every session. A bare `workstation.py` writes the two
    env files. Neither belongs in a diagnostic.
    """
    forbidden = {"--force", "--fix", "--write", "--repair", "--apply"}
    for check in doctor.CHECKS:
        assert not forbidden & set(check.command), f"{check.name} would change the repository"


def test_workstation_is_asked_to_report_not_to_repair(doctor: ModuleType) -> None:
    """`workstation.py` **repairs when run bare**, so the flag is the property.

    This is the one check in the table whose default mode writes files, which
    makes it the exact place the rule would be lost.
    """
    workstation = next(c for c in doctor.CHECKS if c.name == "workstation")
    assert "--check" in workstation.command


def test_a_failing_blocking_check_makes_the_verdict_fail(
    doctor: ModuleType, monkeypatch: pytest.MonkeyPatch
) -> None:
    """**The composite fails when any component fails.**

    Every check is forced to fail; the verdict must be 1. Testing the wiring
    rather than any single tool is the point — the doctor's whole value is that
    it cannot report ready while something it ran said otherwise.
    """
    monkeypatch.setattr(doctor, "run", lambda check: (False, "forced"))
    monkeypatch.setattr(sys, "argv", ["doctor"])
    assert doctor.main() == 1


def test_advisory_failures_alone_do_not_fail_the_verdict(
    doctor: ModuleType, monkeypatch: pytest.MonkeyPatch
) -> None:
    """**An advisory finding is reported and does not block work.**

    The distinction exists because `event-catalog` taught it: gating on a
    finding no lane can act on *"would make every lane's run red for a reason no
    lane could act on — and the cost of that is every other warning being
    skimmed."* If advisories failed the verdict, the doctor would be that.
    """
    monkeypatch.setattr(doctor, "run", lambda check: (check.blocking, "forced"))
    monkeypatch.setattr(sys, "argv", ["doctor"])
    assert doctor.main() == 0


def test_a_skipped_check_is_reported_rather_than_omitted(
    doctor: ModuleType, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """**Absence is not a pass.**

    A check left out of the default run must appear in the output saying so.
    Silently omitting it would make the verdict a stronger claim than the
    evidence supports — `missing_gates` (ADR-0032), and the defect
    `36-empty-array-checks.md` found nine times in shipped constraints.
    """
    monkeypatch.setattr(doctor, "run", lambda check: (True, ""))
    monkeypatch.setattr(sys, "argv", ["doctor"])
    doctor.main()
    out = capsys.readouterr().out
    for check in doctor.CHECKS:
        if check.skip_reason:
            assert check.name in out and "not run" in out


def test_list_runs_nothing(doctor: ModuleType, monkeypatch: pytest.MonkeyPatch) -> None:
    """`--list` must not execute a single check.

    A dry run that runs things is the failure mode that makes people stop
    trusting dry runs.
    """
    def explode(check: object) -> tuple[bool, str]:
        raise AssertionError("--list executed a check")

    monkeypatch.setattr(doctor, "run", explode)
    monkeypatch.setattr(sys, "argv", ["doctor", "--list"])
    assert doctor.main() == 0


def test_every_failure_names_a_next_command(doctor: ModuleType) -> None:
    """**A diagnostic that reports a failure without naming the next command
    has moved the search, not ended it.**"""
    for check in doctor.CHECKS:
        assert check.fix.strip(), f"{check.name} reports a failure with no way forward"
