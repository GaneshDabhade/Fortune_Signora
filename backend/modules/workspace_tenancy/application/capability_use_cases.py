"""Naming a role, putting somebody on it, and answering what they may do.

📁 **[ADR-0410](../../../../docs/architecture/adr/0410-authorization-capability-layer.md)
§6** — [TASK-1479](../../../../docs/BACKLOG.md) slice ⓸.

> ✅ **Settings** — *Roles & permissions*, *New role*.
> ✅ **Team Management** — `Admin`, `Analyst`, *Change to Analyst*,
> *Effective permissions*, *A Member will be able to*.

## ⛔ Nothing here decides what a role may do

📁 **ADR-0410 §2: *"Do not create a second independent authorization model."***
**The grants are `policy.csv` rows.** ⚡ **`EffectivePermissions` READS them
through the same enforcer every request uses** — it does not hold a copy, and
there is no method here that could write one.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol
from uuid import UUID, uuid4

from modules.workspace_tenancy.domain.capability import (
    CapabilityAssignment,
    CapabilityError,
    CapabilityRole,
    fold,
    subject_for,
)
from modules.workspace_tenancy.domain.entities import WorkspaceRole
from signora_platform.authorization import Action, Authorizer, Resource


class CapabilityRepository(Protocol):
    """What this module needs of its own storage."""

    async def roles(self, workspace_id: UUID) -> tuple[CapabilityRole, ...]: ...

    async def role(self, workspace_id: UUID, role_id: UUID) -> CapabilityRole | None: ...

    async def create_role(
        self, workspace_id: UUID, role: CapabilityRole, *, actor_id: UUID
    ) -> None: ...

    async def rename_role(
        self, workspace_id: UUID, role: CapabilityRole, *, actor_id: UUID
    ) -> None: ...

    async def assignment(
        self, workspace_id: UUID, user_id: UUID
    ) -> CapabilityAssignment | None: ...

    async def assign(
        self, workspace_id: UUID, user_id: UUID, role_id: UUID | None, *, actor_id: UUID
    ) -> None: ...

    async def held_roles(self, workspace_id: UUID) -> dict[UUID, CapabilityRole]: ...

    async def holders(self, workspace_id: UUID, role_id: UUID) -> int: ...


class MembershipReader(Protocol):
    """The membership a capability role sits above.

    ⛔ **Declared as a shape rather than imported**, so this layer depends on a
    contract and the composition root supplies the adapter (§6).
    """

    async def role_of(self, workspace_id: UUID, user_id: UUID) -> WorkspaceRole | None: ...


@dataclass(frozen=True, slots=True)
class CreateRoleInput:
    workspace_id: UUID
    actor_id: UUID
    name: str


class CreateCapabilityRole:
    """Name a new role — the design's *New role* in Settings.

    ⚡ **A role created here grants nothing.** 📁 ADR-0410 §5: *"a capability
    that is not yet granted denies, which is the safe direction."* **Its
    `policy.csv` rows are a separate, reviewed change**, and that is the point
    of choosing Casbin over a vendor's rules UI (ADR-0010).

    ⚠️ **So *"New role"* creates something that is deliberately useless until
    somebody grants it something**, and the screen has to say so rather than
    imply a working role.
    """

    def __init__(self, *, capabilities: CapabilityRepository) -> None:
        self._capabilities = capabilities

    async def execute(self, request: CreateRoleInput) -> CapabilityRole:
        existing = await self._capabilities.roles(request.workspace_id)
        # The type refuses a membership-role name; the set refuses a duplicate.
        role = CapabilityRole(id=uuid4(), name=request.name)
        if any(other.key == role.key for other in existing):
            raise CapabilityError(f"“{role.name}” is already a role in this workspace.")
        await self._capabilities.create_role(
            request.workspace_id, role, actor_id=request.actor_id
        )
        return role


@dataclass(frozen=True, slots=True)
class RenameRoleInput:
    workspace_id: UUID
    actor_id: UUID
    role_id: UUID
    name: str


class RenameCapabilityRole:
    """Correct a role's name.

    🔴 **This moves the subject `policy.csv` keys on**, so **a rename without a
    matching policy edit denies everything for everyone holding the role.**
    ⚠️ **Stated at all three layers — the type, the repository and here** —
    because it is the one operation in this module whose blast radius is in a
    file this module does not own.
    """

    def __init__(self, *, capabilities: CapabilityRepository) -> None:
        self._capabilities = capabilities

    async def execute(self, request: RenameRoleInput) -> CapabilityRole:
        existing = await self._capabilities.role(request.workspace_id, request.role_id)
        if existing is None:
            raise CapabilityError("That role is not in this workspace.")
        renamed = existing.renamed(request.name)
        others = await self._capabilities.roles(request.workspace_id)
        if any(other.key == renamed.key and other.id != renamed.id for other in others):
            raise CapabilityError(f"“{renamed.name}” is already a role in this workspace.")
        await self._capabilities.rename_role(
            request.workspace_id, renamed, actor_id=request.actor_id
        )
        return renamed


@dataclass(frozen=True, slots=True)
class AssignRoleInput:
    workspace_id: UUID
    actor_id: UUID
    user_id: UUID
    #: ⛔ **`None` is *change back*** — the design's own affordance, and the
    #: state everybody starts in.
    role_id: UUID | None


class AssignCapabilityRole:
    """*Change to Analyst*, and *change back*.

    🔴 **The person must be a member of this workspace**, checked before
    anything is written. ⛔ **A capability role on somebody who is not a member
    is a row that grants nothing and outlives them** — the same *"a reference
    that is never checked is free text with a UUID type"* the account owner
    slice records, one module over.
    """

    def __init__(
        self, *, capabilities: CapabilityRepository, memberships: MembershipReader
    ) -> None:
        self._capabilities = capabilities
        self._memberships = memberships

    async def execute(self, request: AssignRoleInput) -> None:
        membership = await self._memberships.role_of(request.workspace_id, request.user_id)
        if membership is None:
            raise CapabilityError("That person is not a member of this workspace.")

        if request.role_id is not None:
            role = await self._capabilities.role(request.workspace_id, request.role_id)
            if role is None:
                raise CapabilityError("That role is not in this workspace.")

        await self._capabilities.assign(
            request.workspace_id,
            request.user_id,
            request.role_id,
            actor_id=request.actor_id,
        )


@dataclass(frozen=True, slots=True)
class RoleSummary:
    """One row of Settings' *Roles & permissions*."""

    role: CapabilityRole
    #: ⚡ **Derived on read**, and what a *delete* control must ask before
    #: offering itself — migration `0057`'s `ON DELETE RESTRICT` refuses, and a
    #: control the database will reject is one that goes nowhere.
    holders: int


