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
    # **The same class as the two above, and the reason is stronger here.** An
    # invitation link is the *only* way in: this is the one screen in Signora
    # shown to somebody who is not a member of the workspace it is about, so an
    # in-product entrance would have to live inside a tenant the reader cannot
    # yet see. `ConsoleInvitationDelivery` emits `{app_url}/join/{workspace_id}`.
    #
    # **Declared by Lane A on QE's explicit delegation** (B-123, 2026-08-05):
    # *"widening the check or exempting the route is this lane's call — QE will
    # not decide which."* This lane had argued at C-227 that the declaration was
    # QE's, on the strength of the comment above; **QE overruled that and the
    # overrule is right** — the lane that knows why a route has no entrance is
    # the lane that built it.
    "/join/[workspaceId]": (
        "reached from the invitation link, by design — the only screen shown to "
        "somebody who is not yet a member of the workspace it names"
    ),
    # **Reached from the identity provider, which is as outside as it gets.**
    # A federated sign-in that fails is redirected here by Better Auth, via the
    # `errorCallbackURL` on the sign-in request — so the only inbound reference
    # in the product is a constant in `lib/auth/client.ts`, and there is
    # deliberately no in-product link: nobody navigates to an error.
    #
    # **This route exists because the alternative was the vendor's own page.**
    # Better Auth serves a complete HTML document from `/api/auth/error`, and
    # without `errorCallbackURL` every refused OAuth sign-in landed there —
    # outside Signora, in another product's typography.
    #
    # **Declared by Lane A on the same delegation as the row above** (B-123):
    # the lane that knows why a route has no entrance is the lane that built it.
    # **A developer tool, and the only route here that is not a customer's.**
    # ⚡ **Nothing in the product links to it and nothing should**: it renders
    # only when `emailTransport` is `mailbox`, and `loadAuthConfig` refuses to
    # start with that transport in a deployed environment — so a customer can
    # never reach it, by construction rather than by omission.
    #
    # **Declared by Lane A on the same B-123 delegation as the rows above**:
    # the lane that knows why a route has no entrance is the lane that built
    # it. ⚠️ **Its placement was the product owner's choice** — `infra/` is
    # Lane C's module (TASK-474).
    "/dev/mailbox": (
        "the development mailbox — a developer tool, reachable only where "
        "`emailTransport` is `mailbox`, which cannot be a deployed environment"
    ),
    "/error": (
        "reached by redirect from the identity provider when a federated "
        "sign-in is refused — design 16, and nobody navigates to an error"
    ),
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


#: A JSX link element. **The evidence that a file hands out doors.**
_RENDERS_LINKS: Final = re.compile(r"<(?:Link|a)\b")

#: A route named as an object property — `{ href: '/business', label: … }`.
_HREF_PROPERTY: Final = re.compile(r"href:\s*[\"']([^\"']+)[\"']")


def _navigations(roots: tuple[Path, ...] | None = None) -> list[tuple[str, Path]]:
    """Every in-product navigation, as `(target, the file that offers it)`.

    Covers what this codebase actually writes: `href="…"`, `href={`…`}`,
    `router.push(…)`, `redirect(…)`, `replace(…)` — and **a route named as an
    object property, in a file that renders links.** Verified against the
    repository rather than assumed: a pattern nobody uses would be dead
    matching, and one that is used and unmatched would make the check lie.

    ### The object-property case, and why it is conditional

    **This check could not see the sidebar** until CX-05, and nothing revealed
    it, because `navigation.tsx` holds its routes in an array — `{ href: '/',
    label: 'Attention' }` — and renders them through `<Link href={item.href}>`.
    No pattern above matches either half. **The product's primary source of
    doors was invisible to the check that exists to find missing doors.**

    It went unnoticed because both existing entries had a second, literal
    entrance elsewhere: `/` from six places, and `/settings` from exactly one —
    `no-workspace.tsx`. **Delete that one file and `/settings` reports as an
    orphan**, which is the check being wrong about the most-used screen in the
    product. CX-05 surfaced it by adding the first navigation entry since the
    check was written.

    **Why it is not simply `href:\\s*'…'` everywhere.** `GUARDED_ROUTES` in
    `permissions.ts` has the identical shape — `{ href: '/settings', requires:
    … }` — and it is a *guard declaration*, the opposite of an entrance:
    naming a route there restricts it. Counting it would let a route be
    "reachable" because something forbade it.

    **So the rule is: a route named in a file that renders links is a door; a
    route named in a file that renders nothing is a declaration.** It separates
    the two cases in this repository exactly, and it keeps the check's bias in
    the right direction — a new form of *declaration* stays unmatched, which
    reports a false orphan rather than hiding a real one.
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
            if _RENDERS_LINKS.search(text):
                for target in _HREF_PROPERTY.findall(text):
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
