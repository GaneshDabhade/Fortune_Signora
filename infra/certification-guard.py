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

sys.path.insert(0, str(Path(__file__).resolve().parent))
from registers import bug_rows  # noqa: E402

# ⛔ **Imported, never restated.** `REQUIRED_GATES` and `MINIMUM_COVERAGE` are
# the certification package's, and this file used to carry its own answer for
# both — a hardcoded `95.0` and no notion of a required gate at all (B-435).
# **A copy of a registry is wrong the first time the registry grows**, and this
# one grew on 2026-08-15 when the product owner added `frontend-suite` and
# `eslint`. `record.py` is stdlib-only, so importing it costs nothing.
#
# ⚠️ **Imported by PACKAGE path, not by adding the leaf directory to `sys.path`.**
# Both work at runtime; only this one resolves when a type checker is pointed at
# the file from `backend/`, where `tests.certification` is a real package. The
# leaf-directory form produced `Cannot find implementation or library stub for
# module named "record"` — **the standalone-checking artifact B-435 warned would
# be mistaken for a defect**, and the way to not have that argument is to not
# produce the artifact.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))
from tests.certification.record import MINIMUM_COVERAGE, REQUIRED_GATES  # noqa: E402

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

#: Planning projections — regenerated from the registers, read by lanes and by
#: `infra/coordination.py`, and executed by nothing.
#:
#: ⚡ **D-240 §1, on B-1005**, which ruled the repair **path-based and never
#: suffix-based**: *"recognize the specific authoritative path/role of
#: `modules.toml`, while `coordination.toml` and `queues/*.toml` keep their
#: existing projection semantics."*
#:
#: ⛔ **`docs/coordination/modules.toml` is DELIBERATELY ABSENT.**
#: `_audit_claims` reads it — `_git("show", f"{commit}:docs/coordination/modules.toml")`
#: — so it is an **operand of a gate**, exactly the property `CLOSEOUT_PATHS`
#: excludes `infra/` for. Admitting it would let an ownership change reach
#: `main` outside a certified snapshot and silently alter what the claim audit
#: accepts. That is B-014, one directory over.
#:
#: ⚠️ **An allowlist rather than "every `.toml` under `docs/coordination/` except
#: `modules.toml`", and the direction of the failure is the whole reason.**
#: A new projection file omitted here classifies as executable and costs one
#: unnecessary certification. A new *gate operand* added under that directory
#: would, under a denylist, be absorbed as documentation and become
#: Closeout-legal without anybody deciding it. **The first is cheap and visible;
#: the second is the failure this rule exists to prevent.**
PLANNING_PROJECTIONS = (
    "docs/coordination/coordination.toml",
    "docs/coordination/notices.toml",
    "docs/coordination/workflows.toml",
)

#: Prefixes whose every `.toml` is a per-lane projection.
PLANNING_PROJECTION_DIRS = ("docs/coordination/queues/",)


def _is_non_executable(path: str) -> bool:
    """Whether a single changed path can change what the software does.

    **One predicate, shared by `_is_closeout` and the impact classifier.**
    B-1005 was two classifiers reaching the same blind spot by different
    routes; they were unified once already, and this keeps them unified.
    """
    if path.startswith(CLOSEOUT_PATHS) and path.endswith(CLOSEOUT_SUFFIXES):
        return True
    if path in PLANNING_PROJECTIONS:
        return True
    return path.startswith(PLANNING_PROJECTION_DIRS) and path.endswith(".toml")


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


#: The twelve lifecycle states §20e defines, and nothing else.
#: **A row's state is the leading backticked token of its `Status` CELL** — never
#: a word that happens to appear in the row's prose.
_STATE_TOKEN = re.compile(r"`([A-Z][A-Z ]*[A-Z])`")
_STATUS_CELL = re.compile(r"^\|\s*\*\*Status\*\*\s*\|(.*)$", re.M)
_ROW_HEAD = re.compile(r"^### (TASK-\d+)\b", re.M)


