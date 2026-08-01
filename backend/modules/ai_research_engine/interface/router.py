"""FastAPI routes for the AI Research Engine.

Handlers do three things and nothing else: translate the request into use-case
input, authorize, and translate the result into a response schema.

**The first endpoint in Signora that starts work rather than reading it.**
Every other write records a decision a person already made; this one asks the
platform to spend a model call. That difference is why the response is `202`
and not `201`: nothing has been produced yet, and a status code implying
otherwise would be the API's own version of a spinner that lies.

The route is `/accounts/{account_id}/research`, and both nouns are the
customer's. A seller asks Signora to *research an account*; `entity`,
`opportunity` and `task` are the platform's words for what happens next
(ADR-0034).
"""

from uuid import UUID

from fastapi import APIRouter, HTTPException, Response, status

from apps.api.composition.research import ResearchRead, ResearchRequestWrite
from modules.ai_research_engine.application.request import RequestResearchInput
from modules.ai_research_engine.interface.schemas import ResearchStateResponse
from signora_platform.api import CurrentWorkspace
from signora_platform.authorization import Action, Resource

router = APIRouter(tags=["research"])


@router.post(
    "/workspaces/{workspace_id}/accounts/{account_id}/research",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=ResearchStateResponse,
    summary="Ask Signora to research this account",
)
async def request_research(
    context: CurrentWorkspace,
    research: ResearchRequestWrite,
    account_id: UUID,
    response: Response,
) -> ResearchStateResponse:
    """*"Look into this one properly."*

    **The handler calls no model, and could not.** It is handed a use case with
    no `Infer` in it: the ask is recorded, an event is published in the same
    transaction, and a worker does the work. Research takes about a minute
    against two model calls, and an API that waited would hold a connection
    open for it (CLAUDE.md §7).

    **Asking twice answers `200` rather than starting a second run.** A seller
    who clicks again because nothing visibly happened has not made a mistake
    worth an error — they have asked a question the product can answer, and the
    answer is *"one is already running"*. The second run would finish later,
    cost the same, and produce findings whose derived identities collide with
    the first run's anyway.

    **Who asked is taken from the verified principal, never from the body.**
    A request that could name its own requester would let one member spend
    another's name on a model call, and cost attribution is not something a
    later reader can reconstruct.
    """
    context.authorize(Resource.RESEARCH, Action.ADD)
    result = await research.execute(
        RequestResearchInput(
            workspace_id=context.workspace_id,
            entity_id=account_id,
            requested_by=context.principal.user_id,
        ),
        correlation_id=context.correlation_id,
    )
    if result.already_running:
        response.status_code = status.HTTP_200_OK
    return ResearchStateResponse.from_request(
        request_id=result.request.id,
        requested_at=result.request.requested_at,
        state=result.state,
    )


@router.get(
    "/workspaces/{workspace_id}/accounts/{account_id}/research",
    response_model=ResearchStateResponse,
    summary="What research on this account has found",
)
async def account_research(
    context: CurrentWorkspace, research: ResearchRead, account_id: UUID
) -> ResearchStateResponse:
    """The state of the ask, and the brief when there is one.

    **One endpoint rather than two.** *"Is it still running?"* and *"what did
    it find?"* are the same question asked at different moments, and splitting
    them would make a client stitch a story the module already knows.

    `404` when nobody has ever asked — deliberately the same answer an account
    outside this workspace gets. A caller learning that research *could* be
    requested here is a caller learning the account exists.
    """
    context.authorize(Resource.RESEARCH, Action.READ)
    found = await research.for_account(context.workspace_id, account_id)
    if found is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No research has been requested for this account.",
        )
    return ResearchStateResponse.from_domain(found)


__all__ = ["router"]
