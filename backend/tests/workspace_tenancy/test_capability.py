"""The capability layer's one decision — [TASK-1479](../../../docs/BACKLOG.md) ⓸.

🔴 **The subject is `subject_for`**, which is the whole layer: one string,
handed to an authorizer that already existed, and **the rule that decides
which string.**

📁 **[ADR-0410](../../../docs/architecture/adr/0410-authorization-capability-layer.md)
§5 names the invariant these exist to hold**: *"a member must not acquire an
owner's capability through the new layer."*
"""

from __future__ import annotations

from uuid import uuid4

import pytest

from modules.workspace_tenancy.domain.capability import (
    MAX_ROLE_NAME,
    CapabilityAssignment,
    CapabilityError,
    CapabilityRole,
    subject_for,
)
from modules.workspace_tenancy.domain.entities import WorkspaceRole


class TestAMemberCannotAcquireAnOwnersCapability:
    """🔴 **ADR-0410 §5's invariant, and the type is what holds it.**"""

    @pytest.mark.parametrize("reserved", ["owner", "member", "OWNER", "  Member  "])
    def test_a_capability_role_cannot_be_named_after_a_membership_role(
        self, reserved: str
    ) -> None:
        """⛔ **`sub` is one string.** A role named `owner` would be handed to
        `is_allowed` as `"owner"` and would match **all 44 of that membership
        role's policy rows** — which is exactly the acquisition §5 forbids.

        ⚡ **Case and whitespace too**, because `Owner` and `owner` are one name
        to Casbin's matcher after nothing at all: the matcher is `==`.
        """
        with pytest.raises(CapabilityError):
            CapabilityRole(id=uuid4(), name=reserved)

    def test_the_reserved_names_are_derived_from_the_enum_rather_than_listed(self) -> None:
        """🔴 **A hand-written list would go stale the day a membership role is
        added**, and the stale entry is the one nobody notices.

        ⚡ **Asserted by construction**: every member of the enum is refused,
        whatever it is, so adding a third membership role tomorrow protects
        itself.
        """
        for role in WorkspaceRole:
            with pytest.raises(CapabilityError):
                CapabilityRole(id=uuid4(), name=role.value)

    def test_the_key_is_namespaced_so_a_future_membership_role_cannot_collide(self) -> None:
        """⚠️ **The list can only refuse what exists today.**

        ⛔ A customer could name a role after a membership role this repository
        has not invented yet, and `RESERVED_ROLE_NAMES` would allow it. ✅ **The
        prefix makes the two namespaces disjoint by construction**, which is
        the guarantee a list cannot give.
        """
        analyst = CapabilityRole(id=uuid4(), name="Analyst")

        assert analyst.key.startswith("cap:")
        assert analyst.key not in {role.value for role in WorkspaceRole}


