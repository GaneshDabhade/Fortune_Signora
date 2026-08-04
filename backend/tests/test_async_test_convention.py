"""One async convention, and a guard that a second cannot arrive quietly.

**Written for [B-107](../../docs/BUGS.md), where ten tests had never passed
and nothing said so.** `pyproject.toml` sets `asyncio_mode = "auto"`, so an
`async def test_` is collected and run with no marker at all. A file that also
carries `pytestmark = pytest.mark.anyio` hands the same coroutine to a second
plugin with its own loop, and every test in it errors.

**The reason it survived is that the failure is invisible in the place people
look.** A file whose tests all error still prints a summary line, and the count
of *errors* sits beside the count of *passes* rather than replacing it — so a
lane reading `10 errors` at the bottom of a green-looking run has to notice
that the number it wanted was `10 passed`. One character of markup, in one
file, that nothing in the repository objected to.

**So the objection is written here.** Not in `tests/provider_platform/`, where
it would guard the one file that already had the defect and none of the files
that might next: the rule is about the repository's async convention, and its
scope is every test in it.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Final

TESTS: Final = Path(__file__).resolve().parent

#: `pytest.mark.anyio`, however it is spelled — a `pytestmark` assignment, a
#: decorator, or an `import anyio` that precedes either. Matching the module
#: name rather than one syntax is deliberate: the defect arrived as a
#: `pytestmark` line, and a decorator would have done exactly the same damage.
_ANYIO: Final = re.compile(r"\banyio\b")

#: The suite that tests the guard itself, and must therefore contain the word.
_SELF: Final = "test_async_test_convention.py"


def _test_files() -> list[Path]:
    return sorted(p for p in TESTS.rglob("test_*.py") if p.name != _SELF)


def test_the_repository_has_test_files_to_check() -> None:
    """Guard the guard.

    A glob that silently matched nothing would pass forever while checking
    nothing — the Decorative Logic `CLAUDE.md` §2 names, and the exact shape a
    reader would trust.
    """
    assert len(_test_files()) > 50


def test_no_test_file_uses_anyio() -> None:
    """`asyncio_mode = "auto"` is the convention, and it is the only one.

    A file naming `anyio` is either running a second async plugin over the same
    coroutines — which errors every test in it — or is about to. Neither is a
    thing to discover from a summary line.
    """
    offenders = sorted(
        str(path.relative_to(TESTS))
        for path in _test_files()
        if _ANYIO.search(path.read_text())
    )
    assert offenders == [], (
        f"{offenders} name `anyio`. This repository runs pytest-asyncio in "
        "`auto` mode: an `async def test_` needs no marker, and adding an "
        "`anyio` one hands it to a second event loop where every test in the "
        "file errors. B-107 is what that looks like — ten tests that had never "
        "passed, reported as errors beside a count of passes."
    )
