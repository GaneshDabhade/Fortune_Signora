from dataclasses import dataclass
from uuid import UUID

from modules.workspace_tenancy.application.ports import MembershipRepository, WorkspaceRepository
from modules.workspace_tenancy.domain.entities import Membership
from modules.workspace_tenancy.domain.exceptions import WorkspaceNotFoundError
from signora_platform.pagination import CursorPosition, split_overfetched


@dataclass(frozen=True)
class ListWorkspaceMembersInput:
    workspace_id: UUID
    limit: int
    after: CursorPosition | None


@dataclass(frozen=True)
class ListWorkspaceMembersResult:
    members: list[Membership]
    has_more: bool


class ListWorkspaceMembersUseCase:
    def __init__(
        self,
        *,
        workspace_repository: WorkspaceRepository,
        membership_repository: MembershipRepository,
    ) -> None:
        self._workspace_repository = workspace_repository
        self._membership_repository = membership_repository

    async def execute(self, input_: ListWorkspaceMembersInput) -> ListWorkspaceMembersResult:
        # Confirms the workspace is visible to this caller before listing.
        # Under RLS a workspace the caller cannot see reads as absent, so
        # this raises "not found" rather than distinguishing "forbidden" —
        # which is what keeps workspace ids non-enumerable (11-tenancy.md).
        workspace = await self._workspace_repository.get(input_.workspace_id)
        if workspace is None:
            raise WorkspaceNotFoundError(input_.workspace_id)

        rows = await self._membership_repository.list_page_for_workspace(
            input_.workspace_id, limit=input_.limit + 1, after=input_.after
        )
        members, has_more = split_overfetched(rows, limit=input_.limit)
        return ListWorkspaceMembersResult(members=members, has_more=has_more)
