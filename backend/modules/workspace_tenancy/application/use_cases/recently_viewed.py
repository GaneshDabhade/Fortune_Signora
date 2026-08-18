"""Recording what a person opened, and offering it back.

📁 **`Fortune Signora Session Continuity.dc.html`, tier 4 · work context.**
📁 **Read by** `Fortune Signora Home.dc.html` §04 — *"Pick up where you left
off · last five records touched · context, never urgent."*
"""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from modules.workspace_tenancy.application.ports import RecentlyViewedRepository
from modules.workspace_tenancy.domain.recently_viewed import ViewedKind, ViewedRecord

#: 📁 **Home's own number** — *"last five records touched"*, §04's registry.
#: ⛔ **Not the card's to choose**: the card renders what it is given, and a
#: limit decided in the component would make the API's answer depend on who
#: asked.
HOME_RECENTS = 5


@dataclass(frozen=True, slots=True)
class RecordViewUseCase:
    """One person opened one record.

    ⚡ **Idempotent per record.** 📁 The design asks for *"the last five
    RECORDS"* — ⛔ **an append-only reading log answers with one account five
    times** for somebody who refreshed, which is the single way this card can
    be useless.
    """

    recently_viewed: RecentlyViewedRepository

    async def execute(
        self, workspace_id: UUID, person_id: UUID, entity_id: UUID, kind: ViewedKind
    ) -> None:
        await self.recently_viewed.record(workspace_id, person_id, entity_id, kind)


@dataclass(frozen=True, slots=True)
class RecentRecordsUseCase:
    """What this person opened most recently, newest first.

    ⛔ **Own records only.** There is no parameter that could ask for a
    colleague's — 📁 492 §0's person predicate is in the RLS policy as well as
    the query, so the absence of the parameter is not the only thing preventing
    it.

    ⚡ **The retention window is injected**, because 📁 Session Continuity's
    `U-01` requires 30 days to be *"configuration, not a constant"* — the
    owner is **Legal + Security**, not this lane.
    """

    recently_viewed: RecentlyViewedRepository
    retention_days: int

    async def execute(
        self, workspace_id: UUID, person_id: UUID, *, limit: int = HOME_RECENTS
    ) -> tuple[ViewedRecord, ...]:
        return await self.recently_viewed.recent(
            workspace_id, person_id, limit=limit, within_days=self.retention_days
        )
