"""FastAPI routes for the Knowledge Graph's identity surface.

Handlers translate, authorize, delegate. All business rules live in the
application and domain layers; authentication, membership verification and RLS
context are established by the dependency chain before a handler runs.

**Why this is a separate request rather than a field on the attention list.**
No module in the ratified dependency graph reaches both workflow and entity
names — `Opportunity Engine → Buying Score Engine` only, and the Revenue
Intelligence Platform never reaches the Knowledge Graph
(05-module-dependencies.md). The frontend composes the two, which is the option
that needed no graph change (37-product-surface.md).

**It is a batch, not a lookup.** A page of fifty accounts must cost one request,
not fifty — an obvious N+1 is a defect at write time (CLAUDE.md §14). There is
deliberately **no single-account variant**: one would be used by a loop within a
week, and the batch answers a request for one perfectly well.
"""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Query
from pydantic import BaseModel, ConfigDict, Field

from apps.api.composition.accounts import GraphRead
from modules.knowledge_graph.interface.schemas import (
    AccountCommercialEntryResponse,
    AccountCommercialResponse,
    AccountIdentityEntryResponse,
    ListedAccountResponse,
    SearchGroupResponse,
)
from signora_platform.api import CurrentWorkspace, CursorPage
from signora_platform.authorization import Action, Resource
from signora_platform.pagination import (
    DEFAULT_PAGE_LIMIT,
    MAX_PAGE_LIMIT,
    decode_cursor,
    encode_cursor,
)

router = APIRouter(tags=["accounts"])

#: Bounded by the same ceiling a page is. The caller's realistic use is *"name
#: the rows I just received"*, and a request naming more accounts than a page
#: can hold is either a mistake or a scrape.
IdsParam = Annotated[list[UUID], Query(min_length=1, max_length=MAX_PAGE_LIMIT)]

#: The same shape every paginated surface uses — an opaque string the caller
#: echoes back, never a page number.
CursorParam = Annotated[str | None, Query()]


@router.get(
    "/workspaces/{workspace_id}/account-identities",
    response_model=list[AccountIdentityEntryResponse],
    summary="Who these accounts are, what kind of thing each one is, and how sure "
    "we are about the names",
)
async def account_identities(
    context: CurrentWorkspace, queries: GraphRead, ids: IdsParam
) -> list[AccountIdentityEntryResponse]:
    """Resolve names for a set of accounts.

    An account's name is not a stored field — it is a `legal_name` **claim**,
    from a provider, at a time, and providers can disagree. So this returns the
    name *and* whether your sources agreed on it, resolved fresh on every
    request rather than cached: a stored display name would eventually
    contradict the claims beneath it.

    **The newest claim wins.** A company that renamed should show its new name.
    Where providers disagree the newest is still shown, and `agreement` says so
    — disagreement is surfaced, never silently resolved.

    **Not a page.** This answers a request about accounts the caller already
    has, so it returns a plain list in no particular order; join it to your rows
    by `account.account_id`. An account the workspace does not own is simply
    absent rather than reported, which is the same reason a non-member sees 404.

    **Each row carries `kind` beside the identity** — B-261. Account 360
    persists a collapsed section *per account type, not per record*, and until
    this field existed the page could not read a type: it stored nothing rather
    than store a preference under a guess, which is a preference a rep cannot
    get back. `kind` sits beside the identity rather than inside it, because an
    identity answers *who is this* and a classification is a different question
    about the same account.
    """
    context.authorize(Resource.ACCOUNT, Action.READ)
    entries = await queries.identity_entries(context.workspace_id, tuple(ids))
    return [AccountIdentityEntryResponse.from_domain(entry) for entry in entries]


@router.get(
    "/workspaces/{workspace_id}/account-commercials",
    response_model=list[AccountCommercialEntryResponse],
    summary="What these accounts are worth, and where they stand",
)
async def account_commercials(
    context: CurrentWorkspace, queries: GraphRead, ids: IdsParam
) -> list[AccountCommercialEntryResponse]:
    """Resolve commercial facts for a set of accounts the caller already holds.

    **The sibling of `/account-identities`, and for the same reason.** A surface
    that starts from something other than a browse page — Home's attention card
    starts from the signal queue — has ids and needs facts about them. Paging
    `/accounts-list` until the right rows appear would read the whole book to
    find five accounts.

    **Not a parameter on `/account-identities`.** That endpoint answers *"name
    these ids"*; adding a commercial payload to it would charge three claim
    reads to every caller who wanted a name, and the identity surface is the one
    every screen already uses.

    **Every requested id comes back**, carrying an all-null object when nothing
    has been said. Absence is never inferred, defaulted or zero-filled
    (ADR-0409 §5), and an id the workspace does not own is simply not among the
    ids the query resolves.

    **Not a page.** A plain list in no particular order, joined by `account_id`
    — the same contract as the identity batch, so a caller composes both the
    same way.
    """
    context.authorize(Resource.ACCOUNT, Action.READ)
    commercial = await queries.commercial(context.workspace_id, tuple(ids))
    return [
        AccountCommercialEntryResponse(
            account_id=account_id,
            commercial=AccountCommercialResponse.from_domain(facts),
        )
        for account_id, facts in commercial.items()
    ]


#: Two characters, because one matches most of an alphabet and a customer who
#: has typed one letter has not asked a question yet.
QueryParam = Annotated[str, Query(min_length=2, max_length=200)]
LimitParam = Annotated[int, Query(ge=1, le=MAX_PAGE_LIMIT)]


