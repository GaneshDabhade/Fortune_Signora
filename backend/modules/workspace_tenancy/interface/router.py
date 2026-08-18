"""FastAPI routes for Workspace & Tenancy.

Handlers do three things and nothing else: translate the request into use-case
input, authorize, and translate the result into a response schema. All
business rules live in the application and domain layers; all authentication,
membership verification, and RLS context is established by the dependency
chain before a handler runs (18-authentication.md).
"""

from datetime import UTC, datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Query, Request, status

from modules.workspace_tenancy.application.capability_use_cases import (
    AssignRoleInput,
    CreateRoleInput,
    RenameRoleInput,
)
from modules.workspace_tenancy.application.use_cases import (
    AddMemberInput,
    CreateWorkspaceInput,
    GetWorkspaceInput,
    ListUserWorkspacesInput,
    ListWorkspaceMembersInput,
)
from modules.workspace_tenancy.application.use_cases.accept_invitation import (
    AcceptInvitationInput,
)
from modules.workspace_tenancy.application.use_cases.change_role import ChangeRoleCommand
from modules.workspace_tenancy.application.use_cases.invite_member import InviteMemberCommand
from modules.workspace_tenancy.application.use_cases.leave_workspace import LeaveWorkspaceCommand
from modules.workspace_tenancy.application.use_cases.onboarding import (
    AdvanceOnboardingInput,
    ChooseGoalsInput,
    ConfirmCompanyInput,
    DescribePersonInput,
    FinishOnboardingInput,
    StartOnboardingInput,
)
from modules.workspace_tenancy.application.use_cases.preferences import ChangePreferencesInput
from modules.workspace_tenancy.application.use_cases.remove_member import RemoveMemberCommand
from modules.workspace_tenancy.application.use_cases.saved_views import (
    DeclareSavedViewInput,
    ListSavedViewsInput,
    RetireSavedViewInput,
    ReviseSavedViewInput,
)
from modules.workspace_tenancy.application.use_cases.transfer_ownership import (
    TransferOwnershipCommand,
)
from modules.workspace_tenancy.domain.capability import NotAWorkspaceMemberError
from modules.workspace_tenancy.domain.entities import WorkspaceRole
from modules.workspace_tenancy.domain.exceptions import SavedViewNotFoundError
from modules.workspace_tenancy.domain.onboarding import Answer, CompanySizeBand, Role
from modules.workspace_tenancy.infrastructure.acceptance import accepting_workspace
from modules.workspace_tenancy.infrastructure.composition import (
    build_capability_use_cases,
    build_query_service,
    build_use_cases,
)
from modules.workspace_tenancy.infrastructure.repositories import (
    SqlAlchemyNotificationReadRepository,
    SqlAlchemyNotificationRepository,
)
from modules.workspace_tenancy.interface.schemas import (
    RecordViewRequest,
    ViewedRecordResponse,
    AddMemberRequest,
    AdvanceOnboardingRequest,
    AnswerPayload,
    AssignCapabilityRoleRequest,
    CapabilityRoleListResponse,
    CapabilityRoleResponse,
    ChangePreferencesRequest,
    ChangeRoleRequest,
    ChooseGoalsRequest,
    ConfirmCompanyRequest,
    CreateCapabilityRoleRequest,
    CreateWorkspaceRequest,
    DescribePersonRequest,
    EffectivePermissionsResponse,
    HeldCapabilityRolesResponse,
    HistoryEntryResponse,
    InvitationResponse,
    InviteMemberRequest,
    MarkNotificationsReadRequest,
    NotificationFeedResponse,
    NotificationResponse,
    MembershipResponse,
    ViewerRoleResponse,
    OnboardingRunResponse,
    PreferencesResponse,
    RemoveMemberRequest,
    RenameCapabilityRoleRequest,
    ReviseViewRequest,
    RoleChangePreviewResponse,
    SavedViewResponse,
    SaveViewRequest,
    TransferOwnershipRequest,
    UnreadBadgeResponse,
    SlugAvailabilityResponse,
    WorkspaceResponse,
)
from signora_platform.api import (
    CurrentUser,
    CurrentWorkspace,
    CursorPage,
    correlation_id_of,
)
from signora_platform.authorization import Action, Resource
from signora_platform.pagination import (
    DEFAULT_PAGE_LIMIT,
    MAX_PAGE_LIMIT,
    CursorPosition,
    decode_cursor,
    encode_cursor,
)

router = APIRouter(tags=["workspaces"])

LimitParam = Annotated[int, Query(ge=1, le=MAX_PAGE_LIMIT)]
CursorParam = Annotated[str | None, Query()]


def _position_after(cursor: str | None) -> CursorPosition | None:
    return decode_cursor(cursor) if cursor else None


def _next_cursor(
    items: list[WorkspaceResponse] | list[MembershipResponse] | list[SavedViewResponse],
    has_more: bool,
) -> str | None:
    """The cursor for the following page, or ``None`` on the last page.

    Derived from the final item actually returned, so it always points at a
    real keyset position rather than an estimate.
    """
    if not has_more or not items:
        return None
    last = items[-1]
    return encode_cursor(CursorPosition(created_at=last.created_at, id=last.id))


@router.post(
    "/workspaces",
    status_code=status.HTTP_201_CREATED,
    response_model=WorkspaceResponse,
    summary="Create a workspace",
)
async def create_workspace(
    request: Request, body: CreateWorkspaceRequest, context: CurrentUser
) -> WorkspaceResponse:
    """Creates a workspace and makes the caller its owner.

    Takes the *user*-scoped context, not the workspace-scoped one: there is
    no workspace to be a member of yet. This is the bootstrap case the split
    RLS policies on the ``workspace`` table exist to support (11-tenancy.md);
    the use case activates workspace context mid-transaction once the row
    exists. No Casbin check applies — any authenticated user may create a
    workspace, and plan limits are a separate, future concern.
    """
    result = await build_use_cases(context.session).create_workspace.execute(
        CreateWorkspaceInput(
            name=body.name,
            slug=body.slug,
            created_by=context.principal.user_id,
            created_by_email=context.principal.email,
        ),
        correlation_id=correlation_id_of(request),
    )
    return WorkspaceResponse.from_domain(result.workspace)


@router.get(
    "/workspaces/slug-available",
    response_model=SlugAvailabilityResponse,
    summary="Whether a workspace URL is free",
)
async def check_workspace_slug(slug: str, context: CurrentUser) -> SlugAvailabilityResponse:
    """📁 Screen `03` — *"Checked as you type, 300ms after you stop."*

    ⛔ **Declared BEFORE `GET /workspaces/{workspace_id}`**, or FastAPI matches
    `slug-available` as a workspace id and answers `422`. **Route order is
    behaviour here, not style.**

    ⚡ **User-scoped context, like `create_workspace` above** — there is no
    workspace to be a member of yet, and any signed-in person may create one.
    ⛔ **No Casbin check applies for the same reason**, and the response is a
    boolean over one column: it reveals exactly what pressing *Create* would
    reveal a moment later, and nothing more.
    """
    result = await build_use_cases(context.session).check_workspace_slug.execute(slug)
    return SlugAvailabilityResponse(
        slug=result.slug, available=result.available, reason=result.reason
    )


