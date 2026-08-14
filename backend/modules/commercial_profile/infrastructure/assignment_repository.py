"""Reading and writing who holds an account — migration `0053`.

**The `AccountAssignmentRepository` port, over Postgres.**
[TASK-1479](../../../../docs/BACKLOG.md) slice ⓶, against **ADR-0411**.

### ⚡ Every write returns what it changed

⛔ **Not what it was asked to change.** 📁 **ADR-0405**
puts the inverse with the domain that performed the operation, and the inverse
of a bulk reassignment is *"restore what each account had"* — **which is
knowable only at the moment of writing.** A caller that read the state
separately would be reading it before or after the write, and both are wrong.
"""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import delete, select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from modules.commercial_profile.domain.account_assignment import (
    AccountAssignment,
    AccountRole,
    AssignmentBatch,
    Reassignment,
)
from modules.commercial_profile.infrastructure.models import (
    AccountAssignmentBatchModel,
    AccountAssignmentModel,
)


class SqlAccountAssignmentRepository:
    """The `AccountAssignmentRepository` port, over Postgres."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def for_accounts(
        self, workspace_id: UUID, account_ids: tuple[UUID, ...]
    ) -> tuple[AccountAssignment, ...]:
        """Every assignment on a page of accounts, **in one query.**

        ⚡ **Takes the ids the caller already has.** A read that fetched every
        assignment in the workspace and filtered in Python would be the
        unbounded fetch §14 calls a defect at write time — and the Companies
        table asks this for exactly the rows it is rendering.
        """
        if not account_ids:
            # ⛔ **Not a query with an empty `IN`.** Postgres answers it
            # correctly and it is still a round trip that can only return
            # nothing.
            return ()

        rows = (
            await self._session.execute(
                select(AccountAssignmentModel).where(
                    AccountAssignmentModel.workspace_id == workspace_id,
                    AccountAssignmentModel.account_id.in_(account_ids),
                )
            )
        ).scalars()
        return tuple(
            AccountAssignment(
                workspace_id=row.workspace_id,
                account_id=row.account_id,
                role=AccountRole(row.role),
                member_user_id=row.member_user_id,
            )
            for row in rows
        )

    async def assign(
        self,
        workspace_id: UUID,
        account_ids: tuple[UUID, ...],
        *,
        role: AccountRole,
        member_user_id: UUID,
        actor_id: UUID,
    ) -> Reassignment:
        """Put one member on these accounts, **and report what moved.**

        ⚠️ **The prior holders are read inside the same unit of work as the
        write.** Reading them in the caller would leave a window where another
        request reassigns an account between the read and the write, and the
        reversal would then restore an owner that was already stale — 📁 the
        hidden-input shape §2 names, arriving as a race rather than as a
        parameter.
        """
        held = {
            row.account_id: row.member_user_id
            for row in (
                await self._session.execute(
                    select(AccountAssignmentModel).where(
                        AccountAssignmentModel.workspace_id == workspace_id,
                        AccountAssignmentModel.account_id.in_(account_ids),
                        AccountAssignmentModel.role == role.value,
                    )
                )
            ).scalars()
        }

        moved = tuple(
            (account_id, held.get(account_id))
            for account_id in account_ids
            if held.get(account_id) != member_user_id
        )
        unchanged = tuple(
            account_id for account_id in account_ids if held.get(account_id) == member_user_id
        )
        if not moved:
            return Reassignment(
                role=role, assigned_to=member_user_id, unchanged=unchanged
            )

        # **Upsert on the natural key.** ⛔ The alternative — delete then insert
        # — would make a reassignment two statements, and a failure between
        # them would leave the account held by nobody. **An account momentarily
        # unowned is a state the customer never asked for.**
        await self._session.execute(
            insert(AccountAssignmentModel)
            .values(
                [
                    {
                        "workspace_id": workspace_id,
                        "account_id": account_id,
                        "role": role.value,
                        "member_user_id": member_user_id,
                        "created_by": actor_id,
                        "updated_by": actor_id,
                    }
                    for account_id, _ in moved
                ]
            )
            .on_conflict_do_update(
                index_elements=["workspace_id", "account_id", "role"],
                set_={"member_user_id": member_user_id, "updated_by": actor_id},
            )
        )
        await self._session.flush()
        return Reassignment(
            role=role, assigned_to=member_user_id, previous=moved, unchanged=unchanged
        )

    async def restore(
        self,
        workspace_id: UUID,
        previous: tuple[tuple[UUID, UUID | None], ...],
        *,
        role: AccountRole,
        assigned_to: UUID | None,
        actor_id: UUID,
    ) -> None:
        """Put back exactly what `assign` found — **and only where it still holds.**

        🔴 **The `None` case is one half.** An account that had no owner before
        must end with no owner; **writing nothing for it would leave the new
        owner in place**, so the reversal would report success while half of it
        did not happen.

        🔴 **`assigned_to` is the other half, and it was missing.** Every write
        here is conditional on the batch's own value still being in place —
        📁 **three failing tests, from QE's hypotheses**, showed an
        unconditional restore doing three wrong things:

        * **overwriting an assignment made since** — the batch set an owner, a
          colleague chose a different one, and *take it back* silently
          discarded their decision. **A lost update wearing an undo's clothes.**
        * **re-asserting a stale holder on a second reversal** — an undo
          pressed twice is still one undo.
        * **clearing an account the batch no longer held** — it was never the
          batch's to empty once it had moved on.

        ⚡ **So this is a compare-and-set, and the comparison is the whole
        difference between *undo my change* and *make the world look like it
        used to*.**
        """
        if assigned_to is None:
            # ⛔ **Nothing was assigned, so there is nothing to condition on.**
            # A reversal with no `assigned_to` cannot tell its own change from
            # anybody else's, and guessing would be the destructive write this
            # method exists to avoid.
            return

        cleared = tuple(account for account, holder in previous if holder is None)
        if cleared:
            await self._session.execute(
                delete(AccountAssignmentModel).where(
                    AccountAssignmentModel.workspace_id == workspace_id,
                    AccountAssignmentModel.account_id.in_(cleared),
                    AccountAssignmentModel.role == role.value,
                    # **The condition.** Somebody else's choice is not ours to
                    # clear.
                    AccountAssignmentModel.member_user_id == assigned_to,
                )
            )

        for account_id, holder in previous:
            if holder is None:
                continue
            await self._session.execute(
                update(AccountAssignmentModel)
                .where(
                    AccountAssignmentModel.workspace_id == workspace_id,
                    AccountAssignmentModel.account_id == account_id,
                    AccountAssignmentModel.role == role.value,
                    AccountAssignmentModel.member_user_id == assigned_to,
                )
                .values(member_user_id=holder, updated_by=actor_id)
            )
        await self._session.flush()


class SqlAssignmentBatchStore:
    """This module's own half of a proposed owner change — migration `0054`.

    ⛔ **The accounts are read from here and never from the event.** *Events
    carry identity; ports carry payload* — so a replayed `applied` cannot act
    on a selection somebody has since changed.
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def record(
        self, workspace_id: UUID, batch: AssignmentBatch, *, actor_id: UUID
    ) -> None:
        self._session.add(
            AccountAssignmentBatchModel(
                batch_id=batch.batch_id,
                workspace_id=workspace_id,
                role=batch.role.value,
                member_user_id=batch.member_user_id,
                requested=[str(account) for account in batch.requested],
                # ⛔ **`None`, not `[]`.** The batch has not applied, and those
                # are different answers.
                moved=None,
                created_by=actor_id,
                updated_by=actor_id,
            )
        )
        await self._session.flush()

    async def by_id(self, workspace_id: UUID, batch_id: UUID) -> AssignmentBatch | None:
        row = (
            await self._session.execute(
                select(AccountAssignmentBatchModel).where(
                    AccountAssignmentBatchModel.workspace_id == workspace_id,
                    AccountAssignmentBatchModel.batch_id == batch_id,
                )
            )
        ).scalar_one_or_none()
        if row is None:
            # **A batch this module did not propose is not an error.** Another
            # domain's batch is simply not ours, and the handler does nothing.
            return None

        moved: Reassignment | None = None
        if row.moved is not None:
            moved = Reassignment(
                role=AccountRole(row.role),
                assigned_to=row.member_user_id,
                previous=tuple(
                    (UUID(account), UUID(prior) if prior is not None else None)
                    for account, prior in row.moved
                ),
            )
        return AssignmentBatch(
            batch_id=row.batch_id,
            role=AccountRole(row.role),
            member_user_id=row.member_user_id,
            requested=tuple(UUID(account) for account in row.requested),
            moved=moved,
        )

    async def record_applied(
        self, workspace_id: UUID, batch_id: UUID, moved: Reassignment, *, actor_id: UUID
    ) -> None:
        """Write what the batch actually moved.

        ⚡ **The one `UPDATE` this table takes**, and it is a transition rather
        than an edit: `NULL` becomes a list exactly once.
        """
        await self._session.execute(
            update(AccountAssignmentBatchModel)
            .where(
                AccountAssignmentBatchModel.workspace_id == workspace_id,
                AccountAssignmentBatchModel.batch_id == batch_id,
            )
            .values(
                moved=[
                    [str(account), str(prior) if prior is not None else None]
                    for account, prior in moved.previous
                ],
                updated_by=actor_id,
            )
        )
        await self._session.flush()


__all__ = ["SqlAccountAssignmentRepository", "SqlAssignmentBatchStore"]
