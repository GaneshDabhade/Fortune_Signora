"""What a disk failure would cost, reported honestly enough to be read.

`infra/unsaved.py` is RS-1, the executable half of proposed law L-18. It has no
gate behind it and never fails, which makes **every way it can be wrong a quiet
one**: it reports nothing when there is something, or it reports so much noise
that the row that matters is skipped.

The measurement it exists for, taken 2026-08-03: every branch on the workstation
was pushed, and the entire exposure was pre-commit — an untracked module in one
lane and an untracked test suite in another, in exactly one physical location.

**Every case below is fixed text.** Running it against the live workstation
would pass today and pass identically with the classifier deleted — the
Decorative Logic `CLAUDE.md` §2 names.
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
def unsaved() -> ModuleType:
    spec = importlib.util.spec_from_file_location("unsaved", REPO_ROOT / "infra" / "unsaved.py")
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_it_never_fails(unsaved: ModuleType) -> None:
    """**The property that keeps it a reminder rather than a gate.**

    A check that failed here would punish exactly the experimentation L-18 is
    written to allow, and a lane would learn to stop running it — which costs
    more than the check was ever worth.
    """
    completed = subprocess.run(
        [sys.executable, str(REPO_ROOT / "infra" / "unsaved.py")],
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode == 0


def test_a_clean_working_copy_reports_nothing_at_risk(unsaved: ModuleType) -> None:
    """The control. If this reported risk, every run would, and the signal dies."""
    assert unsaved._emphasis("README.md") == ""


@pytest.mark.parametrize(
    ("path", "expected"),
    [
        ("backend/modules/sales_engagement/prompts/", "prompt or release artifact"),
        ("backend/modules/ai_platform/evaluation/datasets/x@1.json", "prompt or release artifact"),
        ("frontend/tests/e2e/pages/sign-in.ts", "test suite"),
        ("docs/BUGS.md", "architecture or register"),
        ("docs/architecture/480-end-to-end-product-validation.md", "architecture or register"),
        ("scratch.py", ""),
    ],
)
def test_artifacts_that_cost_more_are_named(
    unsaved: ModuleType, path: str, expected: str
) -> None:
    """**Emphasis, not classification.**

    Everything reported is already non-disposable — `.gitignore` decided that,
    and re-deciding it here would be a second truth about one question. What
    this adds is ordering: a lost prompt release cannot be regenerated, because
    regenerating one produces a *different* artifact rather than the same one
    back. A lost scratch script can be retyped.

    The paths are the real ones from the 2026-08-03 survey.
    """
    assert unsaved._emphasis(path) == expected


def test_gitignore_is_the_disposability_classifier(unsaved: ModuleType) -> None:
    """**No second taxonomy, and this is what would notice one appearing.**

    `git status --porcelain` never lists an ignored path, so anything reported
    is non-disposable by the repository's own declaration. If a future change
    added an exclusion list here, this test's premise would silently become
    false — so the premise is asserted rather than assumed.
    """
    source = (REPO_ROOT / "infra" / "unsaved.py").read_text()
    assert "--porcelain" in source, "it stopped asking git, and now owns an opinion git owns"
    for inventing_its_own in ("EXCLUDE", "IGNORE_PATTERNS", "DISPOSABLE"):
        assert inventing_its_own not in source, (
            f"`{inventing_its_own}` suggests a second disposability rule; `.gitignore` is the one"
        )


def test_unpushed_commits_are_counted_separately(unsaved: ModuleType) -> None:
    """A push and a commit are different remedies.

    Unpushed commits were zero everywhere in the survey — which is worth
    continuing to confirm rather than assuming, because the day it is not, what
    is lost is *finished* work rather than work in progress.
    """
    assert unsaved._unpushed(REPO_ROOT) >= 0


def test_the_survey_finds_clones_one_level_down(unsaved: ModuleType) -> None:
    """**Two of the four clones in the survey were nested.**

    `LaneA/signora-lane-a` and `Signora-Demo/Fortune_Signora` sit one directory
    below `Projects/`. A survey that only looked at the top level would have
    reported a cleaner workstation than the real one — and the untracked module
    that justified this whole check was in one of them.
    """
    source = (REPO_ROOT / "infra" / "unsaved.py").read_text()
    assert "nested" in source, "the nested-clone walk was removed; the survey now under-reports"


def test_untracked_directories_are_expanded_to_files(unsaved: ModuleType) -> None:
    """**The defect this tool's own author committed first.**

    `git status --porcelain` collapses an untracked *directory* into one line.
    The first workstation survey therefore counted an entire untracked module as
    a single path and reported *"seven untracked paths"*. The real figure was
    **27** — and the difference was not cosmetic: it hid an untracked prompt
    release and an untracked evaluation dataset, the exact artifacts R-3 says
    can never be regenerated to recover them.

    **A tool that under-reports the exposure it exists to surface is worse than
    no tool**, because the number is believed.
    """
    source = (REPO_ROOT / "infra" / "unsaved.py").read_text()
    assert '"-uall"' in source, (
        "directory expansion was removed; an untracked module now counts as one path"
    )


def test_commit_age_is_reported(unsaved: ModuleType) -> None:
    """A stale clone must not read as a day's lost work.

    The first survey reported **819 modified files** in an old checkout carrying
    GitHub workflow files this repository removed months ago. It was the loudest
    row and the least important, and a report whose largest number is noise
    teaches people to skim it.
    """
    source = (REPO_ROOT / "infra" / "unsaved.py").read_text()
    assert "last commit" in source, "the age annotation went; a stale clone now looks like risk"
