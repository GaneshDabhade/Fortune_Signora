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


def test_it_runs_the_two_gates_it_claims_and_no_others(validate: ModuleType) -> None:
    """**Scope, asserted so it cannot drift.**

    **Two gates, and the reasons are opposite.** The suite is here because it
    needs a database; `tsc --noEmit` is here because it needs *nothing* — it
    takes seconds, and it was in no gate QE ran until `main` was found failing
    it ([B-111](../../docs/BUGS.md)).

    **Everything else stays out.** `lint-imports` and `mypy` belong to
    certification; the image build needs a Docker stack. Folding them in would
    produce a command that looks like certification, takes as long, and records
    nothing — the shape of a gate people learn to skip.

    > **This test was written asserting *one* gate and passed on a technicality
    > when the second arrived** — `npx` is not `npm`. A guard that survives the
    > change it was written to catch is Decorative Logic, so its premise is
    > restated rather than left to coincidence.

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
    assert any("tsc" in text for text in literals), "the tsc gate disappeared"
    assert any("pytest" in text for text in literals), "the suite gate disappeared"
    for absent in ("lint-imports", "mypy", "docker", "npm run"):
        assert not any(absent in text for text in literals), (
            f"validate.py has grown a {absent!r} gate; it runs the suite and tsc, nothing else"
        )


def test_a_subset_can_reach_the_same_safe_database(validate: ModuleType) -> None:
    """**The safe route must exist for a narrower question too.**

    It did not until 2026-08-04. `argparse` rejected anything it did not
    recognise, so `make validate ARGS="-m security_invariant"` exited 2 and the
    only way to ask a narrower question was `pytest` by hand — **at the shared
    database**, which is the whole defect this file exists to remove.

    > QE then made exactly that mistake, checking one slice's claim about the
    > Security Invariant count: **12 failures, every one of them the
    > invocation's**, against a full suite that had passed minutes earlier
    > ([B-116](../../docs/BUGS.md)). A safe path that covers only the expensive
    > case is a safe path people leave.
    """
    source = (REPO_ROOT / "infra" / "validate.py").read_text()
    assert "parse_known_args()" in source, "unrecognised arguments are rejected again"
    assert "*forwarded" in source, "arguments are parsed but not passed to pytest"


def test_a_subset_does_not_measure_itself_against_a_whole_repository_floor(
    validate: ModuleType,
) -> None:
    """**Coverage is dropped when a subset is requested, and that is not a weakening.**

    A partial run cannot satisfy a repository-wide floor, so leaving `--cov` on
    would fail the gate for a reason that says nothing about the code — and the
    habit it teaches is `--quick`, reflexively, including on the full runs where
    the floor is the point.
    """
    source = (REPO_ROOT / "infra" / "validate.py").read_text()
    assert "if not args.quick and not forwarded:" in source


def _is_docstring(node: object) -> bool:
    import ast

    return isinstance(node, ast.Expr) and isinstance(getattr(node, "value", None), ast.Constant)
