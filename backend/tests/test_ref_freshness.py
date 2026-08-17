"""A remote ref is only as fresh as the last fetch, and a stale one must say so.

**The failure this prevents has cost the repository four times**, and it is the
same shape every time: *a measurement that is plausible and wrong, where the
reader cannot tell the difference.* Four Lane C reports on 2026-08-04 reported
idleness at lanes that were shipping · Lane C reported a branch fast-forwardable
against refs it had measured but not pushed or not fetched · `doc-drift`
measured the local `integration` and blamed one lane for another's work
([B-439](../../docs/BUGS.md)) · QE was one step from replying *"your export is
not there"* after grepping a ref older than the one it had been told about.

**`repository-dashboard.py` had solved it for itself and nothing else adopted
it** ([B-441](../../docs/BUGS.md)), so three tools reading `origin/integration`
still had no refresh — including `doc-drift.py`, an hour after B-439 made it
depend on that ref.

⛔ **These are built against a real remote rather than a mock**, because the
behaviour under test IS the fetch. A faked `git fetch` would leave the one
question that matters — *does the ref actually move?* — unasked.
"""

from __future__ import annotations

import importlib.util
import subprocess
from collections.abc import Iterator
from pathlib import Path

import pytest

_SPEC = importlib.util.spec_from_file_location(
    "refs", Path(__file__).resolve().parents[2] / "infra" / "refs.py"
)
assert _SPEC is not None and _SPEC.loader is not None
refs = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(refs)


def _run(*args: str, cwd: Path) -> str:
    return subprocess.run(
        args, cwd=cwd, check=True, capture_output=True, text=True
    ).stdout.strip()


def _commit(repo: Path, name: str) -> None:
    (repo / name).write_text(name)
    _run("git", "add", "-A", cwd=repo)
    _run("git", "commit", "-q", "-m", name, cwd=repo)


@pytest.fixture
def clone_and_remote(tmp_path: Path) -> Iterator[tuple[Path, Path]]:
    """A real clone of a real remote, which has since moved ahead of it.

    This is the ordinary state of every lane between fetches — not a contrived
    one — which is why the tools had to be taught to notice it.
    """
    origin = tmp_path / "origin"
    origin.mkdir()
    _run("git", "init", "-q", "-b", "integration", cwd=origin)
    _run("git", "config", "user.email", "t@t", cwd=origin)
    _run("git", "config", "user.name", "t", cwd=origin)
    _commit(origin, "base")

    clone = tmp_path / "clone"
    _run("git", "clone", "-q", str(origin), str(clone), cwd=tmp_path)
    _run("git", "config", "user.email", "t@t", cwd=clone)
    _run("git", "config", "user.name", "t", cwd=clone)

    # The remote moves. The clone does not know yet — this is the whole defect.
    _commit(origin, "one")
    _commit(origin, "two")

    yield clone, origin


class TestAStaleRefAnnouncesItself:
    def test_it_reports_how_far_behind_the_clone_was(
        self, clone_and_remote: tuple[Path, Path]
    ) -> None:
        """✅ **The behaviour, and the number is the useful part.**

        *"advanced 2 commits"* tells a reader their previous conclusion was
        drawn from a repository two commits old. ⛔ **A bare *"refreshed"* would
        not** — it reads as routine, and routine is what gets skimmed.
        """
        clone, _ = clone_and_remote

        notice = refs.refresh("origin/integration", clone)

        assert notice is not None
        assert "advanced 2 commit(s)" in notice
        assert "stale" in notice

    def test_the_ref_actually_moves(
        self, clone_and_remote: tuple[Path, Path]
    ) -> None:
        """🔴 **The half a mocked fetch could never check.**

        ⛔ **Reporting staleness while leaving the ref stale would be worse than
        silence** — every figure measured after the notice would still be wrong,
        and the notice would read as though it had been dealt with.
        """
        clone, origin = clone_and_remote
        before = _run("git", "rev-parse", "origin/integration", cwd=clone)

        refs.refresh("origin/integration", clone)

        after = _run("git", "rev-parse", "origin/integration", cwd=clone)
        assert before != after
        assert after == _run("git", "rev-parse", "integration", cwd=origin)


class TestSilenceIsReservedForNothingToSay:
    def test_an_already_current_ref_says_nothing(
        self, clone_and_remote: tuple[Path, Path]
    ) -> None:
        """⚡ **The common path, and it must be quiet.**

        A notice on every run is noise, and noise is how an advisory signal
        stops being read — the same reasoning B-439 records about `doc-drift`.
        """
        clone, _ = clone_and_remote
        refs.refresh("origin/integration", clone)

        assert refs.refresh("origin/integration", clone) is None

    def test_a_local_ref_is_left_alone(
        self, clone_and_remote: tuple[Path, Path]
    ) -> None:
        """⛔ **There is nothing to fetch for a local branch**, and pretending
        otherwise would put a network call on every local measurement."""
        clone, _ = clone_and_remote

        assert refs.refresh("integration", clone) is None
        assert refs.refresh("HEAD", clone) is None


class TestSkipIsHonoured:
    def test_skip_does_not_fetch(
        self, clone_and_remote: tuple[Path, Path]
    ) -> None:
        """✅ **`--no-fetch` is the offline path, and it must genuinely skip.**

        ⛔ **Asserting only that it returns `None` would pass even if it fetched
        first** — so the ref itself is checked, which is the behavioural
        question rather than the shape one.
        """
        clone, _ = clone_and_remote
        before = _run("git", "rev-parse", "origin/integration", cwd=clone)

        assert refs.refresh("origin/integration", clone, skip=True) is None

        assert _run("git", "rev-parse", "origin/integration", cwd=clone) == before


class TestItNeverBlocksTheMeasurement:
    def test_an_unreachable_remote_reports_and_returns(
        self, clone_and_remote: tuple[Path, Path]
    ) -> None:
        """⚡ **Offline is a normal state, not an error state.**

        ⛔ **A tool that refused to run without a network is one people stop
        running.** The reading is still useful; what it must not do is present
        an unknown age as a known one. **The ref is still readable here, so the
        run proceeds and the caller is told nothing alarming.**
        """
        clone, origin = clone_and_remote
        _run("git", "remote", "set-url", "origin", str(origin / "gone"), cwd=clone)

        notice = refs.refresh("origin/integration", clone)

        # The fetch fails; the ref is unchanged and still resolves, so there is
        # nothing new to say and the caller measures what it already had.
        assert notice is None
        assert _run("git", "rev-parse", "origin/integration", cwd=clone)
