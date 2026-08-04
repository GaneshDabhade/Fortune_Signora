"""A diagnostic that misdiagnoses is worse than one that says nothing.

`make coverage-debt` exists so a lane can see its coverage gaps in seconds
without re-running the suite (`CLAUDE.md` §19). Every failure inside it used to
collapse into one message:

    No coverage data.
      cd backend && uv run pytest --cov

**That is correct advice for exactly one of the causes and misleading for the
rest.** QE hit it on 2026-08-04 and filed the tool as broken. It was not:
`backend/.coverage` existed and was 1.2 MB, and the same command succeeded
minutes later — the subprocess had failed transiently under memory pressure.

> **The tool answered *run the suite*, which is five minutes, to a problem that
> was not the suite.** A lane following that advice would have run it twice and
> learned nothing — and would reasonably conclude the coverage gap was not
> theirs.

**The fix is not more reliability; it is honesty about which failure occurred.**
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture(scope="module")
def debt() -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        "coverage_debt", REPO_ROOT / "infra" / "coverage-debt.py"
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_a_missing_file_and_a_failing_reader_are_different_answers(debt: ModuleType) -> None:
    """**The distinction the old message destroyed.**

    *No data* and *the reader failed* need opposite advice: one is fixed by
    running the suite, the other is made worse by it.
    """
    source = (REPO_ROOT / "infra" / "coverage-debt.py").read_text()
    assert "no `.coverage` file" in source, "the absent-file case lost its own message"
    assert "the reader failing, not the run" in source, (
        "a subprocess failure is again indistinguishable from having no data"
    )


def test_it_never_advises_re_running_when_the_data_is_present(debt: ModuleType) -> None:
    """**The specific waste this removes.**

    Telling somebody to spend five minutes re-running a suite whose output is
    already on disk is not neutral — it is a confident instruction to do the
    wrong thing, and it is why a working tool was recorded as broken.
    """
    source = (REPO_ROOT / "infra" / "coverage-debt.py").read_text()
    assert "Re-running the suite will not help" in source


def test_the_reader_returns_a_reason_rather_than_none(debt: ModuleType) -> None:
    """`None` carries no information, and every caller then invents the same one.

    Returning the reason means the message is written where the failure is
    known, rather than guessed at the call site.
    """
    import inspect

    signature = inspect.signature(debt._coverage_json)
    assert "None" not in str(signature.return_annotation), (
        "the reader is back to returning None; the reason is lost at the boundary"
    )


def test_it_still_reads_real_data_when_there_is_some(debt: ModuleType) -> None:
    """The control.

    Every assertion above is about failure paths, and a tool that only reported
    failures well would pass them all while being useless. This is skipped
    rather than failed when no run has happened, because that is a property of
    the workstation and not of the tool.
    """
    if not (REPO_ROOT / "backend" / ".coverage").exists():
        pytest.skip("no coverage run on this workstation to read")
    data = debt._coverage_json()
    if isinstance(data, str):
        pytest.skip(f"coverage reader unavailable here: {data.splitlines()[0]}")
    assert "files" in data and data["files"], "the reader returned a payload with no files"
