"""The authentication and workspace-context dependency chain.

This implements the pipeline specified in 18-authentication.md exactly once.
Route handlers depend on ``UserContext`` or ``WorkspaceContext``; they never
read a header, parse a token, open a session, or set RLS context themselves.

**Why membership verification lives behind a Protocol.** Verifying that a
user belongs to a workspace is Workspace & Tenancy's knowledge, but
``signora_platform`` must never import ``modules`` (CI-enforced, see
15-project-structure.md). The Protocol below inverts that dependency: the
platform declares what it needs, and the composition root injects the
concrete implementation. No boundary is crossed.
"""

from collections.abc import AsyncIterator, Callable
from dataclasses import dataclass
from typing import Annotated, Protocol
from uuid import UUID

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from signora_platform.api.context import UserContext, WorkspaceContext
from signora_platform.api.errors import correlation_id_of
from signora_platform.auth import (
    AuthenticatedPrincipal,
    JwtVerifier,
    MissingCredentialsError,
)
from signora_platform.authorization import Authorizer
from signora_platform.db import tenant_scoped_session, user_scoped_session
from signora_platform.observability import logging_context


class MembershipVerifier(Protocol):
    """Resolves a user's role in a workspace, or ``None`` if they are not a
    member. Implemented by Workspace & Tenancy, injected at composition."""

    async def resolve_role(self, workspace_id: UUID, user_id: UUID) -> str | None: ...


MembershipVerifierFactory = Callable[[AsyncSession], MembershipVerifier]
"""Builds a verifier bound to a specific request's session — membership must
be read inside the same transaction that will carry the RLS context."""


class WorkspaceAccessDeniedError(Exception):
    """The caller is not a member of the requested workspace.

    **Maps to HTTP 404, never 403.** A 403 would confirm the workspace
    exists, letting a caller enumerate workspace ids. This is deliberately
    indistinguishable from "no such workspace" (18-authentication.md).
    """

    def __init__(self, workspace_id: UUID) -> None:
        super().__init__("Workspace does not exist.")
        self.workspace_id = workspace_id


@dataclass(frozen=True)
class ApiDependencies:
    """Everything the chain needs, assembled once by the composition root and
    stored on ``app.state``."""

    jwt_verifier: JwtVerifier
    session_factory: async_sessionmaker[AsyncSession]
    authorizer: Authorizer
    membership_verifier_factory: MembershipVerifierFactory


# auto_error=False so a missing header raises our own MissingCredentialsError
# and returns the standard envelope, rather than FastAPI's bare 403 default.
_bearer_scheme = HTTPBearer(auto_error=False)


def _dependencies_of(request: Request) -> ApiDependencies:
    deps = getattr(request.app.state, "api_dependencies", None)
    if not isinstance(deps, ApiDependencies):  # pragma: no cover - wiring error
        raise RuntimeError(
            "ApiDependencies are not configured on app.state; the composition "
            "root must set app.state.api_dependencies."
        )
    return deps


async def get_principal(
    request: Request,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer_scheme)],
) -> AuthenticatedPrincipal:
    """Stages 1-3: verify the token's signature and claims, and build the
    authenticated principal."""
    if credentials is None:
        raise MissingCredentialsError()
    return _dependencies_of(request).jwt_verifier.verify(credentials.credentials)


CurrentPrincipal = Annotated[AuthenticatedPrincipal, Depends(get_principal)]


async def get_user_context(
    request: Request, principal: CurrentPrincipal
) -> AsyncIterator[UserContext]:
    """An authenticated context with **no** workspace selected.

    Only ``app.user_id`` is set, so workspace-owned tables return nothing —
    which is correct, not a limitation. The ``workspace`` table remains
    readable because its RLS policy is membership-based on ``app.user_id``,
    which is exactly what "list the workspaces I belong to" needs.
    """
    deps = _dependencies_of(request)
    correlation_id = correlation_id_of(request)
    with logging_context(correlation_id=correlation_id, user_id=principal.user_id):
        async with user_scoped_session(deps.session_factory, user_id=principal.user_id) as session:
            yield UserContext(
                principal=principal,
                session=session,
                correlation_id=correlation_id,
            )


async def get_workspace_context(
    request: Request, workspace_id: UUID, principal: CurrentPrincipal
) -> AsyncIterator[WorkspaceContext]:
    """Stages 4-7: resolve the workspace, verify membership server-side,
    establish RLS context, and expose the authorizer.

    ``workspace_id`` is taken from the route's path parameter. It is never
    trusted on its own — nor is the ``active_workspace_id`` token claim.
    Membership is read from the database on every request.
    """
    deps = _dependencies_of(request)
    correlation_id = correlation_id_of(request)
    with logging_context(
        correlation_id=correlation_id, user_id=principal.user_id, workspace_id=workspace_id
    ):
        async with tenant_scoped_session(
            deps.session_factory, workspace_id=workspace_id, user_id=principal.user_id
        ) as session:
            role = await deps.membership_verifier_factory(session).resolve_role(
                workspace_id, principal.user_id
            )
            if role is None:
                raise WorkspaceAccessDeniedError(workspace_id)

            yield WorkspaceContext(
                principal=principal,
                workspace_id=workspace_id,
                role=role,
                session=session,
                correlation_id=correlation_id,
                authorizer=deps.authorizer,
            )


CurrentUser = Annotated[UserContext, Depends(get_user_context)]
CurrentWorkspace = Annotated[WorkspaceContext, Depends(get_workspace_context)]