def backlog_states(text: str) -> dict[str, str]:
    """Every row's state, read from its `Status` cell and from nowhere else.

    ⛔ **[B-168](../docs/BUGS.md)'s false positive is the reason this exists.**
    The first implementation matched the word VERIFIED anywhere in a removed line, which
    matched a `READY` cell whose *prose* cited a verified row — *"Released:
    `TASK-1408` is `VERIFIED` and promoted at `e72b6af0`"* — and reported a
    regression that had not happened. **Measured at the time: 12 `VERIFIED`
    status cells before, 12 after, no row changed.**

    ⚡ **The repair is to read the authoritative field rather than the text
    around it.** A row contributes a state only if it has a `Status` cell and
    that cell opens with a backticked token; **prose in a title, a note, an
    evidence line or a reference cannot reach this function's output.**
    """
    states: dict[str, str] = {}
    heads = list(_ROW_HEAD.finditer(text))
    for index, head in enumerate(heads):
        end = heads[index + 1].start() if index + 1 < len(heads) else len(text)
        cell = _STATUS_CELL.search(text, head.start(), end)
        if not cell:
            continue
        token = _STATE_TOKEN.search(cell.group(1))
        if token:
            states[head.group(1)] = token.group(1).strip()
    return states


#: The states only QE may write ([§20e](../CLAUDE.md)) — and therefore the only
#: ones a lane's rebase can *un*-write. **`VERIFIED` was the whole set until
#: [B-232](../docs/BUGS.md)**, which reverted a `PROMOTED` cell straight through
#: the check that prints *"no VERIFIED state is undone"* and onto `main`.
#:
#: ⛔ **The gap was not the logic; it was the noun.** [B-168](../docs/BUGS.md)
#: named the state it had just been burned by, and the guard inherited that
#: name as if it were the rule. **The rule is *QE's judgement*, and QE writes
#: four of these.**
QE_TERMINAL_STATES: frozenset[str] = frozenset(
    {"VERIFIED", "CERTIFIED", "PROMOTED", "DONE"}
)


def verified_regressions(before: str, after: str) -> list[tuple[str, str]]:
    """Rows whose QE-written state has been undone or weakened.

    **The check [B-168](../docs/BUGS.md) asked for, as a function rather than a
    habit.** A clean rebase silently reverted QE's own `VERIFIED` cells three
    times, and twice a conflict happened to make it visible; the third had none.

    ⚠️ **Widened by [B-232](../docs/BUGS.md), which this function watched go
    past.** A lane resolved a rebase conflict in its own favour, `PROMOTED`
    became `IN VALIDATION`, and the promotion that carried it printed **`PASS
    no VERIFIED state is undone`** — truthfully, and uselessly. **All four
    QE-written states are checked now, and a move to a *lower* one counts as
    well as an erasure**, because `PROMOTED → CERTIFIED` is the same defect
    with a smaller step.

    ⛔ **The name is kept.** It is referenced from the promotion path and from
    the regression suite, and renaming it here would be a second change riding
    on a fix — which is what §2 asks a repair not to do.
    """
    order = {"VERIFIED": 1, "CERTIFIED": 2, "PROMOTED": 3, "DONE": 4}
    old, new = backlog_states(before), backlog_states(after)
    lost: list[tuple[str, str]] = []
    for task, state in old.items():
        if state not in QE_TERMINAL_STATES:
            continue
        now = new.get(task, "ABSENT")
        if now == state:
            continue
        if now in order and order[now] >= order[state]:
            continue  # advanced further along QE's own sequence
        lost.append((task, now))
    return sorted(lost)


#: The one bug-row state only QE may write ([§20e](../CLAUDE.md)): *"Verifies and
#: closes — **QE**, never the lane that fixed it."* **`FIXED` is the lane's and
#: `WONTFIX` is a decision, so neither belongs here** — this set is exactly the
#: states a lane's rebase can *un*-write.
QE_BUG_STATES: frozenset[str] = frozenset({"VERIFIED"})


def verified_bug_regressions(before: str, after: str) -> list[tuple[str, str]]:
    """Bug rows whose QE-written state has been undone — **B-197.**

    ⛔ **`verified_regressions` above protects `BACKLOG.md` and read `BUGS.md`
    not at all**: `grep -c 'docs/BUGS.md"'` against this file returned `0`. **So
    a rebase could carry a `VERIFIED` defect back to `OPEN` and the promotion
    would print `PASS` beside it** — truthfully, about the other register.

    ⚡ **It is the same defect B-232 found one register over**, and the same
    repair: **read the authoritative cell, never the prose around it.**
    `registers.bug_rows` already does that, and `BugRow.state` already takes the
    *first* state token because *"`FIXED` — **`VERIFIED` is QE's to set**"*
    contains both words (📁 [B-101](../docs/BUGS.md)). ✅ **This joins that
    parser rather than adding a second one** — a second reading of one register
    is what [B-413](../docs/BUGS.md) cost, where two properties on one dataclass
    disagreed about the same cell.

    ⚠️ **A row leaving the register counts.** `ABSENT` is reported, because
    deleting a `VERIFIED` row hides a closed defect exactly as thoroughly as
    reopening it, and a rebase that drops a row is how B-168 happened.
    """
    old = {r.identifier: r.state for r in bug_rows(before)}
    new = {r.identifier: r.state for r in bug_rows(after)}
    lost: list[tuple[str, str]] = []
    for identifier, state in old.items():
        if state not in QE_BUG_STATES:
            continue
        now = new.get(identifier, "ABSENT")
        if now == state:
            continue
        lost.append((identifier, now or "UNREADABLE"))
    return sorted(lost)