@router.get(
    "/workspaces",
    response_model=CursorPage[WorkspaceResponse],
    summary="List the workspaces the caller belongs to",
)
async def list_workspaces(
    context: CurrentUser,
    limit: LimitParam = DEFAULT_PAGE_LIMIT,
    cursor: CursorParam = None,
) -> CursorPage[WorkspaceResponse]:
    """Scoped by RLS to the caller's own memberships — there is no way to ask
    about another user's workspaces."""
    result = await build_use_cases(context.session).list_user_workspaces.execute(
        ListUserWorkspacesInput(limit=limit, after=_position_after(cursor))
    )
    items = [WorkspaceResponse.from_domain(w) for w in result.workspaces]
    return CursorPage(
        items=items, next_cursor=_next_cursor(items, result.has_more), has_more=result.has_more
    )


@router.get(
    "/workspaces/{workspace_id}",
    response_model=WorkspaceResponse,
    summary="Get a workspace",
)
async def get_workspace(context: CurrentWorkspace) -> WorkspaceResponse:
    context.authorize(Resource.WORKSPACE, Action.READ)
    workspace = await build_use_cases(context.session).get_workspace.execute(
        GetWorkspaceInput(workspace_id=context.workspace_id)
    )
    return WorkspaceResponse.from_domain(workspace)


@router.get(
    "/workspaces/{workspace_id}/members",
    response_model=CursorPage[MembershipResponse],
    summary="List workspace members",
)
async def list_members(
    context: CurrentWorkspace,
    limit: LimitParam = DEFAULT_PAGE_LIMIT,
    cursor: CursorParam = None,
) -> CursorPage[MembershipResponse]:
    context.authorize(Resource.MEMBER, Action.READ)
    result = await build_use_cases(context.session).list_workspace_members.execute(
        ListWorkspaceMembersInput(
            workspace_id=context.workspace_id, limit=limit, after=_position_after(cursor)
        )
    )
    items = [MembershipResponse.from_domain(m) for m in result.members]
    return CursorPage(
        items=items, next_cursor=_next_cursor(items, result.has_more), has_more=result.has_more
    )


@router.get(
    "/workspaces/{workspace_id}/members/me",
    response_model=ViewerRoleResponse,
    summary="The caller's own role in this workspace",
)
async def get_my_role(context: CurrentWorkspace) -> ViewerRoleResponse:
    """What the caller is here, without reading a page of who else is.

    🔴 **[B-284](../../../../docs/BUGS.md).** The shell asked this question of
    `GET .../members` and searched the first page for itself. **A page is 50
    rows, ordered newest-first**, so in a workspace with 51 members the oldest
    one could not find themselves — and the rail, which locks only on a
    *resolved* denial, told an owner that Settings *"requires an owner."*

    ✅ **Authorized like every other route** — 📁 §7, *"authorization for every
    endpoint is a Casbin policy check"*, **and [46](../../../../docs/architecture/46-team-management.md)
    §9 already refused the carve-out this endpoint would otherwise want.**
    ⚡ **`member:read` is the right grant rather than a convenient one**: both
    roles hold it, and *reading your own standing* is the narrowest case of
    reading membership rather than a different permission.

    ⚠️ **It is a self-directed operation, which [C-207](../../../../docs/LANE_COORDINATION.md)
    showed Casbin cannot express** — the tuple carries the caller's *role*, not
    their identity. ⛔ **That does not bite here.** C-207's problem was a grant
    that would have had to *overstate* (*"members may remove members"* to allow
    *"a member may remove themselves"*). **`member:read` overstates nothing**:
    a member may already read the roster, so being allowed to read one row of
    it grants no capability they did not have.

    ✅ **`/me` and not `/{user_id}`**, so no caller can spell another person's
    id into it — which is what keeps the grant honest. The question this
    endpoint answers is only ever about the person asking it.
    """
    context.authorize(Resource.MEMBER, Action.READ)
    return ViewerRoleResponse(
        workspace_id=context.workspace_id,
        user_id=context.principal.user_id,
        role=WorkspaceRole(context.role),
    )


@router.post(
    "/workspaces/{workspace_id}/members",
    status_code=status.HTTP_201_CREATED,
    response_model=MembershipResponse,
    summary="Add a member to a workspace",
)
async def add_member(
    request: Request, context: CurrentWorkspace, body: AddMemberRequest
) -> MembershipResponse:
    context.authorize(Resource.MEMBER, Action.ADD)
    membership = await build_use_cases(context.session).add_member.execute(
        AddMemberInput(
            workspace_id=context.workspace_id,
            user_id=body.user_id,
            role=body.role,
            added_by=context.principal.user_id,
        ),
        correlation_id=correlation_id_of(request),
    )
    return MembershipResponse.from_domain(membership)


@router.get(
    "/workspaces/{workspace_id}/history",
    response_model=CursorPage[HistoryEntryResponse],
    summary="What has happened to this organization",
)
async def organization_history(
    context: CurrentWorkspace,
    limit: LimitParam = DEFAULT_PAGE_LIMIT,
    cursor: CursorParam = None,
) -> CursorPage[HistoryEntryResponse]:
    """*"What happened?"* — in one place, newest first.

    Somebody joined, was invited, was withdrawn, changed role, or was removed.
    **Every fact was already stored**; this is the reading, which is the half
    that could always have been added later — and why the writing was not
    deferred (`CLAUDE.md` §2).

    ⚡ **Cursor-paginated from TASK-443.** It returned every entry there had
    ever been, which is a contract a client cannot work with once a workspace
    has been running a year — and the collection §7 requires to be paged.
    **The keyset is `(occurred_at, source_id)`**, because two things can happen
    in one microsecond and a page boundary between them would drop one.

    **`member:read` authorizes it**, on the reading that already made listing
    members and invitations `member:read`. **Everybody in the organization can
    see it**, deliberately: a history only administrators may read is a history
    that cannot be used to hold administrators accountable.
    """
    context.authorize(Resource.MEMBER, Action.READ)
    entries, has_more = await build_query_service(context.session).organization_history_page(
        context.workspace_id,
        after=decode_cursor(cursor) if cursor else None,
        limit=limit,
    )
    last = entries[-1] if entries and has_more else None
    return CursorPage(
        items=[HistoryEntryResponse.from_domain(entry) for entry in entries],
        next_cursor=(
            encode_cursor(CursorPosition(created_at=last.occurred_at, id=last.source_id))
            if last
            else None
        ),
        has_more=has_more,
    )


@router.get(
    "/workspaces/{workspace_id}/invitations",
    response_model=list[InvitationResponse],
    summary="Who has been invited, and what became of it",
)
async def list_invitations(context: CurrentWorkspace) -> list[InvitationResponse]:
    """*"Who is on their way in, and did anybody not come?"*

    **Every invitation in every state, newest first — including the settled
    ones.** An expired invitation is what tells an administrator somebody was
    invited and never arrived, and a list that quietly omitted it would leave
    them believing a colleague had access.

    **`member:read` authorizes it, and no new grant was needed.** An invitation
    is a deferred membership, and the policy has described reading members since
    M1 — see [46-team-management.md](../../../../docs/architecture/46-team-management.md) §14.

    **Not paginated**, on the same reasoning as the connections list: an
    organization sends a handful of these, not thousands.
    """
    context.authorize(Resource.MEMBER, Action.READ)
    now = datetime.now(UTC)
    invitations = await build_use_cases(context.session).list_invitations.execute(
        context.workspace_id
    )
    return [InvitationResponse.from_domain(i, at=now) for i in invitations]


