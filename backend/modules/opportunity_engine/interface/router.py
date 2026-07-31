"""FastAPI routes for the Opportunity Engine.

Handlers do three things and nothing else: translate the request into query
input, authorize, and translate the result into a response schema. All
business rules live in the application and domain layers; all authentication,
membership verification, and RLS context is established by the dependency
chain before a handler runs (18-authentication.md).

**The first read surface a customer can reach.** Twelve modules produce
intelligence and, until this router, none of it had an HTTP path — the
pipeline ran nine stages ahead of anything a person could see
(37-product-surface.md).

The route is `/workspaces/{workspace_id}/accounts` rather than
`/opportunities`, and the noun is deliberate: **a seller works accounts, not
opportunity records.** The opportunity is Signora's word for the workflow
object; the account is what the customer came to look at.
"""

from typing import Annotated

from fastapi import APIRouter, Query

from apps.api.composition.opportunities import OpportunityRead
from modules.opportunity_engine.interface.schemas import AccountAttentionResponse
from signora_platform.api import CurrentWorkspace, CursorPage
from signora_platform.authorization import Action, Resource
from signora_platform.pagination import (
    DEFAULT_PAGE_LIMIT,
    MAX_PAGE_LIMIT,
    decode_cursor,
    encode_cursor,
)

router = APIRouter(tags=["accounts"])

LimitParam = Annotated[int, Query(ge=1, le=MAX_PAGE_LIMIT)]
CursorParam = Annotated[str | None, Query()]


@router.get(
    "/workspaces/{workspace_id}/accounts",
    response_model=CursorPage[AccountAttentionResponse],
    summary="Accounts worth attention, most pressing first",
)
async def list_accounts(
    context: CurrentWorkspace,
    queries: OpportunityRead,
    limit: LimitParam = DEFAULT_PAGE_LIMIT,
    cursor: CursorParam = None,
) -> CursorPage[AccountAttentionResponse]:
    """*"Which accounts should I work on today?"*

    Open opportunities in this workspace, ranked by the **live** buying score
    — never by the score that opened them, which is a fact about the past. At
    equal score a contested account ranks higher, because opposing readings
    mean a fought-over account rather than an uncertain one.

    Accounts whose evidence has expired still appear, ranked last, carrying
    `score: null` and `evidence: stale`. An opportunity outlives the score
    that created it, and dropping one would be Signora deciding a human's
    workload.

    **Pages are walked by a keyset the pipeline cannot move.** The cursor
    positions on `(opened_at, id)`; ranking is applied over each page. Paging
    by score would let a recomputation between two requests skip an account or
    show it twice.
    """
    context.authorize(Resource.OPPORTUNITY, Action.READ)
    page = await queries.attention_list(
        context.workspace_id,
        after=decode_cursor(cursor) if cursor else None,
        limit=limit,
    )
    position = page.next_position
    return CursorPage(
        items=[AccountAttentionResponse.from_domain(t) for t in page.items],
        next_cursor=encode_cursor(position) if position else None,
        has_more=page.has_more,
    )


__all__ = ["router"]
