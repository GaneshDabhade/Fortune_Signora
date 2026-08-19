"""Composition root for this module: wires infrastructure adapters into use
cases for a given, already-open session. Reused by tests and, once built,
by the FastAPI dependency-injection layer — dependency wiring lives in
exactly one place, never duplicated per call site (CLAUDE.md's dependency
injection standard).
"""

from dataclasses import dataclass
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from modules.workspace_tenancy.application.capability_use_cases import (
    AssignCapabilityRole,
    CreateCapabilityRole,
    EffectivePermissions,
    HeldCapabilityRoles,
    ListCapabilityRoles,
    RenameCapabilityRole,
)
from modules.workspace_tenancy.application.use_cases.workspace_slug import (
    CheckWorkspaceSlugUseCase,
)
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
from modules.workspace_tenancy.application.use_cases.last_used_workspace import (
    RecordWorkspaceEntry,
)
from modules.workspace_tenancy.application.use_cases.leave_workspace import LeaveWorkspace
from modules.workspace_tenancy.application.use_cases.onboarding import (
    AdvanceOnboardingUseCase,
    ChooseGoalsUseCase,
    ConfirmCompanyUseCase,
    DescribePersonUseCase,
    FinishOnboardingUseCase,
    GetOnboardingUseCase,
    SkipOnboardingUseCase,
    StartOnboardingUseCase,
)
from modules.workspace_tenancy.application.use_cases.preferences import (
    ChangePreferencesUseCase,
    AcknowledgeSetupCompleteUseCase,
    ChooseHomeLayoutUseCase,
    DismissFirstRunUseCase,
    GetPreferencesUseCase,
    SkipInviteUseCase,
)
from modules.workspace_tenancy.application.use_cases.remove_member import RemoveMember
from modules.workspace_tenancy.application.use_cases.saved_views import (
    DeclareSavedViewUseCase,
    GetSavedViewUseCase,
    ListSavedViewsUseCase,
    RetireSavedViewUseCase,
    ReviseSavedViewUseCase,
)
from modules.workspace_tenancy.application.notify import Notify
from modules.workspace_tenancy.application.use_cases.transfer_ownership import TransferOwnership
from modules.workspace_tenancy.domain.entities import WorkspaceRole
from modules.workspace_tenancy.domain.notification import NotificationChannelRegistry
from modules.workspace_tenancy.infrastructure.adapters import (
    OutboxEventPublisherAdapter,
    SessionTenantContext,
)
from modules.workspace_tenancy.infrastructure.capability_repository import (
    SqlCapabilityRepository,
)
from modules.workspace_tenancy.infrastructure.delivery import ConsoleInvitationDelivery
from modules.workspace_tenancy.infrastructure.in_app_channel import InAppNotificationChannel
from modules.workspace_tenancy.infrastructure.query_service import WorkspaceQueryService
from modules.workspace_tenancy.infrastructure.repositories import (
    SqlAlchemyInvitationRepository,
    SqlAlchemyMembershipRepository,
    SqlAlchemyNotificationRepository,
    SqlAlchemyOnboardingRunRepository,
    SqlAlchemyPersonPreferencesRepository,
    SqlAlchemyRecentlyViewedRepository,
    SqlAlchemyRoleChangeLog,
    SqlAlchemySavedViewRepository,
    SqlAlchemyWorkspaceRepository,
)
from modules.workspace_tenancy.infrastructure.saved_view_service import SavedViewService
from modules.workspace_tenancy.application.use_cases.recently_viewed import (
    RecentRecordsUseCase,
    RecordViewUseCase,
)
from modules.workspace_tenancy.infrastructure.settings import load_tenancy_settings
from signora_platform.authorization import CasbinAuthorizer
from signora_platform.event_bus import PostgresOutboxEventPublisher


@dataclass(frozen=True)
class WorkspaceTenancyUseCases:
    create_workspace: CreateWorkspaceUseCase
    check_workspace_slug: CheckWorkspaceSlugUseCase
    add_member: AddMemberUseCase
    accept_invitation: AcceptInvitationUseCase
    get_workspace: GetWorkspaceUseCase
    list_workspace_members: ListWorkspaceMembersUseCase
    list_user_workspaces: ListUserWorkspacesUseCase
    invite_member: InviteMember
    list_invitations: ListInvitations
    revoke_invitation: RevokeInvitation
    leave_workspace: LeaveWorkspace
    remove_member: RemoveMember
    resend_invitation: ResendInvitation
    change_role: ChangeRole
    transfer_ownership: TransferOwnership
    declare_saved_view: DeclareSavedViewUseCase
    revise_saved_view: ReviseSavedViewUseCase
    retire_saved_view: RetireSavedViewUseCase
    list_saved_views: ListSavedViewsUseCase
    get_saved_view: GetSavedViewUseCase
    start_onboarding: StartOnboardingUseCase
    get_onboarding: GetOnboardingUseCase
    advance_onboarding: AdvanceOnboardingUseCase
    confirm_company: ConfirmCompanyUseCase
    describe_person: DescribePersonUseCase
    choose_goals: ChooseGoalsUseCase
    finish_onboarding: FinishOnboardingUseCase
    skip_onboarding: SkipOnboardingUseCase
    get_preferences: GetPreferencesUseCase
    change_preferences: ChangePreferencesUseCase
    acknowledge_setup_complete: AcknowledgeSetupCompleteUseCase
    #: 🔴 **Home §10's *Customise* drawer** — one composition's arrangement.
    choose_home_layout: ChooseHomeLayoutUseCase
    #: 🔴 **D-196's mechanism finally has a caller** — Home hierarchy 2, Entry rule 12.
    record_entry: RecordWorkspaceEntry
    dismiss_first_run: DismissFirstRunUseCase
    skip_invite: SkipInviteUseCase
    record_view: RecordViewUseCase
    recent_records: RecentRecordsUseCase


