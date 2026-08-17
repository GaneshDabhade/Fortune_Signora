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
UNRESOLVED_STATES = ("OPEN", "FIXING")

# **The lifecycle, in order, and the order is what makes it readable.** A status
# cell is prose, and the operative state is the one it *opens* with — exactly the
# rule already applied to severity above.
STATES = ("OPEN", "FIXING", "FIXED", "VERIFIED", "WONTFIX")


@dataclass(frozen=True)
class BugRow:
    identifier: str
    severity: str
    status: str
    malformed: bool

    @property
    def blocks_promotion(self) -> bool:
        """🔴 **and** unresolved. A fixed 🔴 is a record, not a blocker."""
        return self.severity == "🔴" and self.unresolved

    @property
    def unresolved(self) -> bool:
        """**Derived from `state`, never parsed a second way.**

        This was `status.startswith(("`OPEN`", "`FIXING`"))`, and **29 of the 39
        open rows write the state in bold** — `**`OPEN`**` — so the prefix never
        matched and the register reported *ten* unresolved rows out of thirty-nine
        ([B-413](../docs/BUGS.md)). **`blocks_promotion` returned `False` for every
        row in the file**, including a 🔴.

        ⛔ **The two properties on this one dataclass disagreed about what the
        status cell said**: `state` located the token with `find`, and this one
        required it at character zero. **Truth has exactly one authoritative
        representation** (§2) — so there is now one reading, and `unresolved` is a
        question asked of it.
        """
        return self.state in UNRESOLVED_STATES

    @property
    def state(self) -> str:
        """The **one** lifecycle state this row is in.

        **The first state token in the cell is the operative one** — the same rule
        `bug_rows` applies to a conditional severity, for the same reason: the rest
        of the cell is commentary, and a row that *names* its next state has not
        reached it.

        Counting by substring instead put nine rows in two buckets at once
        ([B-101](../docs/BUGS.md)), because *"`FIXED` — **`VERIFIED` is QE's to
        set**"* contains both words. The totals then exceeded the number of rows,
        published under a banner promising they were never edited by hand — which
        made them more trusted, not less.
        """
        found = [(self.status.find(f"`{s}`"), s) for s in STATES if f"`{s}`" in self.status]
        return min(found)[1] if found else ""


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
            rows.append(BugRow(identifier, "", "", malformed=True))
            continue
        markers = re.findall(f"[{SEVERITY_MARKERS}]", severity_cell.group(1))
        rows.append(
            BugRow(
                identifier=identifier,
                severity=markers[0] if markers else "",
                status=status_cell.group(1).strip(),
                malformed=False,
            )
        )
    return rows


#: **The `Planning-Sync` trailer — [D-136](../docs/DECISION_REGISTER.md).**
#:
#: A planning correction carries this as a commit trailer so QE can treat it as
#: high-priority synchronization. It is a commit message rather than a file
#: because a shared file is a conflict surface between the two lanes it exists
#: to coordinate.
#:
#: **The full trailer, and the exactness is the point.** `pipeline-dashboard.py`
#: counted every commit on the current branch and called the total *"planning
#: not on integration"* — five `infra/` bug fixes reported as a 🔴 against the
#: Product Office ([B-440](../docs/BUGS.md)). Matching on the bare word
#: `Planning-Sync` is no better: this file's own repair commit says it in prose
#: while carrying no trailer, and a bare grep counts it.
PLANNING_SYNC_TRAILER = "Planning-Sync: required"


def planning_sync_commits(log: str) -> int:
    """How many commits in `log` are planning corrections.

    Takes `git log --format=%B` output rather than running git, so the caller
    owns the range — **which range is the right one is a governance question,
    not a parsing one**, and this file parses and never judges.
    """
    return log.count(PLANNING_SYNC_TRAILER)


CONFLICT_MARKERS = ("<<<<<<< ", "=======", ">>>>>>> ")


def conflict_markers(text: str) -> list[int]:
    """Line numbers carrying an unresolved merge-conflict marker.

    **`malformed_tables` was built for the residue of a split section and does
    not catch this**: a `>>>>>>>` line inside a markdown table is not a table
    separator, so a conflict marker sat in the coordination register through
    several certifications ([B-102](../docs/BUGS.md)) — stranding one row
    outside the table and leaving two others duplicated with contradictory
    statuses.

    **`=======` is matched exactly**, never as a prefix: a markdown setext
    underline is a run of `=` and would otherwise be reported on every heading.

    **Fenced code blocks are skipped**, because a register that *documents* a
    conflict marker is not corrupt — B-102's own row quotes the marker it
    reports, and the check fired on it within a minute of being written. The
    register describing a defect must not be indistinguishable from the register
    having one.
    """
    found: list[int] = []
    fenced = False
    for number, line in enumerate(text.splitlines(), start=1):
        if line.lstrip().startswith("```"):
            fenced = not fenced
            continue
        if fenced:
            continue
        if (
            line.startswith(CONFLICT_MARKERS[0])
            or line.startswith(CONFLICT_MARKERS[2])
            or line.rstrip() == CONFLICT_MARKERS[1]
        ):
            found.append(number)
    return found


def unclosed_fence(text: str) -> int | None:
    """Line number of the code fence nothing closes, or `None`.

    **`conflict_markers` trusts fence parity to decide what to skip, and an
    odd fence inverts that decision for the whole rest of the file** — every
    marker in prose is then silently skipped and every quoted one is reported.
    Found in `docs/BUGS.md` (B-403): a row lost its opening ```` ```bash ````
    to a merge, and the check had been reporting the wrong half of the
    register for three days while blind to the real half.

    **A guard that reasons about structure must first establish that the
    structure holds** (`CLAUDE.md` §2) — otherwise its silence means nothing.
    """
    opened_at: int | None = None
    for number, line in enumerate(text.splitlines(), start=1):
        if line.lstrip().startswith("```"):
            opened_at = None if opened_at is not None else number
    return opened_at


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
