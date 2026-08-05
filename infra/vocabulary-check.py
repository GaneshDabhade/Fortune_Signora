#!/usr/bin/env python3
"""Check the Canonical Domain Vocabulary against the repository.

**The directive that produced this asked for prevention rather than detection.**
*"Our objective is no longer just to detect vocabulary conflicts. Our objective
is to prevent them from being introduced in the first place."*

**A review checklist detects. A check prevents** — and the repository already
knows the difference: `frontend/tests/components/vocabulary.test.tsx` exists
because *"a glossary nobody can violate is documentation pretending to be
code"* (ADR-0034). This is that argument applied to the vocabulary bounded
contexts share rather than the one customers see.

**Five checks, and every one of them is about the register's own integrity or
about a term escaping its owner.** None guesses at synonyms: a synonym is a
judgement, and this file makes no judgements it cannot defend from a grep.

**Advisory, never repairing.** Every finding has more than one correct
resolution — qualify, rename, or rule that the collision is acceptable — and
choosing is a governance decision, not a script's.
"""

from __future__ import annotations

import re
import sys
import tomllib
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
VOCABULARY = REPO_ROOT / "docs" / "coordination" / "vocabulary.toml"
MODULES = REPO_ROOT / "docs" / "coordination" / "modules.toml"
BACKEND = REPO_ROOT / "backend"

#: Statuses whose terms must name an owning context that actually exists.
#:
#: **`reserved` is deliberately absent, and it was in this set for one run.**
#: A reserved term names a context that *has not been built yet* — `Person`
#: belongs to `people`, which ADR-0400 ratified and nobody has created. The
#: whole purpose of reserving a word is to hold it before its module exists,
#: so demanding the module exist defeats the status.
_OWNED = {"canonical", "context-specific", "deprecated", "historical"}

#: The relationship edges that make the register a graph rather than a list.
_EDGES = ("parent", "related", "consumed_by")

#: A `class Foo` or `def foo` declaration — the places a term becomes code.
DECLARATION = re.compile(r"^\s*(?:class|def)\s+([A-Za-z_][A-Za-z0-9_]*)", re.M)


def _terms() -> list[dict[str, object]]:
    return list(tomllib.loads(VOCABULARY.read_text()).get("term", []))


def _known_owners() -> set[str]:
    """Every context a term may belong to.

    **`platform` is included deliberately.** A word like `Owner` is ambiguous
    *across* contexts, so no single module can own the ruling about it — and
    forcing one would put a cross-cutting decision inside whichever module
    happened to hit it first, which is the failure this register exists to
    prevent.
    """
    try:
        registry = tomllib.loads(MODULES.read_text())
    except (OSError, tomllib.TOMLDecodeError):
        return {"platform"}
    return {name for name in registry} | {"platform"}


def _module_of(path: Path) -> str | None:
    parts = path.relative_to(BACKEND).parts
    return parts[1] if len(parts) > 2 and parts[0] == "modules" else None


def _declarations() -> dict[str, set[str]]:
    """Every declared name in `backend/modules/`, grouped by module.

    **Tests are excluded.** A fake named after another context's concept is a
    test double, not vocabulary — and reporting one would train people to
    ignore this check, which costs more than the finding is worth.
    """
    found: dict[str, set[str]] = {}
    for path in sorted(BACKEND.glob("modules/*/**/*.py")):
        if "test" in path.parts or path.name.startswith("test_"):
            continue
        module = _module_of(path)
        if module is None:
            continue
        names = set(DECLARATION.findall(path.read_text(errors="replace")))
        found.setdefault(module, set()).update(names)
    return found


def _by_concept() -> dict[str, dict[str, object]]:
    return {str(t["concept"]): t for t in _terms() if t.get("concept")}


def impact(concept: str) -> list[str]:
    """**"If this concept changes, what else is affected?"** — answered before
    implementation rather than during it.

    **Walks *inbound* edges, not outbound ones**, and the direction is the whole
    point: a term's own `parent` and `related` lists say what it depends on,
    which is the easy half. **What a change costs is everything pointing back at
    it**, and no single term's row can show that.
    """
    terms = _terms()
    hits: list[str] = []
    for term in terms:
        name, cid = str(term.get("name", "")), str(term.get("concept", ""))
        for edge in _EDGES:
            if concept in _list(term, edge):
                hits.append(f"{cid:<22} {name:<22} — via {edge}")
    for term in terms:
        if str(term.get("concept", "")) == concept:
            for event in _list(term, "produces_event"):
                hits.append(f"{'(event)':<22} {event:<22} — this concept publishes it")
    return hits