@router.post(
    "/workspaces/{workspace_id}/invitations",
    status_code=status.HTTP_201_CREATED,
    response_model=InvitationResponse,
    summary="Invite a colleague",
)
async def invite_member(context: CurrentWorkspace, body: InviteMemberRequest) -> InvitationResponse:
    """**The operation that lets an organization grow.**

    Until this existed a workspace was permanently whoever created it:
    `POST /members` takes a `user_id`, and nothing resolves an address to one.

    **Addressed to an email, not a user.** A customer knows a colleague's
    address and must not be asked whether they already have a Signora account,
    how they sign in, or what their identifier is.

    **`member:add` authorizes it.** Inviting *is* adding a member, deferred —
    which is why no policy line was added. Recorded as *sufficient rather than
    fundamental*: the day a role may invite but not remove, the two separate.
    """
    context.authorize(Resource.MEMBER, Action.ADD)
    now = datetime.now(UTC)
    invitation = await build_use_cases(context.session).invite_member.execute(
        InviteMemberCommand(
            workspace_id=context.workspace_id,
            email=body.email,
            role=body.role,
            invited_by=context.principal.user_id,
        ),
        now=now,
    )
    return InvitationResponse.from_domain(invitation, at=now)


@router.post(
    "/workspaces/{workspace_id}/invitations/{invitation_id}/resend",
    response_model=InvitationResponse,
    summary="Send an invitation again",
)
async def resend_invitation(context: CurrentWorkspace, invitation_id: UUID) -> InvitationResponse:
    """**The same invitation, delivered again.**

    Not a new one: the address, the role and the expiry are unchanged, so a
    second row would make *"I already invited them"* and *"I just invited
    them"* indistinguishable — and the live-invitation index would refuse it.

    **Only while it is still waiting.** Re-sending a withdrawn or expired
    invitation would deliver a link that cannot be used, which is worse than
    not sending one.
    """
    context.authorize(Resource.MEMBER, Action.ADD)
    now = datetime.now(UTC)
    invitation = await build_use_cases(context.session).resend_invitation.execute(
        context.workspace_id, invitation_id, now=now
    )
    return InvitationResponse.from_domain(invitation, at=now)


@router.post(
    "/workspaces/{workspace_id}/invitations/{invitation_id}/revoke",
    response_model=InvitationResponse,
    summary="Withdraw an invitation",
)
async def revoke_invitation(context: CurrentWorkspace, invitation_id: UUID) -> InvitationResponse:
    """**Withdraws an offer nobody has acted on.**

    `POST` rather than `DELETE`, because nothing is deleted: the row survives
    with the moment it was withdrawn, which is what makes *"we invited them and
    changed our minds"* readable later.

    **Revocation always wins over an email already opened**, because state is
    checked when somebody accepts and never when the message was sent. There is
    no window.
    """
    context.authorize(Resource.MEMBER, Action.REMOVE)
    now = datetime.now(UTC)
    invitation = await build_use_cases(context.session).revoke_invitation.execute(
        context.workspace_id, invitation_id, now=now
    )
    return InvitationResponse.from_domain(invitation, at=now)


@router.post(
    "/workspaces/{workspace_id}/ownership",
    response_model=list[MembershipResponse],
    summary="Hand this organization over",
)
async def transfer_ownership_endpoint(
    context: CurrentWorkspace, body: TransferOwnershipRequest
) -> list[MembershipResponse]:
    """**One operation, deliberately.**

    Promote-then-demote works and leaves a window in which the organization
    has two owners nobody asked for — permanent if the second step never runs.
    **A transfer that half-happens is worse than one that is refused**, so both
    role changes and both audit rows are one transaction.

    On the workspace, not on a membership: **the thing changing hands is the
    organization**, and neither person is more the subject than the other.
    """
    context.authorize(Resource.MEMBER, Action.ADD)
    outgoing, incoming = await build_use_cases(context.session).transfer_ownership.execute(
        TransferOwnershipCommand(
            workspace_id=context.workspace_id,
            from_membership_id=body.from_membership_id,
            to_membership_id=body.to_membership_id,
            performed_by=context.principal.user_id,
        ),
        now=datetime.now(UTC),
    )
    return [MembershipResponse.from_domain(m) for m in (incoming, outgoing)]


@router.post(
    "/workspaces/{workspace_id}/members/{membership_id}/role",
    response_model=MembershipResponse,
    summary="Change what somebody can do",
)
async def change_role(
    context: CurrentWorkspace, membership_id: UUID, body: ChangeRoleRequest
) -> MembershipResponse:
    """**Organizational authority, not a field.**

    Promoting a colleague hands them the ability to invite, remove and
    administer; demoting one takes it away while they may be mid-task.

    **An owner may demote themselves** when another owner exists — refusing it
    would mean an administrator handing over could not then step back.
    **Demoting the last owner is refused in the domain**, by the same invariant
    that refuses removing them: two ways to reach one failure, refused in one
    place.

    **`member:add` authorizes it**, on the reading that already made inviting
    `member:add` — granting somebody authority in this organization. Recorded
    as *sufficient rather than fundamental*: the day a role may grant
    membership but not administration, the two separate.
    """
    context.authorize(Resource.MEMBER, Action.ADD)
    membership = await build_use_cases(context.session).change_role.execute(
        ChangeRoleCommand(
            workspace_id=context.workspace_id,
            membership_id=membership_id,
            new_role=body.role,
            changed_by=context.principal.user_id,
        ),
        now=datetime.now(UTC),
    )
    return MembershipResponse.from_domain(membership)


@router.post(
    "/workspaces/{workspace_id}/members/{membership_id}/remove",
    response_model=MembershipResponse,
    summary="Remove somebody from this organization",
)
async def remove_member(
    context: CurrentWorkspace, membership_id: UUID, body: RemoveMemberRequest
) -> MembershipResponse:
    """*"This person no longer belongs here."*

    A colleague left the company, a contractor's engagement ended, an
    invitation went to the wrong address, or access had to be withdrawn.
    **Every one is the same operation and none of them is a deletion** — the
    membership survives with the moment, the actor and the reason, because
    decision history, the timeline and every audit question cite it.

    `POST` rather than `DELETE`, and the shape says so: nothing is removed from
    the database, and the response returns the ended membership rather than
    `204`.

    **`member:remove` has authorized this since M1** and nothing could perform
    it. No policy line was added.

    **The last owner is refused**, in the domain rather than here — a check in
    an interface can be raced by a second tab, and a workspace with nobody who
    can administer it is unrecoverable without support.
    """
    context.authorize(Resource.MEMBER, Action.REMOVE)
    membership = await build_use_cases(context.session).remove_member.execute(
        RemoveMemberCommand(
            workspace_id=context.workspace_id,
            membership_id=membership_id,
            removed_by=context.principal.user_id,
            reason=body.reason,
        ),
        now=datetime.now(UTC),
    )
    return MembershipResponse.from_domain(membership)


