"""The published read side of the competitor list.

**The module's second published read, and the second consumer of its
`public/`** — which is the point at which that surface stops being a courtesy
and becomes a contract with stability obligations
([ADR-0403](../../../../docs/architecture/adr/0403-signal-engine-reads-a-declaration.md)).

Separated from `repository.py` on the same terms as the target account
reader: everything there serves this module's own use cases and may change
freely; everything here is a contract with somebody else and may not.

The mapping is the boundary. A consumer receives `DeclaredCompetitorListView`,
never `DeclaredCompetitors`, so this module's validation rules, constructors
and future refactors stay entirely its own.
"""

from __future__ import annotations

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from modules.commercial_profile.infrastructure.models import DeclaredCompetitorsModel
from modules.commercial_profile.infrastructure.versioned import latest
from modules.commercial_profile.public import (
    DeclaredCompetitorListView,
    DeclaredCompetitorView,
)


class SqlDeclaredCompetitorReader:
    """Implements `DeclaredCompetitorReader` for the composition root to inject."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def current(self, workspace_id: UUID) -> DeclaredCompetitorListView | None:
        """The list in force, or ``None`` when nothing has been declared.

        **`None` and an empty tuple are different answers**, and the caller is
        entitled to tell them apart: nobody has said anything, versus somebody
        said *"we compete with nobody"*. Collapsing them would treat a
        considered answer as an unanswered question.
        """
        result = await self._session.execute(latest(DeclaredCompetitorsModel, workspace_id))
        row = result.scalar_one_or_none()
        if row is None:
            return None

        return DeclaredCompetitorListView(
            workspace_id=row.workspace_id,
            competitors=tuple(
                DeclaredCompetitorView(id=UUID(raw["id"]), name=raw["name"])
                for raw in row.competitors
            ),
        )