def _promote(sha: str) -> int:
    """Run every blocking gate, and promote **only** if all of them pass.

    ⛔ **[D-228](../docs/DECISION_REGISTER.md), the product owner, after QE
    promoted while a gate was firing**: *"the promotion command itself must be
    structurally incapable of proceeding after a blocking gate failure."*

    🔴 **Before this existed there was no promotion command.** Promotion was a
    shell sequence an operator typed, so every check beside it was advisory *by
    construction* — **a check whose output nobody is forced to read is a log
    line, not a gate.** ⚡ **The fix is not a warning, a flag or an approval
    step: it is that `git merge` now lives behind the gates in the same
    process, and the only way past a failure is to fix it.**

    ⛔ **There is deliberately no `--force`, no override and no skip.**
    """
    target = _git("rev-parse", sha)
    if not target:
        print(f"promote: '{sha}' is not a commit in this repository.")
        return 2

    failures: list[str] = []

    matching = [run for run in _runs() if str(run.get("commit", "")) == target]
    ok = any(_promotable(run)[0] for run in matching)
    print(f"  {'PASS' if ok else 'FAIL'}  certified — this exact commit")
    if not ok:
        failures.append(f"{target[:7]} is not a certified commit")

    main_backlog = _git("show", "origin/main:docs/BACKLOG.md")
    cand_backlog = _git("show", f"{target}:docs/BACKLOG.md")
    lost = verified_regressions(main_backlog, cand_backlog) if main_backlog and cand_backlog else []
    print(f"  {'PASS' if not lost else 'FAIL'}  no VERIFIED state is undone (B-168)")
    for task, became in lost:
        print(f"          {task}: VERIFIED -> {became}")
    if lost:
        failures.append(f"{len(lost)} row(s) lose a VERIFIED state")

    main_bugs = _git("show", "origin/main:docs/BUGS.md")
    cand_bugs = _git("show", f"{target}:docs/BUGS.md")
    reopened = verified_bug_regressions(main_bugs, cand_bugs) if main_bugs and cand_bugs else []
    print(f"  {'PASS' if not reopened else 'FAIL'}  no VERIFIED defect is reopened (B-197)")
    for identifier, became in reopened:
        print(f"          {identifier}: VERIFIED -> {became}")
    if reopened:
        failures.append(f"{len(reopened)} defect(s) lose a VERIFIED state")

    if failures:
        print()
        print("  PROMOTION REFUSED — a blocking gate failed:")
        for reason in failures:
            print(f"    · {reason}")
        print()
        print("  Nothing was promoted, integrated or recorded. Fix the gate or")
        print("  the commit, re-run, and promotion proceeds on its own.")
        return 1

    head = _git("rev-parse", "HEAD")
    branch = _git("rev-parse", "--abbrev-ref", "HEAD")
    if branch != "main":
        print(f"  PROMOTION REFUSED — HEAD is on '{branch}', not 'main'.")
        return 1

    merged = subprocess.run(
        ["git", "merge", "--ff-only", target],
        cwd=REPO_ROOT, capture_output=True, text=True, check=False,
    )
    if merged.returncode != 0:
        print("  PROMOTION REFUSED — not a fast-forward.")
        print(merged.stderr.strip()[:400])
        return 1

    now = _git("rev-parse", "HEAD")
    if now != target:
        print(f"  EQUALITY VIOLATED — promoted {now[:7]}, certified {target[:7]}.")
        return 1

    print(f"\n  PROMOTED {target[:7]} — promoted == certified, from {head[:7]}.")
    return 0


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


