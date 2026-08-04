"""Stage 1 must not resolve its database from the shell.

**RE-03 gave `make certify` its own database and stopped there.** Stage 1 — the
step QE performs far more often — still resolved
`SIGNORA_TEST_APP_DATABASE_URL` from the environment, which on a multi-lane
workstation points at a shared database carrying whichever lane migrated it
last.

**Three misleading failure lists in one day, all QE's:**

| | |
|---|---|
| Lane B's first validation | 27 failures, **13 Security Invariants** reading `icp_segment has no workspace_id column` — about a migration that creates one. **QE was one step from filing a fabricated tenancy defect against the lane** |
| Lane A's | Passed by luck; the shared database happened to match |
| QE's own gate change | 26 failures against a database at `0036` while the branch was at `0037` |

> **A gate whose result depends on the shell it was launched from is not a
> gate.** [B-022](../../docs/BUGS.md) said so, RE-03 removed it from
> certification, and `infra/validate.py` removes it from the step before.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture(scope="module")
def validate() -> ModuleType:
    spec = importlib.util.spec_from_file_location("validate", REPO_ROOT / "infra" / "validate.py")
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_it_reuses_the_certification_provisioner(validate: ModuleType) -> None:
    """**One provisioner, not two.**

    `tests/certification/database.py` already creates, migrates and — critically
    — **drops in a `finally`**, which is what stops one failed run blocking every
    later run at the same commit. A second copy here would be duplicated truth,
    and the copy nobody maintained would be this one.
    """
    source = (REPO_ROOT / "infra" / "validate.py").read_text()
    assert "from tests.certification import database" in source
    assert "CREATE DATABASE" not in source, "validate.py grew its own provisioning"
    assert "DROP DATABASE" not in source


def test_it_migrates_before_running_the_suite(validate: ModuleType) -> None:
    """**And treats a failed migration as fatal.**

    An unmigrated database fails hundreds of tests for one reason, and that
    reason is the least visible line in the output — which is exactly how three
    QE validations produced misleading failure lists in one day.
    """
    source = (REPO_ROOT / "infra" / "validate.py").read_text()
    assert '"alembic", "upgrade", "head"' in source
    assert "if migrated.returncode:" in source, "a failed migration no longer stops the run"


def test_the_database_is_named_for_the_commit_and_not_for_certification(
    validate: ModuleType,
) -> None:
    """**A validation database must not be mistaken for a certification one.**

    Both are disposable and both are named for their commit; only the verb
    differs. An operator finding `signora_validate_…` left behind knows which
    run made it, and `make certify`'s own drop-if-exists will not remove it by
    accident.
    """
    source = (REPO_ROOT / "infra" / "validate.py").read_text()
    assert 'replace("certify", "validate")' in source


def test_it_runs_one_gate_rather_than_becoming_a_second_certification(
    validate: ModuleType,
) -> None:
    """**Scope, asserted so it cannot drift.**

    `make validate` exists because the *suite* needs a database. `mypy`,
    `lint-imports`, the frontend suite and the image build do not, and folding
    them in would produce a command that looks like certification, takes as long
    as certification, and records nothing — which is the shape of a gate people
    learn to skip.

    **Parsed, not grepped.** A first version searched the file text and failed
    on the module docstring, which *names* those gates in the sentence saying it
    does not run them — the second time in this repository that a check confused
    prose about a thing with a dependency on it. Only string literals in the
    executable body count.
    """
    import ast

    tree = ast.parse((REPO_ROOT / "infra" / "validate.py").read_text())
    tree.body = [node for node in tree.body if not _is_docstring(node)]
    literals = {
        node.value
        for node in ast.walk(tree)
        if isinstance(node, ast.Constant) and isinstance(node.value, str)
    }
    for absent in ("lint-imports", "mypy", "docker", "npm"):
        assert not any(absent in text for text in literals), (
            f"validate.py has grown a {absent!r} gate; it runs the suite and nothing else"
        )


def _is_docstring(node: object) -> bool:
    import ast

    return isinstance(node, ast.Expr) and isinstance(getattr(node, "value", None), ast.Constant)
