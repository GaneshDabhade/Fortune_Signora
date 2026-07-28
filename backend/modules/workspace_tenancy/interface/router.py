"""FastAPI routes for Workspace & Tenancy.

Handlers do three things and nothing else: translate the request into use-case
input, authorize, and translate the result into a response schema. All
business rules live in the application and domain layers; all authentication,
membership verification, and RLS context is established by the dependency
chain before a handler runs (18-authentication.md).
"""

from typing import Annotated

from fastapi import APIRouter, Query, Request, status

from modules.workspace_tenancy.application.use_cases import (
    AddMemberInput,
    CreateWorkspaceInput,
    GetWorkspaceInput,
    ListUserWorkspacesInput,
    ListWorkspaceMembersInput,
)
from modules.workspace_tenancy.infrastructure.composition import build_use_cases
from modules.workspace_tenancy.interface.schemas import (
    AddMemberRequest,
    CreateWorkspaceRequest,
    MembershipResponse,
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
        CreateWorkspaceInput(name=body.name, created_by=context.principal.user_id),
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


__all__ = ["router"]
