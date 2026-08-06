"""The Provider Platform's one HTTP surface — **A7**.

**Why this module serves it rather than the one that owns the list.**
`GET /workspaces/{id}/target-accounts` belongs to Commercial Profile and says
so in its own docstring: *"never a status… whether Signora has looked at any of
them yet is Provider Platform's facts — this response has no field that could
carry one."* It could not gain one either: the dependency matrix runs
**Commercial Profile → Provider Platform**, so the module holding the list may
not read the module holding the attempts, and reversing that edge would make
the graph cyclic (05-module-dependencies.md).

**So the frontend composes the two reads**, which is exactly what
`account-identities` already does for names and for the same reason — the
option that needed no graph change.

**It is a batch, not a lookup**, on that surface's precedent: a target list is
rendered whole, and a per-company request would be a loop within a week.
"""

from typing import Annotated

from fastapi import APIRouter, Query

from apps.api.composition.coverage import CoverageRead
from modules.provider_platform.interface.schemas import SubjectCoverageResponse
from signora_platform.api import CurrentWorkspace
from signora_platform.authorization import Action, Resource
from signora_platform.pagination import MAX_PAGE_LIMIT

router = APIRouter(tags=["target-accounts"])

#: The same ceiling the identity batch uses. A request naming more companies
#: than a page can hold is either a mistake or a scrape, and a target list is
#: a declaration a person typed.
SubjectsParam = Annotated[list[str], Query(min_length=1, max_length=MAX_PAGE_LIMIT)]


@router.get(
    "/workspaces/{workspace_id}/target-account-coverage",
    response_model=list[SubjectCoverageResponse],
    summary="When Signora last looked at these companies",
)
async def target_account_coverage(
    context: CurrentWorkspace, reads: CoverageRead, subjects: SubjectsParam
) -> list[SubjectCoverageResponse]:
    """One entry per company asked about, in the order asked.

    **A company nobody has checked comes back as an entry, not as an omission.**
    *Never checked* is an answer, and a caller reading a missing key renders a
    blank — which is the state the freshness line already refuses in words
    rather than in whitespace.

    **`target_account, read` rather than a new resource.** This is the same
    grant as reading the list itself: it says nothing a member cannot already
    see, and inventing a resource for the timestamps beside a list they may
    read would be a distinction the policy file cannot defend.
    """
    context.authorize(Resource.TARGET_ACCOUNT, Action.READ)
    found = await reads.execute(context.workspace_id, tuple(subjects))
    return [SubjectCoverageResponse.from_domain(entry) for entry in found]
