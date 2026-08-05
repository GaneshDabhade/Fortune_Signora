"""Accepting an offer of membership.

**The one operation in Signora performed by somebody who is not yet in the
workspace**, which is what made it the last piece of Team Management to be
built and why it needed a ruling ([C-208](../../../../../docs/LANE_COORDINATION.md)).

### Acceptance never reads across tenants

`invitation`'s row-level security is `workspace_id = current_setting(
'app.workspace_id')`, like every other tenant-owned table. The accepter is by
definition not a member, so nothing grants them that context — and the row
addressed to them is invisible to them.

**The ruling: an explicit authenticated-but-not-member state, general RLS
untouched, and only the minimum read path acceptance requires. A named
single-purpose path, never a policy change.**

So **the workspace is supplied by the request**. The invitation link carries
both identifiers, the caller names the organization they are joining, and the
session is scoped to that one workspace exactly as any other request is. No
policy is widened, no role bypasses RLS, and no session variable is added.

**What this deliberately does not build is a cross-workspace inbox** — *"show
me every invitation I have"*. That is the one screen in Signora that would read
outside a tenant, nothing has asked for it, and it is the whole reason the
other two options were refused.

### The address is the credential, and the token is not

Naming a workspace and an invitation is **not** authority to join it. Anyone
who guessed both identifiers would otherwise be a member.

**Authority comes from the verified email claim**, which Better Auth proved at
sign-in and the platform re-verifies on every request. The invitation names an
address; acceptance requires that the caller *is* that address. Both halves are
enforced here:

* the claim must be **verified** — an unverified address is an assertion by the
  person making it, and accepting on one would let anybody type their way into
  a customer's data;
* it must **match** the invited address, compared through `normalize_email` so
  two spellings of one address cannot be two different answers.

### Already a member is a success, not a failure

Somebody who follows the link twice, or who was added directly while an
invitation stood, has the membership the invitation offered. Refusing the
second attempt would show an error for a state that is exactly what was asked
for. **The invitation is settled and the existing membership returned.**
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from modules.workspace_tenancy.application.ports import (
    EventPublisher,
    InvitationRepository,
    MembershipRepository,
)
from modules.workspace_tenancy.domain.entities import Membership
from modules.workspace_tenancy.domain.invitation import (
    InvitationError,
    normalize_email,
)


class InvitationNotFoundError(InvitationError):
    """No such invitation in this workspace.

    **Deliberately indistinguishable from an invitation addressed to somebody
    else** — see `NotYoursToAcceptError`. Both answer `404`, because telling
    the two apart would turn this endpoint into a way to ask *"does this
    workspace hold an invitation with this id?"*
    """

    def __init__(self) -> None:
        super().__init__("That invitation does not exist, or it is not yours to accept.")


class NotYoursToAcceptError(InvitationError):
    """The invitation names a different address.

    **The same message and the same status as a missing invitation.** A
    distinct one would confirm to a stranger that a particular workspace had
    invited a particular person, which is a fact about a customer's hiring.
    """

    def __init__(self) -> None:
        super().__init__("That invitation does not exist, or it is not yours to accept.")


class UnverifiedEmailError(InvitationError):
    """The caller's address has not been verified.

    **Its own error, and its own message**, because unlike the two above this
    one is the caller's to fix and telling them so leaks nothing: they already
    know their own address.
    """

    def __init__(self) -> None:
        super().__init__(
            "Verify your email address before accepting an invitation. "
            "An unverified address is a claim rather than a proof."
        )


@dataclass(frozen=True, slots=True)
class AcceptInvitationInput:
    workspace_id: UUID
    invitation_id: UUID
    #: The authenticated caller. **From the verified token, never a request
    #: body** — a user id a caller could choose is a user id they would choose
    #: somebody else's.
    user_id: UUID
    #: The caller's address, from the same verified token.
    email: str
    #: Whether the identity provider has proved that address.
    email_verified: bool


class AcceptInvitationUseCase:
    """Turn a standing offer into a membership."""

    def __init__(
        self,
        *,
        invitations: InvitationRepository,
        memberships: MembershipRepository,
        event_publisher: EventPublisher,
    ) -> None:
        self._invitations = invitations
        self._memberships = memberships
        self._event_publisher = event_publisher

    async def execute(
        self, input_: AcceptInvitationInput, *, now: datetime, correlation_id: UUID
    ) -> Membership:
        """**Order matters, and it is the order of increasing disclosure.**

        The verification check runs first and answers about the caller alone.
        **Everything after it returns one sentence and one status**, so the
        order cannot be used to learn anything by watching which error comes
        back — and there is no separate *"no such workspace"* to distinguish.
        """
        if not input_.email_verified:
            raise UnverifiedEmailError()

        # **There is deliberately no workspace-existence check.** The first
        # draft had one, and an integration test caught it: `workspace`'s
        # row-level security is *membership-based*, so the accepter — who is by
        # definition not a member — could never pass it, and every acceptance
        # answered `workspace_not_found`. It also leaked a distinct code for a
        # workspace the caller cannot see.
        #
        # **The invitation read is the existence proof.** An invitation cannot
        # exist without its workspace, and one that cannot be found is
        # `InvitationNotFoundError` — the same 404 as every other refusal here.
        invitation = await self._invitations.get(input_.workspace_id, input_.invitation_id)
        if invitation is None:
            raise InvitationNotFoundError()

        # **Compared normalized, on both sides.** The stored address was
        # normalized when the invitation was written; the claim is normalized
        # here, so `Ada@Example.COM` accepting an invitation to
        # `ada@example.com` is one person and not two.
        if normalize_email(input_.email) != normalize_email(invitation.invited_email):
            raise NotYoursToAcceptError()

        # **Before the pending check, not after.** Somebody who follows the
        # link a second time has what the invitation offered, and an
        # `InvitationNotPendingError` would report a failure for the state they
        # asked for. The membership they already hold is the honest answer.
        existing = await self._memberships.get(input_.workspace_id, input_.user_id)
        if existing is not None:
            return existing

        # Refuses expired, revoked and already-accepted, each with its own
        # sentence — the aggregate owns that distinction and this does not
        # restate it.
        invitation.require_pending(now)

        membership, member_added = Membership.create(
            workspace_id=input_.workspace_id,
            user_id=input_.user_id,
            role=invitation.role,
            # **Created by the person accepting, not by the inviter.** The
            # inviter offered; this person acted. `invited_by` on the
            # invitation remains the provenance of the offer and never moves.
            created_by=input_.user_id,
            # **The address the offer was made to**, not the claim presented —
            # they are equal by the check above, and storing the stored one
            # keeps the membership a fact about the invitation it came from.
            member_email=invitation.invited_email,
        )
        await self._memberships.add(membership)
        # **Settled after the membership exists.** If the write fails, the
        # invitation is still pending and the link still works; settling first
        # would consume the offer and leave the person outside.
        await self._invitations.settle(invitation.accept(at=now))
        await self._event_publisher.publish([member_added], correlation_id=correlation_id)
        return membership


__all__ = [
    "AcceptInvitationInput",
    "AcceptInvitationUseCase",
    "InvitationNotFoundError",
    "NotYoursToAcceptError",
    "UnverifiedEmailError",
]
