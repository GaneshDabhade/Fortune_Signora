from dataclasses import dataclass
from uuid import UUID

from modules.workspace_tenancy.application.ports import WorkspaceRepository
from modules.workspace_tenancy.domain.entities import Workspace
from modules.workspace_tenancy.domain.exceptions import WorkspaceNotFoundError


@dataclass(frozen=True)
class GetWorkspaceInput:
    workspace_id: UUID


class GetWorkspaceUseCase:
    def __init__(self, *, workspace_repository: WorkspaceRepository) -> None:
        self._workspace_repository = workspace_repository

    async def execute(self, input_: GetWorkspaceInput) -> Workspace:
        workspace = await self._workspace_repository.get(input_.workspace_id)
        if workspace is None:
            raise WorkspaceNotFoundError(input_.workspace_id)
        return workspace
