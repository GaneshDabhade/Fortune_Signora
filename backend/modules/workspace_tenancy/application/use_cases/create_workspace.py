from dataclasses import dataclass
from uuid import UUID

from modules.workspace_tenancy.application.ports import (
    EventPublisher,
    MembershipRepository,
    TenantContext,
    WorkspaceRepository,
)
from modules.workspace_tenancy.domain.entities import Membership, Workspace, WorkspaceRole


@dataclass(frozen=True)
class CreateWorkspaceInput:
    name: str
    created_by: UUID


@dataclass(frozen=True)
class CreateWorkspaceResult:
    workspace: Workspace
    founding_membership: Membership


class CreateWorkspaceUseCase:
    """Creates a workspace and its founding OWNER membership atomically.

    RLS workspace context is activated mid-flow, after the workspace row
    exists (via ``TenantContext``), so the membership insert satisfies the
    standard workspace-scoped RLS policy rather than needing a special case
    — see the bootstrap pattern documented in docs/architecture/11-tenancy.md.
    """

    def __init__(
        self,
        *,
        workspace_repository: WorkspaceRepository,
        membership_repository: MembershipRepository,
        tenant_context: TenantContext,
        event_publisher: EventPublisher,
    ) -> None:
        self._workspace_repository = workspace_repository
        self._membership_repository = membership_repository
        self._tenant_context = tenant_context
        self._event_publisher = event_publisher

    async def execute(
        self, input_: CreateWorkspaceInput, *, correlation_id: UUID
    ) -> CreateWorkspaceResult:
        workspace, workspace_created = Workspace.create(
            name=input_.name, created_by=input_.created_by
        )
        await self._workspace_repository.add(workspace)

        await self._tenant_context.activate_workspace(workspace.id)

        membership, member_added = Membership.create(
            workspace_id=workspace.id,
            user_id=input_.created_by,
            role=WorkspaceRole.OWNER,
            created_by=input_.created_by,
            causation_id=workspace_created.event_id,
        )
        await self._membership_repository.add(membership)

        await self._event_publisher.publish(
            [workspace_created, member_added], correlation_id=correlation_id
        )

        return CreateWorkspaceResult(workspace=workspace, founding_membership=membership)