def _entries(run: dict[str, object], key: str) -> tuple[list[dict[str, object]], list[str]]:
    """The `gates` or `scenarios` list, or a failure saying it was unreadable.

    ⛔ **`run.get(key) or []` is what this replaces, and the `or []` was the
    defect.** A record with no `gates` key, or with a `gates` value that is not a
    list, iterated zero times and produced zero failures — so **absence read as
    success.** 📁 That is the empty-array class `36-empty-array-checks.md` found
    in nine CHECK constraints, and `REQUIRED_GATES`' own comment names it:
    *"a run recording no gates at all would otherwise satisfy 'every gate
    passed' vacuously."* **The package defended against it; this file did not**
    ([B-435](../docs/BUGS.md)).

    **A malformed record is refused, never silently read as empty** — the
    repository's standing preference for operations that refuse an unsafe state
    over ones that recover from it quietly.
    """
    raw = run.get(key)
    if raw is None:
        return [], [f"the record carries no '{key}' at all, so nothing about it can be checked"]
    if not isinstance(raw, list):
        return [], [f"'{key}' is {type(raw).__name__}, not a list — the record is unreadable"]
    entries = [item for item in raw if isinstance(item, dict)]
    if len(entries) != len(raw):
        bad = len(raw) - len(entries)
        return entries, [f"'{key}' holds {bad} entr(y/ies) that are not objects"]
    return entries, []


def _satisfied(run: dict[str, object]) -> tuple[bool, list[str]]:
    """Whether every gate this run **recorded** passed — a question about the run.

    ⚠️ **This is deliberately NOT `CertificationRun.satisfied`, and the docstring
    that claimed it was is what [B-435](../docs/BUGS.md) is about.** The package's
    predicate additionally requires that **every member of today's
    `REQUIRED_GATES` actually ran**, which re-judges history the moment the set
    grows — by design, and the product owner accepted that effect on 2026-08-15.

    ⛔ **`--audit-main` must not inherit it**, for two reasons — and the first
    one QE got wrong before measuring it.

    ⚠️ **NOT because history would be refused.** Applying today's eight-gate set
    to the 230 stored records leaves **2** satisfied, and QE first wrote that this
    would make the audit refuse 209 commits on `main`. **It does not.** The audit
    accepts *"an ancestor of a certified commit that is itself on `main`"*, and a
    certified commit near the tip vouches for everything behind it — fire-tested
    2026-08-15: with this predicate made strict, the audit still reports the
    guarantee holding. **The ancestor rule absorbs it.**

    ⚡ **The real hazard is the window, and it is sharp.** `certified_all` becomes
    **empty** whenever no stored record satisfies the current set — which is
    exactly the state between widening `REQUIRED_GATES` and the first run under
    the new set. With nothing to be an ancestor *of*, **every non-Closeout commit
    on `main` becomes a violation at once** and the audit reports the repository's
    central release guarantee broken. **A historical audit whose verdict depends
    on a gate added this morning is not a historical audit.**

    ✅ **And independently: the product owner ruled it.** *"The records remain
    historical records under the gate set that existed at the time."* Judging them
    by today's bar is the reinterpretation that ruling declined.

    ✅ **`_promotable()` below is the forward-looking question, and that one does
    require the full set** — because a record written today must meet today's bar.
    **Two questions, two predicates, both named.** What B-435 found was one
    predicate quietly answering both.
    """
    gates, failures = _entries(run, "gates")
    scenarios, scenario_failures = _entries(run, "scenarios")
    failures = [*failures, *scenario_failures]
    for gate in gates:
        if not gate.get("passed"):
            failures.append(f"gate '{gate.get('name')}' failed")
    for scenario in scenarios:
        if not scenario.get("passed"):
            failures.append(f"scenario '{scenario.get('name')}' failed")
    if not run.get("tree_clean"):
        failures.append("the working tree was dirty, so the tree certified was never stored")
    coverage = run.get("coverage")
    if isinstance(coverage, int | float) and coverage < MINIMUM_COVERAGE:
        failures.append(f"coverage {coverage}% is below {MINIMUM_COVERAGE}%")
    return not failures, failures


