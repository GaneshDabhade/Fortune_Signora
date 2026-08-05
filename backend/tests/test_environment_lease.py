"""**A lock nobody has seen refuse is a lock nobody knows works.**

[B-118](../../docs/BUGS.md) — two clones drove one PostgreSQL server and each
held its own lease file, so neither could see the other. Validating one commit
twice, minutes apart, gave 40 failures and then 238, with 21 deadlocks and 13
missing catalogs. **The lease was working perfectly and arbitrating nothing.**

These fix the four properties that make the workstation-scoped lease
trustworthy, and the first is the one the old design failed:

**two clones sharing a resource share its lease** · **a held lease refuses**
· **a dead holder is reclaimed** · **different resources do not collide.**

The refusal test is the load-bearing one. A lease that cannot block reports
`FREE` forever, **which reads exactly like a healthy repository** — the same
shape as [B-101](../../docs/BUGS.md) and as every other guard in this
repository that had to be watched failing before it could be believed.
"""

from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path
from types import ModuleType

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
LEASE_PY = REPO_ROOT / "infra" / "environment-lease.py"


@pytest.fixture
def lease(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> ModuleType:
    """The module, with its lease directory redirected into `tmp_path`.

    **Redirected rather than mocked.** The path derivation *is* the subject —
    stubbing it would test the stub.
    """
    monkeypatch.setenv("XDG_RUNTIME_DIR", str(tmp_path))
    spec = importlib.util.spec_from_file_location("environment_lease", LEASE_PY)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules["environment_lease"] = module
    spec.loader.exec_module(module)
    return module


def test_the_lease_path_is_named_for_the_resource_not_the_clone(lease: ModuleType) -> None:
    """**The whole of B-118 in one assertion.**

    The old path was ``REPO_ROOT / ".environment-lease"``, so the lease name
    varied with the checkout and never with the thing being contended. Four
    clones, four leases, one PostgreSQL server.
    """
    path = lease._lease_path()
    assert lease._resource() in path.name
    assert str(REPO_ROOT) not in str(path), "the clone path must not appear in the lease path"


def test_a_second_clone_is_refused_and_told_where_the_holder_is(
    lease: ModuleType, tmp_path: Path
) -> None:
    """**The refusal, run as two processes rather than asserted about one.**

    A same-process test would prove `acquire` returns, not that a *different*
    checkout is stopped — and "different checkout" is the exact thing that was
    broken. So this holds the lease here and runs the real script from a copied
    directory, which is what a second lane is.
    """
    other = tmp_path / "other-clone" / "infra"
    other.mkdir(parents=True)
    (other / "environment-lease.py").write_bytes(LEASE_PY.read_bytes())
    (other / "docker-compose.yml").write_bytes(
        (REPO_ROOT / "infra" / "docker-compose.yml").read_bytes()
    )

    lease.acquire("held-by-this-test")
    try:
        result = subprocess.run(
            [sys.executable, str(other / "environment-lease.py"), "run", "second", "--",
             "echo", "THIS MUST NOT RUN"],
            capture_output=True, text=True,
            env={**os.environ, "XDG_RUNTIME_DIR": str(tmp_path)},
        )
    finally:
        lease.release(force=True)

    assert result.returncode == 4, f"a second clone was not refused: {result.stdout}"
    assert "THIS MUST NOT RUN" not in result.stdout
    assert str(REPO_ROOT) in result.stdout, "the refusal must name the holding clone"


def test_a_dead_holder_does_not_block_the_repository_forever(
    lease: ModuleType, monkeypatch: pytest.MonkeyPatch
) -> None:
    """**`pkill` on a hung certification is a legitimate recovery action.**

    It happened twice in cycle 25. A lease surviving it would convert one stuck
    run into a permanently stuck workstation — and now into four.
    """
    lease._lease_path().write_text(json.dumps({"id": "x", "label": "dead", "pid": 2**22}))
    assert lease.holder() is None
    assert not lease._lease_path().exists(), "a stale lease is reclaimed, not merely ignored"


def test_two_resources_do_not_share_a_lease(
    lease: ModuleType, monkeypatch: pytest.MonkeyPatch
) -> None:
    """**Isolation must not become a global lock.**

    The day [436](../../docs/architecture/436-execution-isolation.md) change ②
    lands, each lane drives its own compose project — and they must then stop
    blocking each other. If the path did not vary with the resource, change ②
    would deliver isolation and keep serialising.
    """
    monkeypatch.setenv("COMPOSE_PROJECT_NAME", "signora-lane-a")
    a = lease._lease_path()
    monkeypatch.setenv("COMPOSE_PROJECT_NAME", "signora-lane-b")
    assert a != lease._lease_path()