def _list(term: dict[str, object], key: str) -> list[str]:
    """A relationship edge as a list of strings, whatever TOML handed back.

    **`dict[str, object]` is honest about a TOML table and useless at a call
    site**, and `mypy --strict` says so — three times, all of them iterating an
    `object`. Narrowing once here beats three `cast`s, and it is the boundary
    where the file stops being data and starts being a graph.
    """
    value = term.get(key)
    return [str(v) for v in value] if isinstance(value, list) else []


def _slug(term: str) -> str:
    return re.sub(r"[^a-z0-9]", "", term.lower())


def check() -> list[str]:
    findings: list[str] = []
    terms = _terms()
    owners = _known_owners()

    #: 1 — a name declared twice is a register that contradicts itself.
    seen: dict[str, int] = {}
    for term in terms:
        name = str(term.get("name", ""))
        seen[name] = seen.get(name, 0) + 1
    for name, count in sorted(seen.items()):
        if count > 1:
            findings.append(f"'{name}' is declared {count} times in the register")

    for term in terms:
        name = str(term.get("name", ""))
        status = str(term.get("status", ""))
        owner = str(term.get("owner", ""))

        #: 2 — an owned status with no real owner. **The check that caught the
        #: gap C-010 named, one artifact over**: a concept belonging to nobody
        #: is a concept two lanes will each assume is theirs.
        if status in _OWNED:
            if not owner:
                findings.append(f"'{name}' is {status} and names no owning context")
            elif owner not in owners:
                findings.append(
                    f"'{name}' names owner '{owner}', which is not in modules.toml"
                )

        #: 3 — a qualified term must say what qualifies it, or it is just a
        #: complaint about a word.
        if status == "qualified" and not term.get("qualifies"):
            findings.append(f"'{name}' is qualified and lists no qualified forms")

        #: 4 — every qualified form must itself be a term. Otherwise the
        #: register tells somebody to use a word it does not define.
        for form in _list(term, "qualifies"):
            if form not in seen:
                findings.append(
                    f"'{name}' qualifies to '{form}', which the register does not define"
                )

    #: 5 — a context-specific term declared as code in a module that does not
    #: own it. **This is the prevention half**, and it is deliberately narrow:
    #: it fires on a declaration, never on a mention, because a docstring
    #: naming another context's concept is how the repository explains itself.
    declarations = _declarations()
    #: **Only `context-specific`.** This check fired on `Dismissed` — canonical,
    #: owned by `opportunity_engine`, and declared in `signal_engine` — and that
    #: is **the outcome the register exists to produce**: 417 refused a *second*
    #: dismissal vocabulary, so the same word appearing in both contexts is the
    #: success case. **A canonical term spreading is the goal; a context-specific
    #: one escaping is the defect**, and the first version could not tell them
    #: apart.
    for term in terms:
        status = str(term.get("status", ""))
        if status != "context-specific":
            continue
        owner = str(term.get("owner", ""))
        if owner in {"", "platform"}:
            continue
        target = _slug(str(term.get("name", "")))
        for module, names in sorted(declarations.items()):
            if module == owner:
                continue
            for declared in sorted(names):
                if _slug(declared) == target:
                    findings.append(
                        f"'{term['name']}' is owned by {owner} and is declared as "
                        f"`{declared}` in {module}"
                    )
    return findings


def main() -> int:
    if "--impact" in sys.argv:
        concept = sys.argv[sys.argv.index("--impact") + 1]
        known = _by_concept()
        if concept not in known:
            print(f"vocabulary: no concept '{concept}'. Known: {', '.join(sorted(known))}")
            return 1
        term = known[concept]
        print(f"{concept} — {term.get('name')}  (owner: {term.get('owner')}, {term.get('status')})")
        print(f"  {term.get('means', '')}")
        rows = impact(concept)
        print(f"\n  affected if this concept changes: {len(rows)}")
        for row in rows:
            print(f"    {row}")
        if not rows:
            print("    nothing — and that is information: it is a leaf, or nobody has recorded the edge")
        return 0
    if not VOCABULARY.exists():
        print("vocabulary-check: no docs/coordination/vocabulary.toml")
        return 0
    terms = _terms()
    findings = check()
    by_status: dict[str, int] = {}
    for term in terms:
        status = str(term.get("status", "?"))
        by_status[status] = by_status.get(status, 0) + 1

    print(f"vocabulary: {len(terms)} term(s)")
    for status, count in sorted(by_status.items()):
        print(f"  {status:<18} {count}")
    print()
    for line in findings:
        print(f"  · {line}")
    print()
    print(
        f"vocabulary-check: {len(findings)} finding(s) — advisory, never repaired here."
        if findings
        else "vocabulary-check: no findings."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
