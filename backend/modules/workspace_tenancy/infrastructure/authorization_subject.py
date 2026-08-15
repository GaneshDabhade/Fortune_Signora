"""The one place the capability layer takes effect — [TASK-1479](../../../../docs/BACKLOG.md) ⓸.

🔴 **Without this file the whole slice is decorative.** A domain type, a table
and a repository that nothing consults would be the unreachable-primitive class
this lane keeps finding: **built, tested, and unable to change what a customer
may do.**

## ⚡ The seam already existed, and it is why `signora_platform/**` is untouched

📁 `signora_platform/api/dependencies.py`:

> ```python
> class MembershipVerifier(Protocol):
>     async def resolve_role(self, workspace_id: UUID, user_id: UUID) -> str | None: ...
> ```
>
> *"Implemented by Workspace & Tenancy, injected at composition."*

⚡ **The platform asks for the string it should authorize against and does not
care how it is computed.** ⛔ **So the capability layer needs no change to a
frozen file** — 📁 ADR-0410 §2: *"adds no new mechanism; it says which
mechanism these belong to."*

## ⚠️ An ADAPTER, and not a change to `WorkspaceQueryService.resolve_role`

🔴 **Two questions that had one answer until today, and they are separating:**

***"What is this person's membership role?"*** — 📁 `WorkspaceQueryService.resolve_role`,
**and a Security Invariant asserts it returns `owner`/`member`, and `None` for
an ended membership.**

***"What subject should authorization use?"*** — **this adapter.**

⛔ **Changing the first to answer the second would have left that invariant
passing while it no longer tested what it names** — 📁 the [§2](../../../../CLAUDE.md)
class: *a guard whose subject has moved is a false claim that survives review.*

## 🔴 `None` still means "not a member", and that is load-bearing

**The platform reads `None` as *not a member* and raises
`WorkspaceAccessDeniedError`, which becomes a `404`** — 📁 the security
property that stops workspace enumeration (18-authentication.md).

⛔ **So this adapter returns `None` if and only if membership does.** ⚡ **A
capability role can never make somebody a non-member**, and a person whose
capability role has been deleted still gets their membership role rather than
`None` — see `subject_for`, where falling back is the difference between *fewer
permissions* and *no permission to open the screen that would fix it.*
"""

from __future__ import annotations

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from modules.workspace_tenancy.domain.capability import subject_for
from modules.workspace_tenancy.domain.entities import WorkspaceRole
from modules.workspace_tenancy.infrastructure.capability_repository import (
    SqlCapabilityRepository,
)
from modules.workspace_tenancy.infrastructure.query_service import WorkspaceQueryService


class CapabilityAwareMembershipVerifier:
    """Satisfies `signora_platform.api.MembershipVerifier` structurally.

    ⚡ **Composes rather than replaces**: membership is still the authoritative
    check, asked first and unchanged, and the capability role only decides
    *which string* a member authorizes as.
    """

    def __init__(self, session: AsyncSession) -> None:
        self._memberships = WorkspaceQueryService(session)
        self._capabilities = SqlCapabilityRepository(session)

    async def resolve_role(self, workspace_id: UUID, user_id: UUID) -> str | None:
        """The subject `Authorizer.is_allowed` is asked about, or `None`.

        ⛔ **Membership first, and its answer decides whether there is one at
        all.** A non-member gets `None` exactly as before — **the capability
        layer never widens who may reach a workspace, only what they may do
        inside it.**
        """
        membership = await self._memberships.get_membership(workspace_id, user_id)
        if membership is None:
            return None

        assignment = await self._capabilities.assignment(workspace_id, user_id)
        if assignment is None or assignment.role_id is None:
            # ⚡ **The ordinary path, and it costs one extra read.** 📁 That is
            # the price of the layer being additive: everyone is in this state
            # until somebody assigns a role, so ADR-0410 §5's *"every current
            # OWNER and MEMBER keeps exactly the authority it has today"* is
            # true by construction rather than by care.
            return WorkspaceRole(membership.role).value

        role = await self._capabilities.role(workspace_id, assignment.role_id)
        return subject_for(WorkspaceRole(membership.role), assignment, role)


__all__ = ["CapabilityAwareMembershipVerifier"]
