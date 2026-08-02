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
    """

    def __init__(self, state: InvitationState) -> None:
        super().__init__(f"This invitation is {state.value} and can no longer be changed.")
        self.state = state


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
        self._require_pending(at)
        return replace(self, revoked_at=at)

    def accept(self, *, at: datetime) -> Invitation:
        self._require_pending(at)
        return replace(self, accepted_at=at)

    def _require_pending(self, at: datetime) -> None:
        current = self.state(at=at)
        if current is not InvitationState.PENDING:
            raise InvitationNotPendingError(current)