class TestWhichStringReachesCasbin:
    def test_no_assignment_is_the_membership_role(self) -> None:
        """✅ **The ordinary state, and it is what makes ADR-0410 §5's migration
        guarantee true by construction rather than by care.** Nobody holds a
        capability role until somebody assigns one."""
        assert subject_for(WorkspaceRole.MEMBER, None, None) == "member"
        assert subject_for(WorkspaceRole.OWNER, None, None) == "owner"

    def test_an_assignment_with_no_role_is_the_membership_role(self) -> None:
        """⚡ **`role_id is None` is *this person holds no capability role***,
        which is a real recorded state — somebody was changed back."""
        assignment = CapabilityAssignment(user_id=uuid4())

        assert subject_for(WorkspaceRole.MEMBER, assignment, None) == "member"

    def test_an_assigned_role_replaces_the_membership_role_rather_than_adding(self) -> None:
        """🔴 **The decision this slice makes**, and ADR-0410 §7 delegates it.

        ⛔ **Not a union.** 📁 The design says *"Change to Analyst"* and
        *"Effective permissions"* — **a change, and one resolved answer** — and
        a union would make a narrower role unbuildable, which the design draws
        `Analyst` as.
        """
        analyst = CapabilityRole(id=uuid4(), name="Analyst")
        assignment = CapabilityAssignment(user_id=uuid4(), role_id=analyst.id)

        subject = subject_for(WorkspaceRole.MEMBER, assignment, analyst)

        assert subject == analyst.key
        assert subject != "member"

    def test_an_owner_with_a_capability_role_is_that_role_and_not_owner(self) -> None:
        """⚠️ **The half that looks wrong and is the point.**

        ⛔ **An owner who has been changed to `Analyst` is an Analyst**, and
        that is what *"Change to Analyst"* means on the screen. ⚡ **Membership
        still says they may administer the workspace** — adding and removing
        people is `WorkspaceRole`'s, checked in `workspace_tenancy` — **so the
        two concerns stay separate exactly as ADR-0410 §1 requires.**
        """
        analyst = CapabilityRole(id=uuid4(), name="Analyst")
        assignment = CapabilityAssignment(user_id=uuid4(), role_id=analyst.id)

        assert subject_for(WorkspaceRole.OWNER, assignment, analyst) == analyst.key

    def test_a_role_that_no_longer_resolves_falls_back_to_membership(self) -> None:
        """🔴 **Not defensive coding — the alternative denies everything.**

        ⛔ A role deleted between two reads would otherwise leave a person with
        no subject at all, **including no permission to open the screen that
        would let somebody fix it.** ✅ **Falling back is the state they were in
        before anybody assigned anything**, which is a state the product
        already supports.
        """
        assignment = CapabilityAssignment(user_id=uuid4(), role_id=uuid4())

        assert subject_for(WorkspaceRole.MEMBER, assignment, None) == "member"

    def test_a_mismatched_role_is_a_caller_defect_rather_than_a_fallback(self) -> None:
        """⛔ **Silently using the membership role here would hide a resolution
        bug behind a working screen** — and the screen would then show
        permissions the enforcement point does not honour, which is ADR-0410
        §3's *"a stale copy of what somebody may do"* arriving by a different
        route."""
        assigned = CapabilityRole(id=uuid4(), name="Analyst")
        somebody_elses = CapabilityRole(id=uuid4(), name="Admin")
        assignment = CapabilityAssignment(user_id=uuid4(), role_id=assigned.id)

        with pytest.raises(CapabilityError):
            subject_for(WorkspaceRole.MEMBER, assignment, somebody_elses)


class TestARoleHasAnIdentityAndTheNameIsNotIt:
    def test_renaming_keeps_the_id(self) -> None:
        original = CapabilityRole(id=uuid4(), name="Analyst")

        renamed = original.renamed("Revenue Analyst")

        assert renamed.id == original.id

    def test_renaming_moves_the_key_and_that_is_the_difference_from_a_tag(self) -> None:
        """⚠️ **Stated rather than hidden.** 📁 The key is what `policy.csv`
        holds, so **a rename is a policy edit as well as a row update** — and a
        renamed role whose grants were not moved denies everything, silently,
        for everyone holding it."""
        original = CapabilityRole(id=uuid4(), name="Analyst")

        renamed = original.renamed("Revenue Analyst")

        assert renamed.key != original.key

    @pytest.mark.parametrize("name", ["   ", "x" * (MAX_ROLE_NAME + 1)])
    def test_a_name_the_screen_cannot_show_is_refused(self, name: str) -> None:
        with pytest.raises(CapabilityError):
            CapabilityRole(id=uuid4(), name=name)

    def test_the_names_the_design_draws_fit(self) -> None:
        """⚡ **The limit is checked against the design rather than chosen.**"""
        for drawn in ("Admin", "Analyst", "Revenue Operations"):
            assert CapabilityRole(id=uuid4(), name=drawn).name == drawn

    def test_two_spellings_a_customer_cannot_tell_apart_produce_one_key(self) -> None:
        """⛔ **`Analyst` and `analyst` are one role to the person who typed
        them**, and the key is what decides."""
        assert (
            CapabilityRole(id=uuid4(), name="Analyst").key
            == CapabilityRole(id=uuid4(), name="  ANALYST ").key
        )
