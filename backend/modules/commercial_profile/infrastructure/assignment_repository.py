"""Reading and writing who holds an account — migration `0053`.

**The `AccountAssignmentRepository` port, over Postgres.** [TASK-1479](../../../../docs/BACKLOG.md)
slice ⓶, against [ADR-0411](../../../../docs/architecture/adr/0411-customer-organized-account-metadata.md).

### ⚡ Every write returns what it changed

⛔ **Not what it was asked to change.** 📁 [ADR-0405](../../../../docs/architecture/adr/0405-an-action-is-approved-before-it-is-effective.md)
puts the inverse with the domain that performed the operation, and the inverse
of a bulk reassignment is *"restore what each account had"* — **which is
knowable only at the moment of writing.** A caller that read the state
separately would be reading it before or after the write, and both are wrong.
"""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from modules.commercial_profile.domain.account_assignment import (
    AccountAssignment,
    AccountRole,
    Reassignment,
)
from modules.commercial_profile.infrastructure.models import AccountAssignmentModel


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
            return Reassignment(role=role, unchanged=unchanged)

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
        return Reassignment(role=role, previous=moved, unchanged=unchanged)

    async def restore(
        self,
        workspace_id: UUID,
        previous: tuple[tuple[UUID, UUID | None], ...],
        *,
        role: AccountRole,
        actor_id: UUID,
    ) -> None:
        """Put back exactly what `assign` found, **including the absences.**

        🔴 **The `None` case is the half that is normally missed.** An account
        that had no owner before must end with no owner — **writing nothing for
        it would leave the new owner in place**, so the reversal would silently
        succeed while half of it did not happen.
        """
        cleared = tuple(account for account, holder in previous if holder is None)
        if cleared:
            await self._session.execute(
                delete(AccountAssignmentModel).where(
                    AccountAssignmentModel.workspace_id == workspace_id,
                    AccountAssignmentModel.account_id.in_(cleared),
                    AccountAssignmentModel.role == role.value,
                )
            )

        restored = [(account, holder) for account, holder in previous if holder is not None]
        if restored:
            await self._session.execute(
                insert(AccountAssignmentModel)
                .values(
                    [
                        {
                            "workspace_id": workspace_id,
                            "account_id": account_id,
                            "role": role.value,
                            "member_user_id": holder,
                            "created_by": actor_id,
                            "updated_by": actor_id,
                        }
                        for account_id, holder in restored
                    ]
                )
                .on_conflict_do_update(
                    index_elements=["workspace_id", "account_id", "role"],
                    set_={
                        "member_user_id": insert(AccountAssignmentModel).excluded.member_user_id,
                        "updated_by": actor_id,
                    },
                )
            )
        await self._session.flush()


__all__ = ["SqlAccountAssignmentRepository"]
