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
from modules.knowledge_graph.interface.schemas import AccountIdentityResponse
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


__all__ = ["router"]
