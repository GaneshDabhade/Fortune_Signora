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

    def test_no_evidence_reclaims_BUT_says_it_could_not_check(
        self, a_lease: Path, monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """🔴 **Corrected 2026-08-16 on QE's challenge, and the correction is the point.**

        ⛔ **This test used to assert only that `None` reclaimed** — identical to
        the `[]` case above. **So `it is free` and `I could not tell` produced
        the same behaviour, and the docstring claiming they "must not be
        collapsed" was describing something the code did not do.**

        ⚡ **QE proposed the mutation; it killed one test, and that test asserted
        how the code was WRITTEN.** 📁 **§2's Decorative Logic exactly** — *"whose
        removal does not change the property it claims to protect"* — **and the
        source-assertion test made it look load-bearing to the next reader.**

        ✅ **Reclaiming is still correct**: blocking every workstation without
        docker is the "never reclaim" trap B-436 names. ⛔ **Reclaiming SILENTLY
        is what was wrong** — it asserts *free* on no evidence.

        📁 **[B-437](../../docs/BUGS.md)'s rule, applied: a bounded conclusion
        must state its bound.**
        """
        _stack(monkeypatch, None)

        assert lease.holder() is None
        assert not a_lease.exists()

        warned = capsys.readouterr().err
        assert "WITHOUT checking the stack" in warned
        assert "nothing about the machine" in warned

    def test_an_answered_idle_stack_reclaims_SILENTLY(
        self, a_lease: Path, monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """✅ **The other half, and it is what makes the distinction real.**

        ⛔ **Warning here too would be noise on the ordinary path** — a crashed
        run on an idle machine is the case the original reclaim was written for,
        and it is not something an operator needs to check.

        ⚡ **Collapsing `None` into `[]` now fails THIS test**, behaviourally,
        which is what the deleted source-assertion test was standing in for.
        """
        _stack(monkeypatch, [])

        assert lease.holder() is None
        assert capsys.readouterr().err == ""


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
