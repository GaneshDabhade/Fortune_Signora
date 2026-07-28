from dataclasses import dataclass
from uuid import UUID

from modules.workspace_tenancy.application.ports import (
    EventPublisher,
    MembershipRepository,
    WorkspaceRepository,
)
from modules.workspace_tenancy.domain.entities import Membership, WorkspaceRole
from modules.workspace_tenancy.domain.exceptions import (
    DuplicateMembershipError,
    WorkspaceNotFoundError,
)


@dataclass(frozen=True)
class AddMemberInput:
    workspace_id: UUID
    user_id: UUID
    role: WorkspaceRole
    added_by: UUID


class AddMemberUseCase:
    """Adds a member to an existing workspace.

    Whether ``added_by`` is *authorized* to add members is a Casbin
    authorization concern evaluated at the interface layer before this use
    case is ever invoked (ADR-0010) — this use case only enforces the
    business invariants that are this module's own responsibility: the
    workspace must exist, and a user may not be a member twice.
    """

    def __init__(
        self,
        *,
        workspace_repository: WorkspaceRepository,
        membership_repository: MembershipRepository,
        event_publisher: EventPublisher,
    ) -> None:
        self._workspace_repository = workspace_repository
        self._membership_repository = membership_repository
        self._event_publisher = event_publisher

    async def execute(self, input_: AddMemberInput, *, correlation_id: UUID) -> Membership:
        workspace = await self._workspace_repository.get(input_.workspace_id)
        if workspace is None:
            raise WorkspaceNotFoundError(input_.workspace_id)

        existing = await self._membership_repository.get(input_.workspace_id, input_.user_id)
        if existing is not None:
            raise DuplicateMembershipError(input_.workspace_id, input_.user_id)

        membership, member_added = Membership.create(
            workspace_id=input_.workspace_id,
            user_id=input_.user_id,
            role=input_.role,
            created_by=input_.added_by,
        )
        await self._membership_repository.add(membership)
        await self._event_publisher.publish([member_added], correlation_id=correlation_id)

        return membership
