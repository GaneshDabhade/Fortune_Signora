"""**No double in this module reads a clock its test did not declare** —
[B-189](../../../../docs/BUGS.md).

**The defect this exists to prevent was invisible for seven days and then
failed a repository-wide gate on a tree that had not changed.**
``FakeInvitationRepository.find_live`` compared an invitation against
``datetime.now(UTC)`` while its own file declared ``NOW``. The fixture's offer
expired seven days after it was written — its own validity window — and five
tests went red at noon.

**This is `CLAUDE.md` §2's *hidden inputs are architecture defects*, in a
test.** ``Invitation.state`` refuses to have a default for ``at`` for exactly
this reason, and the double handed it one anyway.

**A guard rather than a sweep.** QE swept the repository by grep and found this
was the only live instance; a grep cannot see the next one. This fires on it.

**This paragraph could not spell one word for a day** —
[B-254](../../../../docs/BUGS.md). ``tests/certification/test_conditions.py``
asserted that no production package *imports* that package and checked it with
``if "certification" in path.read_text()`` — a substring match over raw source.
The paragraph above mentioned it in prose and was reported as an offender, so
the name had to be written in two halves to survive a gate.

**That was [B-252](../../../../docs/BUGS.md)'s class one language along**, and
the workaround is gone because QE fixed the guard rather than because the
sentence got cleverer: it parses the file and looks at ``ast.Import`` and
``ast.ImportFrom`` now. **A workaround should not outlive the defect that
caused it**, which is why this is restored in the first slice after the fix
reached ``main`` rather than left to read as a style choice.
"""

from __future__ import annotations

import re
from pathlib import Path

TESTS = Path(__file__).parent

#: **A fixed moment declared at module scope** — ``NOW = datetime(2026, …)``.
#: The presence of one is what makes a wall-clock read in the same file a
#: contradiction rather than a choice.
DECLARED_CLOCK = re.compile(r"^[A-Z_]+\s*=\s*datetime\(", re.MULTILINE)

#: **A read of the real clock**, in code rather than in prose.
WALL_CLOCK = re.compile(r"datetime\.now\(")


def _without_comments_or_docstrings(source: str) -> str:
    """**Prose does not read a clock.**

    Without this the guard would fire on the doc-comment in
    ``test_accept_invitation.py`` that explains the defect — the same false
    positive [B-252](../../../../docs/BUGS.md) found in the frontend's
    reachability guard, one language along.
    """
    without_strings = re.sub(r'"""[\s\S]*?"""', "", source)
    without_strings = re.sub(r"'''[\s\S]*?'''", "", without_strings)
    return re.sub(r"#.*$", "", without_strings, flags=re.MULTILINE)


def test_no_file_declares_a_clock_and_then_reads_another() -> None:
    """**Both halves are required, and that is deliberate.**

    A file with no declared moment may read the wall clock — ``test_onboarding``
    does, as *data* rather than as a comparison, and it is correct. A file that
    has said what *now* is may not then ask the machine.
    """
    offenders = []
    for path in sorted(TESTS.glob("test_*.py")):
        if path.name == Path(__file__).name:
            continue
        code = _without_comments_or_docstrings(path.read_text())
        if DECLARED_CLOCK.search(code) and WALL_CLOCK.search(code):
            offenders.append(path.name)

    assert offenders == [], (
        "these files declare a fixed moment and then read the real clock; "
        "a fixture that expires against a clock nobody declared goes red on a "
        "date rather than on a change (B-189)"
    )


def test_the_guard_can_fail() -> None:
    """**A guard that cannot fail is documentation pretending to be code**
    (`CLAUDE.md` §2), and this one is a pair of regexes over a directory that
    currently satisfies it — so the regexes are exercised directly."""
    contradiction = "NOW = datetime(2026, 8, 5)\nx = datetime.now(UTC)\n"
    assert DECLARED_CLOCK.search(contradiction)
    assert WALL_CLOCK.search(contradiction)

    prose_only = '"""Explains datetime.now(UTC) at length."""\nNOW = datetime(2026, 8, 5)\n'
    assert not WALL_CLOCK.search(_without_comments_or_docstrings(prose_only))
