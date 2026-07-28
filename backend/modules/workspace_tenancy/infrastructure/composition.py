"""Composition root for this module: wires infrastructure adapters into use
cases for a given, already-open session. Reused by tests and, once built,
by the FastAPI dependency-injection layer — dependency wiring lives in
exactly one place, never duplicated per call site (CLAUDE.md's dependency
injection standard).
"""

from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from modules.workspace_tenancy.application.use_cases import (
    AddMemberUseCase,
    CreateWorkspaceUseCase,
    GetWorkspaceUseCase,
    ListWorkspaceMembersUseCase,
)
from modules.workspace_tenancy.infrastructure.adapters import (
    OutboxEventPublisherAdapter,
    SessionTenantContext,
)
from modules.workspace_tenancy.infrastructure.query_service import WorkspaceQueryService
from modules.workspace_tenancy.infrastructure.repositories import (
    SqlAlchemyMembershipRepository,
    SqlAlchemyWorkspaceRepository,
)
from signora_platform.event_bus import PostgresOutboxEventPublisher


@dataclass(frozen=True)
class WorkspaceTenancyUseCases:
    create_workspace: CreateWorkspaceUseCase
    add_member: AddMemberUseCase
    get_workspace: GetWorkspaceUseCase
    list_workspace_members: ListWorkspaceMembersUseCase


def build_use_cases(session: AsyncSession) -> WorkspaceTenancyUseCases:
    workspace_repository = SqlAlchemyWorkspaceRepository(session)
    membership_repository = SqlAlchemyMembershipRepository(session)
    tenant_context = SessionTenantContext(session)
    event_publisher = OutboxEventPublisherAdapter(session, delegate=PostgresOutboxEventPublisher())

    return WorkspaceTenancyUseCases(
        create_workspace=CreateWorkspaceUseCase(
            workspace_repository=workspace_repository,
            membership_repository=membership_repository,
            tenant_context=tenant_context,
            event_publisher=event_publisher,
        ),
        add_member=AddMemberUseCase(
            workspace_repository=workspace_repository,
            membership_repository=membership_repository,
            event_publisher=event_publisher,
        ),
        get_workspace=GetWorkspaceUseCase(workspace_repository=workspace_repository),
        list_workspace_members=ListWorkspaceMembersUseCase(
            workspace_repository=workspace_repository,
            membership_repository=membership_repository,
        ),
    )


def build_query_service(session: AsyncSession) -> WorkspaceQueryService:
    """Wires the one synchronous, read-only interface other modules are
    permitted to call directly (docs/architecture/05-module-dependencies.md).
    """
    return WorkspaceQueryService(session)
