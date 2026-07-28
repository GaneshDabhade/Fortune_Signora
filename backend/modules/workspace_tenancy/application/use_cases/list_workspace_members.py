from dataclasses import dataclass
from uuid import UUID

from modules.workspace_tenancy.application.ports import MembershipRepository, WorkspaceRepository
from modules.workspace_tenancy.domain.entities import Membership
from modules.workspace_tenancy.domain.exceptions import WorkspaceNotFoundError


@dataclass(frozen=True)
class ListWorkspaceMembersInput:
    workspace_id: UUID


class ListWorkspaceMembersUseCase:
    def __init__(
        self,
        *,
        workspace_repository: WorkspaceRepository,
        membership_repository: MembershipRepository,
    ) -> None:
        self._workspace_repository = workspace_repository
        self._membership_repository = membership_repository

    async def execute(self, input_: ListWorkspaceMembersInput) -> list[Membership]:
        workspace = await self._workspace_repository.get(input_.workspace_id)
        if workspace is None:
            raise WorkspaceNotFoundError(input_.workspace_id)
        return await self._membership_repository.list_for_workspace(input_.workspace_id)
