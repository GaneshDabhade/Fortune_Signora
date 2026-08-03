"""A bug row is in exactly one lifecycle state, and the register says so in prose.

`infra/registers.py` exists because `state-check` and `kpi` answered *"is this
bug blocking?"* differently. The severity half was centralised; **the status half
was not**, and `kpi.py` went on substring-matching the whole cell:

    fixed    = sum(1 for r in rows if "FIXED"    in r.status)
    verified = sum(1 for r in rows if "VERIFIED" in r.status)

The register's own convention is to record a fix and name the state it has not
yet reached — *"**`FIXED`** — Lane B. **`VERIFIED` is QE's to set**"* — so nine
rows landed in two buckets and the totals exceeded the number of rows. That is
[B-101](../../docs/BUGS.md), and the block it corrupted advertises itself as
never edited by hand, which is what made the wrong figure credible.

**Every case below is fixed text, never the live register.** Asserting that the
real `BUGS.md` totals reconcile would pass today and pass identically with
`BugRow.state` deleted — the Decorative Logic `CLAUDE.md` §2 names. The rows that
distinguish a correct implementation from the broken one are therefore written
out here.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]


def _load_registers() -> ModuleType:
    path = REPO_ROOT / "infra" / "registers.py"
    spec = importlib.util.spec_from_file_location("registers", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    # `@dataclass` resolves annotations through `sys.modules[cls.__module__]`,
    # so the module must be registered before its body executes.
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


registers = _load_registers()


def _row(severity: str, status: str) -> Any:
    """A single constructed row. `Any` because `registers` is loaded by path —
    `infra/` is outside the package mypy resolves, so `BugRow` has no static type
    here. The alternative is a Protocol duplicating the dataclass, which is a
    second definition of one fact (`CLAUDE.md` §2)."""
    text = f"""### B-999 · a constructed row

