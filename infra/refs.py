"""**Refreshing a remote ref before measuring it, in one place.**

A remote-tracking ref is only as fresh as this clone's last `git fetch`. Reading
one without refreshing produces a number that is *plausible and wrong*, and the
reader cannot tell the difference — which is the worst failure shape a
measurement can have.

**It has cost the repository four times, in four different ways:**

  · Four Lane C reports on 2026-08-04 reported idleness at lanes that were
    shipping, because the dashboard read a stale `origin/integration`.
  · Lane C reported `lane-c-sync` fast-forwardable twice against refs it had
    measured but not pushed or not fetched.
  · [B-439](../docs/BUGS.md): `doc-drift` measured the *local* `integration`
    and attributed another lane's promoted work to the slice being handed over.
  · QE was one step from replying *"your export is not there"* after grepping
    an `origin/lane-c-sync` older than the one it had been told about.

**`repository-dashboard.py` fixed it for itself and nothing else adopted it**,
so three tools reading `origin/integration` still had no refresh — including
`doc-drift.py`, an hour after B-439 made it depend on that ref. The behaviour
now exists once (`CLAUDE.md` §2: *behaviour exists exactly once*).

⛔ **`FETCH_HEAD`'s timestamp is deliberately not used.** `git fetch origin
coordination` bumps it without touching `origin/integration`, so it reports
*"fetched seconds ago"* while the ref being measured is a day old — **a false
reassurance is worse than no signal**, because silence at least leaves the
reader's own caution intact.
"""

from __future__ import annotations

import subprocess
from pathlib import Path


def _git(*args: str, root: Path) -> str:
    try:
        return subprocess.run(
            ["git", *args], cwd=root, capture_output=True, text=True, check=True
        ).stdout
    except subprocess.CalledProcessError:
        return ""


def refresh(ref: str, root: Path, *, skip: bool = False) -> str | None:
    """Fetch `ref` before it is measured. Returns what the caller should report.

    `None` means *nothing worth saying* — the ref was already current, or it is
    not a remote ref, or the caller asked to skip. Anything else is a sentence
    for `stderr`.

    **It never raises and never blocks the measurement.** A tool that refused to
    run offline would be one people stop running, and the reading is still
    useful as long as its age is stated rather than hidden.
    """
    if skip or "/" not in ref or not ref.startswith("origin/"):
        return None

    remote, name = ref.split("/", 1)
    before = _git("rev-parse", ref, root=root).strip()
    _git("fetch", "--quiet", remote, name, root=root)
    after = _git("rev-parse", ref, root=root).strip()

    if not after:
        return f"{ref} does not resolve — the reading below cannot be trusted."
    if before == after:
        return None
    if not before:
        return f"{ref} resolved for the first time at {after[:8]}."

    moved = _git("rev-list", "--count", f"{before}..{after}", root=root).strip() or "?"
    return (
        f"{ref} advanced {moved} commit(s) on fetch ({before[:8]} -> {after[:8]}). "
        f"Anything measured before now was stale."
    )