@router.post(
    "/workspaces/{workspace_id}/membership/leave",
    response_model=MembershipResponse,
    summary="Leave this organization",
)
async def leave_workspace(context: CurrentWorkspace) -> MembershipResponse:
    """*"I no longer work here."*

    **The half of team management the product never had.** `member:remove` let
    an administrator end somebody's involvement; nothing let a person end their
    own, so the only way out of an organization was to ask somebody else.

    **It takes no target, and that is the security property rather than a
    convenience.** There is no `membership_id` to substitute, so there is no
    check that the caller owns the one they named — the membership is found
    from the workspace and the verified token. **`Action.LEAVE`'s two grants
    therefore need no self-scoping**, exactly as the enum says: *"the scoping to
    self is the endpoint's, not the policy's."*

    **An owner may leave. A workspace may never become ownerless.** The refusal
    is the domain's, not this handler's — ADR-0404 ruled it into the
    application layer because *"a workspace invariant hidden
    in the policy model is invisible to anyone reading the workspace"*, and a
    check in an interface can be raced by a second tab.

    `POST` and not `DELETE`, for the same reason `remove` is: **nothing is
    deleted.** The membership is ended and returned, because decision history,
    the timeline and every audit question cite it.

    **No reason is asked for.** An administrator removing a colleague records
    why; a person leaving owes the organization no explanation, and
    `ended_by == user_id` is what tells the two apart afterwards.
    """
    context.authorize(Resource.MEMBER, Action.LEAVE)
    membership = await build_use_cases(context.session).leave_workspace.execute(
        LeaveWorkspaceCommand(
            workspace_id=context.workspace_id,
            user_id=context.principal.user_id,
        ),
        now=datetime.now(UTC),
    )
    return MembershipResponse.from_domain(membership)


__all__ = ["router"]


@router.post(
    "/workspaces/{workspace_id}/invitations/accept",
    response_model=MembershipResponse,
    status_code=status.HTTP_200_OK,
    summary="Join an organization you were invited to",
)
async def accept_invitation(context: CurrentUser, workspace_id: UUID) -> MembershipResponse:
    """**The one handler in Signora served to somebody outside the workspace.**

    Everything else on this router takes `CurrentWorkspace`, which verifies
    membership before the handler runs. **That dependency would refuse this
    caller, correctly** — they are not a member, and membership is what they
    are asking for. So this takes `CurrentUser`: authenticated, and nothing
    more ([C-208](../../../../docs/LANE_COORDINATION.md)).

    **There is no `context.authorize` call, and its absence is deliberate.**
    Casbin answers *"may this role do this?"*, and the caller has no role in
    this workspace to answer about. Authority here is the **verified email
    claim**: the invitation names an address, and the use case refuses unless
    the caller is proved to be it.

    **The link carries a workspace and nothing else** — `/join/{workspace_id}`,
    which is what the product already sends. There is no invitation id, because
    an id in a URL looks like a secret while being none: **the offer is found by
    the caller's own verified address**, and at most one live offer per address
    exists. Somebody who forwards their link gives away nothing.

    **Following the link twice succeeds.** Somebody who already holds the
    membership the invitation offered gets it back rather than an error, and
    nothing is published a second time.
    """
    async with accepting_workspace(context.session, workspace_id=workspace_id) as session:
        membership = await build_use_cases(session).accept_invitation.execute(
            AcceptInvitationInput(
                workspace_id=workspace_id,
                # **All three from the verified token, never from a body.** A
                # user id a caller could supply is a user id they would supply
                # somebody else's.
                user_id=context.principal.user_id,
                email=context.principal.email,
                email_verified=context.principal.email_verified,
            ),
            now=datetime.now(UTC),
            correlation_id=context.correlation_id,
        )
    return MembershipResponse.from_domain(membership)


@router.get(
    "/workspaces/{workspace_id}/saved-views",
    response_model=CursorPage[SavedViewResponse],
    summary="The saved views this organization shares",
)
async def list_saved_views(
    context: CurrentWorkspace,
    limit: LimitParam = DEFAULT_PAGE_LIMIT,
    cursor: CursorParam = None,
) -> CursorPage[SavedViewResponse]:
    """**Everybody in the workspace sees the same list.**

    ⚡ **Permission-aware, and the awareness is that a view is shared rather
    than personal** — [452](../../../../docs/architecture/452-app-shell-traceability-audit.md):
    *"a shared view looks the same for everybody."* ⛔ **There is deliberately
    no *my views* filter**, because filtering by author would make a shared
    capability read as a private one and the four screens that asked for this
    all asked for the shared reading.

    **Retired and superseded versions are excluded**, derived from the rows
    rather than from a stored flag.
    """
    context.authorize(Resource.SAVED_VIEW, Action.READ)
    result = await build_use_cases(context.session).list_saved_views.execute(
        ListSavedViewsInput(
            workspace_id=context.workspace_id, limit=limit, after=_position_after(cursor)
        )
    )
    items = [SavedViewResponse.from_domain(v) for v in result.views]
    return CursorPage(
        items=items, next_cursor=_next_cursor(items, result.has_more), has_more=result.has_more
    )


@router.get(
    "/workspaces/{workspace_id}/saved-views/{saved_view_id}",
    response_model=SavedViewResponse,
    summary="One saved view",
)
async def get_saved_view(context: CurrentWorkspace, saved_view_id: UUID) -> SavedViewResponse:
    """**404 covers both *no such view* and *another workspace's view***, which
    is the same non-enumeration rule the workspace endpoints keep."""
    context.authorize(Resource.SAVED_VIEW, Action.READ)
    view = await build_use_cases(context.session).get_saved_view.execute(
        context.workspace_id, saved_view_id
    )
    if view is None:
        raise SavedViewNotFoundError(saved_view_id)
    return SavedViewResponse.from_domain(view)


@router.post(
    "/workspaces/{workspace_id}/saved-views",
    status_code=status.HTTP_201_CREATED,
    response_model=SavedViewResponse,
    summary="Save a view",
)
async def declare_saved_view(context: CurrentWorkspace, body: SaveViewRequest) -> SavedViewResponse:
    """**The author comes from the verified token, never from the body** — an
    author a caller could supply is an author they would supply somebody
    else's."""
    context.authorize(Resource.SAVED_VIEW, Action.ADD)
    view = await build_use_cases(context.session).declare_saved_view.execute(
        DeclareSavedViewInput(
            workspace_id=context.workspace_id,
            name=body.name,
            declaration=body.declaration,
            created_by=context.principal.user_id,
            saved_view_id=body.saved_view_id,
        ),
        now=datetime.now(UTC),
    )
    return SavedViewResponse.from_domain(view)


@router.post(
    "/workspaces/{workspace_id}/saved-views/{saved_view_id}/revisions",
    status_code=status.HTTP_201_CREATED,
    response_model=SavedViewResponse,
    summary="Revise a saved view",
)
async def revise_saved_view(
    context: CurrentWorkspace, saved_view_id: UUID, body: ReviseViewRequest
) -> SavedViewResponse:
    """⚡ **A `POST` creating a revision, never a `PUT` editing the view.**

    The URL says so on purpose: a declaration is never edited, so the resource
    being created is *a revision*, and the one it replaces stays readable at
    its own id. **A `PUT` here would be a verb the storage model cannot honour**
    — the table carries no `UPDATE` grant for a declaration.

    **Revising requires the same grant as declaring**, because it is the same
    act: writing down a question under your own name.
    """
    context.authorize(Resource.SAVED_VIEW, Action.ADD)
    view = await build_use_cases(context.session).revise_saved_view.execute(
        ReviseSavedViewInput(
            workspace_id=context.workspace_id,
            saved_view_id=saved_view_id,
            created_by=context.principal.user_id,
            name=body.name,
            declaration=body.declaration,
        ),
        now=datetime.now(UTC),
    )
    return SavedViewResponse.from_domain(view)


