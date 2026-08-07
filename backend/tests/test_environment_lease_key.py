"""The lease is named for a stack, not for the text of a shell variable.

[B-141](../../docs/BUGS.md), found by QE verifying
[483](../../docs/architecture/483-environment-isolation-audit.md) rather than
accepting it. `infra/docker-compose.yml` declares:

    name: ${COMPOSE_PROJECT_NAME:-signora-v2}

**Docker Compose expands that. The regex reading it did not.** So every clone
without the variable exported computed the *literal string* as its resource
name, and they all computed the same one — **the live lease file was named
`${COMPOSE_PROJECT_NAME:-signora-v2}.lease`, character for character**, while
three separate stacks ran. ⛔ **Two of QE's aborts this session, 270s and 120s,
were that.**

⚠️ **The `"signora-v2"` fallback was also unreachable**: the middle term of
`_resource`'s `or` chain returned a truthy literal, so the third was never
taken. **A default nothing can reach is not a default.**

**Nothing here reads the repository's own compose file.** Asserting that the
current `name:` line expands correctly would pass identically with `_expand`
deleted, so long as somebody exported the variable — the Decorative Logic
`CLAUDE.md` §2 names. The forms below are written out.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]


def _load_lease() -> ModuleType:
    path = REPO_ROOT / "infra" / "environment-lease.py"
    spec = importlib.util.spec_from_file_location("environment_lease", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


lease = _load_lease()


@pytest.mark.parametrize(
    ("declared", "exported", "expected"),
    [
        # ⛔ **The defect itself.** Unset, this returned the literal.
        ("${COMPOSE_PROJECT_NAME:-signora-v2}", None, "signora-v2"),
        # ✅ An exported value wins, which is how a lane names its own stack.
        ("${COMPOSE_PROJECT_NAME:-signora-v2}", "signora-lane-b", "signora-lane-b"),
        # ⚡ A plain literal is already a project name — `docker-compose.prod.yml`
        # declares `name: signora-prod`, and it was the one file that was right.
        ("signora-prod", None, "signora-prod"),
        # ⛔ No default and nothing exported resolves to nothing, so the caller
        # falls back rather than leasing a name no stack answers to.
        ("${COMPOSE_PROJECT_NAME}", None, None),
        ("${COMPOSE_PROJECT_NAME}", "signora-lane-a", "signora-lane-a"),
        # ⚠️ An empty default is not a name.
        ("${COMPOSE_PROJECT_NAME:-}", None, None),
        # ⛔ Anything this does not understand returns `None` on purpose —
        # §6, build for the requirement in front of you. Guessing at a
        # half-parsed name is worse than falling back.
        ("${broken", None, None),
        ("${a:-b:-c}", None, "b:-c"),
    ],
)
def test_expand_reads_the_form_compose_uses(
    monkeypatch: pytest.MonkeyPatch, declared: str, exported: str | None, expected: str | None
) -> None:
    monkeypatch.delenv("COMPOSE_PROJECT_NAME", raising=False)
    if exported is not None:
        monkeypatch.setenv("COMPOSE_PROJECT_NAME", exported)
    assert lease._expand(declared) == expected


def test_the_literal_that_was_the_defect_is_never_returned(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """⛔ The one assertion that would have caught it, stated as itself.

    **A lease path is `LEASE_DIR / f"{_resource()}.lease"`**, so a resource
    containing `$`, `{` or `}` is a filename naming no stack — and every clone
    computing it shares one lease. ⚡ **This asserts the property rather than
    the value**, so it keeps holding if the compose file's default changes.
    """
    monkeypatch.delenv("COMPOSE_PROJECT_NAME", raising=False)
    resolved = lease._expand("${COMPOSE_PROJECT_NAME:-signora-v2}")
    assert resolved is not None
    assert not set(resolved) & set("${}")


def test_two_stacks_do_not_share_a_lease(monkeypatch: pytest.MonkeyPatch) -> None:
    """⚡ The whole point, and it is what B-141 measured as lost.

    QE certifying `signora-prod` must not stop Lane B testing in
    `signora-lane-b`. **Before the fix both computed the same literal**, so the
    second refused to start against a stack the first was not touching.
    """
    monkeypatch.setenv("COMPOSE_PROJECT_NAME", "signora-lane-b")
    lane_b = lease._resource()
    monkeypatch.setenv("COMPOSE_PROJECT_NAME", "signora-prod")
    certifying = lease._resource()
    assert lane_b != certifying
