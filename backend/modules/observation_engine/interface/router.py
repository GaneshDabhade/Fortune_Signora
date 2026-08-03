"""FastAPI routes for a company's recorded changes.

Handlers translate, authorize, delegate. All business rules live in the
application and domain layers; authentication, membership verification and RLS
context are established by the dependency chain before a handler runs.

**The module's first HTTP surface, and everything behind it was already
built.** `Observation` has carried the previous value, the current value, the
direction, the magnitude, the window and the provider since M4 — and until now
no customer could see any of it. That is Epic A's whole shape: exposing what
the platform already knows rather than computing it again.
"""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Query

from apps.api.composition.observations import ObservationRead
from modules.observation_engine.interface.schemas import AccountObservationResponse
from modules.provider_normalization.public import ClaimAttribute
from signora_platform.api import CurrentWorkspace
from signora_platform.authorization import Action, Resource

router = APIRouter(tags=["accounts"])

AttributeParam = Annotated[ClaimAttribute | None, Query()]


@router.get(
    "/workspaces/{workspace_id}/accounts/{account_id}/observations",
    response_model=list[AccountObservationResponse],
    summary="How this company has changed, and who says so",
)
async def account_observations(
    context: CurrentWorkspace,
    queries: ObservationRead,
    account_id: UUID,
    attribute: AttributeParam = None,
) -> list[AccountObservationResponse]:
    """*"Is this company actually growing, or did it hire once?"*

    The brief says *"Grew headcount 15% over 32 days"* and nothing behind it.
    This is what is behind it: every recorded change to this account, with what
    it moved from, what it moved to, who observed it, and the window the move
    happened in.

    ### Each row belongs to one provider, and that is a correctness constraint

    **A reading is only ever a change according to one source.** Apollo saying
    120 on Monday and CoreSignal saying 145 on Tuesday is *disagreement*, not
    growth of 25 — and a client that joins these into a single line per
    attribute draws exactly that phantom. **Group by `provider` before
    plotting.** The Observation Engine refuses to merge them for the same
    reason, and its `series` read is per-provider by construction.

    ### `previous_observed_at` and `observed_at` bound an interval

    The change happened *somewhere between them*, and never more precisely.
    A client drawing a single point is claiming a precision the evidence does
    not have.

    **Not a page.** An account the pipeline has watched for a year has tens of
    changes, not thousands, and `attribute` narrows it further. If a real
    workspace makes this large, that measurement is the trigger for pagination
    ([12-scalability.md](../../../../docs/architecture/12-scalability.md)) —
    not a guess made now.

    **An account with no recorded changes returns `[]`**, not a 404. *Nothing
    has moved here yet* is a well-formed answer to a well-formed question, and
    it is a different sentence from *this account does not exist*.
    """
    context.authorize(Resource.ACCOUNT, Action.READ)
    observations = await queries.observations(
        context.workspace_id, account_id, attribute=attribute
    )
    return [AccountObservationResponse.from_domain(o) for o in observations]


__all__ = ["router"]
