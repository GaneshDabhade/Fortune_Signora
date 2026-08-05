"""FastAPI routes for the Signal Engine's validation surface.

Handlers translate, authorize, delegate. Authentication, membership
verification and RLS context are established by the dependency chain before a
handler runs.
"""

from uuid import UUID

from fastapi import APIRouter

from apps.api.composition.triage import TriageRead
from apps.api.composition.validation import SignalRead
from modules.signal_engine.application.triage import QueueState
from modules.signal_engine.domain.catalog import Relevance
from modules.signal_engine.interface.schemas import (
    AccountValidationResponse,
    HypothesisValidationResponse,
    SignalCatalogResponse,
)
from modules.signal_engine.interface.triage_schemas import (
    QueueEntryResponse,
    QueueResponse,
    ResolutionHistoryResponse,
    ResolutionResponse,
)
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
    # Signals **with the events they cite** (R2-01). Two reads rather than one
    # per hypothesis — the guidance is generic by design, and what makes it
    # legible as guidance about *this* account is the evidence beside it.
    held = await queries.live_with_evidence(context.workspace_id, account_id)
    catalog = queries.catalog()

    return AccountValidationResponse(
        account_id=account_id,
        hypotheses=tuple(
            HypothesisValidationResponse.from_domain(
                signal, catalog.definition(signal.signal_type), events
            )
            for signal, events in sorted(
                held,
                key=lambda pair: (
                    _ORDER[pair[0].relevance],
                    catalog.definition(pair[0].signal_type).title,
                ),
            )
        ),
    )


@router.get(
    "/workspaces/{workspace_id}/signal-catalog",
    response_model=SignalCatalogResponse,
    summary="What Signora can conclude about an account, and what each is called",
)
async def signal_catalog(context: CurrentWorkspace, queries: SignalRead) -> SignalCatalogResponse:
    """The hypothesis vocabulary — **the one place a signal type has a name.**

    Every other surface that shows a hypothesis cites it by key. The attention
    list does, because the module that ranks accounts is forbidden from
    reaching the Signal Engine at all: *it decides what to track and never
    forms hypotheses or weighs them*, and a workflow module that could name one
    is a workflow module that could branch on one.

    So the key travels and the name is resolved here, by its owner. The
    alternative — a translation table in the client — is a second vocabulary,
    and two representations of one truth become contradictory truth.

    **Names only.** What a hypothesis proposes, what it cannot prove and what
    to check are per-account questions the validation surface already answers;
    repeating them here would put the same prose in two places, and the copy
    nobody looks at is the one that goes stale.

    Workspace-scoped like every endpoint, so authorization carries a workspace
    in its tuple. The vocabulary itself is global today — a workspace reads the
    catalog, it does not author one — and the path is what lets that change
    without a client knowing.
    """
    context.authorize(Resource.ACCOUNT, Action.READ)
    return SignalCatalogResponse.from_domain(queries.catalog())


@router.get(
    "/workspaces/{workspace_id}/accounts/{account_id}/triage",
    response_model=QueueResponse,
    summary="What is still yours to deal with on this account, and what has been decided",
)
async def account_triage(
    context: CurrentWorkspace,
    queue: TriageRead,
    account_id: UUID,
    state: QueueState | None = None,
) -> QueueResponse:
    """**A triage queue, not a notification list** — and the difference is
    entirely this read.

    A notification list shows everything that happened. A queue shows what is
    still yours, which means every signal here carries the decision in force
    about it, or none.

    **`state` is derived, never stored.** It is a function of the outcome and
    the current time, which is exactly why *"a snoozed signal returns at the
    stated time with its original evidence intact"*: the clock moves and the
    signal reappears in `open`. **Nothing runs, nothing regenerates, and the
    evidence is intact because nothing touched it** — the account a seller sees
    in a fortnight is the one they postponed, not a fresh reading that
    resembles it.

    **Omitting `state` returns everything, including closed rows.** *"Nothing
    is deleted: every resolution is auditable"*, and a caller reviewing the
    queue needs to see what left it and why.

    **Live hypotheses only**, on this module's existing terms — superseded,
    expired and profile-deactivated ones never enter the queue. Asking somebody
    to decide about a hypothesis Signora has stopped making would be asking
    them to do work the product created and then abandoned.

    An account with nothing live returns an empty list, which is an answer
    rather than an error, and never a 404.
    """
    context.authorize(Resource.ACCOUNT, Action.READ)
    entries = await queue.queue(context.workspace_id, account_id, state=state)
    return QueueResponse(
        account_id=account_id,
        entries=tuple(QueueEntryResponse.from_domain(entry) for entry in entries),
    )


@router.get(
    "/workspaces/{workspace_id}/signals/{signal_id}/decisions",
    response_model=ResolutionHistoryResponse,
    summary="Everything ever decided about this hypothesis, including what was undone",
)
async def signal_decisions(
    context: CurrentWorkspace, queue: TriageRead, signal_id: UUID
) -> ResolutionHistoryResponse:
    """The audit trail the product promises: *"nothing is deleted — every
    resolution is auditable."*

    **A dismissal somebody later regretted is still here**, with the reason
    they gave at the time. That is the whole point of a correction being a new
    record naming the one it replaces rather than an edit: the queue can show
    what is true now while staying answerable about how it got there.

    Oldest first, so the sequence reads as the history it is. A signal nobody
    has decided about returns an empty list rather than a 404 — *"nobody has
    decided yet"* is an answer, and it is not the same as *"no such signal"*.
    """
    context.authorize(Resource.ACCOUNT, Action.READ)
    decisions = await queue.history(context.workspace_id, signal_id)
    return ResolutionHistoryResponse(
        signal_id=signal_id,
        decisions=tuple(ResolutionResponse.from_domain(entry) for entry in decisions),
    )


__all__ = ["router"]
