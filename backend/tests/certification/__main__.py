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
    #: The gate's own output, kept **only so a failure can be diagnosed** — B-140.
    #: It never reaches the certification record: the record states *what a
    #: commit satisfied*, and a transcript of a run is not that.
    output: str = ""


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
    suite = _Outcome(passed=code == 0, detail=summarise_suite(output), output=output)

    invariant_code, invariant_output = _run(
        ["uv", "run", "pytest", "tests/security_invariants", "-q", "-p", "no:randomly"],
        cwd=BACKEND_ROOT,
    )
    invariants = _Outcome(
        passed=invariant_code == 0,
        detail=summarise_suite(invariant_output).replace("passed", "invariants"),
        output=invariant_output,
    )
    return suite, coverage_of(output), invariants


def _mypy() -> _Outcome:
    code, output = _run(["uv", "run", "mypy", "--strict", "."], cwd=BACKEND_ROOT)
    return _Outcome(passed=code == 0, detail=files_checked(output), output=output)


def _typescript() -> _Outcome:
    """`tsc --noEmit` over the frontend.

    **Added 2026-08-04, after `main` was found red** ([B-111](../../../docs/BUGS.md)).
    `CLAUDE.md` §19 lists it beside `mypy --strict` among the conditions for a
    slice to be complete — and it was in no gate QE ran, neither stage 1 nor
    certification.

    **`smoke` does not cover it.** The production image type-checks during
    `next build`, but `.dockerignore` excludes `tests/`, so an error in a test
    file is invisible to the one gate that compiles the frontend. The error that
    reached `main` was in a test file.

    > A check named in the Definition of Done and absent from every gate is a
    > check nobody performs: the lane is asked for it, QE never verifies it, and
    > certification cannot see it.
    """
    code, output = _run(["npx", "tsc", "--noEmit"], cwd=REPOSITORY_ROOT / "frontend")
    errors = len(re.findall(r"error TS\d+", output))
    return _Outcome(
        passed=code == 0,
        detail="clean" if code == 0 else f"{errors} error(s)",
        output=output,
    )


def _import_linter() -> _Outcome:
    code, output = _run(["uv", "run", "lint-imports"], cwd=BACKEND_ROOT)
    return _Outcome(passed=code == 0, detail=contracts_of(output), output=output)


def _smoke() -> _Outcome:
    started = datetime.now(UTC)
    code, output = _run(["bash", "./infra/smoke.sh"], cwd=REPOSITORY_ROOT)
    elapsed = int((datetime.now(UTC) - started).total_seconds())
    detail = f"{stage_count(output)} stages in {elapsed}s"
    if slowest := _slowest_stage(output):
        detail = f"{detail}, slowest {slowest}"
    return _Outcome(passed=code == 0, detail=detail, output=output)


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


def _load_guard() -> object | None:
    """`infra/certification-guard.py`, loaded by path because its name has a dash.

    **Registered in `sys.modules` before execution, and that is not optional.**
    The guard defines `@dataclass(slots=True)` types, and `dataclasses` resolves
    a class's own module out of `sys.modules` while processing it — so a module
    executed unregistered raises `AttributeError` on the decorator rather than
    anywhere the caller can see. `test_repository_generators.py` loads it the
    same way, which is why this matches that loader rather than inventing a
    second one.
    """
    import importlib.util

    path = REPOSITORY_ROOT / "infra" / "certification-guard.py"
    spec = importlib.util.spec_from_file_location("certification_guard", path)
    if spec is None or spec.loader is None:
        return None
    guard = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = guard
    spec.loader.exec_module(guard)
    return guard


