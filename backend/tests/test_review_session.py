"""A review session names the build the reviewer is actually looking at.

`infra/review.py` answers one question a product owner cannot answer for
themselves: *"is what I am about to review a build this repository certified?"*
**Getting it wrong is silent** — the answer is a line on a card, it is plausible
either way, and nobody re-derives it.

The first implementation asked *"is `HEAD` certified?"* and was wrong on `main`
every single time. A Repository Closeout commit **can never be certified**: a
certification record cannot contain its own commit hash, so the commit that
*writes* the record is always created after the run it records (`CLAUDE.md`
§20e). Every review on `main` would have reported *"no certification record for
this commit"* about a repository whose every promotion was certified — the most
damaging shape of wrong, because it is alarming, confident and false.

Walking back to the nearest certified ancestor is sound **only** because
`--audit-main` proves a Closeout commit changes nothing executable. So the walk
verifies that per commit rather than assuming it, and the case that must not
regress is the one where an executable commit sits in between: there the running
software is *not* the certified software, and saying otherwise would be this
repository certifying something it never measured.

**Every history below is fixed text.** Driving the live repository would pass
today and pass identically with the closeout check deleted — the Decorative
Logic `CLAUDE.md` §2 names.
"""

from __future__ import annotations

import importlib.util
import re
import sys
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture(scope="module")
def review() -> ModuleType:
    spec = importlib.util.spec_from_file_location("review", REPO_ROOT / "infra" / "review.py")
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


RUN: dict[str, Any] = {"commit": "c" * 40, "certified_at": "2026-08-03T16:07:45+00:00", "coverage": 95.5}

#: Newest first, exactly as `git rev-list` orders it.
HISTORY = ["closeout2", "closeout1", "c" * 40, "older"]


def _everything_is_a_closeout(commit: str) -> bool:
    return commit.startswith("closeout")


def test_the_certified_commit_itself_is_reported_with_no_distance(review: ModuleType) -> None:
    result = review.verification_from(
        passing={"c" * 40: RUN}, ancestors=["c" * 40, "older"], is_closeout=_everything_is_a_closeout
    )
    assert result["certified"] is True
    assert result["commits_since"] == 0


def test_closeout_commits_above_a_certified_one_still_count_as_certified(
    review: ModuleType,
) -> None:
    """**The case the first implementation got wrong**, and the normal case on
    `main`: the head is a Closeout record written after the run it describes."""
    result = review.verification_from(
        passing={"c" * 40: RUN}, ancestors=HISTORY, is_closeout=_everything_is_a_closeout
    )
    assert result["certified"] is True
    assert result["commit"] == "c" * 40
    assert result["commits_since"] == 2
    assert result["uncertified_executable"] == []


def test_an_executable_commit_above_the_certified_one_is_not_certified(
    review: ModuleType,
) -> None:
    """**The guarantee.** A commit that changes executable code invalidates the
    inheritance — the reviewer is running software nothing measured, and the
    session record must say so rather than crediting the ancestor's result."""
    result = review.verification_from(
        passing={"c" * 40: RUN},
        ancestors=["hotfix00000", "closeout1", "c" * 40],
        is_closeout=lambda commit: commit.startswith("closeout"),
    )
    assert result["certified"] is False
    assert result["uncertified_executable"] == ["hotfix00000"]
    assert "NOT CERTIFIED" in review._verdict(result, long=False)


def test_an_empty_manifest_is_unknown_rather_than_uncertified(review: ModuleType) -> None:
    """*Nobody measured* and *it was measured and failed* are different claims.

    Collapsing them lets the friendlier one absorb the alarming one, which is
    how a review would report a clean build for a repository that has none.
    """
    absent = review._verdict({"known": False}, long=False)
    failed = review._verdict({"known": True, "certified": False}, long=False)
    assert "unknown" in absent
    assert "NOT CERTIFIED" in failed
    assert absent != failed


def test_a_certified_ancestor_beyond_the_walk_is_not_claimed(review: ModuleType) -> None:
    """The walk is bounded. A history longer than the bound reports *not
    certified* rather than searching forever or crediting a commit it never
    reached — an honest negative, not a silent positive."""
    result = review.verification_from(
        passing={"c" * 40: RUN}, ancestors=["a", "b"], is_closeout=_everything_is_a_closeout
    )
    assert result["certified"] is False


def test_the_review_environment_is_derived_and_never_literal(review: ModuleType) -> None:
    """**No port is written into `review.py` as a value.**

    The whole worth of the environment model is that an allocation lives in one
    place. A literal `3000` here would compile, run, and be wrong the day the
    allocation moves — with nothing to catch it, because the review would still
    start.

    **Parsed rather than grepped.** A first version searched the file text and
    failed on a *comment* explaining why the production stack moved off 3000 —
    prose about a port is not a dependency on one, and a check that cannot tell
    the difference teaches people to weaken it. This walks the AST, so only
    values count.
    """
    import ast

    tree = ast.parse((REPO_ROOT / "infra" / "review.py").read_text())
    forbidden = {3000, 8000, 3100, 8100, 3200, 8200}
    literals = {
        node.value
        for node in ast.walk(tree)
        if isinstance(node, ast.Constant) and isinstance(node.value, int)
    }
    offending = literals & forbidden
    assert not offending, (
        f"{sorted(offending)} is written into review.py as a value; derive it from the profile"
    )
    # `localhost:` **followed by digits**. An f-string prefix parses as the bare
    # constant `"http://localhost:"` with the port as a separate FormattedValue,
    # and that is the derived form this test exists to encourage — flagging it
    # would make the correct code fail the check.
    urls = {
        node.value
        for node in ast.walk(tree)
        if isinstance(node, ast.Constant)
        and isinstance(node.value, str)
        and re.search(r"localhost:\d", node.value)
    }
    assert not urls, f"{sorted(urls)} hard-codes a host and port; build it from the profile"