def _promotable(run: dict[str, object]) -> tuple[bool, list[str]]:
    """`_satisfied`, plus every member of today's `REQUIRED_GATES` having run.

    ⚡ **The gate that stops an uncertified promotion, and until
    [B-435](../docs/BUGS.md) it did not check this at all.** A record that simply
    never executed `frontend-suite` was promotable, which is exactly
    [B-122](../docs/BUGS.md)'s scenario: the gate was absent from 228 runs and
    absence was never a failure here.

    ⛔ **Tightening this costs no history.** It is consulted only when somebody
    asks to promote a commit *now*, and a run recorded under a narrower set was
    promoted under that set at the time. **Re-promoting such a commit is refused,
    which is correct** — the bar it would be promoted against is today's.
    """
    satisfied, failures = _satisfied(run)
    gates, _ = _entries(run, "gates")
    ran = {str(gate.get("name")) for gate in gates}
    for missing in sorted(REQUIRED_GATES - ran):
        failures.append(f"required gate '{missing}' did not run")
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
    offending = [path for path in changed if not _is_non_executable(path)]
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
        if not hits and _is_non_executable(path):
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


def _validated_floor() -> str:
    """The newest point QE has already vouched for — a certified commit, else `main`.

    ⚡ **Certification is QE's validation marker and it is recorded**, so a
    commit that is an ancestor of a certified SHA has been through the gates
    even when promotion is blocked and it has not reached `main`.

    ⛔ **`main` alone was the wrong floor** and it degraded exactly when the
    repository most needed the check: **the longer promotion is held, the
    further `integration` runs ahead, and the more legitimate arrivals read as
    smuggled.** ([B-184](../docs/BUGS.md).)

    **Falls back to `main`** when nothing is certified, which is the old
    behaviour and the conservative direction — it over-reports rather than
    under-reports.
    """
    newest = "main"
    for run in _runs():
        commit = str(run.get("commit") or "")
        if not commit or not _satisfied(run)[0]:
            continue
        # Only a certified commit that `integration` actually contains is a
        # floor; a certification of some other line says nothing here.
        if not _is_ancestor(commit, "integration"):
            continue
        if newest == "main" or _is_ancestor(newest, commit):
            newest = commit
    return newest


def _claim_stowaways(claims: list[str]) -> list[tuple[str, str, list[tuple[str, str]]]]:
    """Implementation commits that reached `integration` riding a claim push.

    ⛔ **`--audit-claims` inspected the paths *inside* each claim commit and
    nothing else, so it passed a clean claim while the slice underneath it went
    through with the same push.** ⚡ **A push moves a branch, not a commit** —
    every ancestor not already on the target arrives too, and the guard was
    asking the wrong question about the right object.

    ⚠️ **Third instance before it was fixed.** [B-161](../docs/BUGS.md) is QE's
    own diagnosis, [B-220](../docs/BUGS.md) named the blind spot, and
    [B-238](../docs/BUGS.md) is Lane A reporting it **against itself, with the
    breach as the evidence**. **Three rows describing one defect is the argument
    for a machine rather than a better-remembered rule** (`CLAUDE.md` §2:
    *prefer a violation that is unrepresentable over one that is merely
    discouraged*).

    **The check is Lane A's, and it is exact**: a claim commit is only ever a
    legitimate arrival on `integration` when its parent was *already* there. Any
    other parent is a commit that skipped validation, certification and
    promotion — whatever it contains, and however good it is.

    ⚡ **It reports rather than refuses, deliberately.** The condition is
    historical the moment it is detected: the commits are on the shared ref, and
    the lane that caused it cannot unwind them without a force-push it may not
    perform. **A gate that fails on something nobody present can fix teaches
    people to skip the gate** — the same reasoning `state-check.py` applies to
    `Planning-Sync`. **What QE does about it is validate the stowaway before the
    next snapshot pins it, which is what this makes visible.**
    """
    found: list[tuple[str, str, list[tuple[str, str]]]] = []
    for claim in claims:
        parents = _git("rev-list", "--parents", "-n", "1", claim).split()[1:]
        riders: list[tuple[str, str]] = []
        for parent in parents:
            # ⛔ **`_validated_floor()`, not `main`** — [B-184](../docs/BUGS.md).
            # The docstring above says *"its parent was already there"*, meaning
            # on `integration`; measuring from `main` only answers that while
            # `main` is current. **Promotion had been blocked for days, so
            # `integration` ran 20+ commits ahead and every legitimately
            # fast-forwarded commit read as a stowaway** — including QE's own.
            #
            # ⚠️ **The promotion gate was manufacturing false positives in the
            # check that guards promotion**, and the rate grew with the block.
            # Everything between the floor and the claim's parent that is not
            # itself a claim. On a healthy claim push this range is empty,
            # because the parent *is* what `integration` already pointed at.
            for commit in _git("rev-list", f"{_validated_floor()}..{parent}").splitlines():
                if not commit:
                    continue
                subject = _git("log", "-1", "--format=%s", commit)
                if subject.startswith("Claim TASK-"):
                    continue
                # ⛔ **Executable paths only, and this is the whole
                # discriminator.** The harm B-238 names is *uncertified code*
                # reaching `integration`, never *a commit arriving*. Between a
                # promotion and the next one, `integration` is legitimately
                # ahead of `main` with work QE fast-forwarded — and every claim
                # pushed after that would otherwise name all of it.
                #
                # ⚠️ **Measured on the first live firing, 2026-08-11**: it
                # reported three of Lane C's planning commits, published by QE
                # under an approved push, as stowaways. **0 executable files
                # each. B-238's real stowaway had 5.** A guard that cries on
                # the normal state gets switched off, and then it protects
                # nothing (B-180's lesson, one file over).
                changed = _git("show", "--name-only", "--format=", commit).splitlines()
                if not any(
                    path.startswith(("frontend/", "backend/", "infra/"))
                    for path in changed
                    if path
                ):
                    continue
                riders.append((commit[:7], subject))
        if riders:
            found.append((claim[:7], _git("log", "-1", "--format=%s", claim), riders))
    return found