| | |
|---|---|
| **Severity** | {severity} |
| **Status** | {status} |
"""
    rows = registers.bug_rows(text)
    assert len(rows) == 1
    return rows[0]


class TestTheOperativeStateIsTheFirstOne:
    """The rest of the cell is commentary — the rule severity already follows."""

    def test_a_fixed_row_naming_its_next_state_is_still_fixed(self) -> None:
        row = _row("🟠", "**`FIXED`** — Lane B, 2026-08-02. **`VERIFIED` is QE's to set**")
        assert row.state == "FIXED"

    def test_a_verified_row_recounting_its_fix_is_verified(self) -> None:
        row = _row("🟠", "**`VERIFIED`** — QE, on Lane B's evidence. Was `FIXED` 2026-08-01")
        assert row.state == "VERIFIED"

    def test_an_open_row_describing_the_fix_it_needs_is_open(self) -> None:
        row = _row("🟡", "`OPEN` — the fix is a `FIXED` marker once somebody does it")
        assert row.state == "OPEN"

    def test_a_row_with_no_recognisable_state_reports_none(self) -> None:
        assert _row("🟠", "— |").state == ""


class TestTheBucketsPartitionTheRows:
    """The property the miscount broke: one row, one bucket, totals reconcile."""

    def test_every_state_is_counted_exactly_once(self) -> None:
        cells = [
            "`OPEN` |",
            "**`FIXED`** — **`VERIFIED` is QE's to set**",
            "**`FIXED`** — **`VERIFIED` is another lane's**",
            "**`VERIFIED`** — QE, on independent evidence",
            "`WONTFIX` — recorded and closed",
        ]
        rows = [_row("🟠", c) for c in cells]
        counted = sum(
            1
            for r in rows
            for state in registers.STATES
            if r.state == state
        )
        assert counted == len(rows), "a row landed in two buckets, or in none"

    def test_substring_counting_would_have_double_counted(self) -> None:
        """The bug, stated as a test — so a revert cannot pass quietly."""
        row = _row("🟠", "**`FIXED`** — **`VERIFIED` is QE's to set**")
        assert "FIXED" in row.status and "VERIFIED" in row.status
        assert row.state == "FIXED"


class TestTheSeverityRuleIsUnchanged:
    """B-101 was reported against severity too, and that report was wrong.

    A conditional cell means what it says *today*. QE's own audit read 🔴
    wherever it appeared and called the tool broken; the tool was right.
    """

    @pytest.mark.parametrize(
        ("cell", "expected"),
        [
            ("🟠 unreachable today · 🔴 the moment a workspace watches two accounts", "🟠"),
            ("🔴 blocks the milestone", "🔴"),
            ("— |", ""),
        ],
    )
    def test_the_first_marker_is_operative(self, cell: str, expected: str) -> None:
        assert _row(cell, "`OPEN` |").severity == expected


class TestConflictMarkersAreCaught:
    """A `>>>>>>>` line inside a table is not a table separator.

    `malformed_tables` was built for the residue of a split section and could
    not see this, so a conflict marker sat in the coordination register through
    several certifications ([B-102](../../docs/BUGS.md)) — stranding a row
    outside its table and leaving two more duplicated with contradictory
    statuses. **Every gate in the repository passed.**
    """

    def test_a_real_conflict_is_reported(self) -> None:
        text = "| a | b |\n<<<<<<< HEAD\nx\n=======\ny\n>>>>>>> other (msg)\n"
        assert registers.conflict_markers(text) == [2, 4, 6]

    def test_a_clean_register_reports_nothing(self) -> None:
        assert registers.conflict_markers("| a | b |\n|---|---|\n| 1 | 2 |\n") == []

    @pytest.mark.parametrize("underline", ["=", "===", "====="])
    def test_a_setext_heading_is_not_a_conflict(self, underline: str) -> None:
        """`=======` is matched exactly, never as a prefix — a setext underline
        is a run of `=` and would otherwise fire on every heading."""
        assert registers.conflict_markers(f"Title\n{underline}\n") == []

    def test_a_markdown_rule_is_not_a_conflict(self) -> None:
        assert registers.conflict_markers("text\n---\nmore\n") == []

    def test_a_marker_quoted_in_a_code_fence_is_not_a_conflict(self) -> None:
        """A register that *documents* a conflict marker is not corrupt.

        B-102's own row quotes the marker it reports, and this check fired on it
        within a minute of being written — found by running the check rather
        than by reasoning about it.
        """
        text = "Actual:\n\n```\n>>>>>>> 603a077 (some commit)\n```\n\nend\n"
        assert registers.conflict_markers(text) == []

    def test_a_real_marker_after_a_closed_fence_is_still_caught(self) -> None:
        text = "```\n>>>>>>> quoted\n```\n>>>>>>> real\n"
        assert registers.conflict_markers(text) == [4]

    def test_a_seven_character_setext_underline_is_a_known_false_positive(self) -> None:
        """**The one case this check gets wrong, asserted rather than hidden.**

        A setext underline of exactly seven `=` is indistinguishable from a
        conflict marker by shape alone. It is reported, and the finding is
        advisory, so the cost is one line of noise against catching a corrupt
        register — a trade recorded here so nobody 'fixes' it into silence.
        """
        assert registers.conflict_markers("Title\n=======\n") == [2]


class TestBlockingIsUnaffected:
    """`unresolved` reads the cell's prefix and was always correct.

    Recorded because the promotion gate depends on it: had this been wrong, a 🔴
    could have been silently cleared, and no 🔴 ever was.
    """

    def test_a_fixed_red_does_not_block(self) -> None:
        assert _row("🔴", "**`FIXED`** — Lane A").blocks_promotion is False

    def test_an_open_red_blocks(self) -> None:
        assert _row("🔴", "`OPEN` |").blocks_promotion is True

    def test_a_fixing_red_still_blocks(self) -> None:
        assert _row("🔴", "`FIXING` — Lane B has it").blocks_promotion is True