def test_the_dataset_is_read_from_the_seeder_that_seeds_it(review: ModuleType) -> None:
    """A record naming the wrong dataset is worse than one naming none.

    The product owner's stated direction is several representative datasets, so
    a session record must identify which one it showed. This reads the seeder
    rather than restating its choice.
    """
    # ⚠️ **`playground@3` by [TASK-1480](../../docs/BACKLOG.md), then
    # `playground@4` by [TASK-429](../../docs/BACKLOG.md)** — the version where
    # each company's contacts have names. ⚡ The docstring above is why the
    # literal has to move with the seeder: this test reads the seeder's choice
    # rather than restating it, **so a stale literal here would be the record
    # naming the wrong dataset that it exists to prevent.** It has now caught
    # exactly that, twice.
    assert review._dataset() == "playground@4"


def test_known_limitations_carry_a_title_a_reviewer_can_act_on(review: ModuleType) -> None:
    """A reviewer who rediscovers a known defect spent their session on it.

    An identifier alone does not prevent that — `B-103` means nothing to a
    product owner. The title is what makes the list a warning rather than a
    reference.
    """
    limitations, _ = review._known_limitations()
    assert limitations, "the register has open rows; the card would show none"
    assert all("(no title)" not in row for row in limitations), (
        "a heading stopped parsing — the list degrades to identifiers silently"
    )


def test_defects_a_reviewer_cannot_meet_are_counted_rather_than_dropped(
    review: ModuleType,
) -> None:
    """Filtering must never make a defect disappear.

    The first run showed fourteen open rows, most about `make certify` and
    `state-check` — invisible from a browser and pure noise on a card a product
    owner reads. Filtering them out is right; **losing them is not**, so the
    count is carried and stated.
    """
    shown, hidden = review._known_limitations()
    assert hidden > 0, "no row was classified as unreachable — the filter is inert"
    assert len(shown) + hidden == len(
        [row for row in review.registers.bug_rows((REPO_ROOT / "docs" / "BUGS.md").read_text()) if row.unresolved]
    ), "rows went missing between the register and the card"


def test_an_unrecognised_module_is_shown_rather_than_hidden(review: ModuleType) -> None:
    """**The filter fails toward the reviewer.**

    `Module` is prose, not a taxonomy, so any classifier is partly wrong. The
    direction of the error is the decision: over-reporting costs one glance,
    under-reporting costs the session in which somebody rediscovers a defect
    already written down. A phrase nobody anticipated must therefore be *kept*.
    """
    assert not any(
        phrase in "commercial_profile — the opportunity list"
        for phrase in review.NOT_REACHABLE_BY_A_REVIEWER
    ), "a product module's description matched an exclusion phrase — reviewers would stop seeing it"


def test_the_production_stack_does_not_bind_the_review_ports(review: ModuleType) -> None:
    """**The isolation guarantee, asserted where it can actually fail.**

    `infra/docker-compose.prod.yml` bound `3000:3000` and `8000:8000` — the
    same host ports a review session uses — which made a certification run and
    a product review **mutually exclusive by construction**. It was not a
    theoretical conflict: the product owner could not start a review because a
    leftover `make dr` stack still held both, and `release-preflight.py` existed
    largely to explain the collision rather than remove it.

    The stack now publishes on 3100/8100. **Proven by running both at once** —
    the full 24-stage smoke test completed while a live review session stayed
    healthy — and asserted here so a future edit to the compose file cannot
    quietly reintroduce it. A regression would not fail any other gate: smoke
    would pass on an otherwise-idle machine and fail only when somebody was
    reviewing.
    """
    compose = (REPO_ROOT / "infra" / "docker-compose.prod.yml").read_text()
    published = re.findall(r'^\s*-\s*"(\d+):(\d+)"\s*$', compose, re.M)
    host_ports = {int(host) for host, _ in published}

    profile = review.PROFILE
    collisions = host_ports & {profile.web_port, profile.api_port}
    assert not collisions, (
        f"the production stack publishes {sorted(collisions)}, which human review uses. "
        "A certification run and a product review would again be mutually exclusive."
    )


def test_the_jwt_issuer_matches_the_published_frontend_port(review: ModuleType) -> None:
    """A browser-facing issuer must name the port a browser reaches.

    The issuer is a JWT claim minted by the frontend and verified by the API,
    and it is browser-facing — so it tracks the **host** port, not the
    container's. Moving the published ports without it mints tokens the API
    rejects, and the symptom is every request 401ing with no clue why.
    **The smoke test's cross-tier JWT stage catches it**; this catches it in a
    second, and says which line is wrong.
    """
    compose = (REPO_ROOT / "infra" / "docker-compose.prod.yml").read_text()
    issuers = set(re.findall(r"SIGNORA_JWT_ISSUER:\s*http://localhost:(\d+)", compose))
    frontend = re.search(r'-\s*"(\d+):3000"', compose)
    assert frontend, "the frontend no longer publishes a host port; this test cannot see it"
    assert issuers == {frontend.group(1)}, (
        f"issuer(s) {sorted(issuers)} do not match the published frontend port "
        f"{frontend.group(1)} — tokens would be minted for a port nobody reaches"
    )
