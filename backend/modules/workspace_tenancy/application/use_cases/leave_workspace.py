"""Somebody decides they no longer belong to an organization.

**The same act as `remove_member`, performed by the person it happens to** —
and that difference is the whole of this use case. Removing is something an
administrator does *to* a colleague; leaving is something a person does about
themselves, and a product that offers the first and not the second has told
every member that only somebody else can end their involvement.

### It takes no target, and that is what makes it self-scoped

`RemoveMember` names a `membership_id` because an administrator is pointing at
somebody. **Nothing here points at anybody**: the caller's own membership is
found from the workspace and the authenticated user id, so there is no
identifier a caller could substitute and no check that they own the one they
named. **The safest parameter is the one that does not exist.**

That is also why `Action.LEAVE` needs no self-scoping in the policy — the enum
says so in its own words: *"the scoping to self is the endpoint's, not the
policy's… identity never enters the request tuple."*

### Why leaving is not simply *remove yourself*

It reuses `Membership.end`, and it must — two ways to end a membership with two
implementations would eventually disagree about the invariant that matters. But
it is **not** `RemoveMember` with the caller's own id passed in, because that
use case takes a `reason` written *about* somebody, and requiring a person to
justify their own departure to the organization they are leaving is a sentence
the product should not ask for. **`ended_reason` stays null here**, and the
audit record is no poorer for it: `ended_by == user_id` is exactly the fact
that distinguishes leaving from being removed, and it is derived rather than
stored (`CLAUDE.md` §2).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from modules.workspace_tenancy.application.ports import MembershipRepository
from modules.workspace_tenancy.domain.entities import Membership


class NotAMemberError(Exception):
    """The caller has no live membership in this workspace to end.

    **Reachable, and not only through a race.** `CurrentWorkspace` verifies
    membership before the request arrives, so the ordinary path cannot get
    here — but a second tab that already left, or an administrator removing
    somebody mid-request, both land exactly here.

    **`None` covers the already-left case, and nothing else needs to.** The
    first draft also tested `not membership.is_live`, which cannot fire: both
    the real repository and the fake filter `get` to live memberships, and the
    real one says why — *"an ended membership that still resolved here would
    keep somebody signed in to an organization they had been removed from."*
    **A guard that cannot fail is documentation pretending to be code** (§2),
    so it was removed rather than left looking careful.
    """

    def __init__(self, workspace_id: UUID, user_id: UUID) -> None:
        super().__init__("You are not a member of this organization.")
        self.workspace_id = workspace_id
        self.user_id = user_id


@dataclass(frozen=True, slots=True)
class LeaveWorkspaceCommand:
    """**Two fields, and neither is a target.** The user id is the caller's own,
    taken from the verified token by the endpoint and never from the request."""

    workspace_id: UUID
    user_id: UUID


class LeaveWorkspace:
    def __init__(self, *, memberships: MembershipRepository) -> None:
        self._memberships = memberships

    async def execute(self, command: LeaveWorkspaceCommand, *, now: datetime) -> Membership:
        membership = await self._memberships.get(command.workspace_id, command.user_id)
        if membership is None:
            raise NotAMemberError(command.workspace_id, command.user_id)

        # **Locked before counting, exactly as removal locks.** Two owners
        # leaving at the same moment would each read *two owners*, each compute
        # *one remaining*, and both succeed — leaving an organization nobody can
        # administer. The count is correct and not atomic across transactions;
        # the lock is what makes it so. **This path is likelier to race than
        # removal**, because two people deciding independently to leave need no
        # administrator to coordinate them.
        await self._memberships.lock_membership_set(command.workspace_id)
        live_owners = await self._memberships.count_live_owners(command.workspace_id)
        remaining = live_owners - 1 if membership.role.value == "owner" else live_owners

        # **`by` is the leaver.** In `RemoveMember` this is the administrator,
        # and the two rows are otherwise identical — so `ended_by == user_id` is
        # what a reader uses to tell a departure from a removal, and it is true
        # by construction rather than by a flag somebody has to set correctly.
        membership.end(
            by=command.user_id,
            at=now,
            # **Not asked for.** A person leaving does not owe the organization
            # an explanation, and a nullable column that only ever holds
            # somebody else's account of you is worse empty than absent.
            reason=None,
            remaining_owners=remaining,
        )
        await self._memberships.end(membership)
        return membership


__all__ = ["LeaveWorkspace", "LeaveWorkspaceCommand", "NotAMemberError"]
