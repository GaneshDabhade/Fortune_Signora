"""Per-request contexts produced by the dependency chain.

Two shapes exist, and the distinction is a security boundary rather than a
convenience:

* ``UserContext`` — authenticated, no workspace selected. Only ``app.user_id``
  is set, so workspace-owned tables are correctly invisible. Used for
  operations that span a user's workspaces, such as listing them.
* ``WorkspaceContext`` — authenticated *and* verified as a member of a
  specific workspace. Both RLS settings are established and the caller's
  role is known, so authorization can be evaluated.

A ``WorkspaceContext`` can only be constructed after server-side membership
verification, so possessing one is itself the proof that verification passed.
"""

from dataclasses import dataclass
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from signora_platform.auth import AuthenticatedPrincipal
from signora_platform.authorization import Action, AuthorizationDeniedError, Authorizer, Resource


@dataclass(frozen=True)
class UserContext:
    principal: AuthenticatedPrincipal
    session: AsyncSession
    correlation_id: UUID


@dataclass(frozen=True)
class WorkspaceContext:
    principal: AuthenticatedPrincipal
    workspace_id: UUID
    role: str
    session: AsyncSession
    correlation_id: UUID
    authorizer: Authorizer

    def authorize(self, resource: Resource, action: Action) -> None:
        """Raise ``AuthorizationDeniedError`` unless the caller's role permits the
        action in this workspace.

        Raising rather than returning a boolean is deliberate: a forgotten
        ``if not ctx.is_allowed(...)`` fails open, whereas a forgotten
        ``ctx.authorize(...)`` call is visible in review as a route with no
        authorization at all.
        """
        if not self.authorizer.is_allowed(
            role=self.role, workspace_id=self.workspace_id, resource=resource, action=action
        ):
            raise AuthorizationDeniedError(role=self.role, resource=resource, action=action)
