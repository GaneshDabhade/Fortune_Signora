"""The two registers that record one claim must name the same holder.

`BACKLOG.md` and `ACTIVE_ASSIGNMENTS.md` both record who holds a task, and
neither is authoritative over the other. When they disagree, a lane reading the
first concludes the task is taken and a lane reading the second concludes it is
free — which is the duplicate implementation the Task Claim Protocol exists to
prevent, arriving through the registers instead of through a race.

`state-check` check 5c(a) cannot see this: it reads the board alone, so a
backlog row saying `CLAIMED — Lane X` with no board row is invisible to it.

**Every case below is fixed text, never the live registers.** A test asserting
the real files agree would pass today and prove nothing — it would pass
identically with the check deleted, which is the Decorative Logic `CLAUDE.md`
§2 names. The disagreeing cases are therefore constructed.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path
from types import ModuleType

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]


def _load_state_check() -> ModuleType:
    """Import `infra/state-check.py`, whose filename is not a Python identifier."""
    path = REPO_ROOT / "infra" / "state-check.py"
    spec = importlib.util.spec_from_file_location("state_check", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


state_check = _load_state_check()


def _backlog(*blocks: str) -> str:
    return "## READY\n\n" + "\n\n".join(blocks)


def _task(number: int, status: str, extra: str = "") -> str:
    return (
        f"### TASK-{number:03d} · A task\n\n"
        f"| | |\n|---|---|\n"
        f"| **Module** | Somewhere |\n"
        f"| **Status** | {status} |\n"
        f"{extra}"
    )


def _board(*rows: str) -> str:
    header = (
        "## Current — as of today\n\n"
        "| Lane | Task | Branch | Module | Slice | Status |\n"
        "|---|---|---|---|---|---|\n"
    )
    tail = "\n## Recently completed\n\n| **Lane B** | **TASK-001** | shipped |\n"
    return header + "\n".join(rows) + tail


def _row(lane: str, task: int | None, status: str = "`CLAIMED`") -> str:
    cell = f"**[TASK-{task:03d}](BACKLOG.md)**" if task is not None else "—"
    return f"| **{lane}** | {cell} | `lane-x` | mod | one | {status} |"


class TestBacklogClaims:
    def test_a_claimed_task_names_its_lane(self) -> None:
        text = _backlog(_task(1, "`CLAIMED` — **Lane B**, 2026-08-02"))
        assert state_check._backlog_claims(text) == {"001": "Lane B"}

    def test_ready_is_not_a_claim(self) -> None:
        assert state_check._backlog_claims(_backlog(_task(1, "`READY`"))) == {}

    @pytest.mark.parametrize("status", ["CLAIMED", "ACTIVE", "CHANGES REQUESTED"])
    def test_every_holding_status_counts(self, status: str) -> None:
        text = _backlog(_task(7, f"`{status}` — **Lane A**, 2026-08-02"))
        assert state_check._backlog_claims(text) == {"007": "Lane A"}

    def test_in_validation_is_not_a_claim(self) -> None:
        """⛔ **`IN VALIDATION` is a handover, not a hold — [B-143](../../docs/BUGS.md).**

        **This case sat in the list above and it should not have.** §20e is
        explicit: at `IN VALIDATION` *"implementation, tests, module
        documentation and Slice Handoff are all complete. **The lane's
        responsibility for this task has ended.**"* ⚡ **The row is with QE and
        nobody is working it**, so the execution board's `## Current` — which
        answers *"who is doing what, right now?"* — should not carry it.

        ⚠️ **The finding it produced for days**: `TASK-400`, `IN VALIDATION`
        since 2026-08-06 with 34 commits on `main` and nothing outstanding,
        reported every cycle as work a lane held and routed to Lane A each
        time. **A row nobody could claim.**

        ⛔ **`CHANGES REQUESTED` stays in the list above** — that one *is*
        returned to the lane, and §20e makes it the lane's highest priority.
        **The two are opposite directions across the same boundary.**
        """
        text = _backlog(_task(7, "`IN VALIDATION` — **Lane A**, 2026-08-02"))
        assert state_check._backlog_claims(text) == {}

    def test_a_note_naming_other_tasks_does_not_claim_them(self) -> None:
        """Why parsing is per block rather than per line.

        A claim note routinely names the tasks the lane passed over — this
        repository's own TASK-005 note names three — and a line-oriented scan
        reads every one of them as a claim by the claiming lane.
        """
        text = _backlog(
            _task(
                5,
                "`CLAIMED` — **Lane B**, 2026-08-02",
                "| **On claiming** | TASK-002 is **Lane A**'s; TASK-003 is blocked; "
                "TASK-004 is **Lane A**'s |\n",
            )
        )
        assert state_check._backlog_claims(text) == {"005": "Lane B"}


class TestBoardClaims:
    def test_the_current_section_is_read(self) -> None:
        assert state_check._board_claims(_board(_row("Lane B", 5))) == {"005": {"Lane B"}}

    def test_recently_completed_is_not_a_live_claim(self) -> None:
        """Otherwise every finished task looks contested forever."""
        assert "001" not in state_check._board_claims(_board(_row("Lane B", 5)))

    def test_an_idle_lane_claims_nothing(self) -> None:
        assert state_check._board_claims(_board(_row("Lane A", None))) == {}

    def test_a_next_action_referencing_another_task_is_not_a_claim(self) -> None:
        board = (
            "## Current\n\n"
            "| Lane | Task | Branch | Module | Slice | Status | Next action |\n"
            "|---|---|---|---|---|---|---|\n"
            "| **Lane B** | **TASK-005** | `lane-b` | infra | one | `CLAIMED` | "
            "blocked behind TASK-009 |\n"
        )
        assert state_check._board_claims(board) == {"005": {"Lane B"}}

    def test_two_lanes_on_one_task_are_both_recorded(self) -> None:
        board = _board(_row("Lane A", 2), _row("Lane B", 2))
        assert state_check._board_claims(board) == {"002": {"Lane A", "Lane B"}}


class TestAgreement:
    """The rule itself, exercised the way check 5c(c) applies it."""

    @staticmethod
    def _disagreements(backlog: str, board: str) -> list[tuple[str, str, set[str]]]:
        found = []
        board_claims = state_check._board_claims(board)
        for task, lane in state_check._backlog_claims(backlog).items():
            holders = board_claims.get(task, set())
            if not holders or lane not in holders:
                found.append((task, lane, holders))
        return found

    def test_agreement_is_silent(self) -> None:
        assert (
            self._disagreements(
                _backlog(_task(5, "`CLAIMED` — **Lane B**, 2026-08-02")),
                _board(_row("Lane B", 5)),
            )
            == []
        )

    def test_a_backlog_claim_with_no_board_row_is_caught(self) -> None:
        """**The live case.** This is what the check found on its first run:
        `TASK-001` reads `CLAIMED — Lane B` in the backlog and the board carries
        no row for it, because the row was removed at a Closeout while the
        backlog kept the claim."""
        assert self._disagreements(
            _backlog(_task(1, "`CLAIMED` — **Lane B**, 2026-08-02")),
            _board(_row("Lane A", 2)),
        ) == [("001", "Lane B", set())]

    def test_the_two_registers_naming_different_lanes_is_caught(self) -> None:
        assert self._disagreements(
            _backlog(_task(2, "`CLAIMED` — **Lane B**, 2026-08-02")),
            _board(_row("Lane A", 2)),
        ) == [("002", "Lane B", {"Lane A"})]

    def test_a_board_row_without_a_backlog_claim_is_not_this_check(self) -> None:
        """Deliberately silent — 5c(b) already reports a board row naming a task
        the backlog does not define, and two checks reporting one fact is how a
        register starts crying wolf."""
        assert self._disagreements(_backlog(_task(5, "`READY`")), _board(_row("Lane B", 5))) == []
