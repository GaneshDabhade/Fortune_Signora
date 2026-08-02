"""**Reading the registers, in one place.**

`state-check.py` and `kpi.py` both need to answer *"is this bug blocking?"*, and
they answered it differently — one counted any 🔴 in a severity cell, the other
counted cells beginning with one, and neither agreed with the register's own
rule. **Truth has exactly one authoritative representation** (`CLAUDE.md` §2), so
the parsing lives here and both import it.

**It parses; it never judges.** What to do about a blocking bug is governance.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

SEVERITY_MARKERS = "🔴🟠🟡🟢"
UNRESOLVED_PREFIXES = ("`OPEN`", "`FIXING`")


@dataclass(frozen=True)
class BugRow:
    identifier: str
    severity: str
    status: str
    unresolved: bool
    malformed: bool

    @property
    def blocks_promotion(self) -> bool:
        """🔴 **and** unresolved. A fixed 🔴 is a record, not a blocker."""
        return self.severity == "🔴" and self.unresolved


def bug_rows(text: str) -> list[BugRow]:
    """Every `### B-nnn` section, with its operative severity and status.

    **The first severity marker in the cell is the operative one.** The register
    writes conditional severities — *"🟠 unreachable today · 🔴 the moment a
    workspace watches two accounts"* — and reading the forecast as the present
    would block every promotion on a defect nobody can reach yet.
    """
    parts = re.split(r"^### (B-\d+)[^\n]*\n", text, flags=re.M)
    rows: list[BugRow] = []
    for identifier, body in zip(parts[1::2], parts[2::2], strict=False):
        severity_cell = re.search(r"\| \*\*Severity\*\* \| (.+)", body)
        status_cell = re.search(r"\| \*\*Status\*\* \| (.+)", body)
        if not (severity_cell and status_cell):
            rows.append(BugRow(identifier, "", "", False, malformed=True))
            continue
        markers = re.findall(f"[{SEVERITY_MARKERS}]", severity_cell.group(1))
        status = status_cell.group(1).strip()
        rows.append(
            BugRow(
                identifier=identifier,
                severity=markers[0] if markers else "",
                status=status,
                unresolved=status.startswith(UNRESOLVED_PREFIXES),
                malformed=False,
            )
        )
    return rows


def malformed_tables(text: str) -> list[int]:
    """Line numbers of table separators with no header row above them.

    The residue of a merge that split a section — how a corrupted register
    survived four certifications, because gates read code and not documents.
    """
    return [
        number
        for number, line in enumerate(text.splitlines(), start=1)
        if re.fullmatch(r"-{3,}\|[-|]*", line.strip())
    ]


def task_ids(text: str) -> set[str]:
    return set(re.findall(r"\bTASK-(\d+)\b", text))
