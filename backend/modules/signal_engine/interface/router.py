"""FastAPI routes for the Signal Engine's validation surface.

Handlers translate, authorize, delegate. Authentication, membership
verification and RLS context are established by the dependency chain before a
handler runs.
"""

from uuid import UUID

from fastapi import APIRouter

from apps.api.composition.validation import SignalRead
from modules.signal_engine.interface.schemas import (
    AccountValidationResponse,
    HypothesisValidationResponse,
)
from modules.signal_engine.domain.catalog import Relevance
from signora_platform.api import CurrentWorkspace
from signora_platform.authorization import Action, Resource

router = APIRouter(tags=["accounts"])

#: Most relevant first. Ordering is the *product's* judgement about which
#: hypothesis a seller should validate first, and `Relevance` is the only
#: declaration of importance the platform holds — it is the workspace's own,
#: not an inference. Ties fall back to the title so two runs agree.
_ORDER = {
    Relevance.PRIMARY: 0,
    Relevance.SUPPORTING: 1,
    Relevance.CONTEXTUAL: 2,
    Relevance.IGNORED: 3,
}


@router.get(
    "/workspaces/{workspace_id}/accounts/{account_id}/validation",
    response_model=AccountValidationResponse,
    summary="What to check on this account, and what the evidence cannot tell you",
)
async def account_validation(
    context: CurrentWorkspace, queries: SignalRead, account_id: UUID
) -> AccountValidationResponse:
    """*"What should I do?"* — as far as deterministic evidence can answer it.

    For every hypothesis currently held about this account: what it proposes,
    **what it does not prove**, and what to confirm before acting on it.

    **None of this is a recommendation, and none of it involved a model.** The
    guidance is a property of the hypothesis *type* — what
    `expansion_opportunity` fails to establish is the same for every account
    and every workspace — so it lives in the Signal Catalog, versioned and
    reviewed like code. A recommendation would be specific to this company and
    inferred; this is neither.

    **The limitations are the half that matters.** A score invites
    over-reading, and this is the only place that says what it cannot support.
    The product does not become more certain; the reader becomes better
    calibrated, which is the more useful thing to give somebody about to spend
    an hour on a call.

    **Live hypotheses only** — superseded, expired and profile-deactivated ones
    are excluded, because guidance about something no longer believed is worse
    than none. An account with nothing live returns an empty list, which is an
    answer rather than an error, and never a 404.
    """
    context.authorize(Resource.ACCOUNT, Action.READ)
    signals = await queries.signals(context.workspace_id, account_id)
    catalog = queries.catalog()

    return AccountValidationResponse(
        account_id=account_id,
        hypotheses=tuple(
            HypothesisValidationResponse.from_domain(
                signal, catalog.definition(signal.signal_type)
            )
            for signal in sorted(
                signals,
                key=lambda s: (
                    _ORDER[s.relevance],
                    catalog.definition(s.signal_type).title,
                ),
            )
        ),
    )


__all__ = ["router"]
