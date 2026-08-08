#!/usr/bin/env python3
"""**Refuse a promotion whose target commit was not itself certified.**

`CLAUDE.md` §20e, *Certification is attached to a commit, never to a branch*:

    promoted commit SHA  ==  certified commit SHA

**This is the enforcement, not the reminder.** The rule it protects cannot be
kept by care alone: `git merge --ff-only integration` promotes whatever the
branch points at *when the command runs*, and a lane pushing during
certification silently substitutes an uncertified commit for the certified one.
Nothing about that failure is visible afterwards — `main` looks exactly the
same either way — which is precisely why it needs a machine.

**Unlike `state-check.py`, this exits non-zero and means it.** It is a gate,
not an advisory: a repository invariant that reported and shrugged would be
Decorative Logic (§2).

    python3 infra/certification-guard.py <sha>   # may this commit be promoted?
    python3 infra/certification-guard.py         # is `main`'s head certified?
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import json
import re
import subprocess
import sys
import tomllib
from pathlib import Path
from typing import Final

REPO_ROOT = Path(__file__).resolve().parent.parent
MANIFEST = REPO_ROOT / "certification" / "manifest.json"
MIGRATIONS = REPO_ROOT / "backend" / "migrations" / "versions"

# The guarantee starts here. Commits promoted before the commit-binding rule was
# ratified were certified as *trees* under the previous reading; they are not
# retrospectively defective, and pretending the rule always held would be
# rewriting a record of what was true then (§2). `--audit-main` walks forward
# from this commit and no further back.
# `e44819b` is `main`'s head at the moment of ratification: every commit promoted
# *after* it must satisfy the rule. Set here rather than at the certified commit
# of this cycle because that SHA cannot exist until this file is committed — the
# same self-reference that makes a Closeout commit uncertifiable.
RULE_RATIFIED_AT = "e44819b89352c4f1f800f665b53501cad6cc2f45"

# A Closeout commit cannot be certified: a certification record cannot contain
# its own commit hash, so the commit that *writes* the record is always created
# after the run it records. Rather than pretend otherwise, the exception is
# bounded and machine-checked — a Closeout commit may touch **only** these paths,
# none of which can change what the software does.
CLOSEOUT_PATHS = ("certification/", "docs/", "PROJECT_STATUS.md", "README.md", "CLAUDE.md")
CLOSEOUT_SUFFIXES = (".md", ".json")


def _git(*args: str) -> str:
    result = subprocess.run(
        ["git", *args], cwd=REPO_ROOT, capture_output=True, text=True, check=False
    )
    return result.stdout.strip() if result.returncode == 0 else ""


def _behind_origin() -> list[tuple[str, int]]:
    """Which shared branches this clone holds an older answer for than `origin` does.

    **A fetch updates `origin/integration`; it does not move `integration`.** QE
    fetches constantly — the gatekeeper loop does nothing else — and
    fast-forwards the local branch only when a cycle begins, so between cycles
    the local ref is routinely behind by exactly the commits worth asking about.

    Only *behind* counts. A local branch ahead of `origin` is a promotion not yet
    pushed, which is a normal intermediate state and not a stale answer.
    """
    behind: list[tuple[str, int]] = []
    for ref in ("main", "integration"):
        if not _git("rev-parse", "--verify", "--quiet", f"origin/{ref}"):
            continue  # no remote-tracking ref: nothing to compare against
        count = _git("rev-list", "--count", f"{ref}..origin/{ref}")
        if count.isdigit() and int(count):
            behind.append((ref, int(count)))
    return behind


def _migration_head(commit: str | None = None) -> str | None:
    """The highest migration revision — **in the tree being asked about.**

    **Reading the working tree is right for *"is `main` certified?"* and wrong
    for *"may this commit be promoted?"***, and until 2026-08-04 it did the
    former in both cases.

    A promotion is by definition performed while standing on the *old* `main`,
    so a candidate that adds a migration is compared against a head it has not
    reached yet, and the guard refuses it. **It therefore refused exactly the
    commits it should scrutinise most carefully** — hit twice in one day, the
    first migration-bearing promotions since the check was written
    ([B-110](../docs/BUGS.md)).

    **The expiry rule it enforces is unchanged and must stay**: a record has
    stopped describing a repository once the conditions it names have moved. The
    correction is only *which* tree counts as the repository — for a promotion
    decision, it is the commit being promoted.
    """
    if commit is None:
        heads = sorted(p.name.split("_")[0] for p in MIGRATIONS.glob("[0-9]*_*.py"))
        return heads[-1] if heads else None
    listed = _git("ls-tree", "--name-only", commit, f"{MIGRATIONS.relative_to(REPO_ROOT)}/")
    names = [
        Path(line).name.split("_")[0]
        for line in listed.splitlines()
        if line.strip().endswith(".py") and Path(line).name[:1].isdigit()
    ]
    return sorted(names)[-1] if names else None


def _runs() -> list[dict[str, object]]:
    """Every certification run this repository holds, from wherever it holds it.

    **A commit never contains its own certificate**: the record naming commit `C`
    is written after `C` exists, so it lands in a later commit — usually on
    `integration`, reaching `main` only at Closeout. Reading the working tree
    alone therefore reports a freshly promoted commit as uncertified for exactly
    as long as it takes to write the records, which is the window in which
    somebody would most want to ask.

    So the manifest is read from the tree **and** from every ref that has one,
    and the runs are unioned on their commit. This cannot invent a certification
    — every run still carries its own gates, and `_satisfied` re-derives the
    verdict from them.
    """
    sources: list[str] = []
    if MANIFEST.exists():
        sources.append(MANIFEST.read_text())
    for ref in ("main", "integration", "HEAD"):
        content = _git("show", f"{ref}:certification/manifest.json")
        if content:
            sources.append(content)

    seen: dict[str, dict[str, object]] = {}
    for source in sources:
        try:
            runs = json.loads(source).get("runs") or []
        except json.JSONDecodeError:
            continue
        for run in runs:
            key = f"{run.get('commit')}|{run.get('certified_at')}"
            seen.setdefault(key, run)
    return list(seen.values())


def _satisfied(run: dict[str, object]) -> tuple[bool, list[str]]:
    """Derived exactly as `CertificationRun.satisfied` derives it, and for the
    same reason: an outcome field could disagree with the facts beside it."""
    failures: list[str] = []
    for gate in run.get("gates") or []:
        if not gate.get("passed"):
            failures.append(f"gate '{gate.get('name')}' failed")
    for scenario in run.get("scenarios") or []:
        if not scenario.get("passed"):
            failures.append(f"scenario '{scenario.get('name')}' failed")
    if not run.get("tree_clean"):
        failures.append("the working tree was dirty, so the tree certified was never stored")
    coverage = run.get("coverage")
    if isinstance(coverage, int | float) and coverage < 95.0:
        failures.append(f"coverage {coverage}% is below 95.0%")
    return not failures, failures


def _is_ancestor(candidate: str, descendant: str) -> bool:
    return (
        subprocess.run(
            ["git", "merge-base", "--is-ancestor", candidate, descendant],
            cwd=REPO_ROOT,
            capture_output=True,
        ).returncode
        == 0
    )


def _is_closeout(commit: str) -> tuple[bool, list[str]]:
    """Whether a commit changes nothing executable.

    **Not a judgement about intent — a fact about paths.** A commit calling
    itself a Closeout in its message while touching `backend/modules/` is
    exactly what this refuses to accept.
    """
    changed = [line for line in _git("show", "--name-only", "--format=", commit).splitlines() if line]
    offending = [
        path
        for path in changed
        if not (path.startswith(CLOSEOUT_PATHS) and path.endswith(CLOSEOUT_SUFFIXES))
    ]
    return (not offending and bool(changed)), offending


# ── Repository impact, reported and never applied ─────────────────────────────
#
# TASK-414, step 1 of `docs/architecture/427-impact-based-validation.md`.
#
# **This reports. It skips nothing.** `REQUIRED_GATES` stays a frozenset of six,
# `make certify` keeps no options, and every gate still runs. The whole value is
# evidence: **weeks of runs in which the computed profile can be compared against
# a full one that actually happened.** If the classifier disagrees with reality
# even once, the framework is not ready — and finding that out costs nothing,
# because everything ran anyway.
#
# **It extends this file's classifier rather than adding a second one.**
# `_is_closeout` and `--audit-main` already decide by path, and two classifiers
# would eventually disagree — with the unmaintained one deciding what to skip.

#: Ordered, because the first match wins and the dangerous ones must be first.
#: **Gate paths are matched before anything else**: `infra/`, the `Makefile` and
#: the certification package decide what a gate *means*, so a change to one is
#: platform-impacting whatever else it looks like. B-014 is what that costs when
#: it is not enforced — a gate fix classified as a Closeout.
IMPACT_RULES: Final = (
    ("platform", ("infra/", "Makefile", "backend/tests/certification/")),
    ("security", ("backend/signora_platform/auth/", "backend/tests/security_invariants/")),
    ("platform", ("backend/signora_platform/",)),
    ("persistence", ("backend/migrations/",)),
    ("frontend", ("frontend/",)),
)

#: Checked after the prefix rules, because these are properties of a path
#: anywhere in the tree rather than of a directory.
IMPACT_CONTAINS: Final = (
    ("security", ("tenancy_policy.py", "policy.csv")),
    ("event", ("domain/events.py",)),
    ("contract", ("/public/", "apps/api/composition/")),
    ("prompt", ("/prompts/", "/evaluation/")),
)

#: ══════════════════════════════════════════════════════════════════════════
#: **Which Playwright journeys a change must run** — [D-114](../docs/DECISION_REGISTER.md).
#:
#: **Deterministic, so journey selection is not a developer's judgement call.**
#: The directive asked Product Office to *"define the dependency mapping so this
#: selection becomes deterministic rather than relying on developer
#: judgement"*, and this is that mapping.
#:
#: ⚡ **It lives here rather than in a new file, and the reason is written 40
#: lines above**: *"would eventually disagree — with the unmaintained one
#: deciding what to skip."* A second impact map is exactly that failure, and a
#: journey map is an impact map.
#:
#: **Ordered; first match wins; the widest rules come first.** A change to
#: shared UI infrastructure selects every journey that consumes it, which is
#: what the directive requires for the Design System, App Shell, Navigation,
#: Routing, Workspace and Shared Components.
JOURNEY_RULES: Final = (
    # ⚠️ **Shared infrastructure selects everything.** These are the paths the
    # directive names, and a change to any of them reaches every screen.
    ("__all__", ("frontend/components/ui/", "frontend/components/shell/",
                 "frontend/app/layout.tsx", "frontend/app/(app)/layout.tsx",
                 "frontend/lib/query/", "frontend/lib/state/", "frontend/lib/api/")),
    # Authentication reaches every journey that signs in — which is all of them —
    # so it is also `__all__` rather than only `auth-journey`.
    ("__all__", ("frontend/app/(auth)/", "frontend/lib/auth")),
    ("commercial-profile", ("frontend/components/commercial/",)),
    ("connections", ("frontend/components/integrations/",)),
    ("workflow", ("frontend/components/intelligence/",)),
    ("daily-usage", ("frontend/components/timeline/",)),
    ("permissions.member", ("frontend/components/team/", "frontend/components/workspace/")),
    ("confidence", ("frontend/components/feedback/",)),
    # ── Route-level rules. **Without these, every screen render falls through
    # to the widen-default and selection never narrows** — safe, and useless.
    # Found by testing the map rather than by reading it: an Account 360 render
    # selected `__all__`.
    ("daily-usage", ("frontend/app/(app)/accounts/",)),
    ("business-setup", ("frontend/app/(app)/business/",)),
    ("permissions.member", ("frontend/app/(app)/settings/", "frontend/app/(app)/join/")),
)

#: **Journeys every frontend change runs, whatever else is selected.**
#: The same shape as `ALWAYS` below and for the same reason: a computation that
#: could reason its way out of the golden journey has inverted its purpose.
JOURNEYS_ALWAYS: Final = frozenset({"golden-journey", "accessibility"})


def journeys_for(paths: list[str]) -> frozenset[str]:
    """Which Playwright specs a change must run before integration.

    ⛔ **An unrecognised `frontend/` path selects every journey, never none.**
    Identical to `_impacts`'s rule that an unrecognised path is `platform`:
    **a new directory must not silently reduce validation.** The failure mode
    of getting this wrong is a journey that stops running and nobody noticing,
    which is strictly worse than running too many.

    **Returns an empty set when nothing under `frontend/` changed** — a
    backend-only slice has no journey to run, and saying so is not a reduction.
    """
    touched = [p for p in paths if p.startswith("frontend/")]
    if not touched:
        return frozenset()
    selected: set[str] = set(JOURNEYS_ALWAYS)
    for path in touched:
        for journey, prefixes in JOURNEY_RULES:
            if path.startswith(prefixes):
                if journey == "__all__":
                    return frozenset({"__all__"})
                selected.add(journey)
                break
        else:
            # Unrecognised frontend path — widen rather than narrow.
            return frozenset({"__all__"})
    return frozenset(selected)


#: **Every executable profile carries these, and no computation removes one.**
#: `CLAUDE.md` §11: a Security Invariant failure means a guarantee the
#: architecture depends on has stopped holding. A framework that could reason
#: its way out of them would have inverted their purpose.
ALWAYS: Final = frozenset({"state-check", "doc-drift", "security-invariants"})

PROFILE_GATES: Final = {
    "documentation": frozenset({"state-check", "doc-drift"}),
    "frontend": ALWAYS | {"tsc", "eslint", "frontend-suite", "accessibility", "reachability"},
    "prompt": ALWAYS | {"pytest", "mypy", "prompt-evaluation"},
    "module": ALWAYS | {"pytest", "mypy", "import-linter", "reachability", "runtime-composition"},
    "contract": ALWAYS | {"pytest", "mypy", "import-linter", "smoke", "runtime-composition"},
    "event": ALWAYS | {"pytest", "mypy", "import-linter", "event-catalog", "runtime-composition"},
    "persistence": ALWAYS | {"pytest", "mypy", "migration-reversibility", "smoke", "dr"},
    "security": ALWAYS | {"pytest", "mypy", "import-linter", "tsc", "smoke", "dr"},
    "platform": ALWAYS | {"pytest", "mypy", "tsc", "eslint", "import-linter", "smoke", "dr",
                          "frontend-suite", "migration-reversibility", "event-catalog",
                          "reachability", "runtime-composition", "prompt-evaluation"},
}


def _impacts(paths: list[str]) -> dict[str, set[str]]:
    """Which impacts a set of changed paths carries, and which path caused each.

    **An unrecognised path is `platform`, never `none`.** A new directory must
    not silently reduce validation — that is how the matrix goes wrong without
    anybody editing it, and it is the `missing_gates` rule applied to
    classification rather than to execution.
    """
    found: dict[str, set[str]] = {}
    for path in paths:
        hits = {
            impact
            for impact, prefixes in IMPACT_RULES
            if path.startswith(prefixes)
        } | {
            impact
            for impact, needles in IMPACT_CONTAINS
            if any(n in path for n in needles)
        }
        if path.startswith("backend/modules/"):
            hits.add("module")
        # **Documentation is decided by the test `_is_closeout` already uses**,
        # not by a second list. The first real run of this analysis classified
        # `CLAUDE.md` as `platform` — it is not under `docs/` — while
        # `_is_closeout` classified the same file as non-executable. **Two
        # classifiers in one file, disagreeing on their first disagreement.**
        # That is the exact failure this design was written to avoid, so the
        # rule is shared rather than restated.
        if not hits and path.startswith(CLOSEOUT_PATHS) and path.endswith(CLOSEOUT_SUFFIXES):
            hits = {"documentation"}
        if not hits:
            hits = {"platform"}
        for impact in hits:
            found.setdefault(impact, set()).add(path)
    return found


def _profile(impacts: set[str]) -> tuple[str, frozenset[str]]:
    """The profile a change would compute to, and the gates it names.

    **Union, never intersection.** A slice touching two areas gets both sets —
    stated because the opposite is the single easiest bug to write here.
    """
    if not impacts:
        return "documentation", PROFILE_GATES["documentation"]
    gates: frozenset[str] = frozenset()
    for impact in impacts:
        gates |= PROFILE_GATES.get(impact, PROFILE_GATES["platform"])
    name = "platform" if "platform" in impacts else "+".join(sorted(impacts))
    return name, gates


@dataclass(frozen=True, slots=True)
class ValidationPlan:
    """What must run before a change is handed to QE.

    **A typed record rather than a dict**: the first version returned
    `dict[str, object]` and every reader needed a cast, which is a shape that
    invites a reader to guess. `CLAUDE.md` §2 — *types should make incorrect
    architecture impossible* — applies to a plan somebody executes.
    """

    paths: int
    impacts: dict[str, list[str]]
    profile: str
    gates: list[str]
    journeys: list[str]

    @property
    def every_journey(self) -> bool:
        return self.journeys == ["__all__"]


def validation_plan(paths: list[str]) -> ValidationPlan:
    """**The complete validation plan for a set of changed paths** — [D-115](../docs/DECISION_REGISTER.md).

    > *"The implementation lane should no longer decide which validations to
    > execute. The repository should compute that plan."*

    **One function over the pieces that already existed.** `_impacts` classified
    paths and `PROFILE_GATES` named gates before this directive; `journeys_for`
    was added by [D-114](../docs/DECISION_REGISTER.md). **What was missing was a
    single entry point that answers *"what must I run before handing this
    over?"* in one call** — so this composes rather than computes, and adding a
    future validation means adding it to `PROFILE_GATES`, not here.

    ⛔ **Union, never intersection**, inherited from `_profile` — *the single
    easiest bug to write here.*

    ⛔ **And unknown always widens.** An unrecognised path is `platform`; an
    unrecognised `frontend/` path is every journey. **A plan that shrinks
    because nobody classified a new directory is the `missing_gates` failure
    wearing a planner's clothes.**
    """
    found = _impacts(paths)
    name, gates = _profile(set(found))
    journeys = journeys_for(paths)
    return ValidationPlan(
        paths=len(paths),
        impacts={k: sorted(v) for k, v in sorted(found.items())},
        profile=name,
        gates=sorted(gates),
        journeys=["__all__"] if "__all__" in journeys else sorted(journeys),
    )


def _report_plan(rev_range: str) -> int:
    """`--plan` — what a lane must run before handing work to QE."""
    paths = sorted({p for p in _git("diff", "--name-only", rev_range).splitlines() if p})
    if not paths:
        print("validation plan: nothing changed in that range.")
        return 0
    plan = validation_plan(paths)
    print("")
    print(f"  VALIDATION PLAN — {plan.paths} changed path(s), {rev_range}")
    print(f"  profile: {plan.profile}")
    print("")
    print("  Impacts")
    for impact, causes in plan.impacts.items():
        shown = ", ".join(causes[:2]) + (f" (+{len(causes) - 2})" if len(causes) > 2 else "")
        print(f"    {impact:<14} {shown}")
    print("")
    print(f"  Gates ({len(plan.gates)})")
    for gate in plan.gates:
        print(f"    {gate}")
    js = plan.journeys
    print("")
    print(f"  Playwright journeys ({'ALL' if plan.every_journey else len(js)})")
    if plan.every_journey:
        print("    every journey — shared infrastructure or an unmapped path")
    elif not js:
        print("    none — nothing under frontend/ changed")
    else:
        for j in js:
            print(f"    {j}")
    print("")
    print("  Run these, and they must pass, BEFORE handing work to QE")
    print("  (CLAUDE.md §19 · ENGINEERING_LAWS.md L-15 gate 8 · D-114)")
    print("  ⛔ This plan is computed, not chosen. Unknown paths widen it,")
    print("     never narrow it.\n")
    return 0


def _report_impact(rev_range: str) -> None:
    """Print the impact analysis. **Changes nothing about what runs.**"""
    paths = sorted({p for p in _git("diff", "--name-only", rev_range).splitlines() if p})
    if not paths:
        return
    found = _impacts(paths)
    name, gates = _profile(set(found))
    print(f"\n  Repository impact — {len(paths)} path(s)")
    for impact in sorted(found):
        causes = sorted(found[impact])
        shown = ", ".join(causes[:2]) + (f" (+{len(causes) - 2})" if len(causes) > 2 else "")
        print(f"    {impact:<14} {shown}")
    print(f"\n  Profile that WOULD apply: {name}")
    print(f"  Gates it names ({len(gates)}): {', '.join(sorted(gates))}")
    missing = ALWAYS - gates
    if missing:  # Unreachable by construction; a guard that cannot fail is
        # documentation pretending to be code, so it reports rather than asserts.
        print(f"  REFUSED — profile omits {sorted(missing)}, which is never permitted.")
    print(
        "\n  Reported only. Nothing is skipped, REQUIRED_GATES is unchanged, and"
        "\n  `make certify` still has no options (TASK-414 — step 1 of 427).\n"
    )


# A claim commit is the one thing a feature lane may push to `integration`, so it
# is bounded to the two registers. Anything else in it is code arriving on a
# shared branch without a gate.
CLAIM_PATHS = ("docs/ACTIVE_ASSIGNMENTS.md", "docs/BACKLOG.md")


def _eligible_above(commit: str, lane: str, task: str) -> list[str]:
    """`READY` tasks in this lane's modules that outrank `task` in the backlog.

    **Phase 1 of the execution-queue migration** (`docs/architecture/434-...`).
    §20e has always required *"if the highest `READY` task cannot be taken, say
    why in its backlog note and take the next"* — **and nothing checked it.**
    Lane A skipped a returned slice on 2026-08-05 and recorded no reason; the
    skip was correct and the silence was not.

    **Order is the backlog's own order**, because *"the queue order **is** the
    priority"*. Ownership is joined from `modules.toml`, so this asks the
    registry rather than restating it (D-062).
    """
    # **Read at the commit, never from the working tree.** The first run of this
    # check judged four claims from 2026-08-02 against today's queue and accused
    # all four — of skipping tasks that did not exist when they were made. **A
    # record of what was true then must not be re-scored against now**
    # (`CLAUDE.md` §2), and a guard that manufactures violations is worse than
    # no guard, because somebody has to disprove each one.
    #
    # It also makes history self-limiting: `modules.toml` did not exist before
    # 2026-08-04, so a claim older than the registry yields no opinion at all.
    try:
        registry = tomllib.loads(_git("show", f"{commit}:docs/coordination/modules.toml"))
    except (tomllib.TOMLDecodeError, ValueError):
        return []          # **No registry at that commit, no opinion.**
    mine = {
        m for m, e in registry.items()
        if isinstance(e, dict) and e.get("current_owner") == lane
    }
    if not mine:
        return []
    backlog = _git("show", f"{commit}:docs/BACKLOG.md")
    above: list[str] = []
    for block in re.split(r"(?=^### TASK-)", backlog, flags=re.M):
        header = re.match(r"### (TASK-\d+)", block)
        if not header:
            continue
        if header.group(1) == task:
            break          # Everything after this point ranks lower.
        status = re.search(r"\*\*Status\*\*\s*\|\s*(.+)$", block, re.M)
        if not status or "`READY`" not in status.group(1):
            continue
        module = re.search(r"\*\*Module\*\*\s*\|\s*(.+)$", block, re.M)
        if module and any(f"`{m}`" in module.group(1) for m in mine):
            above.append(header.group(1))
    return above


def _claim_commits(rev_range: str) -> list[str]:
    return _git("rev-list", "--reverse", rev_range, "--grep=^Claim TASK-").splitlines()


def _scope_note() -> None:
    """Say what this clone could not see, and carry on.

    **An audit reports what it examined; `--next-cycle` decides.** Refusing an
    audit for staleness would be actively wrong during a cycle: `integration`
    moves while QE certifies *by design*, and the snapshot rule forbids chasing
    it. So the audits name the gap and proceed — the finding they might miss is
    on a commit that belongs to the next cycle anyway.
    """
    for ref, count in _behind_origin():
        print(f"  note — {count} commit(s) on `origin/{ref}` are not in this clone's `{ref}`.\n")


def _unexplained_skips(commit: str) -> list[tuple[str, str, str, list[str]]]:
    """A claim that took lower-ranked work without naming what it passed over.

    **Phase 1 enforcement, and it reports rather than refuses.** The skip Lane A
    made on 2026-08-05 was *correct* — the task it passed over was blocked on two
    rulings — and the record was what was missing. **This makes the silence
    visible; it does not second-guess the choice.**

    A skip is explained if the passed-over task is named anywhere in the commit,
    message or diff. **Naming it is the whole requirement** — the reason belongs
    in the backlog note, where a human will read it.
    """
    subject = _git("log", "-1", "--format=%s", commit)
    task = re.search(r"TASK-\d+", subject)
    body = _git("show", "--format=%B", commit)
    # **The claiming lane comes from the board row this commit *added*, never
    # from the text anywhere in it.** Searching `body` for `**Lane X**` searched
    # the diff too, and a claim's diff quotes other lanes constantly — Lane C's
    # TASK-900 claim explains that *Lane B skipped this row and was right to*,
    # so the guard read `Lane B`, joined Lane B's eleven modules, and accused
    # the claim of skipping `TASK-203`. **A guard that manufactures violations
    # is worse than no guard**, which this function's own docstring says about
    # the last time it did this.
    #
    # An added `| **Lane X** |` cell is the claim asserting who it is, in the
    # one file that is authoritative about execution. Nothing else qualifies.
    lane = re.search(r"^\+\|\s*\*\*(Lane [A-Z])\*\*\s*\|", body, re.M)
    if not task or not lane:
        return []
    above = [t for t in _eligible_above(commit, lane.group(1), task.group(0)) if t not in body]
    return [(commit[:7], subject, task.group(0), above)] if above else []


#: **The one path a planning-synchronization commit may touch** — C-435.
#:
#: ⛔ **Narrower than `CLAIM_PATHS` by one file, deliberately.** A claim commit
#: may touch `ACTIVE_ASSIGNMENTS.md` because a claim *is* an assignment. A
#: planning commit may not: that file is the arbitration point where two lanes
#: contend, and a Product Office write there could overwrite a lane's claim —
#: which is `D-123`'s prohibition and a mistake this office has already made
#: once, on `TASK-458`.
PLANNING_PATHS = ("docs/BACKLOG.md",)


def _audit_planning() -> int:
    """Every planning commit on `integration` touches `BACKLOG.md` and nothing else.

    ⚡ **Built for C-435 and unused until the product owner rules on it.**
    **The deadlock it would end**: `CLAUDE.md` §20e says *"only executable
    change opens a cycle"*, and `D-136` says a planning correction is
    *"high-priority synchronization"* — the second orders corrections *within*
    a cycle and the first decides whether a cycle happens, so neither can start
    one. **When a lane is idle there is by definition no executable change
    coming, therefore no cycle, therefore the correction that would unblock the
    lane cannot land.**

    ⛔ **This function grants nothing.** It is the *check* that would make the
    grant safe, written ahead of the decision so that ruling on C-435 costs one
    word rather than one cycle. **`BACKLOG.md` is already classified
    non-executable by this file's own `CLOSEOUT_PATHS`, and a test asserts the
    two classifiers agree on it** — so a planning commit provably changes
    nothing the certification model protects.
    """
    _scope_note()
    commits = [
        line.split()[0]
        for line in _git("log", "--format=%H %s", "main..integration").splitlines()
        if "Planning-Sync" in _git("log", "-1", "--format=%B", line.split()[0])
    ] if _git("rev-parse", "--verify", "integration") else []
    if not commits:
        print("audit — no planning-synchronization commits to check.")
        return 0

    violations: list[tuple[str, str, list[str]]] = []
    for commit in commits:
        changed = [
            line
            for line in _git("show", "--name-only", "--format=", commit).splitlines()
            if line
        ]
        offending = [path for path in changed if path not in PLANNING_PATHS]
        if offending:
            violations.append(
                (commit[:7], _git("log", "-1", "--format=%s", commit), offending)
            )

    print(f"audit — {len(commits)} planning commit(s)\n")
    if not violations:
        print(
            "  every one touches only BACKLOG.md.\n\n"
            "⛔ Never ACTIVE_ASSIGNMENTS.md — that is the arbitration point, and a\n"
            "Product Office write there could overwrite a lane's claim (D-123)."
        )
        return 0

    print(f"REFUSED — {len(violations)} planning commit(s) carried more than planning:\n")
    for short, subject, offending in violations:
        print(f"  · {short}  {subject}")
        for path in offending[:5]:
            print(f"      also changed {path}")
    return 1


def _audit_claims() -> int:
    """Every claim commit on `integration` touches the registers and nothing else."""
    _scope_note()
    commits = _claim_commits("main..integration") + _claim_commits(
        f"{RULE_RATIFIED_AT}..main"
    )
    if not commits:
        print("audit — no claim commits to check.")
        return 0

    violations: list[tuple[str, str, list[str]]] = []
    skips: list[tuple[str, str, str, list[str]]] = []
    for commit in commits:
        changed = [
            line
            for line in _git("show", "--name-only", "--format=", commit).splitlines()
            if line
        ]
        offending = [path for path in changed if path not in CLAIM_PATHS]
        if offending:
            violations.append((commit[:7], _git("log", "-1", "--format=%s", commit), offending))
        skips.extend(_unexplained_skips(commit))

    print(f"audit — {len(commits)} claim commit(s)\n")
    if skips:
        # **Reported, not refused** — phase 1 of 434 is observation. A guard
        # that starts by rejecting history teaches people to bypass it; this
        # names the gap and lets the next claim close it.
        print(f"  {len(skips)} claim(s) took work below a higher `READY` task in the same lane,")
        print("  without saying why. §20e: *say why in its backlog note and take the next.*\n")
        for short, subject, task, above in skips:
            print(f"    · {short}  {subject[:56]}")
            print(f"        claimed {task}, skipped {', '.join(above[:4])}")
        print()
    if not violations:
        print(
            "  every one touches only ACTIVE_ASSIGNMENTS.md and BACKLOG.md.\n\n"
            "A claim is the one thing a feature lane may push to `integration`, and\n"
            "none of them carried anything else."
        )
        return 0

    print(f"REFUSED — {len(violations)} claim commit(s) carried more than a claim:\n")
    for short, subject, offending in violations:
        print(f"  · {short}  {subject}")
        for path in offending[:5]:
            print(f"      also changed {path}")
    print(
        "\n  A claim is bounded so that a lane may push it to a shared branch.\n"
        "  Code reaches `integration` by QE fast-forwarding a validated lane branch."
    )
    return 1


def _next_cycle() -> int:
    """What is waiting for certification, and whether it is worth a cycle.

    **A cycle is warranted by executable change, not by movement** (ratified
    2026-08-02, product owner). Production code, infrastructure, migrations,
    tooling and architectural behaviour earn one. **Documentation, claims,
    planning and execution-board maintenance accumulate** until they accompany
    executable work — certifying them alone spends seven minutes of build, suite,
    smoke and scenario proving a markdown table is still true, **which is how a
    team learns to skip cycles.**

    An earlier version asked only whether a commit was a *claim*, so a claim that
    also opened a coordination item counted as substantive and would have
    triggered a cycle for three documentation commits. The test is now the same
    one `_is_closeout` applies: **does anything here change what the software
    does?**

    **It refuses to answer from a stale clone**, because the wrong answer here is
    the reassuring one. Asked while `integration` sat a commit behind
    `origin/integration`, it printed *"Repository Ready — nothing awaits
    certification"* — a confident false negative on the gatekeeper's central
    question, and indistinguishable from the true one. Found live on 2026-08-04,
    by a monitoring loop that fetches and never fast-forwards.
    """
    stale = [(ref, count) for ref, count in _behind_origin() if ref == "integration"]
    if stale:
        _, count = stale[0]
        print(f"REFUSED — `integration` is {count} commit(s) behind `origin/integration`.\n")
        print(
            "  This answer is derived from local refs, so a stale clone produces a\n"
            "  confident wrong answer rather than a visible failure — and the wrong\n"
            "  answer here is `Repository Ready`.\n\n"
            "  git checkout integration && git merge --ff-only origin/integration\n"
        )
        return 1

    pending = _git("rev-list", "--reverse", "main..integration").splitlines()
    if not pending:
        print("Repository Ready — `integration` == `main`. Nothing awaits certification.")
        return 0

    accumulating: list[str] = []
    executable: list[str] = []
    for commit in pending:
        subject = _git("log", "-1", "--format=%s", commit)
        non_executable, _ = _is_closeout(commit)
        line = f"{commit[:7]}  {subject}"
        (accumulating if non_executable else executable).append(line)

    print(f"`integration` is {len(pending)} commit(s) ahead of `main`.\n")
    if accumulating:
        print(f"  {len(accumulating)} documentation/planning commit(s), accumulating:")
        for line in accumulating:
            print(f"    · {line}")
    if executable:
        print(f"\n  {len(executable)} executable commit(s):")
        for line in executable:
            print(f"    · {line}")

    if not executable:
        print(
            "\nNo cycle needed. Nothing here changes what the software does, so it\n"
            "accumulates until it accompanies executable work — a cycle is warranted\n"
            "by executable change, not by movement."
        )
        return 0

    _report_impact("main..integration")
    print(
        f"CERTIFICATION CYCLE AVAILABLE — snapshot at "
        f"{_git('rev-parse', 'integration')[:7]} and begin at stage 0."
    )
    return 0


def _audit_main() -> int:
    """Every commit on `main` since the rule reached it inside a certified snapshot.

    **A promotion fast-forwards to a certified commit, and its ancestors arrive
    with it.** Those ancestors were never *individually* certified and never can
    be: they are intermediate states of a snapshot whose tip is what the gates
    ran against. What the rule actually guarantees, and what this checks, is that
    **no commit reaches `main` except inside a certified snapshot** — every one is
    an ancestor of a certified commit that is itself on `main`.

    The distinction matters because the weaker reading is the one that lets an
    uncertified commit through: a lane pushing after the snapshot produces a
    commit that is an ancestor of *nothing* certified, and that is exactly what
    gets reported here.
    """
    # **The audit must never pass by seeing nothing.** `RULE_RATIFIED_AT` is a
    # fixed SHA, and in a clone that does not contain it — a shallow clone, a lane
    # that has not fetched, a fork — `rev-list` returns empty and this reported
    # success while examining zero commits (B-015). A check that cannot fail is
    # documentation pretending to be code (§2), and this one was written to
    # enforce exactly that principle.
    if not _git("cat-file", "-t", f"{RULE_RATIFIED_AT}^{{commit}}") == "commit":
        print(
            f"CANNOT AUDIT — this clone does not contain the baseline commit "
            f"{RULE_RATIFIED_AT[:7]}.\n\n"
            "  The guarantee is unverified here, which is not the same as held.\n"
            "  `git fetch origin main` and run it again."
        )
        return 2

    _scope_note()
    commits = _git("rev-list", "--reverse", f"{RULE_RATIFIED_AT}..main").splitlines()
    certified_all = {str(run.get("commit", "")) for run in _runs() if _satisfied(run)[0]}
    # Only certified commits that were actually promoted can vouch for anything.
    certified_on_main = [c for c in certified_all if c and _is_ancestor(c, "main")]

    violations: list[tuple[str, str, list[str]]] = []
    counts = {"certified": 0, "in_snapshot": 0, "closeout": 0}
    for commit in commits:
        if commit in certified_all:
            counts["certified"] += 1
            continue
        if any(_is_ancestor(commit, tip) for tip in certified_on_main):
            counts["in_snapshot"] += 1
            continue
        closeout, offending = _is_closeout(commit)
        if closeout:
            counts["closeout"] += 1
            continue
        subject = _git("log", "-1", "--format=%s", commit)
        violations.append((commit[:7], subject, offending))

    if not commits:
        print("audit — no commit has been promoted since the rule was ratified.")
        return 0

    print(f"audit — {len(commits)} commit(s) on `main` since the rule was ratified\n")
    print(f"  {counts['certified']} certified — a promotion target")
    print(f"  {counts['in_snapshot']} inside a certified snapshot — an ancestor of one")
    print(f"  {counts['closeout']} Closeout — changing nothing executable")

    if not violations:
        print(
            "\nNo commit reached `main` outside a certified snapshot. The guarantee holds."
        )
        return 0

    print(f"\nREFUSED — {len(violations)} commit(s) reached `main` uncertified:\n")
    for short, subject, offending in violations:
        print(f"  · {short}  {subject}")
        for path in offending[:5]:
            print(f"      changed {path}")
    print(
        "\n  Each of these is neither a certified commit, nor an ancestor of one on\n"
        "  `main`, nor a Closeout. Something reached `main` without a gate."
    )
    return 1


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "commit",
        nargs="?",
        default="main",
        help="the commit proposed for promotion (default: `main`, i.e. verify what is already there)",
    )
    parser.add_argument(
        "--audit-main",
        action="store_true",
        help="walk every commit on `main` since the rule and prove the guarantee holds",
    )
    parser.add_argument(
        "--audit-claims",
        action="store_true",
        help="a lane may push a claim to `integration` and nothing else — check that it did",
    )
    parser.add_argument(
        "--audit-planning",
        action="store_true",
        help="a planning commit touches BACKLOG.md and nothing else (C-435, unused until ruled)",
    )
    parser.add_argument(
        "--plan",
        metavar="REV_RANGE",
        help="the complete validation plan for a change — gates and Playwright journeys (D-115)",
    )
    parser.add_argument(
        "--next-cycle",
        action="store_true",
        help="is there anything on `integration` worth certifying, and what is it?",
    )
    args = parser.parse_args()

    if args.audit_main:
        return _audit_main()
    if args.audit_claims:
        return _audit_claims()
    if args.audit_planning:
        return _audit_planning()
    if args.plan:
        return _report_plan(args.plan)
    if args.next_cycle:
        return _next_cycle()

    target = _git("rev-parse", args.commit)
    if not target:
        print(f"certification-guard: '{args.commit}' is not a commit in this repository.")
        return 2

    short = target[:7]
    matching = [run for run in _runs() if str(run.get("commit", "")) == target]

    if not matching:
        closeout, _ = _is_closeout(target)
        if closeout and args.commit == "main":
            print(f"CLOSEOUT — {short} changes nothing executable.\n")
            print(
                "  A Closeout commit cannot be certified: a certification record cannot\n"
                "  contain its own commit hash. The exception is bounded to documents and\n"
                "  certification records, and it is checked rather than trusted.\n"
            )
            print("  Run `--audit-main` for the guarantee across the whole branch.")
            return 0
        certified = [str(r.get("commit", ""))[:7] for r in _runs() if _satisfied(r)[0]]
        print(f"REFUSED — {short} has no certification record.\n")
        print(
            "  A commit is promoted because it was certified, never because it is\n"
            "  what `integration` happens to point at (CLAUDE.md §20e).\n"
        )
        if certified:
            print(f"  Certified commits on record: {', '.join(certified[-5:])}")
        print(
            "\n  Certify this exact commit, or promote the one that was certified.\n"
            "  Anything that reached `integration` after the snapshot belongs to the\n"
            "  next cycle — that is the rule working, not the rule obstructing."
        )
        return 1

    run = matching[-1]
    satisfied, failures = _satisfied(run)
    if not satisfied:
        print(f"REFUSED — {short} has a certification record, and it did not pass.\n")
        for failure in failures:
            print(f"  · {failure}")
        print("\n  A failing gate is never overridden (CLAUDE.md §20e).")
        return 1

    # Certification expires by derivation: the conditions it names must still
    # describe the repository, or the record has stopped being about it.
    conditions = run.get("conditions")
    certified_head = conditions.get("migration_head") if isinstance(conditions, dict) else None
    # **The commit's own tree, not the one checked out.** A promotion runs from
    # `main`, which is at the old head by definition — see `_migration_head`.
    head = _migration_head(target)
    if certified_head and head and certified_head != head:
        print(
            f"REFUSED — {short} is certified against migration head {certified_head}, "
            f"and that commit's tree is at {head}.\n"
        )
        print(
            "  `is_certified` reads false by derivation. Nothing is wrong with the\n"
            "  record; it has simply stopped describing this repository."
        )
        return 1

    print(f"CERTIFIED — {short} may be promoted.")
    print(f"  certified at   {run.get('certified_at')}")
    print(f"  migration head {certified_head}")
    print(f"  gates          {len(run.get('gates') or [])} passed, coverage {run.get('coverage')}%")
    print(
        "\n  Promote this SHA and no other:\n"
        f"    git checkout main && git merge --ff-only {target}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