class ListCapabilityRoles:
    def __init__(self, *, capabilities: CapabilityRepository) -> None:
        self._capabilities = capabilities

    async def execute(self, workspace_id: UUID) -> tuple[RoleSummary, ...]:
        roles = await self._capabilities.roles(workspace_id)
        # ⛔ **A loop rather than a comprehension**: `await` inside a generator
        # expression builds an async generator, which `tuple()` cannot consume
        # — and mypy is what said so rather than a failing test.
        summaries: list[RoleSummary] = []
        for role in roles:
            summaries.append(
                RoleSummary(
                    role=role,
                    holders=await self._capabilities.holders(workspace_id, role.id),
                )
            )
        return tuple(summaries)


class HeldCapabilityRoles:
    """Who in this workspace holds which role — **the roster's role chip.**

    🔴 **Why this exists rather than the roster asking per person.** 📁 The
    design draws a role beside every name in Team Management, and ⛔ **a
    membership role rendered there for somebody who effectively authorizes as
    `Analyst` is a false claim on the screen** — the class this repository keeps
    finding. ⚡ **One question for the whole list**, because the alternative is
    an N+1 and [§14](../../../../CLAUDE.md) calls that a defect at write time.

    ⛔ **Separate from the roster's own endpoint, deliberately.** A capability
    role is not part of a membership, and putting it on `MembershipResponse`
    would make a tenancy contract carry an authorization fact — 📁 exactly the
    two concerns ADR-0410 §1 exists to keep apart.
    """

    def __init__(self, *, capabilities: CapabilityRepository) -> None:
        self._capabilities = capabilities

    async def execute(self, workspace_id: UUID) -> dict[UUID, CapabilityRole]:
        return await self._capabilities.held_roles(workspace_id)


@dataclass(frozen=True, slots=True)
class Permission:
    """One thing somebody may do."""

    resource: str
    action: str


@dataclass(frozen=True, slots=True)
class EffectivePermissionsView:
    """What one person may actually do in one workspace.

    📁 **ADR-0410 §3: *"a read of the authorization layer — the resolved answer
    for a person, computed, never stored."*** ⛔ **A stored copy would be the
    §2 defect and a security one too: *a stale copy of what somebody may do is
    a claim the enforcement point does not honour.***
    """

    subject: str
    #: ⚠️ **The role's NAME where they hold one, so the screen can say
    #: *"Analyst"* rather than `cap:analyst`.** `None` means they authorize as
    #: their membership role.
    role_name: str | None
    permissions: tuple[Permission, ...]


@dataclass(frozen=True, slots=True)
class RoleChangeView:
    """What a role change would trade — **both directions.**

    📁 **The design's own words, in Team Management's *Change role* dialog:**
    *"Both directions are shown, because a role change is a trade rather than a
    promotion."*

    ⛔ **`gains` and `loses` are deliberately NOT fields.** ⚡ They are the set
    difference of two lists that are both here, and a third representation of a
    fact these two already carry is the duplication §2 forbids — **the screen
    derives them, once.**
    """

    current: EffectivePermissionsView
    proposed: EffectivePermissionsView


