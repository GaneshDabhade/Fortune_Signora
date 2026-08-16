"""`docs/coordination/*.toml` is a planning projection — except `modules.toml`.

⛔ **[B-1005](../../docs/BUGS.md), ruled by [D-240](../../docs/DECISION_REGISTER.md) §1.**
Two independent classifiers were both blind to `.toml`: `_is_closeout` passed
the prefix and failed the suffix, and `IMPACT_RULES` matched nothing and fell
through to `platform`. **One blind spot, read as *too executable* by the cycle
warrant and *not documentary enough* by `--audit-main`, in the same minute.**

🔴 **The ruling is PATH-based and explicitly not suffix-based**, and the reason
is the case this file exists to pin: **`docs/coordination/modules.toml` is read
by `_audit_claims`**, so it is an operand of a gate. Adding `.toml` to
`CLOSEOUT_SUFFIXES` would have made an ownership change Closeout-legal — able to
reach `main` outside a certified snapshot and silently alter what the claim
audit accepts. 📁 **That is [B-014](../../docs/BUGS.md), one directory over.**

⚠️ **Allowlist, not denylist, and the direction of the failure is the point.**
A new projection omitted from `PLANNING_PROJECTIONS` classifies as executable
and costs one unnecessary certification — cheap and visible. A new *gate
operand* under that directory would, under a denylist, be absorbed as
documentation with nobody deciding it.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]


def _guard() -> ModuleType:
    path = REPO_ROOT / "infra" / "certification-guard.py"
    spec = importlib.util.spec_from_file_location("certification_guard_under_test", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules["certification_guard_under_test"] = module
    spec.loader.exec_module(module)
    return module


NON_EXECUTABLE = [
    pytest.param("docs/coordination/coordination.toml", id="the-published-projection"),
    pytest.param("docs/coordination/notices.toml", id="notices"),
    pytest.param("docs/coordination/workflows.toml", id="workflows"),
    pytest.param("docs/coordination/queues/lane-a.toml", id="a-lane-queue"),
    pytest.param("docs/coordination/queues/lane-c.toml", id="another-lane-queue"),
    pytest.param("docs/BACKLOG.md", id="an-ordinary-markdown-register"),
    pytest.param("PROJECT_STATUS.md", id="the-dashboard"),
    pytest.param("certification/manifest.json", id="the-certification-record"),
]

EXECUTABLE = [
    pytest.param("docs/coordination/modules.toml", id="THE-GATE-OPERAND"),
    pytest.param("backend/modules/people/domain/person.py", id="module-code"),
    pytest.param("infra/state-check.py", id="a-gate-itself"),
    pytest.param("infra/smoke.sh", id="another-gate"),
    pytest.param("frontend/app/page.tsx", id="a-screen"),
    pytest.param("backend/migrations/versions/0059_notification.py", id="a-migration"),
    pytest.param("docs/coordination/queues/lane-a.py", id="a-py-file-in-the-queues-directory"),
    pytest.param("pyproject.toml", id="a-toml-that-is-not-a-projection"),
]


@pytest.mark.parametrize("path", NON_EXECUTABLE)
def test_planning_paths_are_non_executable(path: str) -> None:
    assert _guard()._is_non_executable(path) is True, (
        f"{path} is a planning artifact and must not warrant a certification cycle"
    )


@pytest.mark.parametrize("path", EXECUTABLE)
def test_everything_else_stays_executable(path: str) -> None:
    """🔴 **`modules.toml` is the case that decides the shape of the fix.**

    ⛔ It shares a directory and a file extension with the projections and
    **nothing else that matters**: `_audit_claims` reads it, so a change to it
    changes what a gate accepts.
    """
    assert _guard()._is_non_executable(path) is False, (
        f"{path} must remain executable-class — a Closeout may not carry it"
    )


def test_modules_toml_is_actually_read_by_a_gate() -> None:
    """⚠️ **The premise, asserted rather than trusted to a comment.**

    ⛔ If `_audit_claims` ever stops reading `modules.toml`, the argument for
    excluding it evaporates and this test says so — **rather than leaving a
    future reader to obey a rule whose reason has gone.**
    """
    source = (REPO_ROOT / "infra" / "certification-guard.py").read_text()
    assert "docs/coordination/modules.toml" in source, (
        "the guard no longer reads modules.toml — re-derive whether it is still "
        "a gate operand before leaving it out of PLANNING_PROJECTIONS"
    )


def test_the_allowlist_is_not_empty() -> None:
    """⛔ **Guards against the empty-collection failure this repository keeps finding.**

    An allowlist that silently became empty would turn every case above green
    on the executable side and green on nothing else — the vacuous pass that
    `36-empty-array-checks.md` names.
    """
    guard = _guard()
    assert guard.PLANNING_PROJECTIONS, "PLANNING_PROJECTIONS is empty"
    assert guard.PLANNING_PROJECTION_DIRS, "PLANNING_PROJECTION_DIRS is empty"


def test_both_classifiers_share_the_predicate() -> None:
    """📁 **B-1005 was ONE blind spot reached by TWO routes.**

    ⚡ They were unified once already — the comment at the impact classifier
    records `CLAUDE.md` being classified two ways on the first run. **This
    asserts the unification rather than trusting it**, because a future edit
    that restates the condition at one site is exactly how B-1005 happened.
    """
    source = (REPO_ROOT / "infra" / "certification-guard.py").read_text()
    calls = source.count("_is_non_executable(path)")
    assert calls >= 2, (
        f"expected both classifiers to call the shared predicate, found {calls} call site(s) — "
        "a restated condition at one site is how B-1005 arose"
    )
