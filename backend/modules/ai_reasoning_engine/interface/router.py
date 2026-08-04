"""FastAPI routes for the AI Reasoning Engine's read path.

Handlers translate, authorize, delegate. Authentication, membership
verification and RLS context are established by the dependency chain before a
handler runs.

**This route reads and never writes.** Reaching a conclusion is one model call
plus the context assembly beneath it; §7 forbids an API handler blocking on
pipeline work, and Principle 13 puts that work in a background worker. A `POST`
here would be the most tempting shortcut in the product and the most expensive
one — and it would make this module the agentic thing the M9/M10 split exists
to keep it from becoming.
"""

from uuid import UUID

from fastapi import APIRouter, HTTPException, status

from apps.api.composition.reasoning import DecisionPackageRead
from modules.ai_reasoning_engine.interface.schemas import DecisionPackageResponse
from signora_platform.api import CurrentWorkspace
from signora_platform.authorization import Action, Resource

router = APIRouter(tags=["accounts"])


@router.get(
    "/workspaces/{workspace_id}/accounts/{account_id}/decision-package",
    response_model=DecisionPackageResponse,
    summary="What Signora concluded about this account, and how to disagree with it",
)
async def account_decision_package(
    context: CurrentWorkspace,
    packages: DecisionPackageRead,
    account_id: UUID,
) -> DecisionPackageResponse:
    """*"What do you think, and why should I believe you?"*

    The **most recent** Decision Package for this account. Packages accumulate
    and are never edited: a better conclusion is a new package naming a later
    score, so what a customer was shown in June survives being told something
    different in August. There is no way to ask for an older one here, and that
    is a deliberate absence rather than a missing filter — nothing in the
    product yet asks *"what did you think last month?"*, and an endpoint built
    for a question nobody is asking is speculative (§6).

    **A conclusion arrives with what argues against it.** `alternative_readings`
    carries the hypotheses that were tested and set aside, `support.contested`
    says whether signals read the same evidence differently, and `limitations`
    says what the conclusion cannot see. None of it is optional and none of it
    is a caveat bolted on: a package that stated no limitations is refused at
    construction, because an empty one means the catalog was never consulted.

    **Every sentence a model wrote carries its citations**, and there is no
    flattened paragraph — joining the statements would discard the mapping from
    claim to evidence, which is the only reason to trust any of it.

    **404 when nothing has been concluded**, which is the ordinary state of a
    new account: a package is produced by a background worker after the
    deterministic pipeline has a score worth explaining. It is the same answer
    an account in another workspace receives, which is what stops the endpoint
    from being a workspace enumeration oracle (§7).
    """
    context.authorize(Resource.ACCOUNT, Action.READ)
    package = await packages.latest_for(context.workspace_id, account_id)
    if package is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Signora has not reached a conclusion about this account yet.",
        )
    return DecisionPackageResponse.from_domain(package)


__all__ = ["router"]
