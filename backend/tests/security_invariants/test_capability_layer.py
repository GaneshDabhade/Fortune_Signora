"""A capability role can narrow what a person may do, and never widen it.

📁 **[ADR-0410](../../../docs/architecture/adr/0410-authorization-capability-layer.md)
§5 requires this suite to hold the guarantee rather than the document to
describe it:**

> ✅ ***"The Security Invariants suite gains the guarantee rather than
> documenting it: a member must not acquire an owner's capability through the
> new layer."***

🔴 **Against the real enforcer and the real policy file**, because the whole
layer is *which string reaches Casbin* — and a fake authorizer would prove the
fake.

⚠️ **[TASK-1479](../../../docs/BACKLOG.md) slice ⓸.**
"""

from __future__ import annotations

from uuid import uuid4

import pytest

from modules.workspace_tenancy.domain.capability import (
    CapabilityAssignment,
    CapabilityError,
    CapabilityRole,
    subject_for,
)
from modules.workspace_tenancy.domain.entities import WorkspaceRole
from signora_platform.authorization import Action, CasbinAuthorizer, Resource


@pytest.fixture(scope="module")
def authorizer() -> CasbinAuthorizer:
    """The real enforcer, over the real `policy.csv`."""
    return CasbinAuthorizer()


class TestAMemberCannotAcquireAnOwnersCapability:
    """🔴 **ADR-0410 §5's invariant, end to end.**"""

    def test_no_capability_role_can_be_named_after_a_membership_role(self) -> None:
        """⛔ **`sub` is one string and the matcher is `==`.** A role that could
        be named `owner` would inherit every one of that role's policy rows —
        **which is the acquisition, exactly.**"""
        for membership in WorkspaceRole:
            for spelling in (membership.value, membership.value.upper(), f"  {membership.value} "):
                with pytest.raises(CapabilityError):
                    CapabilityRole(id=uuid4(), name=spelling)

    def test_a_capability_subject_grants_nothing_until_policy_says_so(
        self, authorizer: CasbinAuthorizer
    ) -> None:
        """🔴 **The load-bearing one, and it is a property of Casbin's default.**

        📁 ADR-0410 §5: *"A capability that is not yet granted denies, which is
        the safe direction; the reverse is a security defect."*

        ⚡ **A brand-new role has no `policy.csv` rows**, so it must be refused
        everything — **including the reads a `member` is freely granted.**
        ⛔ **If this ever passed, creating a role would be a privilege
        escalation**: name one, get assigned it, inherit whatever the matcher
        happened to fall through to.
        """
        unknown = CapabilityRole(id=uuid4(), name="Nothing Is Granted To This")
        workspace = uuid4()

        for resource in (Resource.WORKSPACE, Resource.MEMBER, Resource.ACCOUNT):
            for action in (Action.READ, Action.UPDATE):
                assert not authorizer.is_allowed(
                    role=unknown.key,
                    workspace_id=workspace,
                    resource=resource,
                    action=action,
                ), f"a role with no policy rows was allowed to {action} {resource}"

    def test_a_member_on_a_capability_role_loses_the_members_grants(
        self, authorizer: CasbinAuthorizer
    ) -> None:
        """⚡ **Replacement is what makes narrowing possible**, and this is the
        half that proves it is narrowing rather than addition.

        ⛔ **A member may `read` a workspace** — `policy.csv` says so. **A
        member holding an ungranted capability role may not**, because the
        subject Casbin is asked about is no longer `member`.
        """
        workspace, person = uuid4(), uuid4()
        analyst = CapabilityRole(id=uuid4(), name="Analyst")
        assignment = CapabilityAssignment(user_id=person, role_id=analyst.id)

        as_member = subject_for(WorkspaceRole.MEMBER, None, None)
        as_analyst = subject_for(WorkspaceRole.MEMBER, assignment, analyst)

        assert authorizer.is_allowed(
            role=as_member, workspace_id=workspace, resource=Resource.WORKSPACE,
            action=Action.READ,
        )
        assert not authorizer.is_allowed(
            role=as_analyst, workspace_id=workspace, resource=Resource.WORKSPACE,
            action=Action.READ,
        )

    def test_an_owner_on_a_capability_role_loses_the_owners_grants(
        self, authorizer: CasbinAuthorizer
    ) -> None:
        """🔴 **The direction that matters most.**

        ⛔ **An owner narrowed to a capability role must not keep `member,
        add`** — the grant that lets somebody bring a person into the
        workspace. ⚡ **If replacement leaked, narrowing an owner would be
        cosmetic**, and a screen would say *Analyst* while the enforcement
        point still said owner.
        """
        workspace, person = uuid4(), uuid4()
        analyst = CapabilityRole(id=uuid4(), name="Analyst")
        assignment = CapabilityAssignment(user_id=person, role_id=analyst.id)

        assert authorizer.is_allowed(
            role=subject_for(WorkspaceRole.OWNER, None, None),
            workspace_id=workspace, resource=Resource.MEMBER, action=Action.ADD,
        )
        assert not authorizer.is_allowed(
            role=subject_for(WorkspaceRole.OWNER, assignment, analyst),
            workspace_id=workspace, resource=Resource.MEMBER, action=Action.ADD,
        )


