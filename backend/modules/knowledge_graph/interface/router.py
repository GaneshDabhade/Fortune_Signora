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

from apps.api.composition.accounts import GraphRead
from modules.knowledge_graph.interface.schemas import (
    AccountIdentityResponse,
    SearchGroupResponse,
)
from signora_platform.api import CurrentWorkspace
from signora_platform.authorization import Action, Resource
from signora_platform.pagination import MAX_PAGE_LIMIT

router = APIRouter(tags=["accounts"])

#: Bounded by the same ceiling a page is. The caller's realistic use is *"name
#: the rows I just received"*, and a request naming more accounts than a page
#: can hold is either a mistake or a scrape.
IdsParam = Annotated[list[UUID], Query(min_length=1, max_length=MAX_PAGE_LIMIT)]


@router.get(
    "/workspaces/{workspace_id}/account-identities",
    response_model=list[AccountIdentityResponse],
    summary="Who these accounts are, and how sure we are about the names",
)
async def account_identities(
    context: CurrentWorkspace, queries: GraphRead, ids: IdsParam
) -> list[AccountIdentityResponse]:
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
    by `account_id`. An account the workspace does not own is simply absent
    rather than reported, which is the same reason a non-member sees 404.
    """
    context.authorize(Resource.ACCOUNT, Action.READ)
    identities = await queries.identities(context.workspace_id, tuple(ids))
    return [AccountIdentityResponse.from_domain(identity) for identity in identities.values()]


#: Two characters, because one matches most of an alphabet and a customer who
#: has typed one letter has not asked a question yet.
QueryParam = Annotated[str, Query(min_length=2, max_length=200)]
LimitParam = Annotated[int, Query(ge=1, le=MAX_PAGE_LIMIT)]


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
