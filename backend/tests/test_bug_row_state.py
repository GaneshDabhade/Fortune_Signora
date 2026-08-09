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


class TestUnclosedFenceIsCaught:
    """The fence-skip above is only trustworthy if the fences balance.

    One unclosed fence inverts every parity decision after it, so
    `conflict_markers` goes **blind to a real marker in prose** and reports
    quoted ones instead. That is what happened in `docs/BUGS.md` ([B-403]):
    a row lost its opening ```` ```bash ```` to a merge, and for three days
    the check reported the one marker that was correctly quoted while unable
    to see any that were not.

    **A guard that reasons about structure must first establish that the
    structure holds** — otherwise its silence carries no information.
    """

    def test_a_balanced_document_reports_nothing(self) -> None:
        assert registers.unclosed_fence("a\n```\nx\n```\nb\n") is None

    def test_no_fences_at_all_is_balanced(self) -> None:
        assert registers.unclosed_fence("plain prose\n") is None

    def test_an_unclosed_fence_names_the_line_that_opened_it(self) -> None:
        assert registers.unclosed_fence("a\n```bash\nx\ny\n") == 2

    def test_it_names_the_last_opener_not_the_first(self) -> None:
        """Three fences: the first pair balances, the third is the defect."""
        assert registers.unclosed_fence("```\nx\n```\ntext\n```py\ny\n") == 5

    def test_the_blindness_it_exists_to_explain(self) -> None:
        """**B-403's exact shape, and the half that matters.**

        A merge ate the *opening* fence, so the surviving closer on line 2 is
        read as an opener and everything after it is treated as code. The
        genuine marker on line 3 sits in prose and is **silently skipped** —
        `conflict_markers` returns nothing at all and the register reads as
        clean.

        **Under-reporting is the dangerous direction**, and no assertion about
        the marker check could catch it, because its answer is empty either
        way. Only the parity check can.
        """
        corrupt = 'grep -oE "^### "\n```\n>>>>>>> real, in prose\n'
        assert registers.conflict_markers(corrupt) == []
        assert registers.unclosed_fence(corrupt) == 2


class TestBlockingIsUnaffected:
    """The promotion gate, and **the emphasis the register actually writes**.

    ⛔ **This class previously asserted that `unresolved` "was always correct",
    and its own cases are why nobody checked**: `FIXED` was written bolded and
    `OPEN` bare, so the only form the register uses for an open row — `**`OPEN`**`
    — was never constructed. **`startswith` then failed on 29 of 39 open rows and
    `blocks_promotion` returned `False` for every row in the file**, 🔴 included
    ([B-413](../../docs/BUGS.md)).

    ✅ **Every case below now runs in both emphases**, because a register written
    by hand varies emphasis and a gate must not.
    """

    @pytest.mark.parametrize("fmt", ["`{}`", "**`{}`**", "**`{}` — and commentary**"])
    def test_a_fixed_red_does_not_block(self, fmt: str) -> None:
        assert _row("🔴", fmt.format("FIXED")).blocks_promotion is False

    @pytest.mark.parametrize("fmt", ["`{}` |", "**`{}`** |", "**`{}`** — reported, not fixed"])
    def test_an_open_red_blocks(self, fmt: str) -> None:
        assert _row("🔴", fmt.format("OPEN")).blocks_promotion is True

    @pytest.mark.parametrize("fmt", ["`{}` — Lane B has it", "**`{}`** — Lane B has it"])
    def test_a_fixing_red_still_blocks(self, fmt: str) -> None:
        assert _row("🔴", fmt.format("FIXING")).blocks_promotion is True

    def test_the_register_on_disk_agrees_with_its_own_state_column(self) -> None:
        """⚡ **The parity check the unit cases cannot replace.**

        `state` and `unresolved` are two readings of one cell, and they disagreed
        for six days. Constructed rows only ever exercise the forms somebody
        thought to write; **the register is where the unthought-of form lives.**
        """
        register = Path(__file__).resolve().parents[2] / "docs" / "BUGS.md"
        rows = registers.bug_rows(register.read_text(encoding="utf-8"))
        assert rows, "the register parsed to nothing — the section format changed"
        for row in rows:
            assert row.unresolved == (row.state in ("OPEN", "FIXING")), (
                f"{row.identifier}: state={row.state!r} but unresolved={row.unresolved} — "
                f"two readings of one cell disagree"
            )
