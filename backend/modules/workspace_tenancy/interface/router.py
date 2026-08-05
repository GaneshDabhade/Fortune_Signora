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
from modules.workspace_tenancy.application.use_cases.remove_member import RemoveMemberCommand
from modules.workspace_tenancy.application.use_cases.transfer_ownership import (
    TransferOwnershipCommand,
)
from modules.workspace_tenancy.infrastructure.acceptance import accepting_workspace
from modules.workspace_tenancy.infrastructure.composition import (
    build_query_service,
    build_use_cases,
)
from modules.workspace_tenancy.interface.schemas import (
    AddMemberRequest,
    ChangeRoleRequest,
    CreateWorkspaceRequest,
    HistoryEntryResponse,
    InvitationResponse,
    InviteMemberRequest,
    MembershipResponse,
    RemoveMemberRequest,
    TransferOwnershipRequest,
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
    items: list[WorkspaceResponse] | list[MembershipResponse], has_more: bool
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
            created_by=context.principal.user_id,
            created_by_email=context.principal.email,
        ),
        correlation_id=correlation_id_of(request),
    )
    return WorkspaceResponse.from_domain(result.workspace)


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
    response_model=list[HistoryEntryResponse],
    summary="What has happened to this organization",
)
async def organization_history(context: CurrentWorkspace) -> list[HistoryEntryResponse]:
    """*"What happened?"* — in one place, newest first.

    Somebody joined, was invited, was withdrawn, changed role, or was removed.
    **Every fact was already stored**; this is the reading, which is the half
    that could always have been added later — and why the writing was not
    deferred (`CLAUDE.md` §2).

    **`member:read` authorizes it**, on the reading that already made listing
    members and invitations `member:read`. **Everybody in the organization can
    see it**, deliberately: a history only administrators may read is a history
    that cannot be used to hold administrators accountable.
    """
    context.authorize(Resource.MEMBER, Action.READ)
    entries = await build_query_service(context.session).organization_history(context.workspace_id)
    return [HistoryEntryResponse.from_domain(entry) for entry in entries]


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


__all__ = ["router"]


@router.post(
    "/workspaces/{workspace_id}/invitations/{invitation_id}/accept",
    response_model=MembershipResponse,
    status_code=status.HTTP_200_OK,
    summary="Join an organization you were invited to",
)
async def accept_invitation(
    context: CurrentUser, workspace_id: UUID, invitation_id: UUID
) -> MembershipResponse:
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

    **Naming a workspace and an invitation is not authority.** Both travel in a
    URL — forwarded, screenshotted, left in a shared browser — and neither is a
    secret. Guessing them yields a transaction that can read one row the
    guesser cannot act on.

    **Following the link twice succeeds.** Somebody who already holds the
    membership the invitation offered gets it back rather than an error, and
    nothing is published a second time.
    """
    async with accepting_workspace(context.session, workspace_id=workspace_id) as session:
        membership = await build_use_cases(session).accept_invitation.execute(
            AcceptInvitationInput(
                workspace_id=workspace_id,
                invitation_id=invitation_id,
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
