"""The commands the documentation tells a human to run must actually run.

Written by the QE lane after B-005: `docs/RUNNING.md`, the `make demo`
banner and `README.md` all told a new developer to start the API with
``uvicorn apps.api.main:app``. There is no module-level ``app`` — only the
factory — so the documented command failed with an ASGI import error, while
`backend/Dockerfile` and `infra/docker-compose.prod.yml` carried the correct
form. **No gate caught it because no gate reads the lines a person reads:**
`make smoke` starts the API from the container command.

So this asserts the two agree. It is deliberately not a string comparison
against a hard-coded command — that would fail the moment a port changes and
would prove nothing about whether the entry point exists. It resolves each
documented target against the real module instead.
"""

import importlib
import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]

# Every file that names the API entry point, whether a machine or a person
# reads it. A new one is added here when it is written, which is the point:
# a fourth place saying something different is exactly the defect.
FILES_NAMING_THE_ENTRY_POINT = (
    "docs/RUNNING.md",
    "Makefile",
    "backend/Dockerfile",
    "infra/docker-compose.prod.yml",
)

# `apps.api.main:create_app` in a shell line, a Dockerfile CMD array, or a
# compose command list — the separators differ, the target does not.
_INVOCATION = re.compile(r"apps\.api\.main:(?P<target>[A-Za-z_][A-Za-z0-9_]*)")


def _documented_invocations() -> list[tuple[str, int, str, str]]:
    found = []
    for relative in FILES_NAMING_THE_ENTRY_POINT:
        path = REPO_ROOT / relative
        for number, line in enumerate(path.read_text().splitlines(), start=1):
            match = _INVOCATION.search(line)
            if match:
                found.append((relative, number, match.group("target"), line.strip()))
    return found


def test_the_documentation_names_the_api_entry_point_somewhere() -> None:
    """A control. If the regex stops matching, every assertion below passes
    vacuously and this file becomes decoration.
    """
    assert _documented_invocations(), (
        "no file names apps.api.main — either the entry point moved or this "
        "test stopped being able to see it"
    )


@pytest.mark.parametrize(
    ("source", "line_number", "target", "line"),
    _documented_invocations(),
    ids=lambda value: str(value) if isinstance(value, str | int) else "",
)
def test_every_documented_entry_point_exists(
    source: str, line_number: int, target: str, line: str
) -> None:
    module = importlib.import_module("apps.api.main")

    assert hasattr(module, target), (
        f"{source}:{line_number} tells a reader to start the API at "
        f"`apps.api.main:{target}`, which does not exist. Uvicorn fails with "
        f'\'Attribute "{target}" not found in module "apps.api.main"\'.\n'
        f"  {line}"
    )


@pytest.mark.parametrize(
    ("source", "line_number", "target", "line"),
    _documented_invocations(),
    ids=lambda value: str(value) if isinstance(value, str | int) else "",
)
def test_a_factory_entry_point_is_invoked_with_the_factory_flag(
    source: str, line_number: int, target: str, line: str
) -> None:
    """`create_app` returns an application; it is not one. Naming it without
    ``--factory`` fails at startup just as surely as naming a missing
    attribute, and the error message is no clearer.

    The flag may sit on a following line in a Dockerfile array or a compose
    list, so the whole file is searched rather than the matched line.
    """
    module = importlib.import_module("apps.api.main")
    entry_point = getattr(module, target, None)

    if not callable(entry_point):
        return

    assert "--factory" in (REPO_ROOT / source).read_text(), (
        f"{source}:{line_number} starts the API at `apps.api.main:{target}`, "
        f"which is a factory, but the file never passes --factory.\n  {line}"
    )