def _audit_claims() -> int:
    """Every claim commit on `integration` touches the registers and nothing else."""
    _scope_note()
    # ⛔ **Two ranges, and only one of them can still be acted on** —
    # [B-184](../docs/BUGS.md). A claim already on `main` is immutable and was
    # promoted inside a certified snapshot; **nothing any lane does will ever
    # clear it.** Refusing on it made this check exit 1 on every invocation
    # for as long as the repository exists.
    #
    # ⚡ **The harm was never the false alarm.** It is that the only way to
    # keep working was to skip the output — and then the run that reports a
    # real breach looks exactly like the two hundred before it. A gate that
    # cannot pass is not a gate (`CLAUDE.md` §2).
    #
    # ⛔ **Deliberately not a list of forgiven hashes.** That would silence a
    # genuine future breach in the same files, which is the
    # guard-that-cannot-fail shape wearing the opposite coat. **The question is
    # *can this still be fixed*, and `main` answers it.**
    pending = _claim_commits("main..integration")
    historical = _claim_commits(f"{RULE_RATIFIED_AT}..main")
    commits = pending + historical
    if not commits:
        print("audit — no claim commits to check.")
        return 0

    def _offences(shas: list[str]) -> list[tuple[str, str, list[str]]]:
        found: list[tuple[str, str, list[str]]] = []
        for commit in shas:
            changed = [
                line
                for line in _git("show", "--name-only", "--format=", commit).splitlines()
                if line
            ]
            offending = [path for path in changed if path not in CLAIM_PATHS]
            if offending:
                found.append(
                    (commit[:7], _git("log", "-1", "--format=%s", commit), offending)
                )
        return found

    violations = _offences(pending)
    settled = _offences(historical)
    # ⚠️ **Scoped to `pending` for the same reason, and it is the biggest half
    # of the noise** — this reported 131 of 166 claims, 79%, almost all of them
    # promoted months ago and unfixable. **A finding nobody can act on is not a
    # finding**, and 131 lines above the real ones is how a reader learns to
    # scroll past the whole report (B-184).
    skips: list[tuple[str, str, str, list[str]]] = []
    for commit in pending:
        skips.extend(_unexplained_skips(commit))
    # Only a claim that has not yet been promoted can still be unpicked, so the
    # stowaway report is scoped the same way and for the same reason.
    stowaways = _claim_stowaways(pending)

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
    if stowaways:
        # **Reported, never refused** — the reasoning is with `_claim_stowaways`.
        print(f"  {len(stowaways)} claim push(es) carried an implementation commit with them.")
        print("  The claim itself is clean; a push moves a BRANCH, so its parents arrived too.\n")
        for short, subject, riders in stowaways:
            print(f"    · {short}  {subject[:56]}")
            for rider_sha, rider_subject in riders[:4]:
                print(f"        brought {rider_sha}  {rider_subject[:52]}")
        print(
            "\n  These reached `integration` without validation, certification or\n"
            "  promotion. Validate them before the next Certification Snapshot pins\n"
            "  them — a snapshot assumes every commit here was fast-forwarded after\n"
            "  QE validated it (B-161, B-220, B-238).\n"
        )
    if settled:
        # **Reported once, dated, and never counted as a live finding.** These
        # are on `main`: promoted inside a certified snapshot, immutable, and
        # unfixable by anybody. Naming them keeps the count honest; refusing on
        # them would make the verdict a foregone conclusion (B-184).
        print(
            f"  {len(settled)} historical claim(s) on `main` carried more than a claim.\n"
            "  Immutable and already promoted — recorded, not actionable:\n"
        )
        for short, subject, offending in settled:
            print(f"    · {short}  {subject[:56]}")
            for path in offending[:3]:
                print(f"        also changed {path}")
        print()

    if not violations:
        # ⛔ **An empty set is not a passing audit, and this said it was.**
        # With no claim awaiting promotion it printed *"0 claim(s) awaiting
        # promotion touch only ACTIVE_ASSIGNMENTS.md and BACKLOG.md"* followed
        # by *"none of the unpromoted ones carried anything else"* — **both
        # vacuously true, and together they read as a clean result on a set
        # nobody examined.**
        #
        # ⚡ **A reader cannot tell *nothing was wrong* from *nothing was
        # checked***, which is B-125's class and the reason `_plan_shortfall`
        # returns `None` rather than an empty list when it cannot measure.
        # 📁 [B-1037](../docs/BUGS.md).
        if not pending:
            print(
                "  no claim is awaiting promotion, so none was examined.\n\n"
                "This is not a clean result — it is an empty one. `integration` carries\n"
                "no unpromoted claim commit, which is the ordinary state between cycles."
            )
            return 0
        print(
            f"  {len(pending)} claim(s) awaiting promotion touch only "
            "ACTIVE_ASSIGNMENTS.md and BACKLOG.md.\n\n"
            "A claim is the one thing a feature lane may push to `integration`, and\n"
            "none of the unpromoted ones carried anything else."
        )
        return 0

    print(f"REFUSED — {len(violations)} unpromoted claim commit(s) carried more than a claim:\n")
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


