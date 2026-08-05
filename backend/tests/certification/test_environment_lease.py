"""One operation owns the shared environment; the second refuses to start.

**The property under test is prevention, not detection.** Cycle 25 recorded
`pytest 134 passed` against a suite of 2589 because a second operation truncated
its database mid-run. The preflight *detects* a held port and asks the operator
to look; the lease *refuses to start*, so the contamination cannot occur.

**RE-02 was written as "a lock around `make certify`", and the first test below
is why that was wrong.** The damage came from `make smoke` and `make down`
running beside a certification — not from a second `certify`. A certify-lock
would have permitted every command that actually caused it.
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

REPO_ROOT = Path(__file__).resolve().parents[3]


def _load() -> ModuleType:
    path = REPO_ROOT / "infra" / "environment-lease.py"
    spec = importlib.util.spec_from_file_location("environment_lease", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


lease = _load()


@pytest.fixture(autouse=True)
def _isolated(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Never touch the real lease — a test that did could block a certification.

    **Redirects the lease *directory*, not a `LEASE` constant.** That constant
    stopped existing when the lease moved from the clone to the workstation
    ([B-118](../../../docs/BUGS.md)): the path is now computed from
    `LEASE_DIR` and the contended resource, so **every clone driving one Docker
    project resolves the same file.** Redirecting the directory keeps this
    suite off the real one while leaving the derivation itself under test —
    stubbing the path would test the stub.
    """
    # **Named exactly as the module would name it under `XDG_RUNTIME_DIR=tmp_path`.**
    # The cross-clone test below runs a real second process, which computes its
    # own `LEASE_DIR` from the environment — so an arbitrary directory here and
    # a derived one there are two different files, and the second clone would
    # sail past a lease it never saw. **That failure was observed, not
    # imagined**, and it is the same class as B-118 itself: two parties naming
    # one resource differently and neither noticing.
    monkeypatch.setattr(lease, "LEASE_DIR", tmp_path / "signora-leases")
    monkeypatch.delenv(lease.LEASE_VARIABLE, raising=False)


class TestTheLeaseCoversTheEnvironmentNotOneCommand:
    """The challenge that changed RE-02's design."""

    def test_any_operation_blocks_any_other(self) -> None:
        """`down` is refused while `certify` holds it.

        **This is the case a certify-only lock would have permitted**, and it is
        exactly what contaminated cycle 25.
        """
        lease.acquire("certify")
        with pytest.raises(SystemExit) as blocked:
            lease.acquire("down")
        assert blocked.value.code == 4

    def test_the_refusal_names_the_holder(self) -> None:
        """An operator who is told only *"blocked"* goes hunting. B-022's lesson
        applied to a different tool: the answer is a name."""
        lease.acquire("certify")
        current = lease.holder()
        assert current is not None
        assert current["label"] == "certify"
        assert current["pid"] == os.getpid()

    def test_a_released_lease_frees_the_environment(self) -> None:
        identifier = lease.acquire("smoke")
        lease.release(identifier)
        assert lease.holder() is None
        lease.acquire("dr")  # no raise


class TestAKilledRunDoesNotBlockForever:
    """`pkill` on a hung certification is legitimate recovery — it happened twice
    in cycle 25. A lease surviving it would turn one stuck run into a
    permanently stuck repository."""

    def test_a_lease_held_by_a_dead_process_is_reclaimed(self) -> None:
        lease._lease_path().write_text(
            json.dumps(
                {
                    "id": "dead00000001",
                    "label": "certify",
                    # A pid that cannot exist: max pid is well below this.
                    "pid": 2**30,
                    "started_at": "2026-08-03T00:00:00+00:00",
                }
            )
        )
        assert lease.holder() is None
        assert not lease._lease_path().exists()

    def test_a_partially_written_lease_is_not_a_permanent_block(self) -> None:
        """A process killed mid-acquire leaves a truncated file."""
        lease._lease_path().write_text('{"id": "broken", "la')
        assert lease.holder() is None

    def test_a_live_lease_is_not_reclaimed(self) -> None:
        lease.acquire("certify")
        assert lease.holder() is not None


