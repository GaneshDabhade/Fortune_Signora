from dataclasses import dataclass
from uuid import UUID

from sqlalchemy.exc import IntegrityError

from modules.workspace_tenancy.application.ports import (
    EventPublisher,
    MembershipRepository,
    TenantContext,
    WorkspaceRepository,
)
from modules.workspace_tenancy.domain.entities import Membership, Workspace, WorkspaceRole
from modules.workspace_tenancy.domain.exceptions import WorkspaceSlugTakenError


@dataclass(frozen=True)
class CreateWorkspaceInput:
    name: str
    #: 📁 Screen `03`'s URL field. ⛔ **Required, and not derived from `name`
    #: here** — the client suggests, a person edits, and the value stored is
    #: the one they accepted. **Deriving it a second time in this layer would
    #: be two producers of one permanent identifier** ([§2](../../../../CLAUDE.md)).
    slug: str
    created_by: UUID
    #: The founder's verified address, from the token. **Recorded so the roster
    #: can name the one person who is certainly in it** — every later member
    #: gets theirs from the invitation they accepted.
    created_by_email: str | None = None


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
            name=input_.name, slug=input_.slug, created_by=input_.created_by
        )
        # ⚡ **Asked before inserting, so the common case gets the error the
        # design wrote** — *"That URL was taken while you were typing."*
        # ⛔ **This is NOT what makes the slug unique**: the unique constraint
        # is, and the window between this check and the insert is real. **A
        # caller that lost that race gets the same error from the constraint**,
        # which is why `WorkspaceSlugTakenError` is raised in both places
        # rather than only here.
        if await self._workspace_repository.slug_is_taken(workspace.slug):
            raise WorkspaceSlugTakenError(workspace.slug)

        try:
            await self._workspace_repository.add(workspace)
        except IntegrityError as collision:
            # ⛔ **The race, closed.** 📁 [§2](../../../../CLAUDE.md): *a guard
            # that cannot fail is not protection* — and the check above CAN
            # fail to catch this, so the constraint's own refusal is translated
            # rather than left to surface as a 500.
            raise WorkspaceSlugTakenError(workspace.slug) from collision

        await self._tenant_context.activate_workspace(workspace.id)

        membership, member_added = Membership.create(
            workspace_id=workspace.id,
            user_id=input_.created_by,
            role=WorkspaceRole.OWNER,
            created_by=input_.created_by,
            causation_id=workspace_created.event_id,
            member_email=input_.created_by_email,
        )
        await self._membership_repository.add(membership)

        await self._event_publisher.publish(
            [workspace_created, member_added], correlation_id=correlation_id
        )

        return CreateWorkspaceResult(workspace=workspace, founding_membership=membership)