def _report_journeys(rev_range: str) -> int:
    """Name the Playwright specs a change selects.

    ⚠️ **Added 2026-08-14 because [`CLAUDE.md`](../CLAUDE.md) §19 already named
    it** — *"`python3 infra/certification-guard.py --journeys` names which
    specs the change selects; the mapping is deterministic and not a judgement
    call."* 🔴 **`journeys_for` existed and had no way in from the command
    line**, so the constitution instructed a step nobody could perform.

    ⛔ **The rule is repaired by building the mechanism rather than by editing
    the sentence**, because the sentence describes the behaviour the
    repository wants — and 📁 [§2](../CLAUDE.md) puts the defect in the
    document that asserted something untrue of the repository, not in the
    requirement.
    """
    changed = _git("diff", "--name-only", rev_range)
    paths = [line for line in changed.splitlines() if line]
    selected = journeys_for(paths)

    if not selected:
        print("journeys: none — nothing under frontend/ changed")
        return 0
    if "__all__" in selected:
        print(
            "journeys: ALL — a changed frontend path matches no rule, and an "
            "unrecognised path widens rather than narrows (a new directory must "
            "not silently reduce validation)"
        )
        return 0
    for journey in sorted(selected):
        print(f"journeys: {journey}")
    return 0


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
    parser.add_argument(
        "--journeys",
        metavar="REV_RANGE",
        nargs="?",
        const="origin/integration...HEAD",
        help="which Playwright specs a change selects (CLAUDE.md §19)",
    )
    parser.add_argument(
        "--promote",
        metavar="SHA",
        help="run every BLOCKING gate and promote only if all of them pass (D-228)",
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
    if args.journeys:
        return _report_journeys(args.journeys)
    if args.promote:
        return _promote(args.promote)

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
        certified = [str(r.get("commit", ""))[:7] for r in _runs() if _promotable(r)[0]]
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
    satisfied, failures = _promotable(run)
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
    print(
        f"  gates          {len(_entries(run, 'gates')[0])} of {len(REQUIRED_GATES)} required"
        f", coverage {run.get('coverage')}%"
    )
    print(
        "\n  Promote this SHA and no other:\n"
        f"    git checkout main && git merge --ff-only {target}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