@router.post(
    "/workspaces/{workspace_id}/saved-views/{saved_view_id}/retirement",
    response_model=SavedViewResponse,
    summary="Retire a saved view",
)
async def retire_saved_view(context: CurrentWorkspace, saved_view_id: UUID) -> SavedViewResponse:
    """⚡ **Owner only, and this is the one asymmetry in the resource.**

    Reading and writing are every member's, because a shared view is ordinary
    collaboration. **Retiring is not symmetric with creating**: it removes a
    capability *from everybody else*, which is the same shape as
    `member, remove` and is granted the same way.

    ⛔ **Retired, never deleted.** A view that explained a decision must still
    explain it afterwards, so the row stays and only stops being offered.
    """
    context.authorize(Resource.SAVED_VIEW, Action.REMOVE)
    view = await build_use_cases(context.session).retire_saved_view.execute(
        RetireSavedViewInput(workspace_id=context.workspace_id, saved_view_id=saved_view_id),
        now=datetime.now(UTC),
    )
    return SavedViewResponse.from_domain(view)


def _answer(payload: AnswerPayload | None) -> Answer[str] | None:
    return None if payload is None else Answer(value=payload.value, provenance=payload.provenance)


@router.post(
    "/workspaces/{workspace_id}/onboarding",
    status_code=status.HTTP_200_OK,
    response_model=OnboardingRunResponse,
    summary="Begin onboarding, or resume the run already in progress",
)
async def start_onboarding(context: CurrentWorkspace) -> OnboardingRunResponse:
    """⛔ **`200`, not `201`, and the code is the contract.**

    *"Returning to a step shows what was chosen, not an empty form"* — this is
    idempotent by design, and the person most likely to call it twice is the
    one arriving from the resume banner. **A `201` would tell them something
    was created when their existing answers were handed back.**

    **The person is the verified caller, never the body** — a person id a
    client could supply is a person id they would supply somebody else's, and
    onboarding answers are the one record here that is one member's rather
    than the workspace's.
    """
    context.authorize(Resource.ONBOARDING, Action.UPDATE)
    run = await build_use_cases(context.session).start_onboarding.execute(
        StartOnboardingInput(workspace_id=context.workspace_id, person_id=context.principal.user_id)
    )
    return OnboardingRunResponse.from_domain(run)


@router.get(
    "/workspaces/{workspace_id}/onboarding",
    response_model=OnboardingRunResponse,
    summary="This person's onboarding run",
)
async def get_onboarding(context: CurrentWorkspace) -> OnboardingRunResponse:
    """**Own run only, and there is no parameter that could ask for another's.**

    ⚡ **The scoping to self is here rather than in the policy**, exactly as
    `leave`'s is: no identity enters the request tuple, so a grant cannot be
    widened into reading a colleague's answers by editing `policy.csv`.
    """
    context.authorize(Resource.ONBOARDING, Action.READ)
    run = await build_use_cases(context.session).get_onboarding.execute(
        context.workspace_id, context.principal.user_id
    )
    return OnboardingRunResponse.from_domain(run)


@router.post(
    "/workspaces/{workspace_id}/onboarding/step",
    response_model=OnboardingRunResponse,
    summary="Move to a step, saving the one being left",
)
async def advance_onboarding(
    context: CurrentWorkspace, body: AdvanceOnboardingRequest
) -> OnboardingRunResponse:
    """⚡ **This is the autosave the design promises**: *"every step saves on
    advance and on blur."* The transition is persisted rather than held in the
    client, which is what makes *"you can leave at any point"* true."""
    context.authorize(Resource.ONBOARDING, Action.UPDATE)
    run = await build_use_cases(context.session).advance_onboarding.execute(
        AdvanceOnboardingInput(
            workspace_id=context.workspace_id,
            person_id=context.principal.user_id,
            step=body.step,
        )
    )
    return OnboardingRunResponse.from_domain(run)


@router.patch(
    "/workspaces/{workspace_id}/onboarding/company",
    response_model=OnboardingRunResponse,
    summary="Confirm or correct the company facts",
)
async def confirm_company(
    context: CurrentWorkspace, body: ConfirmCompanyRequest
) -> OnboardingRunResponse:
    """⚡ **`PATCH`, and the verb is the rule.** Every field is optional and an
    omitted one is left alone — *"four confirmations, no typing"* means a
    person may answer one and leave three, and a `PUT` would clear whatever
    the request did not repeat."""
    context.authorize(Resource.ONBOARDING, Action.UPDATE)
    size = body.company_size
    run = await build_use_cases(context.session).confirm_company.execute(
        ConfirmCompanyInput(
            workspace_id=context.workspace_id,
            person_id=context.principal.user_id,
            industry=_answer(body.industry),
            company_size=(
                None
                if size is None
                # ⛔ **Parsed into the band here, so an unknown string is a
                # `422` rather than a row nothing can benchmark.**
                else Answer(CompanySizeBand(size.value), size.provenance)
            ),
            region=_answer(body.region),
            timezone=_answer(body.timezone),
        )
    )
    return OnboardingRunResponse.from_domain(run)


@router.patch(
    "/workspaces/{workspace_id}/onboarding/person",
    response_model=OnboardingRunResponse,
    summary="Role and team size",
)
async def describe_person(
    context: CurrentWorkspace, body: DescribePersonRequest
) -> OnboardingRunResponse:
    context.authorize(Resource.ONBOARDING, Action.UPDATE)
    role = body.role
    size = body.team_size
    run = await build_use_cases(context.session).describe_person.execute(
        DescribePersonInput(
            workspace_id=context.workspace_id,
            person_id=context.principal.user_id,
            role=None if role is None else Answer(Role(role.value), role.provenance),
            team_size=None if size is None else Answer(size.value, size.provenance),
        )
    )
    return OnboardingRunResponse.from_domain(run)


@router.put(
    "/workspaces/{workspace_id}/onboarding/goals",
    response_model=OnboardingRunResponse,
    summary="Up to three outcomes",
)
async def choose_goals(
    context: CurrentWorkspace, body: ChooseGoalsRequest
) -> OnboardingRunResponse:
    """⚡ **`PUT`, deliberately unlike the two `PATCH`es above.** The goals are
    a whole selection rather than independent fields: deselecting one is a
    request that sends the remaining two, and a partial verb could not express
    it. **An empty list is a valid selection** — *"skipping entirely is
    permitted."*"""
    context.authorize(Resource.ONBOARDING, Action.UPDATE)
    run = await build_use_cases(context.session).choose_goals.execute(
        ChooseGoalsInput(
            workspace_id=context.workspace_id,
            person_id=context.principal.user_id,
            goals=tuple(body.goals),
        )
    )
    return OnboardingRunResponse.from_domain(run)


