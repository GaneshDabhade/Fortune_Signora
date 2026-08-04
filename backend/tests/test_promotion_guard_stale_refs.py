"""The gatekeeper must not answer its central question from a stale clone.

**`--next-cycle` answers *"is there anything worth certifying?"*** from
`main..integration` — **local** refs. A fetch moves `origin/integration` and
leaves `integration` exactly where it was, and QE's monitoring loop does nothing
but fetch.

> Asked on 2026-08-04 while `integration` sat one commit behind
> `origin/integration`, it printed **"Repository Ready — nothing awaits
> certification"**. That is a *confident false negative* on the one question the
> gatekeeper exists to answer, and it is indistinguishable from the true answer.

**The staleness of a local ref was a hidden input** (`CLAUDE.md` §2) — it changed
the answer without appearing in the question. The correction is not to fetch
inside the tool, which would make a gate depend on the network, but to notice
that the inputs are older than what `origin` last returned and refuse.

**Refuse for `--next-cycle`; note it for the audits.** `integration` moves while
QE certifies *by design*, and the snapshot rule forbids chasing it — an audit
that refused for staleness would be wrong exactly when it is most used.

These tests build a real clone with a real remote, because the property under
test is a property of git: *does a fetch leave the local branch behind?* A fake
would prove only that the fake agreed.
"""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path
from types import ModuleType

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture(scope="module")
def guard() -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        "certification_guard_stale", REPO_ROOT / "infra" / "certification-guard.py"
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _run(*args: str, cwd: Path) -> str:
    return subprocess.run(
        ["git", *args], cwd=cwd, capture_output=True, text=True, check=True
    ).stdout.strip()


def _commit(clone: Path, path: str, text: str, message: str) -> None:
    target = clone / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text)
    _run("add", path, cwd=clone)
    _run("commit", "-m", message, cwd=clone)


@pytest.fixture
def clone(tmp_path: Path) -> Path:
    """A clone whose `origin/integration` is ahead of its `integration`.

    Built the way the real one gets that way: somebody else pushes, this clone
    fetches, and nothing fast-forwards it.
    """
    origin = tmp_path / "origin.git"
    _run("init", "--bare", "--initial-branch=main", str(origin), cwd=tmp_path)

    author = ("-c", "user.email=qe@signora.test", "-c", "user.name=QE")
    first = tmp_path / "first"
    _run("clone", str(origin), str(first), cwd=tmp_path)
    subprocess.run(["git", *author, "config", "user.email", "qe@signora.test"], cwd=first)
    _run("config", "user.name", "QE", cwd=first)
    _run("config", "user.email", "qe@signora.test", cwd=first)
    _commit(first, "docs/BACKLOG.md", "queue\n", "baseline")
    _run("branch", "integration", cwd=first)
    _run("push", "origin", "main", "integration", cwd=first)

    other = tmp_path / "other"
    _run("clone", str(origin), str(other), cwd=tmp_path)
    _run("config", "user.name", "Lane B", cwd=other)
    _run("config", "user.email", "b@signora.test", cwd=other)
    _run("checkout", "integration", cwd=other)
    _commit(other, "docs/ACTIVE_ASSIGNMENTS.md", "board\n", "Lane B reports AVAILABLE")
    _run("push", "origin", "integration", cwd=other)

    _run("fetch", "origin", cwd=first)  # fetched, deliberately not fast-forwarded
    return first


def test_a_fetch_leaves_the_local_branch_behind(clone: Path) -> None:
    """**The control, and the whole premise.**

    If a fetch ever moved the local branch, every assertion below would pass
    while the defect it guards was unreachable.
    """
    assert _run("rev-parse", "integration", cwd=clone) != _run(
        "rev-parse", "origin/integration", cwd=clone
    )
    assert _run("rev-list", "--count", "integration..origin/integration", cwd=clone) == "1"


def test_it_sees_the_branch_this_clone_is_behind_on(
    guard: ModuleType, clone: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(guard, "REPO_ROOT", clone)
    assert guard._behind_origin() == [("integration", 1)]


def test_a_branch_ahead_of_origin_is_not_stale(
    guard: ModuleType, clone: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """**Only *behind* counts.**

    A local branch ahead of `origin` is a promotion QE has not pushed yet — a
    normal intermediate state of the lifecycle, and reporting it as staleness
    would refuse the one command run at exactly that moment.
    """
    monkeypatch.setattr(guard, "REPO_ROOT", clone)
    _run("checkout", "main", cwd=clone)
    _commit(clone, "PROJECT_STATUS.md", "closed out\n", "Closeout")
    assert [ref for ref, _ in guard._behind_origin()] == ["integration"]


def test_next_cycle_refuses_rather_than_reporting_repository_ready(
    guard: ModuleType, clone: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """**The defect, stated as a property.**

    Before the fix this returned 0 and printed `Repository Ready` — while a
    commit sat on `origin/integration` waiting to be assessed.
    """
    monkeypatch.setattr(guard, "REPO_ROOT", clone)
    assert guard._next_cycle() == 1
    printed = capsys.readouterr().out
    assert "REFUSED" in printed
    # The *claim*, not the phrase — the refusal quotes `Repository Ready` while
    # explaining which answer it is refusing to give.
    assert "Nothing awaits certification" not in printed
    assert "merge --ff-only origin/integration" in printed, "no way out was offered"


def test_a_current_clone_still_gets_its_answer(
    guard: ModuleType, clone: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """**The check must not become the answer.**

    A guard that refused unconditionally would pass the test above while
    destroying the command — so the same clone, fast-forwarded, must reach the
    real assessment.
    """
    monkeypatch.setattr(guard, "REPO_ROOT", clone)
    _run("checkout", "integration", cwd=clone)
    _run("merge", "--ff-only", "origin/integration", cwd=clone)

    assert guard._behind_origin() == []
    assert guard._next_cycle() == 0
    printed = capsys.readouterr().out
    assert "REFUSED" not in printed
    assert "No cycle needed" in printed, "a documentation-only commit stopped accumulating"


def test_the_audits_report_the_gap_and_carry_on(
    guard: ModuleType, clone: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """**An audit names what it could not see; it does not refuse.**

    `integration` moves while QE certifies, deliberately (§20e, *`integration`
    keeps moving, and that is fine*). An audit that refused for staleness would
    force QE to chase the head mid-cycle — the exact thing the Certification
    Snapshot forbids.
    """
    monkeypatch.setattr(guard, "REPO_ROOT", clone)
    guard._scope_note()
    printed = capsys.readouterr().out
    assert "note —" in printed
    assert "REFUSED" not in printed


def test_a_clone_without_the_remote_ref_is_not_reported_stale(
    guard: ModuleType, clone: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Absence of a comparison is not evidence of staleness.

    A fork, a shallow clone, or a differently-named remote has nothing to
    compare against, and inventing a warning there would train an operator to
    ignore the one that matters.
    """
    monkeypatch.setattr(guard, "REPO_ROOT", clone)
    _run("remote", "remove", "origin", cwd=clone)
    assert guard._behind_origin() == []
