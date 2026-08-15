"""Reading and writing capability roles — [TASK-1479](../../../../docs/BACKLOG.md) ⓸.

⛔ **No method returns a role's CONTENTS**, and there is nowhere for them to
come from. 📁 [ADR-0410](../../../../docs/architecture/adr/0410-authorization-capability-layer.md)
§2: *"Do not create a second independent authorization model."* **The grants
are `policy.csv` rows keyed on `role_key`**, read by Casbin and by nothing
here.

### ⚠️ `workspace_id` is in every predicate, and RLS is still the authority

📁 [§8](../../../../CLAUDE.md): *"even with RLS in place, queries must still
explicitly filter by `workspace_id` as defense-in-depth."*
"""

from __future__ import annotations

from typing import Any, cast
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.engine import CursorResult
from sqlalchemy.ext.asyncio import AsyncSession

from modules.workspace_tenancy.domain.capability import (
    CapabilityAssignment,
    CapabilityRole,
)
from modules.workspace_tenancy.infrastructure.models import (
    CapabilityAssignmentModel,
    CapabilityRoleModel,
)


class SqlCapabilityRepository:
    """The capability layer's storage, over Postgres."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def roles(self, workspace_id: UUID) -> tuple[CapabilityRole, ...]:
        """Every capability role the workspace has defined, ordered by name.

        ⚡ **Ordered in SQL rather than by the caller** — the design renders
        these as a list a person scans in Settings, and *"whatever order the
        rows came back in"* is a hidden input (§2).
        """
        rows = (
            await self._session.execute(
                select(CapabilityRoleModel)
                .where(CapabilityRoleModel.workspace_id == workspace_id)
                .order_by(CapabilityRoleModel.name)
            )
        ).scalars()
        return tuple(CapabilityRole(id=row.role_id, name=row.name) for row in rows)

    async def role(self, workspace_id: UUID, role_id: UUID) -> CapabilityRole | None:
        row = (
            await self._session.execute(
                select(CapabilityRoleModel).where(
                    CapabilityRoleModel.workspace_id == workspace_id,
                    CapabilityRoleModel.role_id == role_id,
                )
            )
        ).scalar_one_or_none()
        return None if row is None else CapabilityRole(id=row.role_id, name=row.name)

    async def create_role(
        self, workspace_id: UUID, role: CapabilityRole, *, actor_id: UUID
    ) -> None:
        self._session.add(
            CapabilityRoleModel(
                role_id=role.id,
                workspace_id=workspace_id,
                name=role.name,
                # ⚡ **Written from the domain's own property**, so the column
                # and the rule cannot disagree about what the subject is.
                role_key=role.key,
                created_by=actor_id,
                updated_by=actor_id,
            )
        )
        await self._session.flush()

    async def rename_role(
        self, workspace_id: UUID, role: CapabilityRole, *, actor_id: UUID
    ) -> None:
        """Correct a role's name.

        🔴 **This moves `role_key`, which is what `policy.csv` holds** — so a
        rename is a policy edit as well as a row update. ⛔ **A renamed role
        whose grants were not moved denies everything, silently, for everyone
        holding it**, which is why the domain type says so and this method
        repeats it rather than assuming somebody read that one.
        """
        row = (
            await self._session.execute(
                select(CapabilityRoleModel).where(
                    CapabilityRoleModel.workspace_id == workspace_id,
                    CapabilityRoleModel.role_id == role.id,
                )
            )
        ).scalar_one()
        row.name = role.name
        row.role_key = role.key
        row.updated_by = actor_id
        await self._session.flush()

    async def assignment(
        self, workspace_id: UUID, user_id: UUID
    ) -> CapabilityAssignment | None:
        """The capability role one person holds, or `None` if no row exists.

        ⛔ **`None` and `CapabilityAssignment(role_id=None)` are the same
        answer to the caller** — nobody has assigned anything — **and the
        distinction is only whether somebody once did and changed it back.**
        `subject_for` treats them identically, which is why neither is a
        special case anywhere above this line.
        """
        row = (
            await self._session.execute(
                select(CapabilityAssignmentModel).where(
                    CapabilityAssignmentModel.workspace_id == workspace_id,
                    CapabilityAssignmentModel.user_id == user_id,
                )
            )
        ).scalar_one_or_none()
        return (
            None
            if row is None
            else CapabilityAssignment(user_id=row.user_id, role_id=row.role_id)
        )

    async def assign(
        self,
        workspace_id: UUID,
        user_id: UUID,
        role_id: UUID | None,
        *,
        actor_id: UUID,
    ) -> None:
        """Put a person on a capability role, or take them off one.

        ⚡ **One row per person, updated in place**, because *"Change to
        Analyst"* and *"change back"* are the same act with different values —
        📁 and `(workspace_id, user_id)` being the primary key is what makes a
        second assignment unrepresentable rather than merely refused.
        """
        result = await self._session.execute(
            update(CapabilityAssignmentModel)
            .where(
                CapabilityAssignmentModel.workspace_id == workspace_id,
                CapabilityAssignmentModel.user_id == user_id,
            )
            .values(role_id=role_id, updated_by=actor_id)
        )
        # `CursorResult` is what an UPDATE returns; `execute`'s annotation is
        # the wider `Result`, which has no `rowcount`.
        if cast("CursorResult[Any]", result).rowcount == 0:
            self._session.add(
                CapabilityAssignmentModel(
                    workspace_id=workspace_id,
                    user_id=user_id,
                    role_id=role_id,
                    created_by=actor_id,
                    updated_by=actor_id,
                )
            )
        await self._session.flush()

    async def held_roles(self, workspace_id: UUID) -> dict[UUID, CapabilityRole]:
        """Who holds which role, for everybody who holds one.

        🔴 **One query for the whole roster**, and that is the point. ⛔ A
        screen showing a role chip per person would otherwise ask once per row
        — 📁 [§14](../../../../CLAUDE.md): *obvious inefficiency is a defect at
        write time.*

        ⛔ **Somebody who holds no role is ABSENT rather than mapped to
        `None`.** ⚡ The caller asked about one workspace and gets everybody in
        it who has one — **a key with a null value would be a third way of
        saying what two already say** (`assignment` above).
        """
        rows = await self._session.execute(
            select(CapabilityAssignmentModel.user_id, CapabilityRoleModel)
            .join(
                CapabilityRoleModel,
                CapabilityRoleModel.role_id == CapabilityAssignmentModel.role_id,
            )
            .where(
                CapabilityAssignmentModel.workspace_id == workspace_id,
                # ⚡ **The join already drops a `NULL` `role_id`** — *changed
                # back* — and this states it rather than relying on the reader
                # knowing that an inner join does.
                CapabilityAssignmentModel.role_id.is_not(None),
            )
        )
        return {
            user_id: CapabilityRole(id=role.role_id, name=role.name)
            for user_id, role in rows.all()
        }

    async def holders(self, workspace_id: UUID, role_id: UUID) -> int:
        """How many people hold this role.

        ⚡ **Derived on read**, and it is what a *"delete this role"* control
        has to ask before offering itself: migration `0057`'s `ON DELETE
        RESTRICT` will refuse, and **a screen that lets somebody press a button
        the database will reject is a control that goes nowhere.**
        """
        rows = (
            await self._session.execute(
                select(CapabilityAssignmentModel.user_id).where(
                    CapabilityAssignmentModel.workspace_id == workspace_id,
                    CapabilityAssignmentModel.role_id == role_id,
                )
            )
        ).scalars()
        return len(list(rows))


__all__ = ["SqlCapabilityRepository"]
