"""`doc-drift` measures from `origin/integration`, never the local branch.

**The defect these were written from.** The default range was the bare string
``integration..HEAD``. A branch name resolves to whatever *this clone* last had
there, so on a lane whose local ``integration`` was 49 commits behind, the tool
reported **95 changed files and named three modules the slice never touched** —
attributing another lane's promoted work to the slice being handed to QE.

⛔ **The damage is not the noise; it is what noise does to an advisory gate.**
A check that cries drift on work you did not do is a check people learn to run
past, and then it is worth less than nothing — it looks like coverage.

⚡ **Every other tool in `infra/` already used `origin/integration`.**
`repository-dashboard.py` even states the rule: *counted from the ref a lane
can actually claim from, never from the working tree and never from a lane
branch.* `doc-drift.py` was the single outlier.

**Written behaviourally, deliberately.** An earlier fix in this directory was
covered by a test that asserted how the code was *written*, and it turned out to
be Decorative Logic — the mutation killed the test without changing behaviour.
So these build two refs that genuinely disagree and assert on what the tool
*reports*: collapse the default back to the local branch and they fail.
"""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from collections.abc import Iterator
from pathlib import Path

import pytest

_SPEC = importlib.util.spec_from_file_location(
    "doc_drift", Path(__file__).resolve().parents[2] / "infra" / "doc-drift.py"
)
assert _SPEC is not None and _SPEC.loader is not None
drift = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(drift)


def _run(*args: str, cwd: Path) -> None:
    subprocess.run(args, cwd=cwd, check=True, capture_output=True, text=True)


def _commit(repo: Path, path: str, body: str, message: str) -> None:
    target = repo / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(body)
    _run("git", "add", "-A", cwd=repo)
    _run("git", "commit", "-q", "-m", message, cwd=repo)


@pytest.fixture
def diverged(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[Path]:
    """A clone whose local `integration` and `origin/integration` disagree.

    This is the ordinary state of a lane between fetches, not a contrived one:
    the local branch simply has not been fast-forwarded yet.

      base ──▶ local `integration`  ──▶ another lane's module work
                                    ──▶ origin/integration
                                             └──▶ HEAD, touching nothing but infra/
    """
    repo = tmp_path / "clone"
    repo.mkdir()
    _run("git", "init", "-q", "-b", "work", cwd=repo)
    _run("git", "config", "user.email", "t@t", cwd=repo)
    _run("git", "config", "user.name", "t", cwd=repo)

    _commit(repo, "README.md", "base\n", "base")
    _run("git", "branch", "integration", cwd=repo)

    # What another lane promoted after this clone last fetched. `signal_engine`
    # has a design document in MODULE_DOCS and this leaves it untouched, so a
    # tool measuring from the STALE ref must report drift against it.
    _commit(repo, "backend/modules/signal_engine/domain/rules.py", "x = 1\n", "another lane")
    _run("git", "update-ref", "refs/remotes/origin/integration", "HEAD", cwd=repo)

    # This lane's own slice: infrastructure tooling only, no module touched.
    _commit(repo, "infra/tool.py", "y = 2\n", "this lane's slice")

    monkeypatch.setattr(drift, "REPO_ROOT", repo)
    # `main()` reads `sys.argv`, which under pytest is pytest's own. Baseline it
    # to a bare invocation so the DEFAULT path is what runs; a test wanting an
    # explicit range overrides this.
    monkeypatch.setattr(sys, "argv", ["doc-drift.py"])
    yield repo


class TestTheDefaultRangeIsTheRemote:
    def test_a_slice_touching_no_module_reports_no_module(
        self, diverged: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """✅ **The behaviour the defect denied.**

        The slice changed `infra/` and nothing else. Measured from
        `origin/integration` that is zero modules; measured from the stale local
        branch it is one, with a drift finding attached to somebody else's work.
        """
        assert drift.main() == 0

        reported = capsys.readouterr().out
        # ⚠️ **Behaviour first, and the order is deliberate.** The range string
        # is the weakest of the three — it describes how the tool was written.
        # Asserting it first would let it fire before the two that describe what
        # the tool CONCLUDED, and a mutation killed by a source-shaped assertion
        # is how B-436 shipped Decorative Logic that looked load-bearing.
        assert "signal_engine" not in reported, (
            "another lane's promoted module must not appear in this slice's range"
        )
        assert "0 module(s) touched" in reported
        assert "origin/integration..HEAD" in reported

    def test_measuring_from_the_stale_local_branch_would_blame_another_lane(
        self, diverged: Path, monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """🔴 **The defect itself, pinned as executable evidence.**

        ⛔ **Not a test of the fix — a test that the wrong range genuinely
        produces the wrong answer**, so the test above is measuring something
        real rather than passing for an unrelated reason. **A regression test
        whose failure mode was never demonstrated is a test nobody can trust**,
        and this directory has already shipped one of those.
        """
        monkeypatch.setattr(sys, "argv", ["doc-drift.py", "integration..HEAD"])

        drift.main()

        reported = capsys.readouterr().out
        assert "signal_engine" in reported, (
            "the stale range must blame another lane — otherwise the fixture "
            "does not reproduce the defect and the sibling test proves nothing"
        )

    def test_an_explicit_range_is_still_honoured(
        self, diverged: Path, monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """⚡ **The default changed; the argument did not.**

        Explicit ranges are how QE and a lane narrow the question, and changing
        a default must never quietly override one that was passed.
        """
        monkeypatch.setattr(sys, "argv", ["doc-drift.py", "HEAD~1..HEAD"])

        assert drift.main() == 0
        assert "HEAD~1..HEAD" in capsys.readouterr().out


class TestAnUnresolvableRemoteRefuses:
    def test_it_refuses_rather_than_falling_back(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """⛔ **The silent fallback IS the bug, so there is no silent fallback.**

        A clone with no `origin/integration` — never fetched, or a fresh local
        repository — gets a diagnostic naming the cause and exit 2. ⚠️ **Falling
        back to the local branch here would reintroduce the defect on exactly
        the clones least likely to notice it.**
        """
        repo = tmp_path / "lonely"
        repo.mkdir()
        _run("git", "init", "-q", "-b", "work", cwd=repo)
        _run("git", "config", "user.email", "t@t", cwd=repo)
        _run("git", "config", "user.name", "t", cwd=repo)
        _commit(repo, "README.md", "base\n", "base")
        _run("git", "branch", "integration", cwd=repo)

        monkeypatch.setattr(drift, "REPO_ROOT", repo)
        monkeypatch.setattr(sys, "argv", ["doc-drift.py"])

        assert drift.main() == 2

        explained = capsys.readouterr().err
        assert "does not resolve" in explained
        assert "git fetch origin" in explained
