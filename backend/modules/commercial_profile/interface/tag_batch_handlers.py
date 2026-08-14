"""Event handlers: run and take back a bulk *Add tag* — [TASK-466](../../../../docs/BACKLOG.md).

**The consuming domain performing the work**, which is the half
[ADR-0405](../../../../docs/architecture/adr/0405-an-action-is-approved-before-it-is-effective.md)
reserves for it: *"the consuming domain owns performing the operation and
implementing the inverse."*

📁 `action_batch/interface/handlers.py` names this slice by number —
***"The use case remains, and its caller is slice 6. When the consuming domain
performs the work, *it* is what discovers the work could not be done"*** — and
[TASK-466](../../../../docs/BACKLOG.md) is slice 6.

### ⚡ This module imports nothing from `action_batch`

**Measured, not asserted.** 📁 `apps/worker/subscriptions.py` hands every
handler a generic `EventEnvelope`, so a consumer reads `payload["batch_id"]`
and the producing module's types never enter. ⛔ **The event *name* is the
composition root's to know** — it subscribes; this file only handles.

### ⛔ A batch this module did not propose is not an error

**The Action Batch is a shared lifecycle** and other domains will use it, so
`action_batch.applied` arrives for batches that are nobody's business here.
⚡ **The store answers `None` and the handler returns**, because raising would
put a permanent failure into a retry loop that can never succeed (§15:
*distinguish transient failures from permanent ones*).

### ⚠️ Idempotency is convergence, exactly as the producer's handler records

📁 §9 requires consumers to be idempotent on `event_id` and the platform's
ledger provides it. **This adds the second half**: a redelivery that slips past
the ledger finds a batch already applied and stops. 🔴 **The harm a second
application would do is not a duplicate row** — the primary key refuses that —
**it is overwriting the record a reversal depends on**, so the customer's undo
would then operate on the wrong set.
"""

from __future__ import annotations

from collections.abc import Callable
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from modules.commercial_profile.application.assignment_use_cases import (
    ApplyAssignmentBatch,
    ReverseAssignmentBatch,
)
from modules.commercial_profile.application.segment_use_cases import (
    ApplySegmentBatchUseCase,
    ReverseSegmentBatchUseCase,
)
from modules.commercial_profile.application.tag_use_cases import (
    ApplyTagBatchUseCase,
    ReverseTagBatchUseCase,
)
from signora_platform.db import tenant_scoped_session
from signora_platform.event_bus import EventEnvelope
from signora_platform.observability import get_logger

logger = get_logger(__name__)

APPLY_CONSUMER_NAME = "commercial_profile.apply_tag_batch"
REVERSE_CONSUMER_NAME = "commercial_profile.reverse_tag_batch"

#: ⚡ **Separate consumers from the tag pair, deliberately.** Both listen to the
#: same two events, and **one consumer handling both would make a tag batch and
#: an owner batch share an idempotency key** — a replayed event would then be
#: swallowed by whichever ran first.
ASSIGNMENT_APPLY_CONSUMER_NAME = "commercial_profile.apply_assignment_batch"
ASSIGNMENT_REVERSE_CONSUMER_NAME = "commercial_profile.reverse_assignment_batch"

#: TASK-1479 ⓶b. ⛔ **Distinct consumer names, and that is what makes three
#: capabilities share one event stream safely**: each keeps its own position,
#: so a segment batch that fails to apply does not stall tags or owners.
SEGMENT_APPLY_CONSUMER_NAME = "commercial_profile.apply_segment_batch"
SEGMENT_REVERSE_CONSUMER_NAME = "commercial_profile.reverse_segment_batch"
"""**Permanent contracts.** Renaming one resets the idempotency ledger, and
every historical application would be replayed — which here would mean
re-tagging accounts a customer has already seen the outcome of, and
overwriting the record their undo depends on."""

#: The identity rows are attributed to when the platform acts without a user.
#: **The same constant `action_batch`'s and `ai_research_engine`'s handlers
#: use**, for the same reason — and deliberately not the approver: the approver
#: authorised the batch, and the row records who *wrote* it.
SYSTEM_USER_ID = UUID("00000000-0000-0000-0000-000000000001")

ApplyFactory = Callable[[AsyncSession], ApplyTagBatchUseCase]
ReverseFactory = Callable[[AsyncSession], ReverseTagBatchUseCase]


async def apply_tag_batch(
    envelope: EventEnvelope,
    *,
    session_factory: async_sessionmaker[AsyncSession],
    apply: ApplyFactory,
) -> None:
    """Tag the accounts the batch named, because it took effect.

    ⛔ **The payload names a `batch_id` and nothing else is trusted from it.**
    The accounts are read from this module's own row — *events carry identity;
    ports carry payload* — so a replayed event cannot apply a set somebody has
    since changed.
    """
    batch_id = UUID(str(envelope.payload["batch_id"]))
    workspace_id = envelope.workspace_id

    async with tenant_scoped_session(
        session_factory, workspace_id=workspace_id, user_id=SYSTEM_USER_ID
    ) as session:
        await apply(session).execute(workspace_id, batch_id, actor_id=SYSTEM_USER_ID)

    logger.info(
        "tag batch applied",
        extra={"batch_id": str(batch_id), "workspace_id": str(workspace_id)},
    )


