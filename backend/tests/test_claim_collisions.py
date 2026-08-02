"""`state-check` must be able to see a claim that has not been merged yet.

The Task Claim Protocol makes a claim atomic by pushing it, but a claim lives on
the **claiming lane's branch** until it merges. Protocol step 8 pulls
`integration`, so two lanes can each push a claim, each see an unchanged
`integration`, and each conclude they were first — which is what happened on
2026-08-02 (C-019).

These tests exercise the parsing and the collision rule against fixed text
rather than against the repository's own documents. **A test that asserted the
live backlog has no collision would pass today and prove nothing**: it would
pass equally if the check were deleted, which is the shape `CLAUDE.md` §2 calls
Decorative Logic. Every case below therefore includes the failing one.
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


class TestBacklogClaims:
    def test_a_claimed_task_names_its_lane(self) -> None:
        text = _backlog(_task(1, "`CLAIMED` — **Lane B**, 2026-08-02"))
        assert state_check._backlog_claims(text) == {"001": "Lane B"}

    def test_ready_is_not_a_claim(self) -> None:
        assert state_check._backlog_claims(_backlog(_task(1, "`READY`"))) == {}

    @pytest.mark.parametrize("status", ["CLAIMED", "ACTIVE", "IN VALIDATION"])
    def test_every_holding_status_counts(self, status: str) -> None:
        text = _backlog(_task(7, f"`{status}` — **Lane A**, 2026-08-02"))
        assert state_check._backlog_claims(text) == {"007": "Lane A"}

    def test_a_note_naming_other_tasks_does_not_claim_them(self) -> None:
        """The case that made per-block parsing necessary rather than tidy.

        A lane records why it passed over the tasks above the one it took, so a
        claim note routinely names three task ids belonging to somebody else. A
        line-oriented scan reads those as claims by the claiming lane.
        """
        text = _backlog(
            _task(
                5,
                "`CLAIMED` — **Lane B**, 2026-08-02",
                "| **On claiming** | TASK-002 was lost to **Lane A**; "
                "TASK-003 is blocked; TASK-004 is **Lane A**'s |\n",
            )
        )
        assert state_check._backlog_claims(text) == {"005": "Lane B"}


class TestCollisionRule:
    """The rule itself: one task, two lanes, across branches."""

    @staticmethod
    def _across(per_branch: dict[str, str]) -> dict[str, dict[str, str]]:
        across: dict[str, dict[str, str]] = {}
        for ref, text in per_branch.items():
            for task, lane in state_check._backlog_claims(text).items():
                across.setdefault(task, {})[lane] = ref
        return {t: h for t, h in across.items() if len(h) > 1}

    def test_two_lanes_claiming_one_task_is_detected(self) -> None:
        """**The negative case, and the reason this file exists.**

        Neither branch on its own is wrong. Only the pair is, and only a check
        that reads both can say so.
        """
        collisions = self._across(
            {
                "origin/lane-a-product-surface": _backlog(
                    _task(2, "`IN VALIDATION` — **Lane A**, 2026-08-02")
                ),
                "origin/lane-b-commercial-profile": _backlog(
                    _task(2, "`CLAIMED` — **Lane B**, 2026-08-02")
                ),
            }
        )
        assert set(collisions) == {"002"}
        assert collisions["002"] == {
            "Lane A": "origin/lane-a-product-surface",
            "Lane B": "origin/lane-b-commercial-profile",
        }

    def test_the_same_lane_on_two_branches_is_not_a_collision(self) -> None:
        """A lane branch and its merge into `integration` both carry the claim."""
        assert (
            self._across(
                {
                    "origin/integration": _backlog(
                        _task(5, "`CLAIMED` — **Lane B**, 2026-08-02")
                    ),
                    "origin/lane-b-commercial-profile": _backlog(
                        _task(5, "`CLAIMED` — **Lane B**, 2026-08-02")
                    ),
                }
            )
            == {}
        )

    def test_different_lanes_on_different_tasks_are_not_a_collision(self) -> None:
        assert (
            self._across(
                {
                    "origin/lane-a-product-surface": _backlog(
                        _task(4, "`CLAIMED` — **Lane A**, 2026-08-02")
                    ),
                    "origin/lane-b-commercial-profile": _backlog(
                        _task(5, "`CLAIMED` — **Lane B**, 2026-08-02")
                    ),
                }
            )
            == {}
        )


class TestBoardAgreement:
    """The backlog and the board record one claim, so they can disagree."""

    BOARD = (
        "## Current — as of today\n\n"
        "| Lane | Task | Branch | Module | Slice | Status |\n"
        "|---|---|---|---|---|---|\n"
        "| **Lane B** | **[TASK-005](BACKLOG.md)** | `lane-b` | infra | one | `CLAIMED` |\n"
        "\n## Recently completed\n\n"
        "| **Lane B** | **TASK-001** | shipped |\n"
    )

    def test_the_current_section_is_read(self) -> None:
        assert state_check._board_claims(self.BOARD) == {"005": {"Lane B"}}

    def test_recently_completed_is_not_a_live_claim(self) -> None:
        """Otherwise every finished task looks contested forever."""
        assert "001" not in state_check._board_claims(self.BOARD)

    def test_a_next_action_referencing_another_task_is_not_a_claim(self) -> None:
        board = (
            "## Current\n\n"
            "| Lane | Task | Branch | Module | Slice | Status | Next action |\n"
            "|---|---|---|---|---|---|---|\n"
            "| **Lane B** | **TASK-005** | `lane-b` | infra | one | `CLAIMED` | "
            "blocked behind TASK-009 |\n"
        )
        assert state_check._board_claims(board) == {"005": {"Lane B"}}