@router.post(
    "/workspaces/{workspace_id}/onboarding/completion",
    response_model=OnboardingRunResponse,
    summary="Finish onboarding",
)
async def finish_onboarding(context: CurrentWorkspace) -> OnboardingRunResponse:
    context.authorize(Resource.ONBOARDING, Action.UPDATE)
    run = await build_use_cases(context.session).finish_onboarding.execute(
        FinishOnboardingInput(
            workspace_id=context.workspace_id, person_id=context.principal.user_id
        )
    )
    return OnboardingRunResponse.from_domain(run)


@router.post(
    "/workspaces/{workspace_id}/onboarding/skip",
    response_model=OnboardingRunResponse,
    summary="Leave onboarding, keeping what was answered",
)
async def skip_onboarding(context: CurrentWorkspace) -> OnboardingRunResponse:
    """⛔ **A separate resource from `completion`, because leaving is not
    finishing.** *"The dialog says what gets worse in product terms and lets
    them go. No second ask, no guilt copy"* — and the two states have to be
    distinguishable or the resume banner cannot decide whether to appear."""
    context.authorize(Resource.ONBOARDING, Action.UPDATE)
    run = await build_use_cases(context.session).skip_onboarding.execute(
        FinishOnboardingInput(
            workspace_id=context.workspace_id, person_id=context.principal.user_id
        )
    )
    return OnboardingRunResponse.from_domain(run)


@router.get(
    "/workspaces/{workspace_id}/preferences",
    response_model=PreferencesResponse,
    summary="This person's preferences",
)
async def get_preferences(context: CurrentWorkspace) -> PreferencesResponse:
    """**Own preferences only, and there is no parameter that could ask for
    another's.**

    ⚡ **Never 404.** Somebody who has never opened the profile has the
    defaults, so this always answers — which is what leaves the panels with no
    *no preferences yet* branch to write, and therefore none to get wrong.
    """
    context.authorize(Resource.PREFERENCES, Action.READ)
    prefs = await build_use_cases(context.session).get_preferences.execute(
        context.workspace_id, context.principal.user_id
    )
    return PreferencesResponse.from_domain(prefs, now=datetime.now(UTC))


@router.post(
    "/workspaces/{workspace_id}/preferences/first-run-dismissal",
    response_model=PreferencesResponse,
    summary="This person has closed the first-run overlay",
)
async def dismiss_first_run(context: CurrentWorkspace) -> PreferencesResponse:
    """⚡ **An event, not a setting** — 📁 `Authenticated Entry` rule 20's
    overlay is *"dismissible forever"*, and **nothing in the design un-dismisses
    it.**

    ⛔ **Its own path rather than a field on `PATCH /preferences`.** That
    endpoint is the profile panel's, where every field has a control a person
    can move back; **a dismissal in that vocabulary would read as a toggle**,
    and there is none.

    ⚠️ **Idempotent, and the FIRST moment wins.** A double click, a retry or a
    second device answers the same and writes nothing the second time — the
    domain refuses to move a timestamp that already exists.

    ⛔ **No body, and there could not be one.** The only two facts are *who* and
    *when*: the first is the caller's verified identity and the second is the
    server's clock. **A client-supplied moment would let a browser decide when
    somebody stopped being new.**
    """
    context.authorize(Resource.PREFERENCES, Action.UPDATE)
    prefs = await build_use_cases(context.session).dismiss_first_run.execute(
        context.workspace_id,
        context.principal.user_id,
        now=datetime.now(UTC),
    )
    return PreferencesResponse.from_domain(prefs, now=datetime.now(UTC))


@router.post(
    "/workspaces/{workspace_id}/preferences/setup-complete-acknowledgement",
    response_model=PreferencesResponse,
    summary="This person has been told that setup is finished",
)
async def acknowledge_setup_complete(context: CurrentWorkspace) -> PreferencesResponse:
    """⚡ **An event, not a setting** — 📁 Home state 04's strip is *"one-time"*,
    and `AC-H03` says *"shown **exactly once**"*. **Nothing in the design
    un-shows it.**

    ⛔ **It does NOT record that setup is complete**, and the path says
    *acknowledgement* for exactly that reason. 📁 Completion is *"derived from the
    source of truth, never stored on Home"* — **this records only that a reader
    was told.** ⚠️ A route named `/setup-complete` would invite the next caller to
    treat it as the fact, and then two things would answer *"is this workspace
    activated?"*.

    ⚠️ **Idempotent, and the FIRST moment wins**, the same rule its two
    neighbours follow: a double render, a retry or a second tab answers the same
    and writes nothing twice.

    ⛔ **No body, and there could not be one.** The only two facts are *who* and
    *when*: the first is the caller's verified identity and the second is the
    server's clock.
    """
    context.authorize(Resource.PREFERENCES, Action.UPDATE)
    now = datetime.now(UTC)
    prefs = await build_use_cases(context.session).acknowledge_setup_complete.execute(
        context.workspace_id,
        context.principal.user_id,
        now=now,
    )
    return PreferencesResponse.from_domain(prefs, now=now)


@router.post(
    "/workspaces/{workspace_id}/preferences/invite-skip",
    response_model=PreferencesResponse,
    summary="Hide or restore the invite-the-team activation card",
)
async def skip_invite(context: CurrentWorkspace, skip: bool = True) -> PreferencesResponse:
    """📁 ***"Hides them for 30 days per person and is reversible from the
    progress line."***

    ⚡ **One route for both directions**, because the design calls reversal part
    of the same control — ⛔ **two routes would let a product ship the hide and
    forget the way back**, which is the shape this rule exists to prevent.

    ⚠️ **The window is derived from the moment and never stored.** 📁 [§2]: a
    stored expiry is a second representation of a fact the timestamp already
    carries, **and the two disagree the first time a clock moves.**

    ⛔ **Only the invite card.** **CRM and calls are blocking and cannot be
    skipped at all** — there is no parameter here that could name them, which is
    the design's *"blocking cards cannot be dismissed"* made unrepresentable
    rather than merely checked.
    """
    context.authorize(Resource.PREFERENCES, Action.UPDATE)
    prefs = await build_use_cases(context.session).skip_invite.execute(
        context.workspace_id,
        context.principal.user_id,
        skip=skip,
        now=datetime.now(UTC),
    )
    return PreferencesResponse.from_domain(prefs, now=datetime.now(UTC))


@router.patch(
    "/workspaces/{workspace_id}/preferences",
    response_model=PreferencesResponse,
    summary="Change some of this person's preferences",
)
async def change_preferences(
    context: CurrentWorkspace, body: ChangePreferencesRequest
) -> PreferencesResponse:
    """⚡ **`PATCH`, and only what the request actually carried is applied.**

    🔴 **`model_fields_set` is what makes that true.** The profile is several
    panels edited independently, so *Appearance* sending a theme must not clear
    the pronouns *Profile* set — and a plain `null` cannot say *I did not
    mention this*, because clearing a field is itself a legitimate request.
    """
    context.authorize(Resource.PREFERENCES, Action.UPDATE)
    sent = body.model_fields_set
    supplied = {name: getattr(body, name) for name in sent}
    prefs = await build_use_cases(context.session).change_preferences.execute(
        ChangePreferencesInput(
            workspace_id=context.workspace_id,
            # ⛔ **The caller's own verified id, never the body.** A person id a
            # client could supply is a person id they would supply somebody
            # else's, and preferences are the one record here that is one
            # member's rather than the workspace's.
            person_id=context.principal.user_id,
            **supplied,
        )
    )
    return PreferencesResponse.from_domain(prefs, now=datetime.now(UTC))


