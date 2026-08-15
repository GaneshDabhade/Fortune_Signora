"""Naming, assigning and answering — [TASK-1479](../../../docs/BACKLOG.md) ⓸.

🔴 **`EffectivePermissions` is the subject.** 📁 **ADR-0410 §3** calls it *"a
read of the authorization layer — the resolved answer for a person, computed,
never stored"*, and **a stored copy would be a security
defect as well as a §2 one: a stale copy of what somebody may do is a claim
the enforcement point does not honour.**
"""

from __future__ import annotations

from uuid import UUID, uuid4

import pytest

from modules.workspace_tenancy.application.capability_use_cases import (
    AssignCapabilityRole,
    AssignRoleInput,
    CreateCapabilityRole,
    CreateRoleInput,
    EffectivePermissions,
    ListCapabilityRoles,
    RenameCapabilityRole,
    RenameRoleInput,
)
from modules.workspace_tenancy.domain.capability import (
    CapabilityAssignment,
    CapabilityError,
    CapabilityRole,
)
from modules.workspace_tenancy.domain.entities import WorkspaceRole
from signora_platform.authorization import Action, Resource


class _Capabilities:
    def __init__(self, *, roles: tuple[CapabilityRole, ...] = ()) -> None:
        self._roles = list(roles)
        self._assignments: dict[UUID, UUID | None] = {}
        self.created: list[CapabilityRole] = []
        self.renamed: list[CapabilityRole] = []
        self.assigned: list[tuple[UUID, UUID | None]] = []

    async def roles(self, workspace_id: UUID) -> tuple[CapabilityRole, ...]:
        return tuple(self._roles)

    async def role(self, workspace_id: UUID, role_id: UUID) -> CapabilityRole | None:
        return next((r for r in self._roles if r.id == role_id), None)

    async def create_role(
        self, workspace_id: UUID, role: CapabilityRole, *, actor_id: UUID
    ) -> None:
        self.created.append(role)
        self._roles.append(role)

    async def rename_role(
        self, workspace_id: UUID, role: CapabilityRole, *, actor_id: UUID
    ) -> None:
        self.renamed.append(role)
        self._roles = [role if r.id == role.id else r for r in self._roles]

    async def assignment(
        self, workspace_id: UUID, user_id: UUID
    ) -> CapabilityAssignment | None:
        if user_id not in self._assignments:
            return None
        return CapabilityAssignment(user_id=user_id, role_id=self._assignments[user_id])

    async def assign(
        self, workspace_id: UUID, user_id: UUID, role_id: UUID | None, *, actor_id: UUID
    ) -> None:
        self.assigned.append((user_id, role_id))
        self._assignments[user_id] = role_id

    async def holders(self, workspace_id: UUID, role_id: UUID) -> int:
        return sum(1 for held in self._assignments.values() if held == role_id)


class _Memberships:
    def __init__(self, **people: WorkspaceRole) -> None:
        self._people = {UUID(key): value for key, value in people.items()}

    def add(self, user_id: UUID, role: WorkspaceRole) -> None:
        self._people[user_id] = role

    async def role_of(self, workspace_id: UUID, user_id: UUID) -> WorkspaceRole | None:
        return self._people.get(user_id)


class _RecordingAuthorizer:
    """Answers from a set, and records every question.

    ⚡ **Recording is what proves the permissions were ASKED rather than
    held** — the assertion ADR-0410 §3 actually needs.
    """

    def __init__(self, allow: set[tuple[str, str]]) -> None:
        self._allow = allow
        self.asked: list[tuple[str, str, str]] = []

    def is_allowed(
        self, *, role: str, workspace_id: UUID, resource: Resource, action: Action
    ) -> bool:
        self.asked.append((role, str(resource), str(action)))
        return (str(resource), str(action)) in self._allow


