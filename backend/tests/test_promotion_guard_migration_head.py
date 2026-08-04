"""A promotion is judged on the commit's tree, not on the one you are standing in.

**B-110.** `infra/certification-guard.py` refuses a promotion whose certification
record no longer describes the repository — *"add a migration and `is_certified`
reads false"*. That rule is right and must stay.

**What was wrong is which tree counted as the repository.** `_migration_head()`
globbed the *working directory*, and the documented promotion sequence is

    git checkout main && git merge --ff-only <sha>

so the guard was always asked while standing on the **old** `main`. A candidate
that adds a migration is therefore compared against a head it has not reached,
and refused.

> **It refused exactly the commits it should scrutinise most carefully**, and
> thirty-odd cycles hid it because none of them carried a migration. It fired
> twice on 2026-08-04, the first two migration-bearing promotions since the
> check was written.

**It refuses and never wrongly permits**, which is why B-110 is 🟡 — a false
`REFUSED` costs a diagnosis; the inverse would cost the guarantee.

**These tests use real commits**, because the property under test is a property
of git: *does the guard read the tree of the commit it was asked about?* A fake
tree would prove only that the fake was built to agree.
"""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path
from types import ModuleType

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]

#: Two promoted commits whose migration heads differ. **Chosen because they
#: differ** — a pair at the same head would pass every assertion below while the
#: defect was fully present.
AT_0031 = "9a112ae"
AT_0037 = "a955016"


@pytest.fixture(scope="module")
def guard() -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        "certification_guard", REPO_ROOT / "infra" / "certification-guard.py"
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _exists(commit: str) -> bool:
    return (
        subprocess.run(
            ["git", "cat-file", "-e", f"{commit}^{{commit}}"],
            cwd=REPO_ROOT,
            capture_output=True,
            check=False,
        ).returncode
        == 0
    )


@pytest.fixture(autouse=True)
def _requires_history() -> None:
    if not (_exists(AT_0031) and _exists(AT_0037)):
        pytest.skip("shallow clone: the commits this asserts against are absent")


def test_it_reads_the_head_of_the_commit_it_is_asked_about(guard: ModuleType) -> None:
    """**The defect, stated as a property.**

    Two commits, two different heads, one working tree. Before B-110 both
    answers were whatever happened to be checked out.
    """
    assert guard._migration_head(AT_0031) == "0031"
    assert guard._migration_head(AT_0037) == "0037"


def test_the_two_commits_genuinely_differ(guard: ModuleType) -> None:
    """The control.

    If these ever converge, every assertion above passes while reading the
    working tree — the defect restored, invisibly.
    """
    assert guard._migration_head(AT_0031) != guard._migration_head(AT_0037)


def test_no_argument_still_means_the_working_tree(guard: ModuleType) -> None:
    """**`make certified` with no argument asks about `main`'s head**, and
    answering that from the checked-out tree is correct — it is the same tree.
    The fix must not change that path."""
    from_disk = sorted(
        p.name.split("_")[0] for p in (REPO_ROOT / "backend/migrations/versions").glob("[0-9]*_*.py")
    )
    assert guard._migration_head() == from_disk[-1]


def test_the_expiry_rule_is_still_enforced(guard: ModuleType) -> None:
    """**The rule the fix must not weaken.**

    A record whose conditions have moved has stopped describing its commit, and
    the guard must still refuse it. Narrowing *which* tree is compared is not
    the same as removing the comparison — and removing it would have been the
    easy way to stop the false refusals.
    """
    source = (REPO_ROOT / "infra" / "certification-guard.py").read_text()
    assert "certified_head != head" in source, "the expiry comparison was removed, not narrowed"
    assert "is certified against migration head" in source


def test_a_commit_with_no_migrations_returns_none(guard: ModuleType) -> None:
    """An empty answer must not read as a head.

    `None` and `"0000"` behave differently at the comparison: one skips the
    check, the other fails it against every real head.
    """
    empty = subprocess.run(
        ["git", "hash-object", "-t", "tree", "/dev/null"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    ).stdout.strip()
    if not empty:
        pytest.skip("could not construct an empty tree")
    assert guard._migration_head(empty) is None
