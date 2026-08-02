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
import json
import subprocess
import sys
from pathlib import Path

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


def _migration_head() -> str | None:
    heads = sorted(p.name.split("_")[0] for p in MIGRATIONS.glob("[0-9]*_*.py"))
    return heads[-1] if heads else None


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


# A claim commit is the one thing a feature lane may push to `integration`, so it
# is bounded to the two registers. Anything else in it is code arriving on a
# shared branch without a gate.
CLAIM_PATHS = ("docs/ACTIVE_ASSIGNMENTS.md", "docs/BACKLOG.md")


def _claim_commits(rev_range: str) -> list[str]:
    return _git("rev-list", "--reverse", rev_range, "--grep=^Claim TASK-").splitlines()


def _audit_claims() -> int:
    """Every claim commit on `integration` touches the registers and nothing else."""
    commits = _claim_commits("main..integration") + _claim_commits(
        f"{RULE_RATIFIED_AT}..main"
    )
    if not commits:
        print("audit — no claim commits to check.")
        return 0

    violations: list[tuple[str, str, list[str]]] = []
    for commit in commits:
        changed = [
            line
            for line in _git("show", "--name-only", "--format=", commit).splitlines()
            if line
        ]
        offending = [path for path in changed if path not in CLAIM_PATHS]
        if offending:
            violations.append((commit[:7], _git("log", "-1", "--format=%s", commit), offending))

    print(f"audit — {len(commits)} claim commit(s)\n")
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
    """
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

    print(
        f"\nCERTIFICATION CYCLE AVAILABLE — snapshot at "
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
        "--next-cycle",
        action="store_true",
        help="is there anything on `integration` worth certifying, and what is it?",
    )
    args = parser.parse_args()

    if args.audit_main:
        return _audit_main()
    if args.audit_claims:
        return _audit_claims()
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
    head = _migration_head()
    if certified_head and head and certified_head != head:
        print(
            f"REFUSED — {short} is certified against migration head {certified_head}, "
            f"and the repository is at {head}.\n"
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
