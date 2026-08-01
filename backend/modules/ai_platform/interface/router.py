"""FastAPI routes for the AI Platform's narration read path.

Handlers translate, authorize, delegate. Authentication, membership
verification and RLS context are established by the dependency chain before a
handler runs.

**This route reads and never writes.** Producing a narration is a model call of
roughly twenty seconds; §7 forbids an API handler blocking on pipeline work,
and Principle 13 puts that work in a background worker. A `POST` here would be
the most tempting shortcut in the product and the most expensive one.
"""

from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, HTTPException, status

from apps.api.composition.narration import NarrationRead
from modules.ai_platform.interface.schemas import AccountNarrationResponse
from signora_platform.api import CurrentWorkspace
from signora_platform.authorization import Action, Resource

router = APIRouter(tags=["accounts"])


@router.get(
    "/workspaces/{workspace_id}/accounts/{account_id}/narration",
    response_model=AccountNarrationResponse,
    summary="What the evidence about this account says, in plain language",
)
async def account_narration(
    context: CurrentWorkspace, queries: NarrationRead, account_id: UUID
) -> AccountNarrationResponse:
    """*"Why does this matter?"* — the account brief's narrative half.

    The **most recent** grounded explanation for this account. Narrations
    accumulate and are never edited: a better explanation is a new one, so what
    a customer was shown in June survives being told something different in
    August.

    **Every sentence carries the evidence it rests on.** The platform does not
    constrain what a model writes; it constrains what the model may
    *reference*, and a statement citing nothing is refused before it is stored.
    So there is no un-cited summary field here, and there is no flattened
    paragraph — joining the statements would discard the mapping from claim to
    evidence, which is the only reason to trust any of it.

    **404 when nothing has been narrated**, which is the ordinary state of a
    new account: narration is produced by a background worker after the
    deterministic pipeline has something to explain. It is the same answer an
    account in another workspace receives.
    """
    context.authorize(Resource.ACCOUNT, Action.READ)
    narration = await queries.latest_for(context.workspace_id, account_id)
    if narration is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Nothing has been narrated for this account yet.",
        )
    return AccountNarrationResponse.from_domain(narration)


__all__ = ["router"]
