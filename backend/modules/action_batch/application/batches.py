"""Proposing, deciding, applying and reversing a batch.

**The orchestration, and nothing else.** Every rule about which transition is
legal lives in `domain/batch.py` and every rule about what may be written lives
in the schema — this layer loads, calls one domain method, records the result,
and publishes when the result is something outside this module should react to.

⛔ **There is no stored `state` column and this layer must never add one.**
📁 [TASK-464](../../../../docs/BACKLOG.md) names it as the row's risk, and the
persistence slice already paid for it once: **a reversal overwrote `state`, so
reading the decision off it recorded an approval AS a reversal.** The state is
derived by replaying the log through the domain's own methods, **so its guards
run on load** — a batch that could not legally exist cannot be read back.

⚠️ **Two events, not six.** Only `applied` and `reversed` change anything
outside this module; approving is permission for work that has not happened yet.
See `domain/events.py`.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from modules.action_batch.application.ports import ActionBatchRepository
from modules.action_batch.domain.batch import ActionBatch, ActionBatchError, Decision
from modules.action_batch.domain.events import ActionBatchApplied, ActionBatchReversed
from signora_platform.event_bus import EventPublisher
from signora_platform.observability import get_logger

logger = get_logger(__name__)

PRODUCER_MODULE = "action_batch"


class ActionBatchNotFound(LookupError):
    """No such batch **in this workspace**.

    ⛔ **Not `Forbidden`.** A batch in another workspace is not found rather
    than refused — the same rule §7 applies everywhere, because *forbidden*
    confirms the id exists.
    """


@dataclass(frozen=True, slots=True)
class ProposeBatch:
    workspace_id: UUID
    name: str
    item_count: int
    proposed_by: UUID
    #: How long reversal stays possible **after it applies**. `None` says
    #: reversal is not offered for this batch — ⛔ a different answer from a
    #: window that has closed, and the customer is told them differently.
    reversible_for: timedelta | None = None


class ActionBatches:
    """The Action Batch's four use cases."""

    def __init__(
        self,
        repository: ActionBatchRepository,
        publisher: EventPublisher,
        session: AsyncSession,
    ) -> None:
        self._repository = repository
        self._publisher = publisher
        self._session = session

    async def propose(self, request: ProposeBatch, *, now: datetime | None = None) -> ActionBatch:
        """Assemble a batch somebody can be asked to approve.

        ⛔ **Publishes nothing.** A proposal is a question, and no domain
        outside this one acts on a question.
        """
        moment = now or datetime.now(UTC)
        batch = ActionBatch(
            id=uuid4(),
            workspace_id=request.workspace_id,
            name=request.name,
            item_count=request.item_count,
            proposed=Decision(actor_id=request.proposed_by, at=moment),
            reversible_for=request.reversible_for,
        )
        await self._repository.add(batch, actor_id=request.proposed_by)
        logger.info(
            "action batch proposed",
            extra={"batch_id": str(batch.id), "item_count": batch.item_count},
        )
        return batch

    async def approve(
        self, workspace_id: UUID, batch_id: UUID, *, actor_id: UUID, now: datetime | None = None
    ) -> ActionBatch:
        """Somebody decided it should happen. ⛔ **Not that it has.**"""
        return await self._decide(workspace_id, batch_id, actor_id, "approved_by", now)

    async def reject(
        self, workspace_id: UUID, batch_id: UUID, *, actor_id: UUID, now: datetime | None = None
    ) -> ActionBatch:
        """A reviewer decided it should not."""
        return await self._decide(workspace_id, batch_id, actor_id, "rejected_by", now)

    async def withdraw(
        self, workspace_id: UUID, batch_id: UUID, *, actor_id: UUID, now: datetime | None = None
    ) -> ActionBatch:
        """The proposer took it back **before anybody decided**."""
        return await self._decide(workspace_id, batch_id, actor_id, "withdrawn_by", now)

    async def apply(
        self, workspace_id: UUID, batch_id: UUID, *, now: datetime | None = None
    ) -> ActionBatch:
        """Record that it took effect, and tell everybody.

        ⛔ **This records; it does not perform.** The consuming domain does the
        work on the authority of the approval already stored — which is why
        `applied_on` takes no `actor_id`, and why inventing one here would
        attribute the change to whoever happened to flush it.
        """
        batch = await self._load(workspace_id, batch_id)
        moment = now or datetime.now(UTC)
        applied = batch.applied_on(moment)
        await self._repository.record(applied, actor_id=applied.proposed.actor_id)

        # ⚠️ **`decided` is not None here by construction** — `applied_on`
        # refuses anything that is not `APPROVED`, and a batch reaches
        # `APPROVED` only through `_decide`, which records the decision. ⛔ The
        # assertion is for the type-checker and for the reader; it is not a
        # runtime guard standing in for the domain's.
        approver = applied.decided
        if approver is None:  # pragma: no cover — unreachable via the domain
            raise ActionBatchError(
                "an applied batch with no recorded decision is a history that cannot be "
                "cited. The domain refuses this; reaching it means the log was written "
                "by something other than these use cases."
            )

        await self._publish(
            ActionBatchApplied(
                event_id=uuid4(),
                workspace_id=applied.workspace_id,
                occurred_at=moment,
                batch_id=applied.id,
                name=applied.name,
                item_count=applied.item_count,
                approved_by=approver.actor_id,
                # ⛔ **`None` when reversal was never offered** — the domain
                # keeps that distinct from a closed window, and so does this.
                reversible_until=(
                    moment + applied.reversible_for if applied.reversible_for else None
                ),
            )
        )
        logger.info("action batch applied", extra={"batch_id": str(applied.id)})
        return applied

    async def reverse(
        self, workspace_id: UUID, batch_id: UUID, *, actor_id: UUID, now: datetime | None = None
    ) -> ActionBatch:
        """Take it back, **inside the window the customer was shown**.

        ⚡ The window is enforced by the domain's `reversed_by`, which is what
        makes `has_settled` load-bearing rather than descriptive.
        """
        batch = await self._load(workspace_id, batch_id)
        moment = now or datetime.now(UTC)
        undone = batch.reversed_by(actor_id, at=moment)
        await self._repository.record(undone, actor_id=actor_id)

        applied_at = undone.applied_at
        if applied_at is None:  # pragma: no cover — `reversed_by` refuses it
            raise ActionBatchError("a reversed batch that never applied is not representable")

        await self._publish(
            ActionBatchReversed(
                event_id=uuid4(),
                workspace_id=undone.workspace_id,
                occurred_at=moment,
                batch_id=undone.id,
                # ⚠️ **Stated, not inferred from ordering** — a subscriber may
                # see the two events out of order, and the reversal has to say
                # which application it undoes.
                applied_at=applied_at,
                reversed_by=actor_id,
            )
        )
        logger.info("action batch reversed", extra={"batch_id": str(undone.id)})
        return undone

    async def _decide(
        self,
        workspace_id: UUID,
        batch_id: UUID,
        actor_id: UUID,
        method: str,
        now: datetime | None,
    ) -> ActionBatch:
        """The three decisions differ in one domain call and nothing else.

        ⛔ **None of them publishes.** Approval is permission for work that has
        not happened; rejection and withdrawal are the absence of work. A
        subscriber acting on any of them would act before anything took effect.
        """
        batch = await self._load(workspace_id, batch_id)
        moment = now or datetime.now(UTC)
        decided: ActionBatch = getattr(batch, method)(actor_id, at=moment)
        await self._repository.record(decided, actor_id=actor_id)
        logger.info(
            "action batch decided",
            extra={"batch_id": str(decided.id), "state": decided.state.value},
        )
        return decided

    async def _load(self, workspace_id: UUID, batch_id: UUID) -> ActionBatch:
        batch = await self._repository.get(workspace_id, batch_id)
        if batch is None:
            raise ActionBatchNotFound(
                f"no action batch {batch_id} in this workspace. A batch belonging to "
                "another workspace is not found rather than forbidden."
            )
        return batch

    async def _publish(self, event: ActionBatchApplied | ActionBatchReversed) -> None:
        # The platform's `PublishableEvent` Protocol declares settable members,
        # which frozen domain events cannot satisfy — the same finding
        # `signal_engine` and `provider_normalization` both carry, raised
        # rather than worked around.
        await self._publisher.publish(
            [event],  # type: ignore[list-item]
            session=self._session,
            producer_module=PRODUCER_MODULE,
            correlation_id=event.event_id,
        )
