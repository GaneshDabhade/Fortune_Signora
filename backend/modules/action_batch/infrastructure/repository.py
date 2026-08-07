"""The SQL implementation of `ActionBatchRepository`.

**The store is append-only and the aggregate is rebuilt by replaying it.**
Nothing here reconstructs an `ActionBatch` by setting its fields: reconstruction
goes through the same `approved_by` / `applied_on` / `reversed_by` the rest of
the platform calls, so **the domain's guards run on load**. A log that could not
have been produced legally surfaces as an `ActionBatchError` naming the batch,
rather than as an aggregate that is quietly wrong.

⚡ **Replay is deterministic because no domain method reads a clock** — `now` is
always an argument (§2, *hidden inputs are architecture defects*). Replaying a
reversal with the moment it was recorded at gives the answer it gave then,
however long ago that was.
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from modules.action_batch.domain.batch import (
    ActionBatch,
    ActionBatchError,
    Decision,
    Transition,
)
from modules.action_batch.infrastructure.models import (
    ActionBatchModel,
    ActionBatchTransitionModel,
)


def _history(batch: ActionBatch) -> tuple[tuple[Transition, UUID | None, datetime], ...]:
    """What has happened to this batch, in order.

    **Derived from the aggregate rather than tracked beside it**, which is what
    makes `record` idempotent: the same aggregate always yields the same length,
    so re-recording it collides with `uq_action_batch_transition_sequence`
    instead of appending a second copy of the same fact.

    ⛔ **The proposal is deliberately absent.** It is how a batch begins, not
    something that happened to it, and it lives on the batch row.
    """
    events: list[tuple[Transition, UUID | None, datetime]] = []
    if batch.decided is not None:
        # ⚠️ **Which decision it was is *not* simply the current state**, and
        # assuming so was a real defect this slice's round-trip tests caught: a
        # reversal overwrites `state` with `REVERSED`, so a reversed batch
        # would have recorded its approval as a reversal.
        #
        # **It is still derivable, so nothing is stored to say it** (§2). Only
        # an `APPROVED` batch can be applied and only an applied one can be
        # reversed, so `applied_at` being set entails the decision was an
        # approval. Everything else never applied, and its state is its
        # decision.
        decision = (
            Transition.APPROVED if batch.applied_at is not None else Transition(batch.state.value)
        )
        events.append((decision, batch.decided.actor_id, batch.decided.at))
    if batch.applied_at is not None:
        events.append((Transition.APPLIED, None, batch.applied_at))
    if batch.reversal is not None:
        events.append((Transition.REVERSED, batch.reversal.actor_id, batch.reversal.at))
    return tuple(events)


def _replay(row: ActionBatchModel, transitions: list[ActionBatchTransitionModel]) -> ActionBatch:
    """Rebuild an aggregate from its opening row and its log."""
    batch = ActionBatch(
        id=row.id,
        workspace_id=row.workspace_id,
        name=row.name,
        item_count=row.item_count,
        proposed=Decision(actor_id=row.proposed_by, at=row.proposed_at),
        reversible_for=row.reversible_for,
    )
    for entry in transitions:
        transition = Transition(entry.transition)
        if transition is Transition.APPLIED:
            batch = batch.applied_on(entry.occurred_at)
            continue
        actor_id = entry.actor_id
        if actor_id is None:
            # The table's CHECK permits `NULL` only for `applied`, so reaching
            # here means the stored row no longer satisfies the constraint it
            # was written under. **Loud and specific** (§15) — an aggregate
            # rebuilt around a missing actor would be an approval attributed to
            # nobody, which is exactly what this context exists to prevent.
            raise ActionBatchError(
                f"transition {entry.sequence} of batch {row.id} is {transition.value} "
                "and names no actor. Only an application is unattributed, so this row "
                "cannot be replayed without inventing who decided it."
            )
        if transition is Transition.REVERSED:
            batch = batch.reversed_by(actor_id, at=entry.occurred_at)
        elif transition is Transition.APPROVED:
            batch = batch.approved_by(actor_id, at=entry.occurred_at)
        elif transition is Transition.REJECTED:
            batch = batch.rejected_by(actor_id, at=entry.occurred_at)
        else:
            batch = batch.withdrawn_by(actor_id, at=entry.occurred_at)
    return batch


class SqlActionBatchRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, batch: ActionBatch, *, actor_id: UUID) -> None:
        self._session.add(
            ActionBatchModel(
                id=batch.id,
                workspace_id=batch.workspace_id,
                name=batch.name,
                item_count=batch.item_count,
                proposed_by=batch.proposed.actor_id,
                proposed_at=batch.proposed.at,
                reversible_for=batch.reversible_for,
                created_by=actor_id,
                updated_by=actor_id,
            )
        )
        await self._session.flush()

    async def record(self, batch: ActionBatch, *, actor_id: UUID) -> None:
        """Append the transition this aggregate most recently underwent.

        **Its position comes from the aggregate's own history**, never from a
        count of what is already stored — a `max(sequence) + 1` would happily
        write the same fact twice under two different numbers.
        """
        history = _history(batch)
        if not history:
            raise ActionBatchError(
                f"batch {batch.id} is still proposed and has no transition to record. "
                "A proposal is how a batch begins rather than something that happened "
                "to it, and `add` is what writes it."
            )
        transition, transition_actor, occurred_at = history[-1]
        self._session.add(
            ActionBatchTransitionModel(
                id=uuid4(),
                workspace_id=batch.workspace_id,
                batch_id=batch.id,
                sequence=len(history) - 1,
                transition=transition.value,
                actor_id=transition_actor,
                occurred_at=occurred_at,
                created_by=actor_id,
                updated_by=actor_id,
            )
        )
        await self._session.flush()

    async def get(self, workspace_id: UUID, batch_id: UUID) -> ActionBatch | None:
        rows = await self._session.execute(
            select(ActionBatchModel).where(
                # **Both, always.** RLS is the authoritative control and the
                # explicit predicate is defence in depth (§8).
                ActionBatchModel.workspace_id == workspace_id,
                ActionBatchModel.id == batch_id,
            )
        )
        row = rows.scalars().one_or_none()
        if row is None:
            return None

        log = await self._session.execute(
            select(ActionBatchTransitionModel)
            .where(
                ActionBatchTransitionModel.workspace_id == workspace_id,
                ActionBatchTransitionModel.batch_id == batch_id,
            )
            .order_by(ActionBatchTransitionModel.sequence)
        )
        return _replay(row, list(log.scalars()))
