"""A person decides they no longer belong to an organization.

**The half of team management the product never had.** `member:remove` let an
administrator end somebody's involvement and nothing let a person end their
own, so the only way out was to ask somebody else.

The rules a customer would notice going wrong: an organization left with nobody
who can administer it, a departure that could be performed twice, or a leaver
who could name somebody else's membership on the way out.
"""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest

from modules.workspace_tenancy.application.use_cases.leave_workspace import (
    LeaveWorkspace,
    LeaveWorkspaceCommand,
    NotAMemberError,
)
from modules.workspace_tenancy.domain.entities import (
    LastOwnerCannotLeaveError,
    Membership,
    WorkspaceRole,
)
from modules.workspace_tenancy.tests.fakes import FakeMembershipRepository

NOW = datetime(2026, 8, 5, 9, 0, tzinfo=UTC)
WORKSPACE = uuid4()
ANA = uuid4()
RAVI = uuid4()


def repo_with(*memberships: Membership) -> FakeMembershipRepository:
    repo = FakeMembershipRepository()
    repo.memberships.extend(memberships)
    return repo


def member(role: WorkspaceRole, user_id: UUID) -> Membership:
    membership, _ = Membership.create(
        workspace_id=WORKSPACE,
        user_id=user_id,
        role=role,
        created_by=ANA,
    )
    return membership


async def leave(repo: FakeMembershipRepository, user_id: UUID) -> Membership:
    return await LeaveWorkspace(memberships=repo).execute(
        LeaveWorkspaceCommand(workspace_id=WORKSPACE, user_id=user_id),
        now=NOW,
    )


class TestAPersonCanEndTheirOwnInvolvement:
    async def test_a_member_can_leave(self) -> None:
        repo = repo_with(member(WorkspaceRole.OWNER, ANA), member(WorkspaceRole.MEMBER, RAVI))

        left = await leave(repo, RAVI)

        assert left.is_live is False
        assert left.ended_at == NOW

    async def test_the_membership_is_ended_rather_than_deleted(self) -> None:
        """**Decision history, the timeline and every audit question cite it.**
        Removing the row would silently rewrite what a customer already read."""
        repo = repo_with(member(WorkspaceRole.OWNER, ANA), member(WorkspaceRole.MEMBER, RAVI))

        await leave(repo, RAVI)

        # **Not through `get`, which is live-only by design** — an ended
        # membership resolving there would keep somebody signed in to an
        # organization they had left. The row surviving is the thing being
        # asserted, so the assertion reads the store rather than the lookup.
        ended = [m for m in repo.memberships if m.user_id == RAVI]
        assert len(ended) == 1
        assert ended[0].ended_at == NOW

    async def test_the_leaver_is_recorded_as_having_ended_it_themselves(self) -> None:
        """**`ended_by == user_id` is what tells a departure from a removal**,
        and it is true by construction rather than by a flag somebody has to
        set correctly. In `RemoveMember` this field is the administrator."""
        repo = repo_with(member(WorkspaceRole.OWNER, ANA), member(WorkspaceRole.MEMBER, RAVI))

        left = await leave(repo, RAVI)

        assert left.ended_by == RAVI

    async def test_no_reason_is_recorded(self) -> None:
        """A person leaving owes the organization no explanation. The column
        holds somebody else's account of you, and empty is more honest than a
        sentence the product invented."""
        repo = repo_with(member(WorkspaceRole.OWNER, ANA), member(WorkspaceRole.MEMBER, RAVI))

        left = await leave(repo, RAVI)

        assert left.ended_reason is None


class TestAnOrganizationNeverBecomesOwnerless:
    """**ADR-0404, ruled**: *"an owner may leave; a workspace may never become
    ownerless. Enforce the invariant in the application layer rather than the
    authorization engine."*
    """

    async def test_the_last_owner_cannot_leave(self) -> None:
        repo = repo_with(member(WorkspaceRole.OWNER, ANA), member(WorkspaceRole.MEMBER, RAVI))

        with pytest.raises(LastOwnerCannotLeaveError):
            await leave(repo, ANA)

    async def test_an_owner_may_leave_when_another_owner_remains(self) -> None:
        """**The case the invariant must not over-refuse.** An administrator
        handing over and stepping back is the ordinary path, not the dangerous
        one."""
        repo = repo_with(member(WorkspaceRole.OWNER, ANA), member(WorkspaceRole.OWNER, RAVI))

        left = await leave(repo, ANA)

        assert left.is_live is False

    async def test_a_member_may_leave_even_when_one_owner_remains(self) -> None:
        """The rule counts owners, not people. A workspace of one owner and one
        member is not endangered by the member leaving."""
        repo = repo_with(member(WorkspaceRole.OWNER, ANA), member(WorkspaceRole.MEMBER, RAVI))

        left = await leave(repo, RAVI)

        assert left.is_live is False

    async def test_the_refusal_says_what_to_do_next(self) -> None:
        """The sentence is the domain's and reaches a customer verbatim. It is
        the reason this refusal is a 409 rather than a 500."""
        repo = repo_with(member(WorkspaceRole.OWNER, ANA))

        with pytest.raises(LastOwnerCannotLeaveError) as refusal:
            await leave(repo, ANA)

        assert "Make somebody else an owner first" in str(refusal.value)


class TestThereIsNothingToLeaveTwice:
    async def test_leaving_again_is_refused(self) -> None:
        """Reachable from a second tab. Accepting it would overwrite the moment
        the departure actually happened."""
        repo = repo_with(member(WorkspaceRole.OWNER, ANA), member(WorkspaceRole.MEMBER, RAVI))
        await leave(repo, RAVI)

        with pytest.raises(NotAMemberError):
            await leave(repo, RAVI)

    async def test_somebody_with_no_membership_is_refused(self) -> None:
        """`CurrentWorkspace` verifies membership before the request arrives, so
        the ordinary path cannot reach this — an administrator removing the
        caller mid-request can."""
        repo = repo_with(member(WorkspaceRole.OWNER, ANA))

        with pytest.raises(NotAMemberError):
            await leave(repo, RAVI)

    async def test_the_refusal_names_no_identifier(self) -> None:
        """Customer-facing copy interpolates no UUID — the same rule the signal
        resolution messages are held to."""
        repo = repo_with(member(WorkspaceRole.OWNER, ANA))

        with pytest.raises(NotAMemberError) as refusal:
            await leave(repo, RAVI)

        assert str(RAVI) not in str(refusal.value)
        assert str(WORKSPACE) not in str(refusal.value)


class TestLeavingCannotBeAimedAtSomebodyElse:
    async def test_the_command_carries_no_target(self) -> None:
        """**The safest parameter is the one that does not exist.** `RemoveMember`
        takes a `membership_id` because an administrator is pointing at
        somebody; nothing here points at anybody, so there is no identifier to
        substitute and no ownership check that could be written wrongly.
        """
        assert set(LeaveWorkspaceCommand.__dataclass_fields__) == {"workspace_id", "user_id"}

    async def test_one_person_leaving_ends_only_their_own_membership(self) -> None:
        repo = repo_with(member(WorkspaceRole.OWNER, ANA), member(WorkspaceRole.MEMBER, RAVI))

        await leave(repo, RAVI)

        remaining = await repo.get(WORKSPACE, ANA)
        assert remaining is not None
        assert remaining.is_live is True
