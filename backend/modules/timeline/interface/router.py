"""FastAPI routes for the timeline feed.

Handlers translate, authorize, delegate. Authentication, membership
verification and RLS context are established by the dependency chain before a
handler runs.
"""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Query

from apps.api.composition.timeline import TimelineRead
from modules.timeline.interface.schemas import TimelineEntryResponse
from signora_platform.api import CurrentWorkspace
from signora_platform.api.responses import CursorPage
from signora_platform.authorization import Action, Resource
from signora_platform.pagination import (
    DEFAULT_PAGE_LIMIT,
    MAX_PAGE_LIMIT,
    decode_cursor,
    encode_cursor,
)

router = APIRouter(tags=["timeline"])

LimitParam = Annotated[int, Query(ge=1, le=MAX_PAGE_LIMIT)]
CursorParam = Annotated[str | None, Query()]


@router.get(
    "/workspaces/{workspace_id}/accounts/{account_id}/timeline",
    response_model=CursorPage[TimelineEntryResponse],
    summary="What has happened with this account",
)
async def account_timeline(
    workspace_id: UUID,
    account_id: UUID,
    context: CurrentWorkspace,
    queries: TimelineRead,
    limit: LimitParam = DEFAULT_PAGE_LIMIT,
    cursor: CursorParam = None,
) -> CursorPage[TimelineEntryResponse]:
    """*"What has actually happened with this account?"*

    Everything the pipeline recorded about this account, newest first — an
    observation arriving, a business event detected, a signal found relevant, a
    score moving, an opportunity opening or changing hands.

    **Nothing here is Signora's opinion.** Every entry restates what the module
    that owned the fact already decided, and names that module so a reader can
    go there for the reasoning. Timeline ranks nothing, scores nothing and
    explains nothing — those are other modules' jobs and it does not repeat
    them.

    **Entries are ordered by when things happened, not when Signora noticed.**
    Detection can lag occurrence by days; a funding round announced in March
    reads in March.

    **Pages walk a keyset nothing can move.** The cursor positions on
    `(occurred_at, id)` and entries are immutable, so a page boundary cannot
    skip or repeat an entry however much the pipeline writes between requests.
    """
    context.authorize(Resource.TIMELINE, Action.READ)
    page = await queries.feed(
        context.workspace_id,
        account_id,
        after=decode_cursor(cursor) if cursor else None,
        limit=limit,
    )
    position = page.next_position
    return CursorPage(
        items=[TimelineEntryResponse.from_domain(entry) for entry in page.items],
        next_cursor=encode_cursor(position) if position and page.has_more else None,
        has_more=page.has_more,
    )
