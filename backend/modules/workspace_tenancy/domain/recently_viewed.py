"""What a person opened, so Home can offer it back.

📁 **`Fortune Signora Session Continuity.dc.html`, tier 4 · work context** —
*"active AI thread, in-flight agent run reference, last search query, last
workspace, **recently viewed records**"*. **Tier 4's medium is the server**
(`D-01`, *"four tiers, one medium each"*), which is why this is a domain object
and not browser state.

📁 **What reads it** — `Fortune Signora Home.dc.html` §04: *"Pick up where you
left off · last five records touched · **context, never urgent**."* ⛔ **Home
stores nothing of its own**, by its own reconciliation, so the fact lives here.

## 🔴 *"Touched"* is *viewed*, and Home did not decide that

⚠️ **Home says *"touched"* and never defines it.** ✅ **Session Continuity names
the same list and defines it as *viewed*** — its tier-4 fact is *"recently
viewed records"* and its restore rule says *"silent where it only informs a list
**(recents)**"*. ⛔ **This module does not get to widen that to *edited* or
*created***: those are different facts and would need their own source.

## ⚡ A view is idempotent per record

**Opening the same account twice is one entry with a later time, not two.**
📁 The design asks for *"the last five **records**"* — ⛔ **five rows for one
account is the answer nobody wants**, and it is what an append-only reading log
would return for a person who refreshed.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from uuid import UUID


class ViewedKind(StrEnum):
    """What sort of record was opened.

    📁 **The design's own example names three** — *"Vantage Logistics"*,
    *"EMEA enterprise pipeline"*, *"Norvell Energy research"*. ⛔ **A closed
    enum rather than free text**: a kind nothing can open is a row the card
    would render with nowhere to go.
    """

    ACCOUNT = "account"
    REPORT = "report"
    RESEARCH = "research"


@dataclass(frozen=True, slots=True)
class ViewedRecord:
    """One record this person opened, and when they last opened it.

    ⛔ **Carries no title.** 📁 The name of an account is the Knowledge Graph's
    to state and changes without this module hearing about it — **storing it
    here would be a second representation of a fact that moves**
    ([§2](../../../../CLAUDE.md)). ✅ **Home resolves names through the identity
    surface**, exactly as its attention card already does.
    """

    workspace_id: UUID
    person_id: UUID
    entity_id: UUID
    kind: ViewedKind
    viewed_at: datetime
