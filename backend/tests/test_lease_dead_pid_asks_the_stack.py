"""A dead pid is evidence about the record, not about the machine — [B-436](../../docs/BUGS.md).

**The row exists because there was no ``BLOCKED`` path to fire-test.** Every
dead pid reclaimed, so the diagnostic could not be exercised and the near-miss
QE reported could not be reproduced. These tests are that path.

⛔ **Neither *never reclaim* nor *always reclaim*** — B-436 records that both
failure modes are real. **The third behaviour: reclaim only where there is
evidence the stack is idle, and fall back to the previous behaviour only where
there is no evidence either way.**
"""

from __future__ import annotations

import importlib.util
import json
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest

_SPEC = importlib.util.spec_from_file_location(
    "environment_lease",
    Path(__file__).resolve().parents[2] / "infra" / "environment-lease.py",
)
assert _SPEC is not None and _SPEC.loader is not None
lease = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(lease)

DEAD_PID = 2**22  # ⚡ Above every Linux default `pid_max`; cannot be alive.


@pytest.fixture
def a_lease(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[Path]:
    """A lease file naming a process that does not exist."""
    path = tmp_path / "signora-test.lease"
    monkeypatch.setattr(lease, "_lease_path", lambda: path)
    path.write_text(
        json.dumps(
            {"pid": DEAD_PID, "label": "certify", "started_at": "2026-08-16T09:00:00Z"}
        )
    )
    yield path


def _stack(monkeypatch: pytest.MonkeyPatch, containers: list[str] | None) -> None:
    monkeypatch.setattr(lease, "_running_containers", lambda: containers)


class TestADeadPidDoesNotProveTheMachineIsFree:
    def test_a_busy_stack_blocks_instead_of_being_reclaimed(
        self, a_lease: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """🔴 **QE's near-miss, reproduced.**

        The recorded pid was dead *and* another clone had a live run the record
        never knew about. ⛔ **A plain retry would have reclaimed and run.**
        """
        _stack(monkeypatch, ["signora-v2-postgres-1", "signora-v2-redis-1"])

        current = lease.holder()

        assert current is not None, "a busy stack must not be reclaimed"
        assert a_lease.exists(), "the lease file must survive"

    def test_the_block_names_the_containers_rather_than_the_dead_pid(
        self, a_lease: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """⛔ **Naming a dead pid sends the operator hunting for a corpse.**

        The containers are what exists, so they are what the message names.
        """
        _stack(monkeypatch, ["signora-v2-postgres-1"])

        described = lease._describe(lease.holder() or {})

        assert "signora-v2-postgres-1" in described
        assert str(DEAD_PID) not in described

    def test_an_idle_stack_is_still_reclaimed(
        self, a_lease: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """✅ **The case the original behaviour was written for, preserved.**

        A crashed run leaving a lock nobody can clear must still self-heal, or
        one stuck run becomes a permanently stuck repository.
        """
        _stack(monkeypatch, [])

        assert lease.holder() is None
        assert not a_lease.exists()

    def test_no_evidence_falls_back_to_the_previous_behaviour(
        self, a_lease: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """⚡ **Strictly better, never worse.**

        Where docker cannot be asked, this does exactly what it did before —
        which is what makes the change safe on a workstation without docker
        rather than a new way to block one.
        """
        _stack(monkeypatch, None)

        assert lease.holder() is None
        assert not a_lease.exists()

    def test_none_and_empty_are_not_collapsed(self) -> None:
        """🔴 **The distinction the whole fix rests on.**

        ``[]`` is *docker answered, nothing is running*. ``None`` is *nobody
        answered*. ⛔ A helper returning ``[]`` for both would turn *I could not
        tell* into *it is free*, which is the defect this exists to remove — and
        every test above would still pass.
        """
        source = (
            Path(__file__).resolve().parents[2] / "infra" / "environment-lease.py"
        ).read_text()
        body = source.split("def _running_containers")[1].split("\ndef ")[0]

        assert body.count("return None") >= 3, (
            "each unanswerable path must return None, never an empty list"
        )
        assert "return [name for name" in body


class TestALivePidIsUnchanged:
    def test_a_live_holder_still_blocks_without_asking_docker(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """⚡ **The stack is only consulted when the pid is dead.**

        A live holder is already conclusive, and asking docker would add ten
        seconds of timeout to the common path for no additional certainty.
        """
        import os

        path = tmp_path / "live.lease"
        monkeypatch.setattr(lease, "_lease_path", lambda: path)
        path.write_text(json.dumps({"pid": os.getpid(), "label": "smoke"}))

        def _refuse() -> list[str] | None:  # pragma: no cover - must not run
            raise AssertionError("docker must not be consulted for a live pid")

        monkeypatch.setattr(lease, "_running_containers", _refuse)

        current: dict[str, Any] | None = lease.holder()

        assert current is not None
        assert current["label"] == "smoke"
