"""Offering, listing and withdrawing membership of an organization.

**Three use cases in one file** because they are one customer capability and
share every rule: the same aggregate, the same clock, the same live-invitation
constraint. Splitting them would put `INVITATION_VALID_FOR` in one file and the
reason it matters in another.

### The clock is injected, everywhere

`now` is a parameter on every operation with no default. An invitation's state
depends on it, so a use case reading the wall clock itself would make the same
declared inputs produce different results — which is the definition of a hidden
input (`CLAUDE.md` §2).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from modules.workspace_tenancy.application.ports import (
    InvitationDelivery,
    InvitationRepository,
    MembershipRepository,
    WorkspaceRepository,
)
from modules.workspace_tenancy.domain.entities import WorkspaceRole
from modules.workspace_tenancy.domain.exceptions import WorkspaceNotFoundError
from modules.workspace_tenancy.domain.invitation import (
    Invitation,
    InvitationError,
    normalize_email,
)


class AlreadyInvitedError(InvitationError):
    """A live invitation to this address already exists.

    **Refused rather than silently resent**, because a resend is a deliberate
    act with its own control. An invite that quietly became a resend would make
    *"I already invited them"* and *"I just invited them"* indistinguishable in
    the audit trail.
    """

    def __init__(self, email: str) -> None:
        super().__init__(f"{email} has already been invited and has not yet responded.")
        self.email = email


class InvitationNotFoundError(InvitationError):
    def __init__(self, invitation_id: UUID) -> None:
        super().__init__(f"Invitation {invitation_id} does not exist in this organization.")
        self.invitation_id = invitation_id


@dataclass(frozen=True, slots=True)
class InviteMemberCommand:
    workspace_id: UUID
    email: str
    role: WorkspaceRole
    invited_by: UUID


class InviteMember:
    def __init__(
        self,
        *,
        workspaces: WorkspaceRepository,
        memberships: MembershipRepository,
        invitations: InvitationRepository,
        delivery: InvitationDelivery,
    ) -> None:
        self._workspaces = workspaces
        self._memberships = memberships
        self._invitations = invitations
        self._delivery = delivery

    async def execute(self, command: InviteMemberCommand, *, now: datetime) -> Invitation:
        workspace = await self._workspaces.get(command.workspace_id)
        if workspace is None:
            raise WorkspaceNotFoundError(command.workspace_id)

        # Normalized before the lookup, not after: the stored form is what the
        # partial unique index compares, so checking a raw address would miss a
        # live invitation that differs only in case.
        email = normalize_email(command.email)

        existing = await self._invitations.find_live(command.workspace_id, email)
        if existing is not None:
            raise AlreadyInvitedError(email)

        invitation = Invitation.offer(
            workspace_id=command.workspace_id,
            email=email,
            role=command.role,
            invited_by=command.invited_by,
            now=now,
        )
        await self._invitations.add(invitation)
        # **After the write, deliberately.** A message sent before the row was
        # durable would arrive for an invitation that may not exist, and this
        # port cannot fail the operation (see `InvitationDelivery`).
        await self._delivery.send(invitation, workspace_name=workspace.name)
        return invitation


class ListInvitations:
    def __init__(self, *, invitations: InvitationRepository) -> None:
        self._invitations = invitations

    async def execute(self, workspace_id: UUID) -> list[Invitation]:
        """Every invitation in every state.

        **Including the settled ones, which is the point.** An expired
        invitation is what tells an administrator somebody was invited and
        never came — deleting it would erase the only signal to act on.
        """
        return await self._invitations.list_for_workspace(workspace_id)


class RevokeInvitation:
    def __init__(self, *, invitations: InvitationRepository) -> None:
        self._invitations = invitations

    async def execute(
        self, workspace_id: UUID, invitation_id: UUID, *, now: datetime
    ) -> Invitation:
        invitation = await self._invitations.get(workspace_id, invitation_id)
        if invitation is None:
            raise InvitationNotFoundError(invitation_id)
        # The domain refuses anything not pending, and carries the state it
        # found — so the interface can say *withdrawn* or *expired* rather than
        # a single unhelpful refusal.
        revoked = invitation.revoke(at=now)
        await self._invitations.settle(revoked)
        return revoked


__all__ = [
    "AlreadyInvitedError",
    "InvitationNotFoundError",
    "InviteMember",
    "InviteMemberCommand",
    "ListInvitations",
    "RevokeInvitation",
]
