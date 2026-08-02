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
    args = parser.parse_args()

    if args.audit_main:
        return _audit_main()

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