class TestReentrancy:
    """`certify` runs `smoke.sh` inside its own lease. Without inheritance the
    nested acquisition would block on its own parent forever."""

    def test_an_inherited_lease_does_not_reacquire(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv(lease.LEASE_VARIABLE, "abc123456789")
        code = lease.run("smoke", [sys.executable, "-c", "pass"])
        assert code == 0
        assert not lease._lease_path().exists(), "a nested run must not take a second lease"

    def test_run_releases_even_when_the_command_fails(self) -> None:
        code = lease.run("smoke", [sys.executable, "-c", "raise SystemExit(3)"])
        assert code == 3
        assert lease.holder() is None, "a failing gate must hand the environment back"

    def test_run_passes_the_lease_to_the_child(self) -> None:
        code = lease.run(
            "certify",
            [
                sys.executable,
                "-c",
                f"import os,sys; sys.exit(0 if os.environ.get('{lease.LEASE_VARIABLE}') else 1)",
            ],
        )
        assert code == 0


class TestForceIsAnEscapeHatchNotADefault:
    def test_release_without_the_identifier_leaves_another_holders_lease(self) -> None:
        lease.acquire("certify")
        lease.release("someone-elses-id")
        assert lease.holder() is not None

    def test_force_releases_regardless(self) -> None:
        lease.acquire("certify")
        lease.release(force=True)
        assert lease.holder() is None


class TestGatePreconditionsDoNotContradict:
    """`dr` and `smoke` want opposite things from the review ports.

    **`release-preflight` requires 3000 and 8000 to be *free*** so `smoke` can
    bind them. **`dr` requires the production stack to be *up*** on exactly
    those ports, because it restarts a running system and checks nothing was
    lost.

    Wiring the preflight into `dr` therefore made `dr` unrunnable — `make up`
    brought the stack up, and the preflight then refused. It was caught within
    one cycle of being introduced, by running the gate rather than by reasoning
    about it, and this asserts it cannot come back.
    """

    def test_dr_does_not_depend_on_the_preflight(self) -> None:
        makefile = (REPO_ROOT / "Makefile").read_text()
        recipe = makefile.split("\ndr:")[1].split("\n\n")[0]
        assert "release-preflight" not in recipe.split("\n")[0]

    def test_dr_still_takes_the_lease(self) -> None:
        """Dropping the preflight must not drop the contention protection —
        that was the half `dr` actually needed."""
        makefile = (REPO_ROOT / "Makefile").read_text()
        recipe = makefile.split("\ndr:")[1].split("\n\n")[0]
        assert "environment-lease.py run dr" in recipe

    def test_smoke_keeps_both(self) -> None:
        makefile = (REPO_ROOT / "Makefile").read_text()
        assert "smoke: release-preflight" in makefile
        assert "environment-lease.py run smoke" in makefile


class TestTheLeaseBelongsToTheWorkstationNotTheClone:
    """**The four clones, and the lease that could not see them.**

    [B-118](../../../docs/BUGS.md). The lease was `REPO_ROOT/.environment-lease`,
    so four checkouts held four files over one Docker project and none could see
    another's — **Lane A holding the environment was invisible to QE by
    construction.** Validating one commit twice, minutes apart, gave 40 failures
    and then 238, with 21 deadlocks and 13 missing catalogs. **The lease was
    working perfectly and arbitrating nothing.**

    The class above fixed *that a second operation refuses*. This fixes *that a
    second **clone** does*, which is a different claim and the one that was false.
    """

    def test_the_path_is_named_for_the_resource_not_the_clone(self) -> None:
        """**The whole of B-118 in one assertion.**"""
        path = lease._lease_path()
        assert lease._resource() in path.name
        assert str(REPO_ROOT) not in str(path), "the clone path must not appear in the lease path"

    def test_a_second_clone_is_refused_and_told_where_the_holder_is(
        self, tmp_path: Path
    ) -> None:
        """**Run as two processes, because one process cannot prove this.**

        A same-process test shows `acquire` returns; it cannot show that a
        *different checkout* is stopped, and "different checkout" is the exact
        thing that was broken. So the real script is copied to another directory
        and run there — which is what a second lane is.
        """
        other = tmp_path / "other-clone" / "infra"
        other.mkdir(parents=True)
        (other / "environment-lease.py").write_bytes(
            (REPO_ROOT / "infra" / "environment-lease.py").read_bytes()
        )
        (other / "docker-compose.yml").write_bytes(
            (REPO_ROOT / "infra" / "docker-compose.yml").read_bytes()
        )

        lease.acquire("held-by-this-test")
        try:
            result = subprocess.run(
                [sys.executable, str(other / "environment-lease.py"), "run", "second",
                 "--", "echo", "THIS MUST NOT RUN"],
                capture_output=True, text=True,
                env={**os.environ, "XDG_RUNTIME_DIR": str(lease.LEASE_DIR.parent)},
            )
        finally:
            lease.release(force=True)

        assert result.returncode == 4, f"a second clone was not refused: {result.stdout}"
        assert "THIS MUST NOT RUN" not in result.stdout
        assert str(REPO_ROOT) in result.stdout, "the refusal must name the holding clone"

    def test_two_resources_do_not_share_a_lease(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """**Isolation must not become a global lock.**

        The day [436](../../../docs/architecture/436-execution-isolation.md)
        change ② lands, each lane drives its own compose project — and they must
        then stop blocking each other. If the path did not vary with the
        resource, change ② would deliver isolation and keep serialising.
        """
        monkeypatch.setenv("COMPOSE_PROJECT_NAME", "signora-lane-a")
        a = lease._lease_path()
        monkeypatch.setenv("COMPOSE_PROJECT_NAME", "signora-lane-b")
        assert a != lease._lease_path()
