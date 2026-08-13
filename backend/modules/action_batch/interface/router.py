"""The Action Batch's HTTP surface — [TASK-465](../../../../docs/BACKLOG.md).

**Two endpoints, and the pair is the row.** One accepts an application and
answers immediately; the other says how far it got. **Neither performs the
work**, and the first one's status code is the whole argument.

⚠️ **Amended by [TASK-466](../../../../docs/BACKLOG.md), 2026-08-13, and the
gap was named a cycle before it was closed.** 📁 That row's own cell:
***"its HTTP surface publishes two endpoints of seven… there is no `propose`,
`approve` or `reverse` route, so a screen cannot create a batch or take one
back."***

🔴 **Building the first consumer proved it.** A proposed batch could not be
approved, so it could never apply, so nothing could be reversed — **and the
*Add tag* control would have proposed work nobody could accept.** ✅ **`approve`
and `reverse` are added here, on the module's own router**, which is where 📁
[D-235](../../../../docs/DECISION_REGISTER.md) ① puts them: *"human approval
stays a separate product boundary."* ⛔ **The published port stays `propose`
and nothing else.**
"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, HTTPException, status

from modules.action_batch.application.batches import ActionBatchNotFound
from modules.action_batch.domain.batch import ActionBatchError
from modules.action_batch.infrastructure.composition import build_action_batches
from modules.action_batch.interface.schemas import ActionBatchProgressResponse
from signora_platform.api import CurrentWorkspace
from signora_platform.authorization import Action, Resource

router = APIRouter(tags=["action batches"])


@router.post(
    "/workspaces/{workspace_id}/action-batches/{batch_id}/apply",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=ActionBatchProgressResponse,
    summary="Apply an approved batch",
)
async def apply_batch(context: CurrentWorkspace, batch_id: UUID) -> ActionBatchProgressResponse:
    """*"Do the thing we agreed to."*

    🔴 **`202`, and the code IS the contract.** 📁 [§14](../../../../CLAUDE.md):
    *a handler responds once the request has been durably accepted, never after
    the work.* ⛔ **`200` here would say the work is done**, which is exactly the
    risk this row was written against: *a customer told **applied** before the
    work finishes.*

    **What has happened when this returns**: the batch is recorded as accepted
    and the acceptance is in the outbox, in one transaction. **A worker applies
    it.** ⚡ **The response says `progress: accepted`**, and the screen has
    everything it needs to say so honestly.

    ⛔ **Nothing here performs the change.** 📁 This context *"records; it does
    not perform"* — the consuming domain does the work on the authority of the
    approval already stored.

    **Asking twice is refused rather than queued.** ⚠️ **Two dispatches of one
    approval means the change runs twice**, which is a defect to surface rather
    than a job to enqueue — so the domain refuses it and this answers `409`.
    """
    context.authorize(Resource.ACTION_BATCH, Action.UPDATE)

    batches = build_action_batches(context.session)
    try:
        accepted = await batches.request_application(
            context.workspace_id, batch_id, actor_id=context.principal.user_id
        )
    except ActionBatchNotFound as missing:
        # ⛔ **`404`, never `403`** — 📁 §7, because *forbidden* confirms the id
        # exists and that is a workspace-enumeration oracle.
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(missing)) from missing
    except ActionBatchError as refusal:
        # ⚡ **`409`, and the domain's own sentence.** The request was
        # well-formed; the batch is simply not in a state where it can be
        # applied, and paraphrasing that here would put a worse explanation in
        # front of the customer.
        raise HTTPException(status.HTTP_409_CONFLICT, str(refusal)) from refusal

    return ActionBatchProgressResponse.from_domain(accepted)


@router.get(
    "/workspaces/{workspace_id}/action-batches/{batch_id}",
    response_model=ActionBatchProgressResponse,
    summary="How far an action batch has got",
)
async def read_batch(context: CurrentWorkspace, batch_id: UUID) -> ActionBatchProgressResponse:
    """*"Is it done yet?"*

    🔴 **The read [P-A](../../../../docs/DOMAIN_DISCOVERY_REGISTER.md) exists
    for**, and 📁 [455](../../../../docs/architecture/455-context-definitions-r02-r03.md)
    applies it to this slice by name: ⛔ **a batch that is *still running* and
    one that *failed to start* must never render alike.** ✅ **`progress`
    distinguishes them and `failure_reason` says why**, so the screen never has
    to choose between a spinner that never stops and an error it cannot
    explain.
    """
    context.authorize(Resource.ACTION_BATCH, Action.READ)

    batch = await build_action_batches(context.session).current(context.workspace_id, batch_id)
    if batch is None:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            "no action batch with that id in this workspace",
        )

    return ActionBatchProgressResponse.from_domain(batch)


@router.post(
    "/workspaces/{workspace_id}/action-batches/{batch_id}/approve",
    response_model=ActionBatchProgressResponse,
    summary="Approve a proposed batch",
)
async def approve_batch(
    context: CurrentWorkspace, batch_id: UUID
) -> ActionBatchProgressResponse:
    """*"Yes, do this."*

    🔴 **The route [TASK-466](../../../../docs/BACKLOG.md) found missing while
    building the first consumer**, and its own row named the gap a cycle
    earlier: ⛔ ***"its HTTP surface publishes two endpoints of seven… there is
    no `propose`, `approve` or `reverse` route, so a screen cannot create a
    batch or take one back."***

    ⚡ **This is where human approval lives**, and 📁
    [D-235](../../../../docs/DECISION_REGISTER.md) ① is why it is here rather
    than on the published port: *"human approval stays a separate product
    boundary."* ⛔ **A consuming domain may propose and may never approve** —
    *intelligence suggests; humans commit.*

    ⛔ **Approving is not applying.** 📁 The module's own words: *"`APPROVED`
    with no `applied_at` is a real state, not an inconsistency — approval and
    application are two moments."* **The screen asks for the application
    separately**, which is what keeps *"I agreed to this"* and *"it has
    started"* two facts a customer can tell apart.

    **`200`, not `201`** — nothing is created; a decision is recorded against
    something that already existed.
    """
    context.authorize(Resource.ACTION_BATCH, Action.UPDATE)

    batches = build_action_batches(context.session)
    try:
        approved = await batches.approve(
            context.workspace_id, batch_id, actor_id=context.principal.user_id
        )
    except ActionBatchNotFound as missing:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(missing)) from missing
    except ActionBatchError as refusal:
        raise HTTPException(status.HTTP_409_CONFLICT, str(refusal)) from refusal

    return ActionBatchProgressResponse.from_domain(approved)


@router.post(
    "/workspaces/{workspace_id}/action-batches/{batch_id}/reverse",
    response_model=ActionBatchProgressResponse,
    summary="Take an applied batch back, inside the window",
)
async def reverse_batch(
    context: CurrentWorkspace, batch_id: UUID
) -> ActionBatchProgressResponse:
    """*"Undo what we did."*

    🔴 **The half [TASK-466](../../../../docs/BACKLOG.md) calls a defect when it
    is missing**: ⛔ ***"a batch that applies but cannot be reversed in the
    window is a defect, not a limitation."***

    ⚡ **The window is enforced by the domain, not by this handler.** 📁
    `reversed_by` refuses a settled batch, which is what makes `has_settled`
    load-bearing rather than descriptive — **and a second check here would be
    behaviour existing twice** ([§2](../../../../CLAUDE.md)).

    ⛔ **Nothing here performs the inverse.** The reversal is announced, and the
    consuming domain that did the work undoes it — 📁
    [ADR-0405](../../../../docs/architecture/adr/0405-an-action-is-approved-before-it-is-effective.md):
    *the consuming domain owns performing the operation and implementing the
    inverse.*

    **`409` when the window has closed**, with the domain's own sentence — ⚠️
    and *"reversal was never offered"* and *"the window has closed"* are
    different refusals, which is why the domain answers rather than this file.
    """
    context.authorize(Resource.ACTION_BATCH, Action.UPDATE)

    batches = build_action_batches(context.session)
    try:
        undone = await batches.reverse(
            context.workspace_id, batch_id, actor_id=context.principal.user_id
        )
    except ActionBatchNotFound as missing:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(missing)) from missing
    except ActionBatchError as refusal:
        raise HTTPException(status.HTTP_409_CONFLICT, str(refusal)) from refusal

    return ActionBatchProgressResponse.from_domain(undone)