def build_use_cases(session: AsyncSession) -> WorkspaceTenancyUseCases:
    workspace_repository = SqlAlchemyWorkspaceRepository(session)
    membership_repository = SqlAlchemyMembershipRepository(session)
    invitation_repository = SqlAlchemyInvitationRepository(session)
    saved_view_repository = SqlAlchemySavedViewRepository(session)
    onboarding_repository = SqlAlchemyOnboardingRunRepository(session)
    preferences_repository = SqlAlchemyPersonPreferencesRepository(session)
    recently_viewed_repository = SqlAlchemyRecentlyViewedRepository(session)
    # 📁 Session Continuity U-01 — the window is configuration.
    tenancy_settings = load_tenancy_settings()
    tenant_context = SessionTenantContext(session)
    # **Constructed here, at the composition root**, from the module's own
    # settings rather than from `os.environ` anywhere downstream (§6, §20b).
    delivery = ConsoleInvitationDelivery(app_url=tenancy_settings.app_url)
    event_publisher = OutboxEventPublisherAdapter(session, delegate=PostgresOutboxEventPublisher())

    return WorkspaceTenancyUseCases(
        create_workspace=CreateWorkspaceUseCase(
            workspace_repository=workspace_repository,
            membership_repository=membership_repository,
            tenant_context=tenant_context,
            event_publisher=event_publisher,
        ),
        check_workspace_slug=CheckWorkspaceSlugUseCase(
            workspace_repository=workspace_repository,
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
        leave_workspace=LeaveWorkspace(memberships=membership_repository),
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
        declare_saved_view=DeclareSavedViewUseCase(
            workspaces=workspace_repository, saved_views=saved_view_repository
        ),
        revise_saved_view=ReviseSavedViewUseCase(
            workspaces=workspace_repository, saved_views=saved_view_repository
        ),
        retire_saved_view=RetireSavedViewUseCase(
            workspaces=workspace_repository, saved_views=saved_view_repository
        ),
        list_saved_views=ListSavedViewsUseCase(
            workspaces=workspace_repository, saved_views=saved_view_repository
        ),
        get_saved_view=GetSavedViewUseCase(
            workspaces=workspace_repository, saved_views=saved_view_repository
        ),
        # ⚡ **Only `start` needs the workspace repository.** Every other
        # onboarding use case loads the run, and a run existing is already
        # proof the workspace did — asking again would be a second check of
        # something the first one settled.
        start_onboarding=StartOnboardingUseCase(
            workspaces=workspace_repository, runs=onboarding_repository
        ),
        get_onboarding=GetOnboardingUseCase(runs=onboarding_repository),
        advance_onboarding=AdvanceOnboardingUseCase(runs=onboarding_repository),
        confirm_company=ConfirmCompanyUseCase(runs=onboarding_repository),
        describe_person=DescribePersonUseCase(runs=onboarding_repository),
        choose_goals=ChooseGoalsUseCase(runs=onboarding_repository),
        finish_onboarding=FinishOnboardingUseCase(runs=onboarding_repository),
        skip_onboarding=SkipOnboardingUseCase(runs=onboarding_repository),
        get_preferences=GetPreferencesUseCase(preferences=preferences_repository),
        change_preferences=ChangePreferencesUseCase(preferences=preferences_repository),
        record_entry=RecordWorkspaceEntry(
            preferences=preferences_repository,
            # 📁 **Rule 21's source**, read at entry — the same append-only log
            # `change_role` writes to.
            history=SqlAlchemyRoleChangeLog(session),
        ),
        acknowledge_setup_complete=AcknowledgeSetupCompleteUseCase(
            preferences=preferences_repository
        ),
        choose_home_layout=ChooseHomeLayoutUseCase(preferences=preferences_repository),
        dismiss_first_run=DismissFirstRunUseCase(preferences=preferences_repository),
        skip_invite=SkipInviteUseCase(preferences=preferences_repository),
        record_view=RecordViewUseCase(recently_viewed=recently_viewed_repository),
        recent_records=RecentRecordsUseCase(
            recently_viewed=recently_viewed_repository,
            retention_days=tenancy_settings.recents_retention_days,
        ),
    )


def build_saved_view_service(session: AsyncSession) -> SavedViewService:
    """The `public/` reader and writer, for consumers outside this module.

    ⚡ **A parameter nowhere and a construction here**, unlike the ports this
    module *consumes*: `SavedViewReader` and `SavedViewWriter` are
    `workspace_tenancy`'s own contract, so building the adapter behind them is
    this composition root's job rather than another lane's — which is the
    distinction [C-238](../../../../docs/LANE_COORDINATION.md) was raised
    about, seen from the owning side.
    """
    return SavedViewService(SqlAlchemySavedViewRepository(session))


def build_query_service(session: AsyncSession) -> WorkspaceQueryService:
    """Wires the one synchronous, read-only interface other modules are
    permitted to call directly (docs/architecture/05-module-dependencies.md).
    """
    return WorkspaceQueryService(session)


@dataclass(frozen=True, slots=True)
class CapabilityUseCases:
    """ADR-0410's six, built together — TASK-1479 slice ⓸."""

    list_roles: ListCapabilityRoles
    create_role: CreateCapabilityRole
    rename_role: RenameCapabilityRole
    assign_role: AssignCapabilityRole
    effective_permissions: EffectivePermissions
    held_roles: HeldCapabilityRoles


class _MembershipReaderAdapter:
    """`MembershipReader`, over this module's own query service.

    ⛔ **Declared in `application/` as a Protocol and satisfied here**, so the
    use cases depend on a shape rather than on a concrete reader (§6).
    """

    def __init__(self, session: AsyncSession) -> None:
        self._service = WorkspaceQueryService(session)

    async def role_of(self, workspace_id: UUID, user_id: UUID) -> WorkspaceRole | None:
        membership = await self._service.get_membership(workspace_id, user_id)
        return None if membership is None else WorkspaceRole(membership.role)


def build_capability_use_cases(session: AsyncSession) -> CapabilityUseCases:
    """⚡ **The authorizer is constructed here and nowhere downstream.**

    📁 `EffectivePermissions` reads the authorization layer, so it needs the
    same enforcer the request path uses — **and a second one built with
    different paths would be the two-sources-of-truth defect the whole slice
    exists to avoid.**
    """
    capabilities = SqlCapabilityRepository(session)
    memberships = _MembershipReaderAdapter(session)
    return CapabilityUseCases(
        list_roles=ListCapabilityRoles(capabilities=capabilities),
        create_role=CreateCapabilityRole(capabilities=capabilities),
        rename_role=RenameCapabilityRole(capabilities=capabilities),
        assign_role=AssignCapabilityRole(capabilities=capabilities, memberships=memberships),
        effective_permissions=EffectivePermissions(
            capabilities=capabilities, memberships=memberships, authorizer=CasbinAuthorizer()
        ),
        held_roles=HeldCapabilityRoles(capabilities=capabilities),
    )


def build_notification_channels(session: AsyncSession) -> NotificationChannelRegistry:
    """**Which channels this deployment can actually reach.**

    📁 **[TASK-495](../../../docs/BACKLOG.md)**, shaped after
    `ai_platform/infrastructure/composition.py`'s `build_provider_registry` —
    ✅ *"An adapter is registered only when its credentials exist"* — 🔴 **and
    the half that is easy to lose: *"There is deliberately no fallback between
    them."***

    ⛔ **`Channel` names four members and this registers ONE.** ⚡ **The other
    three are not missing features; they are what makes the refusal
    expressible** — a request for `EMAIL` fails legibly here rather than
    arriving in-app and reporting that it reached an inbox.

    ⚠️ **In-app needs no credential and is registered unconditionally**, which
    is the one channel of which that is true: it writes a row in Signora's own
    database, so *"is it configured"* has no separate answer. 📁 **Novu is
    [ADR-0017](../../../docs/architecture/adr/0017-notifications.md)'s and
    arrives behind `bought_infra_adapters/` when a channel it carries is
    actually requested** — ⛔ **an adapter written for a call nobody makes is
    the speculative abstraction §6 forbids.**
    """
    registry = NotificationChannelRegistry()
    registry.register(InAppNotificationChannel(SqlAlchemyNotificationRepository(session)))
    return registry


def build_notifier(session: AsyncSession) -> Notify:
    """**The one trigger every module calls.**

    ⚡ **Returned as the concrete use case rather than as `Notifier`** so
    `mypy` resolves the structural conformance at every call site that annotates
    the port — 📁 the same reason `test_notification_read_is_per_person.py`
    returns its repository AS the protocol instead of asking `hasattr`.
    """
    return Notify(channels=build_notification_channels(session))
