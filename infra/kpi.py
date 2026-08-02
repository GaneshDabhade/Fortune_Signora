#!/usr/bin/env python3
"""**Engineering KPIs, derived from the repository rather than reported about it.**

Every figure here is computed from the certification manifest, git history and
the registers. **Nothing is entered by hand**, for the same reason no gate result
is: a number somebody typed is a number that stops being true quietly, and the
first person to notice is the one who trusted it.

**These measure how the process is running, never whether the software is
correct.** A short certification is not a good one, and a long one is not a bad
one — the gates decide correctness and these describe throughput. Reading them
the other way round is how a team starts optimising the measurement.

    python3 infra/kpi.py            # human-readable
    python3 infra/kpi.py --markdown # the block PROJECT_STATUS.md carries
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
from datetime import datetime
from pathlib import Path

import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from registers import bug_rows  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parent.parent
MANIFEST = REPO_ROOT / "certification" / "manifest.json"


def _git(*args: str) -> str:
    result = subprocess.run(
        ["git", *args], cwd=REPO_ROOT, capture_output=True, text=True, check=False
    )
    return result.stdout.strip() if result.returncode == 0 else ""


def _read(relative: str) -> str:
    path = REPO_ROOT / relative
    return path.read_text() if path.exists() else ""


def _runs() -> list[dict]:
    if not MANIFEST.exists():
        return []
    return json.loads(MANIFEST.read_text()).get("runs") or []


def _satisfied(run: dict) -> bool:
    gates = all(g.get("passed") for g in run.get("gates") or [])
    scenarios = all(s.get("passed") for s in run.get("scenarios") or [])
    coverage = run.get("coverage")
    floor = not isinstance(coverage, int | float) or coverage >= 95.0
    return gates and scenarios and bool(run.get("tree_clean")) and floor


def _commit_time(sha: str) -> datetime | None:
    stamp = _git("show", "-s", "--format=%cI", sha)
    try:
        return datetime.fromisoformat(stamp) if stamp else None
    except ValueError:
        return None


def certification_kpis() -> dict[str, str]:
    runs = _runs()
    passing = [r for r in runs if _satisfied(r)]
    # Timings are scoped to recent cycles. Runs from earlier days were certified
    # under a different process and closed out much later, and averaging them in
    # produces a number that describes neither.
    recent = passing[-5:]

    # Certification duration: the gates are wall-clock work, and `smoke` is the
    # only one that records its own. Everything else is inferred from the gap
    # between a certified commit and the record that names it, which is the
    # closest honest proxy the repository actually holds.
    durations: list[float] = []
    promotion_lags: list[float] = []
    for run in recent:
        commit = str(run.get("commit", ""))
        certified_at = run.get("certified_at")
        started = _commit_time(commit)
        if not (started and certified_at):
            continue
        try:
            finished = datetime.fromisoformat(str(certified_at))
        except ValueError:
            continue
        durations.append((finished - started).total_seconds() / 60)

        # Certification → Repository Ready: the gap between a run finishing and the
        # Closeout commit that records it landing on `main`.
        #
        # An earlier version of this compared every certified commit against
        # `main`'s *latest* commit, which reported 773 minutes — a number with no
        # meaning at all, since it grew every time anything was committed. A KPI
        # that drifts upward on its own teaches people to ignore the panel.
        closeout = _git(
            "log", "--format=%H %cI", "--grep=^Repository Closeout", f"{commit}..main"
        ).splitlines()
        if closeout:
            try:
                landed = datetime.fromisoformat(closeout[-1].split()[1])
                promotion_lags.append((landed - finished).total_seconds() / 60)
            except (ValueError, IndexError):
                pass

    smoke_times: list[int] = []
    for run in passing:
        for gate in run.get("gates") or []:
            if gate.get("name") == "smoke":
                match = re.search(r"(\d+)s", str(gate.get("detail", "")))
                if match:
                    smoke_times.append(int(match.group(1)))

    def mean(values: list[float], unit: str) -> str:
        return f"{sum(values) / len(values):.1f} {unit}" if values else "—"

    return {
        "Certification cycles": str(len(runs)),
        "Certified": f"{len(passing)} of {len(runs)}",
        "Mean time to certify (last 5)": mean(durations, "min"),
        "Mean smoke duration": mean([float(t) for t in smoke_times], "s"),
        "Mean certify → Ready (last 5)": mean(promotion_lags, "min"),
    }


def release_kpis() -> dict[str, str]:
    """**Release Engineering observability, derived and never reported by hand.**

    Only metrics git and the manifest can actually answer appear here. The ones
    that would need a human to type a number — time a slice spent in
    `IN VALIDATION`, changes-requested counts, rollback rate — are deliberately
    **absent rather than estimated**: a figure nobody can recompute is the thing
    this whole file exists to avoid, and an absent metric is honest where an
    invented one is not.
    """
    runs = _runs()
    passing = [r for r in runs if _satisfied(r)]

    # Release frequency and batch size, read from the gaps between certified
    # commits. `git rev-list --count` is the whole measurement: the candidate's
    # input set is exactly what lies between the last certified commit and it,
    # which is why no bookkeeping is needed to know what a release contained.
    batches: list[int] = []
    ages: list[float] = []
    previous: str | None = None
    for run in passing:
        commit = str(run.get("commit", ""))
        if previous:
            count = _git("rev-list", "--count", f"{previous}..{commit}")
            if count.isdigit():
                batches.append(int(count))
            # Candidate age: how long the oldest unreleased commit waited.
            oldest = _git("log", "--format=%cI", "--reverse", f"{previous}..{commit}")
            certified_at = run.get("certified_at")
            first = oldest.splitlines()[:1]
            if first and certified_at:
                try:
                    delta = datetime.fromisoformat(str(certified_at)) - datetime.fromisoformat(
                        first[0]
                    )
                    ages.append(delta.total_seconds() / 60)
                except ValueError:
                    pass
        previous = commit

    span = ""
    if len(passing) >= 2:
        try:
            first_at = datetime.fromisoformat(str(passing[0]["certified_at"]))
            last_at = datetime.fromisoformat(str(passing[-1]["certified_at"]))
            hours = (last_at - first_at).total_seconds() / 3600
            if hours > 0:
                span = f"{len(passing) / hours:.2f} releases/hour over {hours:.0f}h"
        except (ValueError, KeyError):
            pass

    def mean(values: list[float], unit: str) -> str:
        return f"{sum(values) / len(values):.1f} {unit}" if values else "—"

    rate = f"{100 * len(passing) / len(runs):.0f}%" if runs else "—"
    return {
        # **Named precisely, because the obvious name would lie.** This counts
        # `make certify` runs, and a candidate rejected at *validation* never
        # reaches one — so three rejected candidates during a four-cycle block
        # left this reading 100%. It is a true statement about certification and
        # a false impression of release health, which is the worse of the two.
        # **Candidate outcomes are a judgement line in Repository Health**
        # (QUALITY_ENGINEERING §10), not a figure this file can derive: nothing
        # machine-readable records a validation rejection.
        "Certification run success rate": f"{rate} ({len(passing)} of {len(runs)} runs)",
        "  ↳ excludes": "candidates rejected at validation — see Repository Health",
        "Commits per release": (
            f"mean {sum(batches) / len(batches):.1f}, median "
            f"{sorted(batches)[len(batches) // 2]}, range {min(batches)}–{max(batches)}"
            if batches
            else "—"
        ),
        "Mean candidate age": mean(ages, "min") + "  — oldest commit → certified",
        "Release frequency": span or "—",
    }


def register_kpis() -> dict[str, str]:
    bugs = _read("docs/BUGS.md")
    coordination = _read("docs/LANE_COORDINATION.md")
    backlog = _read("docs/BACKLOG.md")

    # One authority for what a row means, shared with state-check (registers.py).
    rows = bug_rows(bugs)
    # **One row, one bucket** — `BugRow.state`, not a substring search. These four
    # must sum to the number of rows, and did not until B-101.
    fixed = sum(1 for r in rows if r.state == "FIXED")
    verified = sum(1 for r in rows if r.state == "VERIFIED")
    wontfix = sum(1 for r in rows if r.state == "WONTFIX")
    still_open = sum(1 for r in rows if r.unresolved)
    by_severity = {
        marker: sum(1 for r in rows if r.severity == marker)
        for marker in ("🔴", "🟠", "🟡", "🟢")
        if any(r.severity == marker for r in rows)
    }
    open_red = sum(1 for r in rows if r.blocks_promotion)

    ready = len(re.findall(r"^### TASK-\d+", backlog, re.M))
    waiting = len(re.findall(r"^\| \*\*TASK-\d+\*\* \|", backlog, re.M))
    tasks = len(set(re.findall(r"\bTASK-(\d+)\b", backlog)))
    claimed = backlog.count("`CLAIMED`") - 1 if "`CLAIMED`" in backlog else 0

    items = len(re.findall(r"^#{2,3} C-\d+", coordination, re.M))
    closed = (
        len(re.findall(r"^#{2,3} C-\d+", coordination.split("\n## Closed")[1], re.M))
        if "\n## Closed" in coordination
        else 0
    )

    # **Unclaimed READY depth.** The leading indicator of a supply problem: when it
    # reaches zero, a lane with nothing to claim reaches for work that has no task
    # id and no agreed scope — which is exactly how one stalled on M7. It measures
    # the queue, never the plan; what belongs in the queue is the product owner's.
    ready_blocks = re.split(r"^### TASK-", backlog, flags=re.M)[1:]
    unclaimed = sum(
        1
        for block in ready_blocks
        if "`READY`" in block.split("\n\n")[0] or "`READY`" in block[:400]
    )

    return {
        "Queue depth (claimable now)": f"{unclaimed} — a lane with none reaches for undefined work",
        "Open bugs": f"{still_open} open · {fixed} fixed awaiting verification · "
        f"{verified} verified · {wontfix} won't fix",
        "Bugs by severity": " · ".join(f"{k} {v}" for k, v in by_severity.items()) or "—",
        "Open 🔴 (blocks promotion)": str(open_red),
        "Coordination items": f"{items} · {closed} closed",
        "Backlog": f"{tasks} tasks · {ready} READY · {waiting} WAITING/BLOCKED · "
        f"{max(claimed, 0)} claimed",
    }


def automation_kpis() -> dict[str, str]:
    """**How much of the governance is enforced rather than merely written.**

    Counted by what the tools actually assert, not by what they intend to. The
    denominator is deliberately the rules a machine *could* check — a rule like
    *"the backlog's order is the product owner's judgement"* is not in it, because
    a script asserting priority would be inventing authority.
    """
    checks = 0
    for script in ("infra/state-check.py", "infra/certification-guard.py", "infra/doc-drift.py"):
        checks += _read(script).count("findings.append") + _read(script).count("REFUSED")
    invariants = _git("grep", "-c", "security_invariant", "--", "backend/tests/security_invariants")
    files = len([line for line in invariants.splitlines() if line])
    return {
        "Governance checks, executable": str(checks),
        "Security Invariant files": str(files),
        "Gate commands": "make test · smoke · dr · certify · certified · state-check · doc-drift · kpi",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--markdown", action="store_true")
    args = parser.parse_args()

    sections = {
        "Certification": certification_kpis(),
        "Release flow": release_kpis(),
        "Defects and queues": register_kpis(),
        "Automation": automation_kpis(),
    }

    if args.markdown:
        print("| Indicator | Value |")
        print("|---|---|")
        for section, values in sections.items():
            print(f"| **{section}** | |")
            for key, value in values.items():
                print(f"| {key} | {value} |")
        print()
        print(
            "*Generated by `make kpi`. Every figure is derived from the certification "
            "manifest, git history and the registers — none is entered by hand.*"
        )
        return 0

    for section, values in sections.items():
        print(f"\n  {section}")
        for key, value in values.items():
            print(f"    {key:<32} {value}")
    print(
        "\n  These measure how the process runs, never whether the software is correct.\n"
        "  A short certification is not a good one; the gates decide that."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
