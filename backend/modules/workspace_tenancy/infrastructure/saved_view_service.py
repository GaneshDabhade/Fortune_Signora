"""What another module sees when it reads a saved view.

**TASK-451.** Implements `SavedViewReader` and `SavedViewWriter` from this
module's [`public/`](../public/saved_views.py) — the halves slice 1 published
and nothing implemented.

### Composed over the repository, never a second query

⚡ **Every read here delegates to `SqlAlchemySavedViewRepository`.** *Live*
means exactly what it means to this module's own use cases — not retired, not
superseded — **decided in one place**, on the precedent `build_triage` states
for the same reason: a second definition of *live* would disagree the first
time a version landed.

### Why the reader and the writer are separate types on one class

**The ports are separate because they are granted differently** — every member
reads the views their workspace shares, and creating one is an act with an
author. ⚡ **One class satisfying both is a composition-root convenience, not a
merge of the two grants**: a caller is handed the port it needs, and the
authorization that decides which happens at the endpoint, in Casbin.
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from modules.workspace_tenancy.domain.saved_view import (
    SavedView,
    checked_declaration,
    checked_name,
)
from modules.workspace_tenancy.infrastructure.repositories import SqlAlchemySavedViewRepository
from modules.workspace_tenancy.public.saved_views import SavedViewListView, SavedViewView
from signora_platform.pagination import DEFAULT_PAGE_LIMIT, CursorPosition, split_overfetched


def to_view(view: SavedView) -> SavedViewView:
    """The aggregate as another module may hold it.

    ⛔ **The declaration is passed through untouched and uninspected** — this
    function does not know what a key in it means, which is
    [D-091](../../../../docs/DECISION_REGISTER.md)'s whole content.
    """
    return SavedViewView(
        id=view.id,
        workspace_id=view.workspace_id,
        name=view.name,
        declaration=view.declaration,
        created_by=view.created_by,
        created_at=view.created_at,
        supersedes=view.supersedes,
        retired_at=view.retired_at,
    )


class SavedViewService:
    """Reads and writes saved views for consumers outside this module."""

    def __init__(self, repository: SqlAlchemySavedViewRepository) -> None:
        self._repository = repository

    async def by_id(self, workspace_id: UUID, saved_view_id: UUID) -> SavedViewView | None:
        """**`None` is an answer rather than a failure**, as the contract says:
        a view from another workspace is invisible under RLS, and retrying will
        not make it appear."""
        view = await self._repository.get(workspace_id, saved_view_id)
        return None if view is None else to_view(view)

    async def live(
        self,
        workspace_id: UUID,
        *,
        after: CursorPosition | None = None,
        limit: int = DEFAULT_PAGE_LIMIT,
    ) -> SavedViewListView:
        rows = await self._repository.list_live_page(workspace_id, limit=limit + 1, after=after)
        page, has_more = split_overfetched(rows, limit=limit)
        return SavedViewListView(
            items=tuple(to_view(view) for view in page),
            has_more=has_more,
            # **From the last row of the page**, and the page is unfiltered
            # here — so unlike a filtered read there is no seam to skip past.
            next_position=(
                CursorPosition(created_at=page[-1].created_at, id=page[-1].id)
                if has_more and page
                else None
            ),
        )

    async def save(self, view: SavedViewView) -> None:
        """Record a view, or a new version naming the one it replaces.

        ⚠️ **The declaration is re-checked by the aggregate on the way in.**
        A `SavedViewView` is a Pydantic model a consumer constructed, so it
        carries no guarantee that the name is non-empty — passing it straight
        to SQL would let a caller store through `public/` what the domain
        refuses through the use case, which is the same rule enforced in two
        strengths.
        """
        await self._repository.add(
            SavedView(
                id=view.id,
                workspace_id=view.workspace_id,
                name=checked_name(view.name),
                declaration=checked_declaration(view.declaration),
                created_by=view.created_by,
                created_at=view.created_at,
                supersedes=view.supersedes,
                retired_at=view.retired_at,
            )
        )

    async def retire(self, workspace_id: UUID, saved_view_id: UUID, *, at: datetime) -> None:
        """Stop offering it, without removing what it explained.

        ⛔ **Silently does nothing when the view is absent or already retired**,
        because the row-level guard is `retired_at IS NULL` — the first
        timestamp is the one that happened.
        """
        current = await self._repository.get(workspace_id, saved_view_id)
        if current is None or current.is_retired:
            return
        await self._repository.mark_retired(current.retire(at=at))


__all__ = ["SavedViewService", "to_view"]