@router.get(
    "/workspaces/{workspace_id}/accounts-list",
    response_model=CursorPage[ListedAccountResponse],
    summary="Every account this workspace knows, a page at a time",
)
async def accounts_list(
    context: CurrentWorkspace,
    queries: GraphRead,
    limit: LimitParam = DEFAULT_PAGE_LIMIT,
    cursor: CursorParam = None,
) -> CursorPage[ListedAccountResponse]:
    """*"Show me my accounts."* — browse, not search.

    **A second read rather than a parameter on `/account-search`**, and the
    reason is in that endpoint's own guard: it refuses blank input because *"an
    empty pattern matches every claim in the workspace… the one that forgets
    ships a search box that dumps the customer's whole book of business on the
    first keystroke."* **Relaxing that guard to build this would break
    search.** Browse and search are two questions and want two reads.

    **The rows carry the same identity a search result does**, resolved by the
    same rule — so a table renders one type whether the customer typed
    something or not.

    ⛔ **Keyset pagination, never offset.** The graph is written continuously:
    a resolution binds a new provider identity and an account appears, so an
    offset page would skip or repeat rows between two requests and a customer
    paging the list would silently miss accounts.

    **Oldest first**, which is stable — a list ordered by anything the graph
    recomputes would reshuffle underneath somebody reading it.
    """
    context.authorize(Resource.ACCOUNT, Action.READ)
    page = await queries.list_accounts(
        context.workspace_id,
        after=decode_cursor(cursor) if cursor else None,
        limit=limit,
    )
    position = page.next_position
    return CursorPage(
        items=[ListedAccountResponse.from_domain(item) for item in page.items],
        next_cursor=encode_cursor(position) if position else None,
        has_more=page.has_more,
    )


@router.get(
    "/workspaces/{workspace_id}/account-search",
    response_model=list[SearchGroupResponse],
    summary="Find an account by name",
)
async def account_search(
    context: CurrentWorkspace,
    queries: GraphRead,
    q: QueryParam,
    limit: LimitParam = 10,
) -> list[SearchGroupResponse]:
    """*"Show me Databricks."* — the question a ranked list cannot answer.

    **Its own path rather than a parameter on `/account-identities`.** That
    endpoint answers *"name these ids I already hold"*: `ids` is required, it
    is deliberately **not a page**, and it returns no order. This answers
    *"which ids match this text"*, needs an order and a bound, and happens to
    return the same shape. One path choosing between two contracts by which
    parameter arrived is two endpoints wearing one coat.

    **Matched against every name a source has given, not the one displayed.**
    A company that renamed is found under its old name and shown under its
    new one — which is what somebody who has not heard about the rename is
    typing. It also means a result may not visibly contain the search text,
    so **every row says which name matched**: `is_renamed` marks the rows
    where that differs from what is being shown, and those are the only rows
    worth annotating.

    **Results arrive grouped by kind, and every kind is present.** ⚠️ **This
    reverses what this docstring said until 2026-08-05** — *"a type Signora
    cannot search is absent, never an empty group"* — on the product owner's
    ruling:

    > *"Return the group with zero matches rather than omitting it. The
    > absence of results and the absence of the group represent different
    > business meanings."*

    **The old rule was not wrong about the danger; it was wrong about the
    remedy.** An empty group *would* claim Signora looked — so the group now
    says whether it did. `coverage` carries three states that must not be
    collapsed: **`searched`** (it looked; `results` may be empty and that is
    an answer), **`not_applicable`** (it cannot look — search matches a legal
    name and only a company has one), **`not_requested`** (the caller excluded
    it). Omitting the group said all three at once, and therefore said none.

    **Empty is an answer.** No match returns a `searched` group with no
    results rather than a 404: the customer asked a well-formed question and
    *nothing here is called that* is the honest response.

    **Ordered by matched name**, so the same query returns the same rows in the
    same order on every run — a list that reshuffles between keystrokes is one
    a customer cannot click. **There is no relevance score**, and `matched_name`
    is the field the order was computed from, so the ranking can be read off
    the results rather than taken on trust.
    """
    context.authorize(Resource.ACCOUNT, Action.READ)
    found = await queries.find_accounts_grouped(context.workspace_id, q, limit=limit)
    return [SearchGroupResponse.from_domain(group) for group in found]


__all__ = ["router"]


class AccountCountResponse(BaseModel):
    """How many accounts this workspace holds.

    📁 **The design's header prints two numbers** — *"8,412 total · 312 in
    view"*. ⚡ **This is the first.** The second is the page the customer is
    looking at, which the screen already knows.

    ⛔ **Its own read rather than a field on the page.** `CursorPage` is
    platform-owned and frozen ([§20a](../../../CLAUDE.md)), and **a `COUNT(*)`
    attached to every page would be charged to a customer who is only
    scrolling.**
    """

    model_config = ConfigDict(frozen=True)

    total: int = Field(
        ge=0,
        description="Every account in this workspace, not only the loaded page. "
        "Zero is a real answer and means the book is empty.",
    )


@router.get(
    "/workspaces/{workspace_id}/accounts-count",
    response_model=AccountCountResponse,
    summary="How many accounts this workspace holds",
)
async def accounts_count(
    context: CurrentWorkspace,
    queries: GraphRead,
) -> AccountCountResponse:
    """The total the Companies header states beside the page count.

    ⚠️ **Separate from the list deliberately.** The list is keyset-paginated
    and cannot know the size of the book; **a screen that printed the loaded
    count beside the word *total* would be wrong by more with every page.**
    """
    context.authorize(Resource.ACCOUNT, Action.READ)
    return AccountCountResponse(total=await queries.count_accounts(context.workspace_id))
