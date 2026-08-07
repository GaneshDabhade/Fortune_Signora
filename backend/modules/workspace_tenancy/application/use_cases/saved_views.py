"""Declaring, revising, retiring and reading a saved view.

**TASK-451**, slice 3 of
[455 §4](../../../../../docs/architecture/455-context-definitions-r02-r03.md).
Slice 1 published the contract, slice 2 built the aggregate and its table;
this is the layer a screen can actually reach.

### Four use cases, and the shape of each is set by the aggregate

**Nothing here decides anything the domain can decide.** `declare` checks the
name, `revise` refuses a retired view, `retire` refuses a second retirement —
so these read, call the aggregate, and persist. **A rule that appeared here
instead would be a rule the aggregate's own tests could not reach.**

### ⛔ What none of them do

**Parse, validate, execute, rank or optimise a declaration**
([D-091](../../../../../docs/DECISION_REGISTER.md)). A use case that looked
inside one would make `workspace_tenancy` responsible for another module's
semantics, which is the whole boundary this context keeps.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any
from uuid import UUID

from modules.workspace_tenancy.application.ports import SavedViewRepository, WorkspaceRepository
from modules.workspace_tenancy.domain.exceptions import (
    SavedViewNotFoundError,
    WorkspaceNotFoundError,
)
from modules.workspace_tenancy.domain.saved_view import SavedView
from signora_platform.pagination import CursorPosition, split_overfetched


@dataclass(frozen=True)
class DeclareSavedViewInput:
    workspace_id: UUID
    name: str
    declaration: dict[str, Any]
    created_by: UUID
    #: Supplied by the caller so a retry is idempotent, on `TargetAccount`'s
    #: precedent and the public contract's own words.
    saved_view_id: UUID | None = None


@dataclass(frozen=True)
class ReviseSavedViewInput:
    workspace_id: UUID
    saved_view_id: UUID
    #: **Its own actor, never carried forward from the version being
    #: replaced** — attributing a revision to whoever wrote the first one is
    #: the misattribution `revise` exists to refuse.
    created_by: UUID
    name: str | None = None
    declaration: dict[str, Any] | None = None


@dataclass(frozen=True)
class RetireSavedViewInput:
    workspace_id: UUID
    saved_view_id: UUID


@dataclass(frozen=True)
class ListSavedViewsInput:
    workspace_id: UUID
    limit: int
    after: CursorPosition | None


@dataclass(frozen=True)
class ListSavedViewsResult:
    views: list[SavedView]
    has_more: bool


class _SavedViewUseCase:
    """The workspace check every one of them performs first.

    **Under RLS a workspace the caller cannot see reads as absent**, so this
    raises *not found* rather than distinguishing *forbidden* — which is what
    keeps workspace ids non-enumerable
    ([11-tenancy.md](../../../../../docs/architecture/11-tenancy.md)), and it
    is `ListWorkspaceMembersUseCase`'s existing shape rather than a new one.
    """

    def __init__(
        self, *, workspaces: WorkspaceRepository, saved_views: SavedViewRepository
    ) -> None:
        self._workspaces = workspaces
        self._saved_views = saved_views

    async def _require_workspace(self, workspace_id: UUID) -> None:
        if await self._workspaces.get(workspace_id) is None:
            raise WorkspaceNotFoundError(workspace_id)

    async def _require_view(self, workspace_id: UUID, saved_view_id: UUID) -> SavedView:
        view = await self._saved_views.get(workspace_id, saved_view_id)
        if view is None:
            raise SavedViewNotFoundError(saved_view_id)
        return view


class DeclareSavedViewUseCase(_SavedViewUseCase):
    """Somebody wrote a question down and named it."""

    async def execute(
        self, input_: DeclareSavedViewInput, *, now: datetime | None = None
    ) -> SavedView:
        await self._require_workspace(input_.workspace_id)
        view = SavedView.declare(
            workspace_id=input_.workspace_id,
            name=input_.name,
            declaration=input_.declaration,
            created_by=input_.created_by,
            now=now,
            saved_view_id=input_.saved_view_id,
        )
        await self._saved_views.add(view)
        return view


class ReviseSavedViewUseCase(_SavedViewUseCase):
    """A change is a new version naming the one it replaces.

    ⛔ **The earlier row is not touched.** It stays readable, which is what
    lets a colleague who acted on last week's reading still explain it.
    """

    async def execute(
        self, input_: ReviseSavedViewInput, *, now: datetime | None = None
    ) -> SavedView:
        await self._require_workspace(input_.workspace_id)
        current = await self._require_view(input_.workspace_id, input_.saved_view_id)
        revision = current.revise(
            name=input_.name,
            declaration=input_.declaration,
            created_by=input_.created_by,
            now=now,
        )
        await self._saved_views.add(revision)
        return revision


class RetireSavedViewUseCase(_SavedViewUseCase):
    """Stop offering it, without removing what it explained."""

    async def execute(
        self, input_: RetireSavedViewInput, *, now: datetime | None = None
    ) -> SavedView:
        await self._require_workspace(input_.workspace_id)
        current = await self._require_view(input_.workspace_id, input_.saved_view_id)
        retired = current.retire(at=now)
        await self._saved_views.mark_retired(retired)
        return retired


class ListSavedViewsUseCase(_SavedViewUseCase):
    """The views in force, a page at a time.

    **Overfetches by one rather than counting**, the precedent every paged
    read here follows: a count is a scan to answer a question asked only to
    decide whether to draw one more control.
    """

    async def execute(self, input_: ListSavedViewsInput) -> ListSavedViewsResult:
        await self._require_workspace(input_.workspace_id)
        rows = await self._saved_views.list_live_page(
            input_.workspace_id, limit=input_.limit + 1, after=input_.after
        )
        views, has_more = split_overfetched(rows, limit=input_.limit)
        return ListSavedViewsResult(views=views, has_more=has_more)


class GetSavedViewUseCase(_SavedViewUseCase):
    """One view, or nothing.

    ⚡ **Returns `None` rather than raising**, because the public contract says
    *"absence is a legitimate answer, not an error"* — a view from another
    workspace is invisible under RLS and retrying will not make it appear.
    **The endpoint turns that into a 404; the read does not pretend it failed.**
    """

    async def execute(self, workspace_id: UUID, saved_view_id: UUID) -> SavedView | None:
        await self._require_workspace(workspace_id)
        return await self._saved_views.get(workspace_id, saved_view_id)


__all__ = [
    "DeclareSavedViewInput",
    "DeclareSavedViewUseCase",
    "GetSavedViewUseCase",
    "ListSavedViewsInput",
    "ListSavedViewsResult",
    "ListSavedViewsUseCase",
    "RetireSavedViewInput",
    "RetireSavedViewUseCase",
    "ReviseSavedViewInput",
    "ReviseSavedViewUseCase",
]
