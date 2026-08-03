#!/usr/bin/env python3
"""**Can a customer get to this screen?**

The sibling of [`runtime-composition.py`](runtime-composition.py), and
deliberately the same shape: that one asks *"does the deployed worker consume
what this module projects?"*, this asks *"does any screen lead to this route?"*
**Both answer the same class of question — something is built, correct, tested,
and nothing reaches it.**

**Two defects made this worth automating, and both were found by hand:**

* **The Connection Center was reachable only by typing its URL.** The only links
  to `/settings/connections` in the whole codebase were the two OAuth redirect
  helpers *inside the connection flow itself* — so a customer could reach it
  only by already being in it. **A closed loop with no door**
  ([43-customer-experience.md](../docs/architecture/43-customer-experience.md)).
* **Timeline shipped complete and inert** ([B-301](../docs/BUGS.md)) — the
  backend half of the same failure, which is why the two checks are siblings.

**The rule that makes it catch the real defect.** *"Has an inbound link"* would
have passed the Connection Center: it had two. **An entrance is a link from
outside the route's own subtree** — a link from `/settings/connections/callback`
to `/settings/connections` is the loop closing, not a door opening.

**It reports; it does not fail a build.** Some routes are legitimately entered
from outside the application — an email link, an OAuth redirect — and those are
declared below with a reason, so an exemption is a decision rather than an
omission.

    python3 infra/reachability.py
    python3 infra/reachability.py --strict   # exit 1 if any route has no entrance
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Final

REPO_ROOT: Final = Path(__file__).resolve().parent.parent
APP: Final = REPO_ROOT / "frontend" / "app"
SEARCHED: Final = ("frontend/app", "frontend/components", "frontend/lib")

#: Routes a customer reaches without an in-product link, each with the reason.
#:
#: **A judgement, maintained by QE**, and deliberately short: every entry is a
#: claim that something outside the product sends a customer here, and a list
#: that grows without argument is how a check stops meaning anything.
ENTERED_FROM_OUTSIDE: Final = {
    "/sign-in": "the front door — typed, bookmarked, or redirected to by the shell",
    "/sign-up": "linked from marketing and from /sign-in",
    "/verify-email": "reached from the verification email, by design",
    "/reset-password": "reached from the password-reset email, by design",
}


def _routes(app: Path = APP) -> dict[str, Path]:
    """Every navigable route, by URL path.

    Next.js route groups — `(app)`, `(auth)` — are organisational and do not
    appear in a URL, so they are stripped. A customer never types `(app)`.
    """
    found: dict[str, Path] = {}
    for page in sorted(app.rglob("page.tsx")):
        parts = [
            part
            for part in page.relative_to(app).parent.parts
            if not (part.startswith("(") and part.endswith(")"))
        ]
        found["/" + "/".join(parts)] = page
    return found


def _navigations(roots: tuple[Path, ...] | None = None) -> list[tuple[str, Path]]:
    """Every in-product navigation, as `(target, the file that offers it)`.

    Covers what this codebase actually writes: `href="…"`, `href={`…`}`,
    `router.push(…)`, `redirect(…)` and `replace(…)`. **Verified against the
    repository rather than assumed** — a pattern nobody uses would be dead
    matching, and one that is used and unmatched would make the check lie.
    """
    patterns = (
        r'href="([^"]+)"',
        r"href=\{`([^`]+)`\}",
        r"(?:router\.push|redirect|replace)\(\s*[\"'`]([^\"'`]+)[\"'`]",
    )
    found: list[tuple[str, Path]] = []
    for root in roots or tuple(REPO_ROOT / d for d in SEARCHED):
        if not root.is_dir():
            continue
        for source in sorted(root.rglob("*.tsx")) + sorted(root.rglob("*.ts")):
            text = source.read_text()
            for pattern in patterns:
                for target in re.findall(pattern, text):
                    if target.startswith("/"):
                        found.append((target, source))
    return found


def _normalise(target: str) -> str:
    """`/accounts/${id}?x=1` → `/accounts/[id]`, so a link matches its route."""
    target = target.split("?")[0].split("#")[0]
    target = re.sub(r"\$\{[^}]+\}", "[dynamic]", target)
    return target.rstrip("/") or "/"


def _route_pattern(route: str) -> re.Pattern[str]:
    """A route with `[accountId]` matches a link with a dynamic segment."""
    escaped = re.escape(route).replace(r"\[dynamic\]", "[dynamic]")
    return re.compile("^" + re.sub(r"\\\[[^\]]+\\\]", r"(\\[dynamic\\]|[^/]+)", escaped) + "$")


def _is_inside(source: Path, route: str, app: Path = APP) -> bool:
    """Whether the link comes from within the route's own subtree.

    **This is the rule that catches the real defect.** A link from
    `/settings/connections/*` back to `/settings/connections` is the loop
    closing; it is not a door.
    """
    if route == "/":
        return False
    try:
        relative = source.relative_to(app)
    except ValueError:
        return False
    segments = [
        part
        for part in relative.parent.parts
        if not (part.startswith("(") and part.endswith(")"))
    ]
    return ("/" + "/".join(segments)).startswith(route)


def analyse(
    app: Path = APP, roots: tuple[Path, ...] | None = None
) -> tuple[list[str], list[str], list[str], dict[str, Path]]:
    """`(reachable, declared, unreachable, routes)` — the whole judgement, in
    one function so a test can drive it against a constructed tree."""
    routes = _routes(app)
    navigations = [(_normalise(target), source) for target, source in _navigations(roots)]
    reachable: list[str] = []
    unreachable: list[str] = []
    declared: list[str] = []
    for route in sorted(routes):
        pattern = _route_pattern(route)
        entrances = [
            source
            for target, source in navigations
            if pattern.match(target) and not _is_inside(source, route, app)
        ]
        if entrances:
            reachable.append(route)
        elif route in ENTERED_FROM_OUTSIDE:
            declared.append(route)
        else:
            unreachable.append(route)
    return reachable, declared, unreachable, routes


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args()

    reachable, declared, unreachable, routes = analyse()

    print("\n  Customer Reachability\n")
    print(f"    Navigable routes                   {len(routes)}")
    print(f"    Reachable from inside the product  {len(reachable)}")
    print(f"    Entered from outside, declared     {len(declared)}")
    print(
        f"    No entrance at all                 {len(unreachable)}"
        f"{'   ← every one is a defect' if unreachable else ''}\n"
    )

    for route in reachable:
        print(f"      ✓ {route}")
    for route in declared:
        print(f"      · {route:<28} {ENTERED_FROM_OUTSIDE[route]}")
    if unreachable:
        print("\n    NO ENTRANCE — built, and no screen leads here:")
        for route in unreachable:
            print(f"      ✗ {route}")

    print(
        "\n  **An entrance is a link from outside the route's own subtree.** The"
        "\n  Connection Center had two inbound links and was still unreachable:"
        "\n  both were inside the connection flow, so a customer could reach it"
        "\n  only by already being there. Counting those would make this check"
        "\n  pass on the exact defect it exists to catch."
    )
    return 1 if (args.strict and unreachable) else 0


if __name__ == "__main__":
    sys.exit(main())
