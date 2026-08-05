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
    ListUserWorkspacesUseCase,
    ListWorkspaceMembersUseCase,
)
from modules.workspace_tenancy.application.use_cases.accept_invitation import (
    AcceptInvitationUseCase,
)
from modules.workspace_tenancy.application.use_cases.change_role import ChangeRole
from modules.workspace_tenancy.application.use_cases.invite_member import (
    InviteMember,
    ListInvitations,
    ResendInvitation,
    RevokeInvitation,
)
from modules.workspace_tenancy.application.use_cases.remove_member import RemoveMember
from modules.workspace_tenancy.application.use_cases.transfer_ownership import TransferOwnership
from modules.workspace_tenancy.infrastructure.adapters import (
    OutboxEventPublisherAdapter,
    SessionTenantContext,
)
from modules.workspace_tenancy.infrastructure.delivery import ConsoleInvitationDelivery
from modules.workspace_tenancy.infrastructure.query_service import WorkspaceQueryService
from modules.workspace_tenancy.infrastructure.repositories import (
    SqlAlchemyInvitationRepository,
    SqlAlchemyMembershipRepository,
    SqlAlchemyRoleChangeLog,
    SqlAlchemyWorkspaceRepository,
)
from modules.workspace_tenancy.infrastructure.settings import load_tenancy_settings
from signora_platform.event_bus import PostgresOutboxEventPublisher


@dataclass(frozen=True)
class WorkspaceTenancyUseCases:
    create_workspace: CreateWorkspaceUseCase
    add_member: AddMemberUseCase
    accept_invitation: AcceptInvitationUseCase
    get_workspace: GetWorkspaceUseCase
    list_workspace_members: ListWorkspaceMembersUseCase
    list_user_workspaces: ListUserWorkspacesUseCase
    invite_member: InviteMember
    list_invitations: ListInvitations
    revoke_invitation: RevokeInvitation
    remove_member: RemoveMember
    resend_invitation: ResendInvitation
    change_role: ChangeRole
    transfer_ownership: TransferOwnership


def build_use_cases(session: AsyncSession) -> WorkspaceTenancyUseCases:
    workspace_repository = SqlAlchemyWorkspaceRepository(session)
    membership_repository = SqlAlchemyMembershipRepository(session)
    invitation_repository = SqlAlchemyInvitationRepository(session)
    tenant_context = SessionTenantContext(session)
    # **Constructed here, at the composition root**, from the module's own
    # settings rather than from `os.environ` anywhere downstream (§6, §20b).
    delivery = ConsoleInvitationDelivery(app_url=load_tenancy_settings().app_url)
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
        # **Reachable only from the acceptance endpoint**, which is the only
        # handler that establishes workspace context without membership
        # (C-208). It is built here like everything else; what makes it a named
        # single-purpose path is `infrastructure/acceptance.py`, not this line.
        accept_invitation=AcceptInvitationUseCase(
            invitations=invitation_repository,
            memberships=membership_repository,
            event_publisher=event_publisher,
        ),
        get_workspace=GetWorkspaceUseCase(workspace_repository=workspace_repository),
        list_workspace_members=ListWorkspaceMembersUseCase(
            workspace_repository=workspace_repository,
            membership_repository=membership_repository,
        ),
        list_user_workspaces=ListUserWorkspacesUseCase(workspace_repository=workspace_repository),
        invite_member=InviteMember(
            workspaces=workspace_repository,
            memberships=membership_repository,
            invitations=invitation_repository,
            delivery=delivery,
        ),
        list_invitations=ListInvitations(invitations=invitation_repository),
        revoke_invitation=RevokeInvitation(invitations=invitation_repository),
        remove_member=RemoveMember(memberships=membership_repository),
        transfer_ownership=TransferOwnership(
            memberships=membership_repository,
            history=SqlAlchemyRoleChangeLog(session),
        ),
        change_role=ChangeRole(
            memberships=membership_repository,
            history=SqlAlchemyRoleChangeLog(session),
        ),
        resend_invitation=ResendInvitation(
            workspaces=workspace_repository,
            invitations=invitation_repository,
            delivery=delivery,
        ),
    )


def build_query_service(session: AsyncSession) -> WorkspaceQueryService:
    """Wires the one synchronous, read-only interface other modules are
    permitted to call directly (docs/architecture/05-module-dependencies.md).
    """
    return WorkspaceQueryService(session)