async def reverse_tag_batch(
    envelope: EventEnvelope,
    *,
    session_factory: async_sessionmaker[AsyncSession],
    reverse: ReverseFactory,
) -> None:
    """Untag exactly what the batch changed, because it was taken back.

    ⚠️ **The window is `action_batch`'s to enforce and is not re-checked
    here.** 📁 `has_settled` lives there and the aggregate refuses a late
    reversal, so **a second implementation of the window would be behaviour
    existing twice** (§2) — and the two would eventually disagree about whether
    a customer may still undo something.
    """
    batch_id = UUID(str(envelope.payload["batch_id"]))
    workspace_id = envelope.workspace_id

    async with tenant_scoped_session(
        session_factory, workspace_id=workspace_id, user_id=SYSTEM_USER_ID
    ) as session:
        await reverse(session).execute(workspace_id, batch_id)

    logger.info(
        "tag batch reversed",
        extra={"batch_id": str(batch_id), "workspace_id": str(workspace_id)},
    )


ApplyAssignmentFactory = Callable[[AsyncSession], ApplyAssignmentBatch]
ReverseAssignmentFactory = Callable[[AsyncSession], ReverseAssignmentBatch]


async def apply_assignment_batch(
    envelope: EventEnvelope,
    *,
    session_factory: async_sessionmaker[AsyncSession],
    apply: ApplyAssignmentFactory,
) -> None:
    """Put the member on the accounts the batch named, because it took effect.

    ⛔ **The payload names a `batch_id` and nothing else is trusted from it** —
    the accounts are read from this module's own row, exactly as the tag
    handler above does and for the same reason.
    """
    batch_id = UUID(str(envelope.payload["batch_id"]))
    workspace_id = envelope.workspace_id

    async with tenant_scoped_session(
        session_factory, workspace_id=workspace_id, user_id=SYSTEM_USER_ID
    ) as session:
        await apply(session).execute(workspace_id, batch_id, actor_id=SYSTEM_USER_ID)

    logger.info(
        "assignment batch applied",
        extra={"batch_id": str(batch_id), "workspace_id": str(workspace_id)},
    )


async def reverse_assignment_batch(
    envelope: EventEnvelope,
    *,
    session_factory: async_sessionmaker[AsyncSession],
    reverse: ReverseAssignmentFactory,
) -> None:
    """Put back exactly what the batch moved, because it was taken back.

    ⚡ **Conditional on the batch's own value still being in place** — 📁 three
    defects fixed at `935cbbd5`: an assignment made since, a second reversal,
    and an account the batch no longer held. **An undo undoes its own change,
    not everybody's.**
    """
    batch_id = UUID(str(envelope.payload["batch_id"]))
    workspace_id = envelope.workspace_id

    async with tenant_scoped_session(
        session_factory, workspace_id=workspace_id, user_id=SYSTEM_USER_ID
    ) as session:
        await reverse(session).execute(workspace_id, batch_id, actor_id=SYSTEM_USER_ID)

    logger.info(
        "assignment batch reversed",
        extra={"batch_id": str(batch_id), "workspace_id": str(workspace_id)},
    )


ApplySegmentFactory = Callable[[AsyncSession], ApplySegmentBatchUseCase]
ReverseSegmentFactory = Callable[[AsyncSession], ReverseSegmentBatchUseCase]


async def apply_segment_batch(
    envelope: EventEnvelope,
    *,
    session_factory: async_sessionmaker[AsyncSession],
    apply: ApplySegmentFactory,
) -> None:
    """Put the companies into the grouping, because the batch took effect.

    ⛔ **The payload names a `batch_id` and nothing else is trusted from it** —
    the accounts come from this module's own row, so a redelivered event cannot
    apply a selection somebody has since changed.
    """
    batch_id = UUID(str(envelope.payload["batch_id"]))
    workspace_id = envelope.workspace_id

    async with tenant_scoped_session(
        session_factory, workspace_id=workspace_id, user_id=SYSTEM_USER_ID
    ) as session:
        await apply(session).execute(workspace_id, batch_id, actor_id=SYSTEM_USER_ID)

    logger.info(
        "segment batch applied",
        extra={"batch_id": str(batch_id), "workspace_id": str(workspace_id)},
    )


async def reverse_segment_batch(
    envelope: EventEnvelope,
    *,
    session_factory: async_sessionmaker[AsyncSession],
    reverse: ReverseSegmentFactory,
) -> None:
    """Take the companies back out, because the batch was taken back.

    ⛔ **Removes what the batch ADDED, never what it requested.** A company
    curated into the grouping before the batch stays in it — it was not this
    batch's doing.
    """
    batch_id = UUID(str(envelope.payload["batch_id"]))
    workspace_id = envelope.workspace_id

    async with tenant_scoped_session(
        session_factory, workspace_id=workspace_id, user_id=SYSTEM_USER_ID
    ) as session:
        await reverse(session).execute(workspace_id, batch_id)

    logger.info(
        "segment batch reversed",
        extra={"batch_id": str(batch_id), "workspace_id": str(workspace_id)},
    )
