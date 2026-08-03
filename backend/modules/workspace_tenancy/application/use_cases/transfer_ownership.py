"""Handing an organization over.

**One business operation, and that is the whole reason it exists.** Promote
then demote works, and leaves a window in which the organization has two
owners nobody asked for — a state that becomes permanent if the second step
never runs.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from modules.workspace_tenancy.application.ports import MembershipRepository, RoleChangeLog
from modules.workspace_tenancy.application.use_cases.remove_member import (
    MembershipNotFoundError,
)
from modules.workspace_tenancy.domain.entities import (
    Membership,
    WorkspaceRole,
    transfer_ownership,
)


@dataclass(frozen=True, slots=True)
class TransferOwnershipCommand:
    workspace_id: UUID
    #: The membership handing over. **Named explicitly rather than inferred
    #: from the caller**: an owner may transfer on behalf of another owner who
    #: has left the company, and inferring it would make that impossible.
    from_membership_id: UUID
    to_membership_id: UUID
    performed_by: UUID


class TransferOwnership:
    def __init__(self, *, memberships: MembershipRepository, history: RoleChangeLog) -> None:
        self._memberships = memberships
        self._history = history

    async def execute(
        self, command: TransferOwnershipCommand, *, now: datetime
    ) -> tuple[Membership, Membership]:
        # The same lock every membership-shape change takes. It is what stops a
        # concurrent demotion or removal observing — or racing — the moment
        # between the two role changes.
        await self._memberships.lock_membership_set(command.workspace_id)

        outgoing = await self._memberships.get_by_id(
            command.workspace_id, command.from_membership_id
        )
        if outgoing is None:
            raise MembershipNotFoundError(command.from_membership_id)
        incoming = await self._memberships.get_by_id(command.workspace_id, command.to_membership_id)
        if incoming is None:
            raise MembershipNotFoundError(command.to_membership_id)

        previous_incoming = incoming.role
        transfer_ownership(outgoing=outgoing, incoming=incoming, by=command.performed_by, at=now)

        await self._memberships.save_role(incoming)
        await self._memberships.save_role(outgoing)
        # **Two rows, and that is correct** — two people's authority changed,
        # and an audit showing one would leave the other's unexplained. Written
        # in the same transaction as the roles, so the record and the fact
        # cannot disagree.
        await self._history.record(
            workspace_id=command.workspace_id,
            membership_id=incoming.id,
            previous_role=previous_incoming,
            new_role=WorkspaceRole.OWNER,
            changed_by=command.performed_by,
            at=now,
        )
        await self._history.record(
            workspace_id=command.workspace_id,
            membership_id=outgoing.id,
            previous_role=WorkspaceRole.OWNER,
            new_role=WorkspaceRole.MEMBER,
            changed_by=command.performed_by,
            at=now,
        )
        return outgoing, incoming


__all__ = ["TransferOwnership", "TransferOwnershipCommand"]