class TestTheLayerIsAdditiveUntilSomebodyUsesIt:
    """📁 **ADR-0410 §5: *"No existing membership changes meaning. Every current
    OWNER and every current MEMBER keeps exactly the authority it has
    today."*** ⚡ **True by construction, and this is what proves it.**"""

    @pytest.mark.parametrize("membership", list(WorkspaceRole))
    def test_a_person_with_no_assignment_authorizes_exactly_as_before(
        self, authorizer: CasbinAuthorizer, membership: WorkspaceRole
    ) -> None:
        """⛔ **The subject is the bare membership role**, so every one of that
        role's `policy.csv` grants applies unchanged. ⚡ **Nobody holds a
        capability role until somebody assigns one**, which is why the
        migration needs no step."""
        workspace = uuid4()

        assert subject_for(membership, None, None) == membership.value
        assert authorizer.is_allowed(
            role=subject_for(membership, None, None),
            workspace_id=workspace, resource=Resource.WORKSPACE, action=Action.READ,
        )

    def test_an_assignment_that_was_changed_back_authorizes_as_before(
        self, authorizer: CasbinAuthorizer
    ) -> None:
        """⚡ ***"Change back"* is a real act**, and it must restore exactly what
        the person had — **not something equivalent-looking.**"""
        changed_back = CapabilityAssignment(user_id=uuid4(), role_id=None)

        assert subject_for(WorkspaceRole.OWNER, changed_back, None) == "owner"
        assert authorizer.is_allowed(
            role=subject_for(WorkspaceRole.OWNER, changed_back, None),
            workspace_id=uuid4(), resource=Resource.MEMBER, action=Action.ADD,
        )

    def test_a_deleted_role_returns_a_person_to_their_membership_and_never_to_nothing(
        self, authorizer: CasbinAuthorizer
    ) -> None:
        """🔴 **The failure mode this fallback exists for.**

        ⛔ **A subject of `""` or a raised error would deny everything** —
        including reading the screen somebody would use to fix it. ⚡ **Falling
        back is a state the product already supports**, and it is the one they
        were in yesterday.

        ⚠️ **Migration `0057` makes this hard to reach** — `ON DELETE RESTRICT`
        refuses to delete a role people hold — **but the read is not
        transactional with the assignment**, so the window exists and the rule
        is stated rather than assumed away.
        """
        orphaned = CapabilityAssignment(user_id=uuid4(), role_id=uuid4())

        assert subject_for(WorkspaceRole.MEMBER, orphaned, None) == "member"
        assert authorizer.is_allowed(
            role=subject_for(WorkspaceRole.MEMBER, orphaned, None),
            workspace_id=uuid4(), resource=Resource.WORKSPACE, action=Action.READ,
        )


class TestThePolicyFileHoldsNoCapabilityGrantsYet:
    def test_no_capability_subject_appears_in_policy_csv(self) -> None:
        """⚠️ **A guard on the slice's own claim, not on the code.**

        ⛔ **This slice ships the layer and grants nothing through it**, so
        `policy.csv` must contain no `cap:` subject. 🔴 **The day somebody adds
        one, this test fails and they have to say what they granted and to
        whom** — which is the review ADR-0410 §2 says `policy.csv` exists to
        get.
        """
        from pathlib import Path

        policy = Path(__file__).resolve().parents[2] / (
            "signora_platform/authorization/policies/policy.csv"
        )

        assert "cap:" not in policy.read_text()
