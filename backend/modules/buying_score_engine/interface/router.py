"""FastAPI routes for the Buying Score Engine.

Handlers translate, authorize, delegate. All business rules live in the
application and domain layers; authentication, membership verification and RLS
context are established by the dependency chain before a handler runs.

**The route nests under the account deliberately.** A score is not a resource a
seller goes looking for — it is a property of an account they are already
reading, so `…/accounts/{account_id}/score` is the shape a client expects and
the shape the URL should tell the truth about. The identity endpoint sits
beside the collection instead (`…/account-identities`) because it names *many*
accounts in one request and cannot nest under one of them; that was a
consequence of batching, never a ruling about ownership.

**Nesting is not ownership.** `accounts` is the customer's noun, and this
endpoint belongs to the Buying Score Engine alone (§7) — no handler here
touches an opportunity, and the Opportunity Engine's router is untouched by it.
"""

from datetime import UTC, datetime
from uuid import UUID

from fastapi import APIRouter, HTTPException, status

from apps.api.composition.scores import BuyingScoreRead
from modules.buying_score_engine.interface.schemas import AccountScoreResponse
from signora_platform.api import CurrentWorkspace
from signora_platform.authorization import Action, Resource

router = APIRouter(tags=["accounts"])


@router.get(
    "/workspaces/{workspace_id}/accounts/{account_id}/score",
    response_model=AccountScoreResponse,
    summary="Why this account is scored where it is",
)
async def account_score(
    context: CurrentWorkspace, queries: BuyingScoreRead, account_id: UUID
) -> AccountScoreResponse:
    """*"Why this account?"*

    The current reading for one account **with its full ledger** — every
    business event that contributed, what each one added, and why the ones that
    added nothing added nothing. The score reproduces from the lines below
    exactly: sum the counted points, divide by the ceiling, cap at 100.

    **A reading, not a gauge.** It was exactly correct when computed and stays
    exactly correct until `valid_until`; `is_current` says whether that period
    still holds. An expired reading is returned rather than withheld, because
    an account going quiet is information the customer is entitled to see.

    **Contradiction is shown, never resolved.** When opposing readings are both
    live the account is `contested` and the outweighed lines are marked
    `dissenting` — the score is not reduced to split the difference, because a
    fought-over account warrants more attention rather than average attention.

    **404 when this account has never been scored**, which is the same answer a
    caller gets for an account in another workspace. That is deliberate: a
    distinguishable response would make account identifiers enumerable across
    tenants.
    """
    context.authorize(Resource.ACCOUNT, Action.READ)
    score = await queries.current(context.workspace_id, account_id)
    if score is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No score has been computed for this account.",
        )
    return AccountScoreResponse.from_domain(score, now=datetime.now(UTC))


__all__ = ["router"]