class TestNamingARole:
    async def test_a_new_role_is_created(self) -> None:
        capabilities = _Capabilities()

        role = await CreateCapabilityRole(capabilities=capabilities).execute(
            CreateRoleInput(workspace_id=uuid4(), actor_id=uuid4(), name="Analyst")
        )

        assert capabilities.created == [role]

    async def test_a_duplicate_name_is_refused(self) -> None:
        existing = CapabilityRole(id=uuid4(), name="Analyst")
        capabilities = _Capabilities(roles=(existing,))

        with pytest.raises(CapabilityError):
            await CreateCapabilityRole(capabilities=capabilities).execute(
                CreateRoleInput(workspace_id=uuid4(), actor_id=uuid4(), name="  ANALYST ")
            )

        assert capabilities.created == []

    async def test_a_membership_role_name_is_refused_before_any_write(self) -> None:
        """🔴 **ADR-0410 §5's invariant, reaching the use case.** The type
        refuses it, and this asserts nothing was written on the way."""
        capabilities = _Capabilities()

        with pytest.raises(CapabilityError):
            await CreateCapabilityRole(capabilities=capabilities).execute(
                CreateRoleInput(workspace_id=uuid4(), actor_id=uuid4(), name="owner")
            )

        assert capabilities.created == []

    async def test_renaming_onto_another_role_s_name_is_refused(self) -> None:
        first = CapabilityRole(id=uuid4(), name="Analyst")
        second = CapabilityRole(id=uuid4(), name="Admin")
        capabilities = _Capabilities(roles=(first, second))

        with pytest.raises(CapabilityError):
            await RenameCapabilityRole(capabilities=capabilities).execute(
                RenameRoleInput(
                    workspace_id=uuid4(), actor_id=uuid4(), role_id=second.id, name="analyst"
                )
            )

        assert capabilities.renamed == []

    async def test_renaming_a_role_to_its_own_name_differently_cased_is_allowed(self) -> None:
        """⚠️ **The case the duplicate check must not catch.** ⛔ Refusing here
        would make *"Analyst"* → *"analyst"* impossible, which is a correction a
        customer is entitled to make."""
        role = CapabilityRole(id=uuid4(), name="Analyst")
        capabilities = _Capabilities(roles=(role,))

        renamed = await RenameCapabilityRole(capabilities=capabilities).execute(
            RenameRoleInput(
                workspace_id=uuid4(), actor_id=uuid4(), role_id=role.id, name="analyst"
            )
        )

        assert renamed.name == "analyst"


class TestChangingSomebodysRole:
    async def test_a_member_can_be_changed_to_a_role(self) -> None:
        person, role = uuid4(), CapabilityRole(id=uuid4(), name="Analyst")
        capabilities = _Capabilities(roles=(role,))
        memberships = _Memberships()
        memberships.add(person, WorkspaceRole.MEMBER)

        await AssignCapabilityRole(
            capabilities=capabilities, memberships=memberships
        ).execute(
            AssignRoleInput(
                workspace_id=uuid4(), actor_id=uuid4(), user_id=person, role_id=role.id
            )
        )

        assert capabilities.assigned == [(person, role.id)]

    async def test_change_back_is_the_same_act_with_no_role(self) -> None:
        person = uuid4()
        capabilities = _Capabilities()
        memberships = _Memberships()
        memberships.add(person, WorkspaceRole.OWNER)

        await AssignCapabilityRole(
            capabilities=capabilities, memberships=memberships
        ).execute(
            AssignRoleInput(
                workspace_id=uuid4(), actor_id=uuid4(), user_id=person, role_id=None
            )
        )

        assert capabilities.assigned == [(person, None)]

    async def test_somebody_who_is_not_a_member_is_refused_before_any_write(self) -> None:
        """⛔ **A capability role on a non-member is a row that grants nothing
        and outlives them** — the *"a reference that is never checked is free
        text with a UUID type"* rule, one module over."""
        role = CapabilityRole(id=uuid4(), name="Analyst")
        capabilities = _Capabilities(roles=(role,))

        with pytest.raises(CapabilityError):
            await AssignCapabilityRole(
                capabilities=capabilities, memberships=_Memberships()
            ).execute(
                AssignRoleInput(
                    workspace_id=uuid4(), actor_id=uuid4(), user_id=uuid4(), role_id=role.id
                )
            )

        assert capabilities.assigned == []

    async def test_a_role_that_is_not_here_is_refused_before_any_write(self) -> None:
        person = uuid4()
        capabilities = _Capabilities()
        memberships = _Memberships()
        memberships.add(person, WorkspaceRole.MEMBER)

        with pytest.raises(CapabilityError):
            await AssignCapabilityRole(
                capabilities=capabilities, memberships=memberships
            ).execute(
                AssignRoleInput(
                    workspace_id=uuid4(), actor_id=uuid4(), user_id=person, role_id=uuid4()
                )
            )

        assert capabilities.assigned == []