def _plan_shortfall(recorded: set[str]) -> tuple[list[str] | None, str]:
    """What the repository says must run, against what this record contains.

    **B-131.** `validation_plan` computes the gates a change requires; this
    compares them with the gates the run actually recorded. **It reports and
    refuses nothing** — 427 step 1's discipline applied to QE's own gate set:
    measure the disagreement while everything still runs.

    Enforcing it would mean adding to `REQUIRED_GATES`, which makes every
    prior record unsatisfied because none of them executed these gates. That
    is a change to what certification *means* (ADR-0032), not one a run may
    make about itself.

    **The plan is computed, never restated here.** Two answers to "what must
    run?" would drift, and the unmaintained one would be this copy.

    Returns `(None, reason)` when the plan could not be computed at all — an
    absent measurement reported as silence is B-125's class, and this file is
    not going to be its third instance.
    """
    guard = _load_guard()
    if guard is None:
        return None, "certification-guard.py could not be loaded"

    _, base = _run(["git", "rev-parse", "--verify", "--quiet", "origin/main"], cwd=REPOSITORY_ROOT)
    if not base.strip():
        return None, "no origin/main to measure against"

    _, diffed = _run(
        ["git", "diff", "--name-only", f"{base.strip()}..HEAD"], cwd=REPOSITORY_ROOT
    )
    changed = [line for line in diffed.splitlines() if line]
    if not changed:
        # Not the same as "could not measure": a candidate level with
        # `origin/main` has nothing to plan for.
        return [], "no change against origin/main"

    plan = guard.validation_plan(changed)  # type: ignore[attr-defined]
    return sorted(set(plan.gates) - recorded), str(plan.profile)


def _report_plan_shortfall(gates: tuple[GateResult, ...]) -> None:
    missing, note = _plan_shortfall({gate.name for gate in gates})
    if missing is None:
        print(f"\n  validation plan     NOT MEASURED — {note}")
        return
    if note == "no change against origin/main":
        print("\n  validation plan     nothing changed against origin/main")
        return
    if not missing:
        print(f"\n  validation plan     {note} — every planned gate is in this record")
        return
    print(f"\n  validation plan     {note}: {len(missing)} planned gate(s) NOT recorded")
    for gate in missing:
        print(f"    · {gate}")
    print("    reported only — nothing skipped, nothing refused (B-131)")


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


#: How much of a failing gate's output to show. **Enough to carry pytest's
#: `short test summary info` block**, which is the last thing it prints and the
#: only part that names anything.
_TAIL_LINES = 40


def _report_gate_output(
    gates: list[GateResult], captured: dict[str, _Outcome]
) -> None:
    """The tail of every failing gate's own output — **B-140**.

    ⚠️ **Written after a certification failed and could not be diagnosed.**
    `pytest` recorded `3928 passed` beside a red verdict; the run that produced
    it had already been discarded, the same invocation passed on re-run, and
    there was **nothing left to read.** A gate that reports a verdict without
    the evidence forces the next step to be *"run it again and hope"*, which is
    how a flake becomes indistinguishable from a defect.

    ⛔ **It prints and never records.** The certification record states what a
    commit satisfied; a transcript of one run is not that, and putting it in the
    manifest would make an immutable evidence file grow without bound.
    """
    for gate in gates:
        if gate.passed:
            continue
        outcome = captured.get(gate.name)
        if outcome is None or not outcome.output.strip():
            print(f"\n  {gate.name} — no output was captured")
            continue
        lines = outcome.output.rstrip().splitlines()
        shown = lines[-_TAIL_LINES:]
        elided = len(lines) - len(shown)
        print(f"\n  {gate.name} — last {len(shown)} line(s)"
              + (f", {elided} elided" if elided else ""))
        for line in shown:
            print(f"    {line}")


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
    typescript = _typescript()
    print(f"  tsc --noEmit        {typescript.detail}")

    gates = [
        GateResult(name="pytest", passed=suite.passed, detail=suite.detail),
        GateResult(name="security-invariants", passed=invariants.passed, detail=invariants.detail),
        GateResult(name="mypy", passed=types.passed, detail=types.detail),
        GateResult(name="import-linter", passed=contracts.passed, detail=contracts.detail),
        GateResult(name="tsc", passed=typescript.passed, detail=typescript.detail),
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

    _report_plan_shortfall(run.gates)

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
    _report_gate_output(gates, {"pytest": suite, "security-invariants": invariants,
                                "mypy": types, "import-linter": contracts,
                                "tsc": typescript, "smoke": smoke})
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
