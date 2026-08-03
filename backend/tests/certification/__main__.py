"""`make certify` — run every gate, then record what happened.

**Orchestration, not a new test framework.** Each gate below is the one the
repository already runs; this executes them in one pass, captures each gate's own
summary, and writes a `CertificationRun`. Nothing here re-asserts a guarantee a
gate already proves — certification's contribution is the record, not a second
opinion.

Two properties make the record trustworthy rather than decorative:

**Every fact is measured here, none is passed in.** There is no flag that marks a
gate as passing, no way to supply a coverage number, and no verdict to override.
A run either executed a gate or is missing it, and a missing required gate is a
failure rather than an absence (`record.REQUIRED_GATES`).

**Failed runs are written too.** A manifest holding only successes would claim a
platform that never failed to certify. The exit code reports the verdict; the
manifest records the attempt either way.

The gates deliberately run **before** the conditions are read, so a run that
cannot even determine its own conditions — an unreleased prompt, a branched
migration head — fails loudly rather than recording a certification of a
platform that could not start.
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from tests.certification import conditions as repository_conditions
from tests.certification import database as disposable_database
from tests.certification.record import CertificationRun, GateResult, ScenarioResult
from tests.certification import attempts
from tests.certification.store import MANIFEST, append, render, report_path

BACKEND_ROOT = Path(__file__).resolve().parents[2]
REPOSITORY_ROOT = BACKEND_ROOT.parent

#: Read out of pytest's own summary line rather than counted here — the gate's
#: output is the gate's language, and a second parser would drift from it.
_PASSED = re.compile(r"(\d+) passed")
_COVERAGE = re.compile(r"Total coverage: ([\d.]+)%")
_CONTRACTS = re.compile(r"Contracts: (\d+) kept, (\d+) broken")


@dataclass(frozen=True, slots=True)
class _Outcome:
    passed: bool
    detail: str


def summarise_suite(output: str) -> str:
    """A pytest run's own count, read from its summary line.

    Extracted as a pure function because **the parsers are the part of this
    command that can be wrong quietly.** A gate that fails is loud; a gate whose
    summary silently stops matching records `no summary line` beside a passing
    run, and nobody reads a detail field on a green record.
    """
    match = _PASSED.search(output)
    return f"{match.group(1)} passed" if match else "no summary line"


def coverage_of(output: str) -> float:
    match = _COVERAGE.search(output)
    return float(match.group(1)) if match else 0.0


def contracts_of(output: str) -> str:
    match = _CONTRACTS.search(output)
    return f"{match.group(1)} kept, {match.group(2)} broken" if match else "no summary line"


def files_checked(output: str) -> str:
    match = re.search(r"no issues found in (\d+) source files", output)
    return f"strict, clean over {match.group(1)} files" if match else "no summary line"


#: Terminal colour, which `smoke.sh` writes around every stage heading.
_ANSI = re.compile(r"\x1b\[[0-9;]*m")


def stage_count(output: str) -> int:
    """How many stages the smoke gate announced.

    **Strips terminal colour first, and that is not incidental.** `smoke.sh`
    prints each heading as `\033[1m14b. …\033[0m`, so a pattern anchored to a
    digit at the start of the line matches nothing at all — which is how the
    first real certification run recorded `0 stages` beside a passing gate.
    A parser that under-reports silently is worse than one that raises.
    """
    return len(re.findall(r"^\d+[a-z]*\. ", _ANSI.sub("", output), re.MULTILINE))


def _run(command: list[str], *, cwd: Path) -> tuple[int, str]:
    result = subprocess.run(command, cwd=cwd, capture_output=True, text=True, check=False)
    return result.returncode, result.stdout + result.stderr


def _pytest() -> tuple[_Outcome, float, _Outcome]:
    """The suite, its coverage, and the Security Invariants — **one run**.

    Three facts from one execution rather than three executions: running the
    suite twice would double a two-minute gate to record a number the first run
    already produced, and the two runs could disagree.
    """
    code, output = _run(
        ["uv", "run", "pytest", "--cov", "-q", "-p", "no:randomly"], cwd=BACKEND_ROOT
    )
    suite = _Outcome(passed=code == 0, detail=summarise_suite(output))

    invariant_code, invariant_output = _run(
        ["uv", "run", "pytest", "tests/security_invariants", "-q", "-p", "no:randomly"],
        cwd=BACKEND_ROOT,
    )
    invariants = _Outcome(
        passed=invariant_code == 0,
        detail=summarise_suite(invariant_output).replace("passed", "invariants"),
    )
    return suite, coverage_of(output), invariants


def _mypy() -> _Outcome:
    code, output = _run(["uv", "run", "mypy", "--strict", "."], cwd=BACKEND_ROOT)
    return _Outcome(passed=code == 0, detail=files_checked(output))


def _import_linter() -> _Outcome:
    code, output = _run(["uv", "run", "lint-imports"], cwd=BACKEND_ROOT)
    return _Outcome(passed=code == 0, detail=contracts_of(output))


def _smoke() -> _Outcome:
    started = datetime.now(UTC)
    code, output = _run(["bash", "./infra/smoke.sh"], cwd=REPOSITORY_ROOT)
    elapsed = int((datetime.now(UTC) - started).total_seconds())
    detail = f"{stage_count(output)} stages in {elapsed}s"
    if slowest := _slowest_stage(output):
        detail = f"{detail}, slowest {slowest}"
    return _Outcome(passed=code == 0, detail=detail)


def _slowest_stage(output: str) -> str:
    """The stage that dominated the run, carried into the durable record.

    **A total cannot explain variance.** Across 28 runs the smoke gate sat
    between 104s and 193s except twice — 4830s and 1096s, both completing every
    stage. Neither was explainable afterwards, because the record kept one
    number. This puts the answer *in* the record, so the next outlier is
    diagnosed from the manifest rather than from a re-run that may not reproduce
    it.
    """
    for line in output.splitlines():
        stripped = re.sub(r"\033\[[0-9;]*m", "", line).strip()
        if match := re.match(r"^(\d+)s\s+(.+)$", stripped):
            return f"{match.group(2)} {match.group(1)}s"
    return ""


def _scenarios() -> tuple[ScenarioResult, ...]:
    """The customer journeys. **One today**, and the catalogue grows here.

    `baseline@1` traversed end to end is what `tests/ai_research_engine` proves
    against a real database: provider payload → normalization → graph →
    observations → business events → signals → score → opportunity → research
    findings → brief → stored → announced. It is named as a scenario rather than
    re-implemented, because ADR-0032 forbids a second scenario system and
    `20-provider-simulation.md` already owns the catalogue.
    """
    code, output = _run(
        ["uv", "run", "pytest", "tests/ai_research_engine", "-q", "-p", "no:randomly"],
        cwd=BACKEND_ROOT,
    )
    return (
        ScenarioResult(
            name="baseline@1 research lifecycle",
            passed=code == 0,
            detail=summarise_suite(output).replace("passed", "assertions"),
        ),
    )


def _tools() -> tuple[tuple[str, str], ...]:
    versions: list[tuple[str, str]] = [
        ("python", ".".join(str(part) for part in sys.version_info[:3]))
    ]
    for tool, command, pattern in (
        ("pytest", ["uv", "run", "pytest", "--version"], r"([\d.]+)"),
        ("mypy", ["uv", "run", "mypy", "--version"], r"([\d.]+)"),
    ):
        _, output = _run(command, cwd=BACKEND_ROOT)
        match = re.search(pattern, output)
        if match:
            versions.append((tool, match.group(1)))
    return tuple(versions)


def main() -> int:
    """Every gate, then the record. **No options**, deliberately: a mode that
    skipped a gate would produce a run that cannot certify, and a command whose
    convenient path yields worthless evidence teaches people to use it."""
    commit = repository_conditions.commit()
    with disposable_database.disposable(disposable_database.name_for(commit)) as target:
        return _certify(target)


def _certify(target: disposable_database.Disposable) -> int:
    """The gates, against a database this run created and will destroy.

    **RE-03.** Until now the target came from whatever the launching shell
    exported, and a run in a shell that exported nothing silently measured the
    shared database — recorded verbatim in an attempt log as
    `"test_database": "(unset — defaults to shared)"`. **The workstation may
    affect execution speed; it must never affect execution correctness.**
    """
    # **`os.environ`, not a dict passed to each subprocess.** Nine call sites run
    # a gate, and threading an env through each would let one be forgotten —
    # which is the exact shape of the defect this removes. It also keeps the
    # in-process readers honest: `attempts.start()` records the database name
    # from the environment, and a subprocess-only override would have made the
    # attempt log say `(unset — defaults to shared)` about a run that was
    # correctly isolated.
    os.environ.update(target.environment)
    print("certification — running every gate")
    print(f"  database            {target.name}  (created for this run, dropped afterwards)\n")

    migrated, output = _run(["uv", "run", "alembic", "upgrade", "head"], cwd=BACKEND_ROOT)
    if migrated:
        # **Before any gate, and fatal.** A suite run against an unmigrated
        # database fails in hundreds of places for one reason, and the reason is
        # the least visible line in that output.
        print(f"  migrations          FAILED\n\n{output}")
        return 1
    print("  migrations          applied to head")

    # **Before the first gate**, so an attempt that hangs, is killed or crashes
    # is still counted. `append()` below runs only after every gate, so an
    # aborted run would otherwise leave no trace in any file — which is how a
    # 22-minute hang became invisible to every metric the repository has.
    attempt = attempts.start()

    suite, coverage, invariants = _pytest()
    print(f"  pytest              {suite.detail}")
    print(f"  coverage            {coverage:.2f}%")
    print(f"  security-invariants {invariants.detail}")
    types = _mypy()
    print(f"  mypy                {types.detail}")
    contracts = _import_linter()
    print(f"  import-linter       {contracts.detail}")

    gates = [
        GateResult(name="pytest", passed=suite.passed, detail=suite.detail),
        GateResult(name="security-invariants", passed=invariants.passed, detail=invariants.detail),
        GateResult(name="mypy", passed=types.passed, detail=types.detail),
        GateResult(name="import-linter", passed=contracts.passed, detail=contracts.detail),
    ]
    smoke = _smoke()
    print(f"  smoke               {smoke.detail}")
    gates.append(GateResult(name="smoke", passed=smoke.passed, detail=smoke.detail))

    scenarios = _scenarios()
    for scenario in scenarios:
        print(f"  scenario            {scenario.name} — {scenario.detail}")

    now = repository_conditions.current()
    run = CertificationRun(
        commit=repository_conditions.commit(),
        tree_clean=repository_conditions.tree_is_clean(),
        certified_at=datetime.now(UTC),
        conditions=now,
        gates=tuple(gates),
        scenarios=scenarios,
        coverage=coverage,
        tools=_tools(),
    )

    append(run)
    report = report_path(run)
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(render(run, now))

    print(f"\nrecorded in {MANIFEST.relative_to(REPOSITORY_ROOT)}")
    print(f"report      {report.relative_to(REPOSITORY_ROOT)}")

    certified = run.certifies(now)
    # The attempt log is git-ignored, so this survives the `git checkout --`
    # that a failed run's next attempt requires — and which deletes the
    # manifest entry recording the failure.
    attempt.conclude(
        outcome="certified" if certified else "failed",
        failing_gates=tuple(gate.name for gate in run.gates if not gate.passed),
        coverage=coverage,
    )

    if certified:
        print(f"\nCERTIFIED  {run.commit[:12]}")
        return 0
    print("\nNOT CERTIFIED")
    for reason in run.failures:
        print(f"  · {reason}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