# ── Capability roles (TASK-1479 ⓸, ADR-0410) ────────────────────────────────


@router.get(
    "/workspaces/{workspace_id}/capability-roles",
    response_model=CapabilityRoleListResponse,
    summary="The roles this organization has defined, and how many people hold each",
)
async def capability_roles(context: CurrentWorkspace) -> CapabilityRoleListResponse:
    """Settings' *Roles & permissions*.

    ⚡ **A member may read this and may not change it** — `policy.csv` grants
    `member, capability_role, read` and withholds `update`. 📁 Team Management
    shows a colleague's role to everyone; **defining roles is administration**,
    which is the same class as adding a member.
    """
    context.authorize(Resource.CAPABILITY_ROLE, Action.READ)
    summaries = await build_capability_use_cases(context.session).list_roles.execute(
        context.workspace_id
    )
    return CapabilityRoleListResponse(
        roles=[
            CapabilityRoleResponse(
                role_id=summary.role.id, name=summary.role.name, holders=summary.holders
            )
            for summary in summaries
        ]
    )


@router.get(
    "/workspaces/{workspace_id}/capability-assignments",
    response_model=HeldCapabilityRolesResponse,
    summary="Who holds which role",
)
async def capability_assignments(context: CurrentWorkspace) -> HeldCapabilityRolesResponse:
    """The role chip beside every name in Team Management.

    🔴 **One question for the whole roster.** ⛔ Asking per person would be an
    N+1 on a screen that renders every colleague — 📁 [§14](../../../../CLAUDE.md),
    *obvious inefficiency is a defect at write time.*

    ⚠️ **Separate from `GET /members`, deliberately.** 📁 ADR-0410 §1 keeps
    membership and capability apart, and **a capability role on a membership
    response would put an authorization fact inside a tenancy contract.**
    """
    context.authorize(Resource.CAPABILITY_ROLE, Action.READ)
    held = await build_capability_use_cases(context.session).held_roles.execute(
        context.workspace_id
    )
    return HeldCapabilityRolesResponse(
        assignments={str(user_id): role.name for user_id, role in held.items()}
    )


@router.post(
    "/workspaces/{workspace_id}/capability-roles",
    response_model=CapabilityRoleResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Name a new role",
)
async def create_capability_role(
    context: CurrentWorkspace, body: CreateCapabilityRoleRequest
) -> CapabilityRoleResponse:
    """The design's *New role*.

    ⚠️ **The role this creates grants nothing.** 📁 ADR-0410 §5: *"a capability
    that is not yet granted denies, which is the safe direction."* **Its grants
    are `policy.csv` rows, which are a separate reviewed change** — the point of
    choosing Casbin over a vendor's rules UI (ADR-0010).

    ⛔ **So the screen must say so** rather than imply a working role, and
    `holders: 0` on the response is the only honest thing it can report.
    """
    context.authorize(Resource.CAPABILITY_ROLE, Action.UPDATE)
    role = await build_capability_use_cases(context.session).create_role.execute(
        CreateRoleInput(
            workspace_id=context.workspace_id,
            # Taken from the verified caller, never from the request.
            actor_id=context.principal.user_id,
            name=body.name,
        )
    )
    return CapabilityRoleResponse(role_id=role.id, name=role.name, holders=0)


@router.patch(
    "/workspaces/{workspace_id}/capability-roles/{role_id}",
    response_model=CapabilityRoleResponse,
    summary="Correct a role's name",
)
async def rename_capability_role(
    context: CurrentWorkspace, role_id: UUID, body: RenameCapabilityRoleRequest
) -> CapabilityRoleResponse:
    """🔴 **A rename moves the subject `policy.csv` keys on.**

    ⛔ **A rename without a matching policy edit denies everything, silently,
    for everyone holding the role.** ⚠️ Stated at every layer that can see it —
    the type, the repository, the use case and here — because it is the one
    operation in this module whose blast radius is in a file the module does
    not own.
    """
    context.authorize(Resource.CAPABILITY_ROLE, Action.UPDATE)
    use_cases = build_capability_use_cases(context.session)
    role = await use_cases.rename_role.execute(
        RenameRoleInput(
            workspace_id=context.workspace_id,
            actor_id=context.principal.user_id,
            role_id=role_id,
            name=body.name,
        )
    )
    summaries = await use_cases.list_roles.execute(context.workspace_id)
    holders = next((s.holders for s in summaries if s.role.id == role.id), 0)
    return CapabilityRoleResponse(role_id=role.id, name=role.name, holders=holders)


@router.put(
    "/workspaces/{workspace_id}/members/{user_id}/capability-role",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Change what a colleague may do, or change it back",
)
async def assign_capability_role(
    context: CurrentWorkspace, user_id: UUID, body: AssignCapabilityRoleRequest
) -> None:
    """Team Management's *Change to Analyst*, and *change back*.

    ⚡ **`PUT` of the whole assignment rather than `PATCH`**: there is one
    field, `role_id: null` is *change back*, and *"I did not mention it"* is
    not a state a customer can be in.

    ⛔ **`204`, because there is nothing to return that the caller did not
    send** — and what the person may now DO is a different question, answered
    by *Effective permissions* against the enforcer rather than guessed from
    this response.
    """
    context.authorize(Resource.CAPABILITY_ROLE, Action.UPDATE)
    await build_capability_use_cases(context.session).assign_role.execute(
        AssignRoleInput(
            workspace_id=context.workspace_id,
            actor_id=context.principal.user_id,
            user_id=user_id,
            role_id=body.role_id,
        )
    )


@router.get(
    "/workspaces/{workspace_id}/members/{user_id}/effective-permissions",
    response_model=EffectivePermissionsResponse,
    summary="What this person is actually able to do here",
)
async def effective_permissions(
    context: CurrentWorkspace, user_id: UUID
) -> EffectivePermissionsResponse:
    """Team Management's *Effective permissions* and *A Member will be able to*.

    📁 **ADR-0410 §3: *"a read of the authorization layer — the resolved answer
    for a person, computed, never stored."*** ⚡ **Every entry was asked of the
    same enforcer that decides the request path**, so this screen and the
    enforcement point cannot disagree.

    ⛔ **A `404` for somebody who is not a member**, on the same terms as every
    other route here: an absence and *"a member who may do nothing"* are
    different facts, and the second would be a sentence about somebody who is
    not there.
    """
    context.authorize(Resource.CAPABILITY_ROLE, Action.READ)
    view = await build_capability_use_cases(context.session).effective_permissions.execute(
        context.workspace_id, user_id
    )
    if view is None:
        raise NotAWorkspaceMemberError(user_id)
    return EffectivePermissionsResponse.from_domain(view, user_id=user_id)


