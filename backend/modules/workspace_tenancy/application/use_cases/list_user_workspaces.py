from dataclasses import dataclass

from modules.workspace_tenancy.application.ports import WorkspaceRepository
from modules.workspace_tenancy.domain.entities import Workspace
from signora_platform.pagination import CursorPosition, split_overfetched


@dataclass(frozen=True)
class ListUserWorkspacesInput:
    limit: int
    after: CursorPosition | None


@dataclass(frozen=True)
class ListUserWorkspacesResult:
    workspaces: list[Workspace]
    has_more: bool


class ListUserWorkspacesUseCase:
    """Lists the workspaces the current caller belongs to.

    Runs under a user-scoped session with no workspace context: the
    ``workspace`` table's RLS policy is membership-based on ``app.user_id``,
    so the database itself restricts the result to the caller's workspaces.
    There is no `user_id` argument because the caller cannot ask about
    anyone else.
    """

    def __init__(self, *, workspace_repository: WorkspaceRepository) -> None:
        self._workspace_repository = workspace_repository

    async def execute(self, input_: ListUserWorkspacesInput) -> ListUserWorkspacesResult:
        # Over-fetch by one to determine has_more without a second COUNT.
        rows = await self._workspace_repository.list_visible(
            limit=input_.limit + 1, after=input_.after
        )
        workspaces, has_more = split_overfetched(rows, limit=input_.limit)
        return ListUserWorkspacesResult(workspaces=workspaces, has_more=has_more)
