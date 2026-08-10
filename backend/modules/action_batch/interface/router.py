"""The Action Batch's HTTP surface — [TASK-465](../../../../docs/BACKLOG.md).

**Two endpoints, and the pair is the row.** One accepts an application and
answers immediately; the other says how far it got. **Neither performs the
work**, and the first one's status code is the whole argument.
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