class EffectivePermissions:
    """Answer *"A Member will be able to…"* by asking the enforcer.

    ⚡ **Every pair is asked of the same `Authorizer` every request uses**, so
    the screen and the enforcement point cannot disagree — 📁 which is the
    whole reason §3 forbids storing it.

    ## ⛔ Only what is GRANTED is returned, and that is deliberate

    ⚠️ **The alternative — every `(resource, action)` pair with an allowed
    flag — would enumerate combinations that mean nothing**: `leave` an
    account, `resolve` a workspace. **126 pairs of which most are not product
    concepts**, and a screen listing *"may not resolve workspace"* has invented
    a capability to deny.

    ✅ **The design asks *"what will they be able to do"*, which is a list of
    permissions rather than a matrix of answers.**
    """

    def __init__(
        self,
        *,
        capabilities: CapabilityRepository,
        memberships: MembershipReader,
        authorizer: Authorizer,
    ) -> None:
        self._capabilities = capabilities
        self._memberships = memberships
        self._authorizer = authorizer

    async def execute(self, workspace_id: UUID, user_id: UUID) -> EffectivePermissionsView | None:
        """`None` when the person is not a member.

        ⛔ **Not an empty permission list**, which would read as *"a member who
        may do nothing"* — 📁 [P-A](../../../../docs/DOMAIN_DISCOVERY_REGISTER.md):
        an absence and an empty result are different facts.
        """
        membership = await self._memberships.role_of(workspace_id, user_id)
        if membership is None:
            return None
        return await self._today(workspace_id, user_id, membership)

    async def preview(
        self, workspace_id: UUID, user_id: UUID, role_id: UUID | None
    ) -> RoleChangeView | None:
        """What *Change to Analyst* — or *change back* — would actually trade.

        ⚡ **Both sides come from the same enforcer as the request path**, so the
        dialog cannot promise something the enforcement point will refuse. 📁 It
        is the §3 read taken twice, and **nothing is stored either time.**

        ⚠️ **Today every capability role grants nothing**, so `proposed` is
        empty and the dialog honestly says the person would lose everything —
        📁 ADR-0410 §5's *"a capability that is not yet granted denies"*, shown
        to the customer before they click rather than discovered afterwards.
        ⛔ **And it stops being empty on its own** the day somebody adds a
        `cap:` row: **computed, so there is no second place to update.**

        ⛔ **`role_id` naming a role that is not here RAISES rather than falling
        back.** ⚠️ `subject_for`'s fallback is right for a role that vanished
        *under* somebody; here it would render *"no change"* for a change that
        cannot be made — 📁 the P-A shape again, one layer up.
        """
        membership = await self._memberships.role_of(workspace_id, user_id)
        if membership is None:
            return None

        proposed_role: CapabilityRole | None = None
        if role_id is not None:
            proposed_role = await self._capabilities.role(workspace_id, role_id)
            if proposed_role is None:
                raise CapabilityError("That role is not in this workspace.")

        return RoleChangeView(
            current=await self._today(workspace_id, user_id, membership),
            proposed=self._as(
                workspace_id,
                subject_for(
                    membership,
                    CapabilityAssignment(user_id=user_id, role_id=role_id),
                    proposed_role,
                ),
                proposed_role,
            ),
        )

    async def _today(
        self, workspace_id: UUID, user_id: UUID, membership: WorkspaceRole
    ) -> EffectivePermissionsView:
        assignment = await self._capabilities.assignment(workspace_id, user_id)
        role: CapabilityRole | None = None
        if assignment is not None and assignment.role_id is not None:
            role = await self._capabilities.role(workspace_id, assignment.role_id)
        return self._as(workspace_id, subject_for(membership, assignment, role), role)

    def _as(
        self, workspace_id: UUID, subject: str, role: CapabilityRole | None
    ) -> EffectivePermissionsView:
        granted = tuple(
            Permission(resource=str(resource), action=str(action))
            for resource in Resource
            for action in Action
            if self._authorizer.is_allowed(
                role=subject, workspace_id=workspace_id, resource=resource, action=action
            )
        )
        return EffectivePermissionsView(
            subject=subject,
            # ⚡ **The name only when the subject IS the role**, so a person who
            # fell back to their membership role is not shown a role they are
            # not effectively holding.
            role_name=role.name if role is not None and subject == role.key else None,
            permissions=granted,
        )


__all__ = [
    "AssignCapabilityRole",
    "AssignRoleInput",
    "CapabilityRepository",
    "CreateCapabilityRole",
    "CreateRoleInput",
    "EffectivePermissions",
    "EffectivePermissionsView",
    "HeldCapabilityRoles",
    "ListCapabilityRoles",
    "MembershipReader",
    "Permission",
    "RenameCapabilityRole",
    "RenameRoleInput",
    "RoleChangeView",
    "RoleSummary",
    "fold",
]