@router.get(
    "/workspaces/{workspace_id}/members/{user_id}/capability-role/preview",
    response_model=RoleChangePreviewResponse,
    summary="What changing this person's role would gain them, and what it would cost",
)
async def preview_capability_role_change(
    context: CurrentWorkspace, user_id: UUID, role_id: Annotated[UUID | None, Query()] = None
) -> RoleChangePreviewResponse:
    """Team Management's *Change role — Member → Analyst*, before it happens.

    📁 **The design requires both directions**: *"Both directions are shown,
    because a role change is a trade rather than a promotion."* ⛔ **A dialog
    that showed only what somebody gains would describe a promotion**, and this
    layer's whole purpose is that a capability role can narrow.

    ⚡ **`role_id` omitted is *change back*** — the same convention as the `PUT`
    it previews, and deliberately the same word for the same act.

    ⚠️ **`READ`, not `UPDATE`.** ⛔ Reading what a change *would* do grants
    nothing and changes nothing; requiring the authority to perform it would
    stop a member seeing why a control is not theirs — 📁 which is the
    `onlyOwnersCan` shape the product already uses, one tier up.
    """
    context.authorize(Resource.CAPABILITY_ROLE, Action.READ)
    view = await build_capability_use_cases(context.session).effective_permissions.preview(
        context.workspace_id, user_id, role_id
    )
    if view is None:
        raise NotAWorkspaceMemberError(user_id)
    return RoleChangePreviewResponse.from_domain(view, user_id=user_id)


#: 📁 **The design is *"a 400px popover, not a page"***, and this is what fits
#: in one. ⛔ **Not a page size a caller may raise** — ⚡ **a popover that could
#: be asked for a thousand items is the *Notification Center* screen**, which is
#: Workflow 17's decomposition and explicitly not this row's.
NOTIFICATION_PANEL_LIMIT = 50


@router.get(
    "/workspaces/{workspace_id}/notifications",
    response_model=NotificationFeedResponse,
    summary="What this person has been told",
)
async def list_notifications(context: CurrentWorkspace) -> NotificationFeedResponse:
    """**This person's notifications, newest first.**

    🔴 **Own notifications only, and there is no parameter that could ask for
    another's** — 📁 the same rule `GET /preferences` records. ⚡ **The recipient
    is the caller's verified id**, the RLS policy narrows by it, and the query
    filters by it again ([§8](../../../../CLAUDE.md), defence in depth).

    ⛔ **No `limit` query parameter.** ⚡ **The panel's size is a design fact
    rather than a caller's choice** — 📁 *"a 400px popover, not a page"* — and an
    adjustable one would be the paginated Notification Center arriving through a
    query string.

    ⚠️ **Newest first, because the panel groups by DAY.** ⛔ **A page assembled
    from the oldest rows would group correctly and show the wrong days.**
    """
    context.authorize(Resource.NOTIFICATION, Action.READ)
    notifications = await SqlAlchemyNotificationRepository(context.session).feed(
        context.workspace_id,
        context.principal.user_id,
        limit=NOTIFICATION_PANEL_LIMIT,
    )
    return NotificationFeedResponse(
        notifications=[NotificationResponse.from_domain(n) for n in notifications]
    )


@router.post(
    "/workspaces/{workspace_id}/notifications/unread",
    response_model=UnreadBadgeResponse,
    summary="How many of these this person has not read",
)
async def unread_notifications(
    context: CurrentWorkspace, body: MarkNotificationsReadRequest
) -> UnreadBadgeResponse:
    """**Own read state only, and there is no parameter that could ask for
    another's** — 📁 the rule `GET /preferences` records, applied to a fact
    that is more sensitive because it is behavioural.

    ⚡ **`POST` for a read, deliberately.** ⛔ **The caller supplies a list of
    notification ids and a list does not fit in a query string** — 📁 the same
    reason `account-identities` takes ids, except that one fits and this one is
    bounded by a page. **Nothing is created; the verb is carrying the question.**

    ⚠️ **The caller supplies the candidates because this module does not know
    what a notification is** — 📁 ADR-0017 owns delivery. ✅ **So the honest
    question is *which of THESE has this person not read***, and a signature
    promising a count over a set it cannot see would be answering for
    something it has never been told about.
    """
    context.authorize(Resource.NOTIFICATION, Action.READ)
    badge = await SqlAlchemyNotificationReadRepository(context.session).unread(
        context.workspace_id, context.principal.user_id, body.notification_ids
    )
    return UnreadBadgeResponse.from_domain(badge)


@router.post(
    "/workspaces/{workspace_id}/notifications/read",
    response_model=UnreadBadgeResponse,
    summary="This person has read these",
)
async def mark_notifications_read(
    context: CurrentWorkspace, body: MarkNotificationsReadRequest
) -> UnreadBadgeResponse:
    """**Mark as read, and answer with the badge that results.**

    ⚡ **Returning the new count rather than `204`** — ⛔ **otherwise every
    caller marks read and then asks, which is two round trips for one act and a
    window in which the badge is stale.**

    ✅ **Idempotent.** **Marking twice is something a customer does by
    double-clicking**, and the first read time survives ([§2](../../../../CLAUDE.md)).

    ⛔ **There is no un-read route**, and the absence is deliberate: the table
    has no `UPDATE` grant, and 📁 the design does not ask for one. ⚠️ **If it
    ever does, it is a `DELETE` rather than an edit.**
    """
    context.authorize(Resource.NOTIFICATION, Action.UPDATE)
    repository = SqlAlchemyNotificationReadRepository(context.session)
    await repository.mark_read(
        context.workspace_id, context.principal.user_id, body.notification_ids
    )
    badge = await repository.unread(
        context.workspace_id, context.principal.user_id, body.notification_ids
    )
    return UnreadBadgeResponse.from_domain(badge)


@router.post(
    "/workspaces/{workspace_id}/recently-viewed",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Record that this person opened a record",
)
async def record_view(context: CurrentWorkspace, body: RecordViewRequest) -> None:
    """📁 **Session Continuity tier 4** — *"recently viewed records"*, whose
    medium is the server (`D-01`, *"four tiers, one medium each"*).

    ⚡ **Idempotent per record.** Opening the same account twice moves its time
    rather than adding a row — 📁 Home asks for *"the last five **records**"*,
    and an append-only log answers with one account five times for somebody who
    refreshed.

    ⛔ **Own history only, and there is no parameter that could ask otherwise.**
    The person is the verified caller; 492 §0's predicate is in the RLS policy
    as well as the query, so the absence of the parameter is not the only thing
    preventing it.

    **204, deliberately.** Recording a view returns nothing a caller needs, and
    a body would invite the browser to block a navigation on reading it.
    """
    context.authorize(Resource.RECENTLY_VIEWED, Action.UPDATE)
    await build_use_cases(context.session).record_view.execute(
        context.workspace_id, context.principal.user_id, body.entity_id, body.kind
    )


@router.get(
    "/workspaces/{workspace_id}/recently-viewed",
    response_model=list[ViewedRecordResponse],
    summary="What this person opened most recently",
)
async def recently_viewed(context: CurrentWorkspace) -> list[ViewedRecordResponse]:
    """📁 **Home's `card.recents`** — *"last five records touched. Context,
    never urgent."*

    ⚡ **Five is the design's number and is applied here**, not in the card: a
    limit chosen in a component would make the answer depend on who asked.

    ⛔ **An empty list is an answer, not a fault.** 📁 Session Continuity:
    *"if a tier has no record, the screen renders empty rather than
    reconstructing a plausible state. Fabricated continuity is worse than
    none."*
    """
    context.authorize(Resource.RECENTLY_VIEWED, Action.READ)
    records = await build_use_cases(context.session).recent_records.execute(
        context.workspace_id, context.principal.user_id
    )
    return [ViewedRecordResponse.from_domain(record) for record in records]
