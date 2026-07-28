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
