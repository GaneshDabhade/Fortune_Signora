"""An offer of membership, addressed to an email that may not be a user yet.

**The aggregate that lets an organization grow.** Until it existed, every
workspace was permanently whoever created it: ``POST /members`` takes a
``user_id``, and nothing resolves an address to one.

### Four states, and the type refuses to store two of them

``accepted_at`` and ``revoked_at`` are facts with a moment. **``PENDING`` is
the absence of both; ``EXPIRED`` is read from the clock.** A stored ``expired``
flag would need something to write it, and until that thing ran the row would
be wrong — the same reasoning that makes ``evidence_state`` derived rather than
persisted (``CLAUDE.md`` §2).

**``at`` is therefore an argument on ``state``, with no default.** An invitation
cannot report its own state without being told when *now* is, which makes the
clock a declared input rather than a hidden one (§2, *hidden inputs are
architecture defects*).

### It is immutable, and there is no method that edits it

Changing the role on a live invitation would mean the email said *member* and
acceptance granted *owner* — the product telling somebody one thing and doing
another. **A change is a revocation and a new offer**, and the partial unique
index in migration ``0031`` makes that the only reachable path.

### The inviter is provenance, never an owner

``invited_by`` records who acted and **never moves**, exactly like
``decided_by`` on a workflow state. An invitation belongs to the workspace, so
acceptance still succeeds after the inviter has left.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import UTC, datetime, timedelta
from enum import StrEnum
from uuid import UUID, uuid4

from modules.workspace_tenancy.domain.entities import WorkspaceRole

#: How long an offer stands. **A standing grant to enter a customer's data, so
#: it ends** — one that never expired would be a credential nobody remembers
#: issuing. Seven days is long enough to survive a holiday weekend and short
#: enough that a forgotten invitation surfaces rather than lingers.
INVITATION_VALID_FOR = timedelta(days=7)

#: Longest address RFC 5321 permits, and what the column stores.
MAX_EMAIL_LENGTH = 320


class InvitationState(StrEnum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    REVOKED = "revoked"
    EXPIRED = "expired"


class InvitationError(Exception):
    """An invitation was asked to do something its state does not permit."""


class InvalidInvitationEmailError(InvitationError):
    def __init__(self, value: str) -> None:
        super().__init__(f"{value!r} is not an address an invitation can be sent to.")
        self.value = value


class InvitationNotPendingError(InvitationError):
    """Revoking or accepting something already settled.

    Carries the state it actually found, because *"this was withdrawn"* and
    *"this expired"* are different sentences to a customer and only one of them
    offers a next step.

    ### 🔴 The three subclasses below, and why they exist — [B-214](../../../../docs/BUGS.md)

    ⛔ **This class carried the distinction and nothing could read it.** The
    comment above has said since it was written that the two sentences differ,
    **and the API answered `invitation_not_pending` for all three states** —
    so a screen could not tell an expired invitation from a withdrawn one, and
    the design's `14 Invitation expired` was unreachable.

    ⚡ **The error map is keyed by *type***, so one class cannot yield three
    codes. **Three subclasses can**, and they are subclasses rather than
    replacements so **every existing `except InvitationNotPendingError` keeps
    working unchanged** — the state that was already on the instance is now
    also in the type, which is [§2](../../../../CLAUDE.md)'s *types should make
    incorrect architecture impossible* applied to a distinction that was
    already true and merely unreadable.

    ⚠️ **`for_state` is the only constructor callers use.** A caller choosing
    the subclass itself could raise *expired* for a revoked invitation, which
    is the misattribution the split exists to end.
    """

    def __init__(self, state: InvitationState) -> None:
        super().__init__(f"This invitation is {state.value} and can no longer be changed.")
        self.state = state

    @staticmethod
    def for_state(state: InvitationState) -> InvitationNotPendingError:
        """The error that says which settled state it actually is."""
        return _NOT_PENDING_BY_STATE.get(state, InvitationNotPendingError)(state)


class InvitationExpiredError(InvitationNotPendingError):
    """It ran out of time. ⚡ **The one settled state with a next step** — the
    person can be invited again, and screen `14` exists to say so."""


class InvitationRevokedError(InvitationNotPendingError):
    """Somebody withdrew it. ⛔ **Deliberately not merged with expiry**: one is
    the clock and the other is a decision, and only the first is worth
    offering to redo."""


class InvitationAlreadyAcceptedError(InvitationNotPendingError):
    """Already accepted. **A second acceptance is not a failure to explain as
    one** — the person is a member, which is what they were trying to be."""


#: ⛔ **Exhaustive over the settled states, and `PENDING` is deliberately
#: absent** — a pending invitation never reaches this map, and an entry for it
#: would be a branch that cannot fire (§2, *a guard that cannot fail*).
_NOT_PENDING_BY_STATE: dict[InvitationState, type[InvitationNotPendingError]] = {
    InvitationState.EXPIRED: InvitationExpiredError,
    InvitationState.REVOKED: InvitationRevokedError,
    InvitationState.ACCEPTED: InvitationAlreadyAcceptedError,
}


def normalize_email(value: str) -> str:
    """The one place an address is put into the form everything else compares.

    **Lowercased and stripped**, because acceptance matches it against a
    verified JWT claim and two spellings of one address would be two live
    invitations the unique index cannot see as one.

    Deliberately **not** full RFC validation: the address is proved by Better
    Auth when somebody signs in with it, and a regular expression that rejects
    a legitimate address is worse than one that accepts a typo — the typo is
    visible on the screen and revocable in a click.
    """
    candidate = value.strip().lower()
    if not candidate or len(candidate) > MAX_EMAIL_LENGTH:
        raise InvalidInvitationEmailError(value)
    local, separator, domain = candidate.partition("@")
    if not separator or not local or "." not in domain or domain.startswith("."):
        raise InvalidInvitationEmailError(value)
    return candidate


@dataclass(frozen=True, slots=True)
class Invitation:
    id: UUID
    workspace_id: UUID
    invited_email: str
    role: WorkspaceRole
    expires_at: datetime
    invited_by: UUID
    created_at: datetime
    accepted_at: datetime | None = None
    revoked_at: datetime | None = None

    @classmethod
    def offer(
        cls,
        *,
        workspace_id: UUID,
        email: str,
        role: WorkspaceRole,
        invited_by: UUID,
        now: datetime | None = None,
    ) -> Invitation:
        moment = now or datetime.now(UTC)
        return cls(
            id=uuid4(),
            workspace_id=workspace_id,
            invited_email=normalize_email(email),
            role=role,
            expires_at=moment + INVITATION_VALID_FOR,
            invited_by=invited_by,
            created_at=moment,
        )

    def state(self, *, at: datetime) -> InvitationState:
        """What this invitation is, at a stated moment.

        **The clock is an argument with no default.** An invitation that read
        the wall clock itself would give a different answer to a test than to a
        request, and the state would stop being reproducible.
        """
        if self.accepted_at is not None:
            return InvitationState.ACCEPTED
        if self.revoked_at is not None:
            return InvitationState.REVOKED
        if at >= self.expires_at:
            return InvitationState.EXPIRED
        return InvitationState.PENDING

    def revoke(self, *, at: datetime) -> Invitation:
        """Withdraw the offer.

        **Expired invitations refuse revocation**, and that is not pedantry: an
        administrator revoking one would believe they had closed a door that had
        already shut, and the record would claim an act that changed nothing.
        """
        self.require_pending(at)
        return replace(self, revoked_at=at)

    def accept(self, *, at: datetime) -> Invitation:
        self.require_pending(at)
        return replace(self, accepted_at=at)

    def require_pending(self, at: datetime) -> None:
        """Refuse anything a settled invitation cannot do.

        **Public because resending needs it too**, and a use case reaching into
        a private method would be the boundary leaking rather than the rule
        being shared.
        """
        current = self.state(at=at)
        if current is not InvitationState.PENDING:
            # **`for_state`, never the base class directly** — B-214. Raising
            # the base here would put the distinction back out of the type's
            # reach, which is the whole defect.
            raise InvitationNotPendingError.for_state(current)
