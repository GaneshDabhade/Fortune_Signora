"""The published read side of the target account list.

**The only place this module is read from outside**, and the whole of its
implementation: a query, and a copy into the frozen views declared in
`public/`. It is separated from `repository.py` deliberately — everything
there serves this module's own use cases and may change freely; everything
here is a contract with somebody else and may not.

The mapping is the boundary. A consumer receives `TargetAccountListView`,
never `TargetAccountList`, so this module's validation rules, constructors and
future refactors stay entirely its own.
"""

from __future__ import annotations

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from modules.commercial_profile.infrastructure.models import TargetAccountListModel
from modules.commercial_profile.infrastructure.versioned import latest
from modules.commercial_profile.public import (
    TargetAccountListView,
    TargetAccountView,
)


class SqlTargetAccountReader:
    """Implements `TargetAccountReader` for the composition root to inject."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def current(self, workspace_id: UUID) -> TargetAccountListView | None:
        """The list in force, or ``None`` when nothing has been declared.

        **The whole list, never a delta.** What has and has not been
        synchronized is not a fact this module holds (ADR-0036 §4).
        """
        result = await self._session.execute(latest(TargetAccountListModel, workspace_id))
        row = result.scalar_one_or_none()
        if row is None:
            return None

        return TargetAccountListView(
            workspace_id=row.workspace_id,
            version=row.version,
            accounts=tuple(
                TargetAccountView(id=UUID(raw["id"]), name=raw["name"]) for raw in row.accounts
            ),
        )
