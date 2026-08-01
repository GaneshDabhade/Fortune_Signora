"""FastAPI routes for the Business Event Engine's evidence surface.

Handlers translate, authorize, delegate. Authentication, membership
verification and RLS context are established by the dependency chain before a
handler runs.

**Addressed by event, not nested under an account.** A citation carries
`business_event:<id>` and nothing else — a reader following one has the event's
identity and need not already know which company it belongs to. Requiring the
account in the path would make every caller carry a fact the citation format
deliberately omits.
"""

from uuid import UUID

from fastapi import APIRouter, HTTPException, status

from apps.api.composition.evidence import BusinessEventRead
from modules.business_event_engine.interface.schemas import BusinessEventEvidenceResponse
from signora_platform.api import CurrentWorkspace
from signora_platform.authorization import Action, Resource

router = APIRouter(tags=["evidence"])


@router.get(
    "/workspaces/{workspace_id}/business-events/{event_id}",
    response_model=BusinessEventEvidenceResponse,
    summary="What happened, and every provider reading that says so",
)
async def business_event_evidence(
    context: CurrentWorkspace, queries: BusinessEventRead, event_id: UUID
) -> BusinessEventEvidenceResponse:
    """*"Prove it."* — the end of every citation in the product.

    A business event with the **observations underneath it**: which provider
    reported what, what the value was before, and when they saw it.

    **This is the claim Signora actually makes.** Every other surface says
    something *about* this fact — the signal interprets it, the score weighs it,
    the narration describes it — and each of those is Signora's own reasoning.
    The readings here are the only content the platform did not write, which is
    why a citation has to end at them rather than at another summary.

    **Corroboration is reported rather than assumed.** A fact supported by one
    provider is not a weaker fact; it is a differently-supported one, and a
    reader who cannot tell the two apart will assume agreement nobody measured.

    **404 when the event is not this workspace's**, identical to one that does
    not exist — a citation is a bare identifier, and a distinguishable answer
    would make evidence enumerable across tenants.
    """
    context.authorize(Resource.ACCOUNT, Action.READ)
    evidence = await queries.business_event_evidence(context.workspace_id, event_id)
    if evidence is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No such business event in this workspace.",
        )
    return BusinessEventEvidenceResponse.from_domain(evidence)


__all__ = ["router"]
