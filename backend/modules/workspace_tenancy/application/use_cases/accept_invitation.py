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
* the offer is **looked up by that address**, through `normalize_email`, so
  two spellings of one address cannot be two different answers — and reading
  somebody else's invitation is not a check that could be forgotten, it is a
  query that does not exist.

### Already a member is a success, not a failure

Somebody who follows the link twice, or who was added directly while an
invitation stood, has the membership the invitation offered. Refusing the
second attempt would show an error for a state that is exactly what was asked
for.

**The membership check therefore runs before the offer is looked for.** The
offer is found by address among *live* invitations, and acceptance settles it —
so a second click finds nothing, and without this ordering the person would be
told there is no invitation to a workspace they are already in.
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
    """This workspace has no standing offer to this address.

    **One sentence covering every reason**, and that is the design rather than
    laziness: never invited, already accepted, withdrawn. Telling them apart
    would answer *"has this workspace invited this person?"* to anybody who can
    sign in — a fact about a customer's hiring.

    **Expiry is the deliberate exception** and is raised by the aggregate with
    its own words. An expired offer is one the person genuinely held, and
    *"that expired"* is the only refusal here that tells them what to do next.
    """

    def __init__(self) -> None:
        super().__init__("There is no invitation to this organization for your address.")


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

        # **Membership is checked before the offer is looked for, and that
        # ordering is load-bearing.** `find_live` excludes accepted offers, so
        # somebody following their link a second time finds nothing — and would
        # be told there is no invitation, for a workspace they are already in.
        # An integration test caught exactly that when this use case moved from
        # an id lookup to an address lookup; the unit tests did not, because the
        # fake had already returned before reaching the repository.
        #
        # A member asking to accept is told what is true: they are a member.
        existing = await self._memberships.get(input_.workspace_id, input_.user_id)
        if existing is not None:
            return existing

        # **The offer is looked up by the caller's own verified address**, not
        # by an identifier in the link. That is what makes *"this is not yours"*
        # unreachable rather than checked: there is no code path here that can
        # read somebody else's invitation, so no check to forget.
        #
        # It also matches the link the product actually sends —
        # `/join/{workspace_id}`, carrying no invitation id — because the id
        # would look like a secret while being none. At most one live offer per
        # address exists, guaranteed by the partial unique index that
        # `find_live` mirrors.
        #
        # **There is deliberately no workspace-existence check.** The first
        # draft had one, and an integration test caught it: `workspace`'s
        # row-level security is *membership-based*, so the accepter — who is by
        # definition not a member — could never pass it, and every acceptance
        # answered `workspace_not_found`.
        invitation = await self._invitations.find_live(
            input_.workspace_id, normalize_email(input_.email)
        )
        if invitation is None:
            raise InvitationNotFoundError()

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
    "UnverifiedEmailError",
]
