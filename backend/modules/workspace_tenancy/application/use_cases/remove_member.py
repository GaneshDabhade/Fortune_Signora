"""Somebody no longer belongs to an organization.

**Not a deletion, and the language matters.** A customer doing this has had
somebody leave the company, ended a contractor's engagement, corrected a
mistaken invitation, or responded to a security incident. Every one of those is
*this person no longer belongs*, and none of them is *delete a row* — which is
why the membership survives with the moment, the actor and the reason
(46-team-management.md, D3).

**`member:remove` has authorized this since M1** and nothing could perform it.
This use case is the operation that grant already assumed.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from modules.workspace_tenancy.application.ports import MembershipRepository
from modules.workspace_tenancy.domain.entities import Membership


class MembershipNotFoundError(Exception):
    def __init__(self, membership_id: UUID) -> None:
        super().__init__(f"Membership {membership_id} does not exist in this organization.")
        self.membership_id = membership_id


@dataclass(frozen=True, slots=True)
class RemoveMemberCommand:
    workspace_id: UUID
    membership_id: UUID
    removed_by: UUID
    #: Why, in the customer's words. Optional — an administrator correcting a
    #: typo should not be made to justify it — and kept verbatim when given,
    #: because it is somebody's sentence about a colleague.
    reason: str | None = None


class RemoveMember:
    def __init__(self, *, memberships: MembershipRepository) -> None:
        self._memberships = memberships

    async def execute(self, command: RemoveMemberCommand, *, now: datetime) -> Membership:
        membership = await self._memberships.get_by_id(command.workspace_id, command.membership_id)
        if membership is None:
            raise MembershipNotFoundError(command.membership_id)

        # **Locked before counting.** Two owners removed concurrently would each
        # read *two owners*, each compute *one remaining*, and both succeed —
        # leaving an organization nobody can administer. The count is correct
        # and not atomic across transactions; the lock is what makes it so.
        await self._memberships.lock_membership_set(command.workspace_id)
        # **Counted inside the same transaction as the write.** The last-owner
        # rule spans every membership in the workspace, so the number is read
        # here and the aggregate refuses on it — the invariant belongs to the
        # workspace, and the count is what makes that enforceable without
        # loading the whole set.
        live_owners = await self._memberships.count_live_owners(command.workspace_id)
        remaining = live_owners - 1 if membership.role.value == "owner" else live_owners

        membership.end(
            by=command.removed_by,
            at=now,
            reason=command.reason,
            remaining_owners=remaining,
        )
        await self._memberships.end(membership)
        return membership


__all__ = ["MembershipNotFoundError", "RemoveMember", "RemoveMemberCommand"]
