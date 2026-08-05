"""FastAPI routes for Sales Engagement's approach read path.

Handlers translate, authorize, delegate. Authentication, membership
verification and RLS context are established by the dependency chain before a
handler runs.

**The module's first interface layer, and it arrives four slices late by
design.** `pyproject.toml` recorded the reason in its own comment: the module
*"owns no fact and therefore has nothing to expose over HTTP yet"*, and
creating an empty package to satisfy a linter would have been *"a placeholder
pretending to be structure."* A-ii is the slice that changes the premise.

**This route reads and never writes.** Assembling an approach is deterministic
— it ranks a declared committee against recorded evidence — so nothing here
blocks on a model. The synthesis that turns the ranking into prose is a
separate use case, and keeping it out is what stops a read path acquiring a
provider (§7).
"""

from uuid import UUID

from fastapi import APIRouter, Query

from apps.api.composition.approach import ApproachRead
from modules.sales_engagement.application.approach import ApproachInput
from modules.sales_engagement.interface.schemas import ApproachResponse
from signora_platform.api import CurrentWorkspace
from signora_platform.authorization import Action, Resource

router = APIRouter(tags=["accounts"])


@router.get(
    "/workspaces/{workspace_id}/accounts/{account_id}/approach",
    response_model=ApproachResponse,
    summary="Who to approach at this account, and why them",
)
async def account_approach(
    context: CurrentWorkspace,
    approaches: ApproachRead,
    account_id: UUID,
    product_id: UUID | None = Query(
        default=None,
        description=(
            "Which of your products this is about. Supply it and the portfolio is not "
            "consulted at all — an answer is an answer, not a hint to be re-checked."
        ),
    ),
) -> ApproachResponse:
    """*"Who do I talk to here, and what do I say?"*

    **Always answers.** There is no 404: an account with no committee declared
    and no evidence recorded still receives roles that did not rank and the
    reasons they did not, which is more useful than an empty screen and is the
    only shape that tells a seller what to fix. *"No evidence names your CFO"*
    is the sentence a ranked list structurally cannot carry.

    **`product_id` is the seller's override.** Supplying it means the portfolio
    is never read and `fits` comes back empty — showing a product ranking beside
    somebody's own answer invites them to re-litigate a decision they made.
    Omitting it asks the platform to infer, and when two products fit equally
    well **the tie is left standing**: the reasoning runs against the widest
    committee and the unresolved question arrives in `unknowns`, rather than
    a coin being tossed out of sight.

    **Nothing here is written by a model.** Every value is derived from a
    declaration the customer made or an event the pipeline recorded, and each
    ranked role carries the evidence that ranked it.
    """
    context.authorize(Resource.ACCOUNT, Action.READ)
    approach = await approaches.execute(
        ApproachInput(
            workspace_id=context.workspace_id,
            account_id=account_id,
            product_id=product_id,
        )
    )
    return ApproachResponse.from_domain(approach)


__all__ = ["router"]
