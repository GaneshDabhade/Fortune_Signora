"""What somebody is allowed to do, changed.

**Organizational authority rather than a field.** Promoting a colleague hands
them the ability to invite, remove and administer; demoting one takes it away
while they may be mid-task. Both are recorded, because a role that changes
without a trace makes *"who made Ravi an owner?"* unanswerable by anything.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from modules.workspace_tenancy.application.ports import MembershipRepository, RoleChangeLog
from modules.workspace_tenancy.application.use_cases.remove_member import (
    MembershipNotFoundError,
)
from modules.workspace_tenancy.domain.entities import Membership, WorkspaceRole


@dataclass(frozen=True, slots=True)
class ChangeRoleCommand:
    workspace_id: UUID
    membership_id: UUID
    new_role: WorkspaceRole
    changed_by: UUID


class ChangeRole:
    def __init__(self, *, memberships: MembershipRepository, history: RoleChangeLog) -> None:
        self._memberships = memberships
        self._history = history

    async def execute(self, command: ChangeRoleCommand, *, now: datetime) -> Membership:
        # Same lock as removal, and for the same reason: demoting the last owner
        # and removing them are one failure reached two ways, and neither check
        # is atomic across transactions without it.
        await self._memberships.lock_membership_set(command.workspace_id)

        membership = await self._memberships.get_by_id(command.workspace_id, command.membership_id)
        if membership is None:
            raise MembershipNotFoundError(command.membership_id)

        live_owners = await self._memberships.count_live_owners(command.workspace_id)
        remaining = live_owners - 1 if membership.role is WorkspaceRole.OWNER else live_owners

        previous = membership.change_role(
            to=command.new_role,
            by=command.changed_by,
            at=now,
            remaining_owners=remaining,
        )
        await self._memberships.save_role(membership)
        # **After the change, in the same transaction.** A history row written
        # before the change could describe one that was then refused.
        await self._history.record(
            workspace_id=command.workspace_id,
            membership_id=membership.id,
            previous_role=previous,
            new_role=command.new_role,
            changed_by=command.changed_by,
            at=now,
        )
        return membership


__all__ = ["ChangeRole", "ChangeRoleCommand"]
