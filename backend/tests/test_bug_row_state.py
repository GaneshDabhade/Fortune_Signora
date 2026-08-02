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


def _row(severity: str, status: str) -> object:
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
