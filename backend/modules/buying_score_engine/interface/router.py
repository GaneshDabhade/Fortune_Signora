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
from modules.buying_score_engine.interface.schemas import (
    AccountScoreResponse,
    ScoringModelResponse,
)
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


@router.get(
    "/workspaces/{workspace_id}/scoring-model",
    response_model=ScoringModelResponse,
    summary="What each kind of finding implies commercially",
)
async def scoring_model(
    context: CurrentWorkspace, queries: BuyingScoreRead
) -> ScoringModelResponse:
    """*"Is this good news or bad news?"* — **for a kind of finding, not an
    account.**

    The per-account read above needs an account. A surface that ranks findings
    needs to know what each kind *means* before it has one in hand: Home draws
    attention severity from posture, and severity is wrong on the first paint if
    it has to wait for a per-account round trip.

    **Posture and nothing else.** Weights are the input to a ranking this module
    performs; publishing them would let a client compute a second ranking that
    disagrees with the score. Posture is a closed vocabulary a screen renders as
    an affordance — the ledger already puts it on the wire per contribution, and
    this is the same fact one level up.

    **The workspace's model, not the shipped artifact.** `scoring_model`
    resolves a workspace's tuning over Signora's defaults, so a workspace that
    has changed nothing still receives a complete answer.

    **No 404.** Every workspace has a model in force, because the artifact is
    the floor — an absent answer here would be indistinguishable from a
    workspace whose findings mean nothing.
    """
    context.authorize(Resource.ACCOUNT, Action.READ)
    return ScoringModelResponse.from_domain(await queries.scoring_model(context.workspace_id))


__all__ = ["router"]
