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
    # `make review` starts the API itself rather than printing a command for
    # somebody to paste, so a fifth place now names the entry point — and a
    # launcher that fails on it fails after seeding, minutes in.
    "infra/review.py",
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


# ---------------------------------------------------------------------------
# B-278 — a documented command whose own output corrupts the file it writes
# ---------------------------------------------------------------------------
#
# `npm run` prints a two-line banner naming the package and the script, and it
# prints it to **stdout**. Harmless when a person is reading it; fatal the
# moment the line redirects into a file that something else must parse.
#
#     cd frontend && npm run keys:generate >> ../infra/.env.prod-local
#
# lands `> signora-frontend@0.1.0 keys:generate` in the env file, and `make up`
# then refuses with *unexpected character ">" in variable name*. Lane A hit it
# for real bringing a stack up from a clone that had never had one.
#
# **No existing gate could see it**, which is what makes it worth a test rather
# than a careful reader: the line lives inside an `echo` in a `test -f` guard,
# so nothing ever executes it, and `make up` passes on every machine where the
# file already exists — which is every machine that has run it once. It is
# reachable only from a fresh clone, exactly once.
#
# `--silent` suppresses the banner, and this repository already knew that:
# `demo-users`, `demo-prepare`, `infra/workstation.py` and `infra/smoke.sh` all
# use it. **Only the instruction a human was told to type omitted it.**

FILES_A_HUMAN_COPIES_COMMANDS_FROM = (
    "Makefile",
    "README.md",
    "docs/RUNNING.md",
)

# `npm run <script>` whose output is redirected into a file. `2>` and `>&` are
# deliberately excluded — redirecting stderr is not this defect, and a banner
# on stdout is unaffected by it.
_REDIRECTED_NPM_RUN = re.compile(r"npm run\b(?P<flags>.*?)(?<![0-9&])>{1,2}\s*[^\s&|]")


def _redirected_npm_invocations() -> list[tuple[str, int, str]]:
    found = []
    for relative in FILES_A_HUMAN_COPIES_COMMANDS_FROM:
        path = REPO_ROOT / relative
        for number, line in enumerate(path.read_text().splitlines(), start=1):
            if _REDIRECTED_NPM_RUN.search(line):
                found.append((relative, number, line.strip()))
    return found


def test_some_documented_command_redirects_npm_output() -> None:
    """A control. If the regex stops matching, the assertion below passes
    vacuously and this section becomes decoration — the failure mode this
    repository calls Decorative Logic.
    """
    assert _redirected_npm_invocations(), (
        "no documented command redirects `npm run` output any more — either "
        "the instruction was removed or this test stopped being able to see it"
    )


@pytest.mark.parametrize(
    ("source", "line_number", "line"),
    _redirected_npm_invocations(),
    ids=lambda value: str(value) if isinstance(value, str | int) else "",
)
def test_a_redirected_npm_command_silences_the_banner(
    source: str, line_number: int, line: str
) -> None:
    match = _REDIRECTED_NPM_RUN.search(line)
    assert match is not None

    assert "--silent" in match.group("flags"), (
        f"{source}:{line_number} redirects `npm run` output into a file "
        f"without --silent. npm prints a two-line banner to stdout before the "
        f"script runs, so the banner lands in the file (B-278).\n"
        f"  {line}\n"
        f"Add --silent, as demo-users, demo-prepare, infra/workstation.py and "
        f"infra/smoke.sh already do."
    )