class TestSettingsRolesAndPermissions:
    async def test_each_role_reports_how_many_people_hold_it(self) -> None:
        """⚡ **What a *delete* control must ask before offering itself** —
        migration `0057` refuses to delete a role people hold, and a control
        the database will reject is one that goes nowhere."""
        analyst = CapabilityRole(id=uuid4(), name="Analyst")
        admin = CapabilityRole(id=uuid4(), name="Admin")
        capabilities = _Capabilities(roles=(admin, analyst))
        workspace = uuid4()
        for _ in range(3):
            await capabilities.assign(workspace, uuid4(), analyst.id, actor_id=uuid4())

        summaries = await ListCapabilityRoles(capabilities=capabilities).execute(workspace)

        by_name = {summary.role.name: summary.holders for summary in summaries}
        assert by_name == {"Admin": 0, "Analyst": 3}


class TestEffectivePermissionsIsReadRatherThanHeld:
    async def test_it_asks_the_enforcer_for_every_answer(self) -> None:
        """🔴 **The assertion ADR-0410 §3 actually needs.**

        ⛔ **Not *"the list looks right"*** — a stored copy would produce a
        list that looked right too, until it went stale. ⚡ **This asserts the
        enforcer was ASKED**, with the resolved subject, for the pairs it
        reports.
        """
        person = uuid4()
        memberships = _Memberships()
        memberships.add(person, WorkspaceRole.MEMBER)
        authorizer = _RecordingAuthorizer({("workspace", "read")})

        view = await EffectivePermissions(
            capabilities=_Capabilities(), memberships=memberships, authorizer=authorizer
        ).execute(uuid4(), person)

        assert view is not None
        assert authorizer.asked, "the enforcer was never consulted"
        assert all(subject == "member" for subject, _, _ in authorizer.asked)
        assert [(p.resource, p.action) for p in view.permissions] == [("workspace", "read")]

    async def test_it_reports_only_what_is_granted(self) -> None:
        """⛔ **Not every `(resource, action)` pair with a flag.** ⚠️ That would
        enumerate combinations that mean nothing — *leave* an account, *resolve*
        a workspace — **and a screen listing *"may not resolve workspace"* has
        invented a capability to deny.**"""
        person = uuid4()
        memberships = _Memberships()
        memberships.add(person, WorkspaceRole.OWNER)
        authorizer = _RecordingAuthorizer(set())

        view = await EffectivePermissions(
            capabilities=_Capabilities(), memberships=memberships, authorizer=authorizer
        ).execute(uuid4(), person)

        assert view is not None
        assert view.permissions == ()
        assert len(authorizer.asked) == len(Resource) * len(Action)

    async def test_it_answers_for_the_capability_role_when_one_is_held(self) -> None:
        person = uuid4()
        analyst = CapabilityRole(id=uuid4(), name="Analyst")
        capabilities = _Capabilities(roles=(analyst,))
        workspace = uuid4()
        await capabilities.assign(workspace, person, analyst.id, actor_id=uuid4())
        memberships = _Memberships()
        memberships.add(person, WorkspaceRole.MEMBER)
        authorizer = _RecordingAuthorizer(set())

        view = await EffectivePermissions(
            capabilities=capabilities, memberships=memberships, authorizer=authorizer
        ).execute(workspace, person)

        assert view is not None
        assert view.subject == analyst.key
        assert view.role_name == "Analyst"
        assert all(subject == analyst.key for subject, _, _ in authorizer.asked)

    async def test_a_non_member_is_absent_rather_than_permitted_nothing(self) -> None:
        """⛔ **`None`, not an empty permission list.** 📁 **P-A**: an absence
        and an empty result are different facts, and *"a member who
        may do nothing"* is a sentence about somebody who is not there."""
        authorizer = _RecordingAuthorizer(set())

        view = await EffectivePermissions(
            capabilities=_Capabilities(), memberships=_Memberships(), authorizer=authorizer
        ).execute(uuid4(), uuid4())

        assert view is None
        assert authorizer.asked == []

    async def test_a_role_that_no_longer_resolves_reports_no_role_name(self) -> None:
        """⚠️ **The screen must not say *Analyst* for somebody who is
        effectively a member again.** ⛔ Showing a role they are not authorizing
        as is ADR-0410 §3's stale claim wearing a different coat."""
        person = uuid4()
        capabilities = _Capabilities()
        workspace = uuid4()
        await capabilities.assign(workspace, person, uuid4(), actor_id=uuid4())
        memberships = _Memberships()
        memberships.add(person, WorkspaceRole.MEMBER)

        view = await EffectivePermissions(
            capabilities=capabilities,
            memberships=memberships,
            authorizer=_RecordingAuthorizer(set()),
        ).execute(workspace, person)

        assert view is not None
        assert view.subject == "member"
        assert view.role_name is None
