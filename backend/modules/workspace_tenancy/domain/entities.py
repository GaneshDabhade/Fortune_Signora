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

from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from uuid import UUID, uuid4

from modules.workspace_tenancy.domain.events import MemberAdded, WorkspaceCreated
from modules.workspace_tenancy.domain.exceptions import InvalidWorkspaceNameError

MAX_WORKSPACE_NAME_LENGTH = 200


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
    created_at: datetime
    updated_at: datetime
    created_by: UUID
    updated_by: UUID

    @classmethod
    def create(cls, *, name: str, created_by: UUID) -> tuple[Workspace, WorkspaceCreated]:
        normalized_name = name.strip()
        if not normalized_name or len(normalized_name) > MAX_WORKSPACE_NAME_LENGTH:
            raise InvalidWorkspaceNameError(name)

        now = datetime.now(UTC)
        workspace_id = uuid4()
        workspace = cls(
            id=workspace_id,
            name=normalized_name,
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

    @property
    def is_live(self) -> bool:
        return self.ended_at is None

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
        )
        event = MemberAdded(
            workspace_id=workspace_id,
            user_id=user_id,
            role=role.value,
            causation_id=causation_id,
        )
        return membership, event
