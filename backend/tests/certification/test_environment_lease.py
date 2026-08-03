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
    """Never touch the real lease — a test that did could block a certification."""
    monkeypatch.setattr(lease, "LEASE", tmp_path / ".environment-lease")
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
        lease.LEASE.write_text(
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
        assert not lease.LEASE.exists()

    def test_a_partially_written_lease_is_not_a_permanent_block(self) -> None:
        """A process killed mid-acquire leaves a truncated file."""
        lease.LEASE.write_text('{"id": "broken", "la')
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
        assert not lease.LEASE.exists(), "a nested run must not take a second lease"

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
