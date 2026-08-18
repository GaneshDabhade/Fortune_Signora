"""Every browser target refuses a portless `E2E_URL` rather than running against port 80.

`infra/environments.py current()` returns `None` on `integration`, `main` **and a
detached head** — and certification runs detached at the pinned SHA. No environment
means no `SIGNORA_WEB_PORT`, which makes `E2E_URL` end in a bare colon.

The failure mode is what makes this worth a test rather than a comment: the suite
runs, every browser test fails with `ERR_CONNECTION_REFUSED`, and **the run reports
them as ordinary failures**. A gate that reports red about nothing is worse than no
gate, because it is indistinguishable from a broken product (B-1014).

The assertions are on the *shape* — every target consuming `E2E_URL` must depend on
the guard — so a browser target added later is caught by construction rather than by
somebody remembering this file exists.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
MAKEFILE = REPO_ROOT / "Makefile"
GUARD = "require-e2e-url"


def _makefile() -> str:
    return MAKEFILE.read_text()


def _targets_using_e2e_url() -> set[str]:
    """Targets whose recipe reaches the browser through `E2E_URL`.

    Read from the recipe bodies rather than from a hand-kept list — a list is the
    thing that goes stale, and going stale here silently un-guards a target.
    """
    text = _makefile()
    found: set[str] = set()
    current: str | None = None
    for line in text.splitlines():
        match = re.match(r"^([a-z][a-z0-9-]*):", line)
        if match:
            current = match.group(1)
            continue
        if line.startswith("\t") and current and "$(E2E_URL)" in line:
            # The guard inspects `$(E2E_URL)` itself; it cannot depend on itself.
            if current != GUARD:
                found.add(current)
    return found


def test_the_guard_exists() -> None:
    assert re.search(rf"^{GUARD}:", _makefile(), re.M), (
        f"`{GUARD}` is gone. Every browser target below depends on it; without it "
        "they run against port 80 and report the result as test failures."
    )


def test_every_browser_target_depends_on_the_guard() -> None:
    text = _makefile()
    unguarded = {
        target
        for target in _targets_using_e2e_url()
        if not re.search(rf"^{re.escape(target)}:.*\b{GUARD}\b", text, re.M)
    }
    assert not unguarded, (
        f"browser target(s) reaching E2E_URL without the guard: {sorted(unguarded)}. "
        f"Add `{GUARD}` as a prerequisite — a portless URL must refuse, not run."
    )


def test_at_least_one_browser_target_is_discovered() -> None:
    """Guards the test above against passing vacuously.

    If the recipe scan silently stopped matching, `unguarded` would be empty and
    the assertion would hold while protecting nothing — Decorative Logic
    (`CLAUDE.md` §2).
    """
    assert len(_targets_using_e2e_url()) >= 5


@pytest.mark.parametrize("url", ["http://localhost:", "http://localhost", ""])
def test_the_guard_refuses_a_portless_url(url: str) -> None:
    result = subprocess.run(
        ["make", GUARD, f"E2E_URL={url}"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0, f"a portless URL was accepted: {url!r}"
    assert "REFUSED" in result.stderr
    assert "B-1014" in result.stderr


def test_the_guard_accepts_a_real_port() -> None:
    """The other direction, without which the test above passes on a guard that
    refuses everything — which would be a gate nobody can run."""
    result = subprocess.run(
        ["make", GUARD, "E2E_URL=http://localhost:3200"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
