"""The Workspace & Tenancy aggregates: Workspace and Membership.

Modeled as two separate aggregates, not one nested aggregate, deliberately:
Workspace and Membership have independent lifecycles (memberships are
added and removed continuously; the workspace itself rarely changes), and
loading every membership every time a workspace is touched would be an
unnecessary cost with no consistency requirement forcing it. The application
layer's use cases coordinate the two where a single business operation
(e.g. creating a workspace) needs to touch both atomically.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from uuid import UUID, uuid4

from modules.workspace_tenancy.domain.events import MemberAdded, WorkspaceCreated
from modules.workspace_tenancy.domain.exceptions import (
    InvalidWorkspaceNameError,
    InvalidWorkspaceSlugError,
)

MAX_WORKSPACE_NAME_LENGTH = 200

#: 📁 Screen `03` — *"eu.signora.app/**northwind**"*. **The address bar is the
#: constraint**: short enough to type, long enough to disambiguate two
#: companies with the same first word.
MIN_WORKSPACE_SLUG_LENGTH = 3
MAX_WORKSPACE_SLUG_LENGTH = 63

#: ⛔ **Lowercase, digits and single inner hyphens. Nothing else.**
#: ⚡ **This is a hostname label, not a title** — 📁 the design puts it after a
#: `/` in monospace, and a slug that needed percent-encoding to appear there
#: would not be the thing the screen showed somebody.
_SLUG = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")

#: ⛔ **Reserved, because a customer may not take a path the product owns.**
#: ⚠️ **Refused rather than silently suffixed**: somebody who typed `api` and
#: got `api-2` was never told, and the address they remember is wrong.
RESERVED_WORKSPACE_SLUGS = frozenset(
    {"api", "app", "www", "admin", "signora", "static", "assets", "auth", "login", "health"}
)


def normalize_workspace_slug(candidate: str) -> str:
    """Fold a candidate into the one form that can be stored.

    ⚡ **Case and surrounding space only.** ⛔ **It does not invent a slug from
    a name** — 📁 the design pre-fills the field from the email domain and
    lets somebody edit it, so the suggestion is the *client's* to make and the
    stored value is whatever they accepted. **Deriving here as well would be
    two producers of one string** ([§2](../../../../CLAUDE.md)).
    """
    return candidate.strip().lower()


def validate_workspace_slug(candidate: str) -> str:
    """The normalized slug, or `InvalidWorkspaceSlugError`.

    ⚠️ **Length is checked before shape**, so *"nw"* is told it is too short
    rather than told it has the wrong characters — which it does not.
    """
    slug = normalize_workspace_slug(candidate)
    if not (MIN_WORKSPACE_SLUG_LENGTH <= len(slug) <= MAX_WORKSPACE_SLUG_LENGTH):
        raise InvalidWorkspaceSlugError(candidate)
    if not _SLUG.match(slug):
        raise InvalidWorkspaceSlugError(candidate)
    if slug in RESERVED_WORKSPACE_SLUGS:
        raise InvalidWorkspaceSlugError(candidate)
    return slug


class WorkspaceRole(StrEnum):
    """Deliberately minimal today (owner/member). Casbin owns fine-grained,
    resource-level permission evaluation (ADR-0010); this role is the coarse
    membership-level distinction Workspace & Tenancy itself is responsible
    for, e.g. "who may add/remove other members."
    """

    OWNER = "owner"
    MEMBER = "member"


@dataclass
class Workspace:
    id: UUID
    name: str
    #: 📁 Screen `03` — *"Workspace URL … **Permanent once created.**"*
    #: ⛔ **There is no rename operation and that is deliberate**: the design
    #: says permanent, and a link somebody shared must not stop resolving
    #: because a colleague tidied the name.
    slug: str
    created_at: datetime
    updated_at: datetime
    created_by: UUID
    updated_by: UUID

    @classmethod
    def create(
        cls, *, name: str, slug: str, created_by: UUID
    ) -> tuple[Workspace, WorkspaceCreated]:
        normalized_name = name.strip()
        if not normalized_name or len(normalized_name) > MAX_WORKSPACE_NAME_LENGTH:
            raise InvalidWorkspaceNameError(name)
        normalized_slug = validate_workspace_slug(slug)

        now = datetime.now(UTC)
        workspace_id = uuid4()
        workspace = cls(
            id=workspace_id,
            name=normalized_name,
            slug=normalized_slug,
            created_at=now,
            updated_at=now,
            created_by=created_by,
            updated_by=created_by,
        )
        event = WorkspaceCreated(
            workspace_id=workspace_id,
            name=normalized_name,
            created_by=created_by,
        )
        return workspace, event


class LastOwnerCannotLeaveError(Exception):
    """The only person who can administer this organization was leaving.

    **Refused in the domain, not in a dialog.** A workspace with no owner is
    one nobody can administer and nobody can repair without support — and a
    check in the interface can be raced by a second tab.
    """

    def __init__(self, workspace_id: UUID) -> None:
        super().__init__(
            "This organization would be left with nobody who can administer it. "
            "Make somebody else an owner first."
        )
        self.workspace_id = workspace_id


class RoleUnchangedError(Exception):
    """Setting a role to the one it already holds.

    **Refused rather than accepted as a no-op**, because it would write an audit
    row saying somebody's authority changed when it did not — and a history with
    entries that record nothing is one nobody trusts.
    """

    def __init__(self, membership_id: UUID, role: WorkspaceRole) -> None:
        super().__init__(f"They already have this role ({role.value}).")
        self.membership_id = membership_id
        self.role = role


class MembershipAlreadyEndedError(Exception):
    """Ending something that has already ended would claim an act that changed
    nothing, and would overwrite the moment it actually happened."""

    def __init__(self, membership_id: UUID) -> None:
        super().__init__("This person has already been removed from the organization.")
        self.membership_id = membership_id


@dataclass
class Membership:
    id: UUID
    workspace_id: UUID
    user_id: UUID
    role: WorkspaceRole
    created_at: datetime
    updated_at: datetime
    created_by: UUID
    updated_by: UUID
    #: When this person stopped belonging. **A membership is ended, never
    #: deleted** — decision history, the timeline and every audit question cite
    #: it, and removing the row would silently rewrite what a customer already
    #: read (46-team-management.md, D3).
    ended_at: datetime | None = None
    ended_by: UUID | None = None
    ended_reason: str | None = None
    #: The address this membership was created with — the founder's verified
    #: claim, or the address an administrator invited. **A fact about an act,
    #: not a mirror of a profile**, which is what keeps it inside §13: a
    #: display name would go stale, and this cannot.
    member_email: str | None = None

    @property
    def is_live(self) -> bool:
        return self.ended_at is None

    def change_role(
        self,
        *,
        to: WorkspaceRole,
        by: UUID,
        at: datetime,
        remaining_owners: int,
    ) -> WorkspaceRole:
        """Change what somebody is allowed to do, and return what they were.

        **The same invariant as ending a membership**, and deliberately the same
        argument: demoting the last owner leaves an organization nobody can
        administer, which is the identical outcome to removing them. Two ways to
        reach one failure, refused in one place.

        **An owner may demote themselves** when another owner exists. Refusing
        it would mean an administrator handing over could not then step back,
        and the invariant already protects the case that matters.
        """
        if not self.is_live:
            raise MembershipAlreadyEndedError(self.id)
        if self.role is WorkspaceRole.OWNER and to is not WorkspaceRole.OWNER:
            if remaining_owners == 0:
                raise LastOwnerCannotLeaveError(self.workspace_id)
        if to is self.role:
            raise RoleUnchangedError(self.id, self.role)

        previous = self.role
        self.role = to
        self.updated_at = at
        self.updated_by = by
        return previous

    def end(
        self,
        *,
        by: UUID,
        at: datetime,
        reason: str | None,
        remaining_owners: int,
    ) -> None:
        """Record that this person no longer belongs.

        ``remaining_owners`` counts owners **other than this membership**, and
        is an argument with no default because the aggregate cannot see them:
        the last-owner rule spans the whole membership set, so the count is
        read inside the same transaction and passed in. Making it a required
        argument is what stops a caller forgetting the invariant exists.
        """
        if not self.is_live:
            raise MembershipAlreadyEndedError(self.id)
        if self.role is WorkspaceRole.OWNER and remaining_owners == 0:
            raise LastOwnerCannotLeaveError(self.workspace_id)

        self.ended_at = at
        self.ended_by = by
        # Kept verbatim. It is somebody's sentence about a colleague, and a
        # normalised or truncated version would be the product editing it.
        self.ended_reason = reason.strip() if reason and reason.strip() else None
        self.updated_at = at
        self.updated_by = by

    @classmethod
    def create(
        cls,
        *,
        workspace_id: UUID,
        user_id: UUID,
        role: WorkspaceRole,
        created_by: UUID,
        causation_id: UUID | None = None,
        member_email: str | None = None,
    ) -> tuple[Membership, MemberAdded]:
        now = datetime.now(UTC)
        membership = cls(
            id=uuid4(),
            workspace_id=workspace_id,
            user_id=user_id,
            role=role,
            created_at=now,
            updated_at=now,
            created_by=created_by,
            updated_by=created_by,
            member_email=member_email,
        )
        event = MemberAdded(
            workspace_id=workspace_id,
            user_id=user_id,
            role=role.value,
            causation_id=causation_id,
        )
        return membership, event


class OwnershipTransferError(Exception):
    """A transfer was asked for that cannot be performed as one act."""


def transfer_ownership(
    *,
    outgoing: Membership,
    incoming: Membership,
    by: UUID,
    at: datetime,
) -> None:
    """Hand the organization over — **one operation, not two role changes.**

    Composing this from `promote` and `demote` leaves an intermediate state
    with **two owners that nobody asked for**, and if the second step fails,
    is abandoned, or the browser closes, the organization is left in a shape
    no customer chose. **A transfer that half-happens is worse than one that
    is refused.**

    So both mutations happen here, and the caller performs them inside one
    transaction. **The last-owner invariant is deliberately not consulted**:
    it protects against ending with nobody, and this ends with exactly one —
    checking it mid-operation would refuse the very thing that satisfies it.
    """
    # **No same-workspace check here, deliberately.** It was written, and the
    # test proved it could never fire: both memberships are fetched scoped to
    # one workspace, and RLS scopes them again beneath that. A guard that
    # cannot fail is documentation pretending to be code (`CLAUDE.md` §2), and
    # the real protection is asserted where it actually lives — the repository
    # returns nothing for a membership in another organization.
    if outgoing.id == incoming.id:
        raise OwnershipTransferError("They already own this organization.")
    if not outgoing.is_live:
        raise MembershipAlreadyEndedError(outgoing.id)
    # **Checked before anything is mutated.** Somebody removed while the dialog
    # was open would otherwise be promoted, then found to have left.
    if not incoming.is_live:
        raise MembershipAlreadyEndedError(incoming.id)
    if outgoing.role is not WorkspaceRole.OWNER:
        raise OwnershipTransferError("Only an owner can hand over an organization.")

    incoming.role = WorkspaceRole.OWNER
    outgoing.role = WorkspaceRole.MEMBER
    for membership in (incoming, outgoing):
        membership.updated_at = at
        membership.updated_by = by
