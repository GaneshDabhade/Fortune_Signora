"""Somebody no longer belongs to an organization.

**The rules a customer would notice going wrong**: an organization left with
nobody who can administer it, a departure that quietly erased who decided what,
or a removal that could be performed twice and overwrote the moment it really
happened.
"""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest

from modules.workspace_tenancy.application.use_cases.remove_member import (
    MembershipNotFoundError,
    RemoveMember,
    RemoveMemberCommand,
)
from modules.workspace_tenancy.domain.entities import (
    LastOwnerCannotLeaveError,
    Membership,
    MembershipAlreadyEndedError,
    WorkspaceRole,
)
from modules.workspace_tenancy.tests.fakes import FakeMembershipRepository

NOW = datetime(2026, 8, 2, 9, 0, tzinfo=UTC)
WORKSPACE = uuid4()
ANA = uuid4()
RAVI = uuid4()


def member(role: WorkspaceRole, user_id: UUID | None = None) -> Membership:
    membership, _ = Membership.create(
        workspace_id=WORKSPACE,
        user_id=user_id or uuid4(),
        role=role,
        created_by=ANA,
    )
    return membership


async def remove(
    repo: FakeMembershipRepository, membership: Membership, *, reason: str | None = None
) -> Membership:
    return await RemoveMember(memberships=repo).execute(
        RemoveMemberCommand(
            workspace_id=WORKSPACE,
            membership_id=membership.id,
            removed_by=ANA,
            reason=reason,
        ),
        now=NOW,
    )


class TestTheRecordSurvives:
    async def test_the_membership_is_ended_rather_than_deleted(self) -> None:
        # Decision history, the timeline and every audit question cite a
        # membership. Deleting one would silently rewrite what a customer has
        # already read.
        repo = FakeMembershipRepository()
        one, two = member(WorkspaceRole.OWNER), member(WorkspaceRole.MEMBER)
        repo.memberships.extend([one, two])

        await remove(repo, two)

        assert len(repo.memberships) == 2
        assert two.ended_at == NOW

    async def test_it_records_who_ended_it(self) -> None:
        repo = FakeMembershipRepository()
        one, two = member(WorkspaceRole.OWNER), member(WorkspaceRole.MEMBER)
        repo.memberships.extend([one, two])

        await remove(repo, two)

        assert two.ended_by == ANA

    async def test_it_keeps_the_reason_verbatim(self) -> None:
        # Somebody's sentence about a colleague. A normalised or truncated
        # version would be the product editing it.
        repo = FakeMembershipRepository()
        one, two = member(WorkspaceRole.OWNER), member(WorkspaceRole.MEMBER)
        repo.memberships.extend([one, two])

        await remove(repo, two, reason="  Left the company on 1 August  ")

        assert two.ended_reason == "Left the company on 1 August"

    async def test_an_absent_reason_stays_absent(self) -> None:
        # An administrator correcting a mistaken invitation should not be made
        # to justify it, and an empty string is not a reason.
        repo = FakeMembershipRepository()
        one, two = member(WorkspaceRole.OWNER), member(WorkspaceRole.MEMBER)
        repo.memberships.extend([one, two])

        await remove(repo, two, reason="   ")

        assert two.ended_reason is None

    async def test_who_created_the_membership_never_changes(self) -> None:
        # The audit trail must still answer *who let this person in* after they
        # have gone.
        repo = FakeMembershipRepository()
        one, two = member(WorkspaceRole.OWNER), member(WorkspaceRole.MEMBER)
        repo.memberships.extend([one, two])

        await remove(repo, two)

        assert two.created_by == ANA


class TestAnOrganizationAlwaysHasSomebodyWhoCanAdministerIt:
    async def test_the_last_owner_cannot_be_removed(self) -> None:
        repo = FakeMembershipRepository()
        sole = member(WorkspaceRole.OWNER)
        repo.memberships.extend([sole, member(WorkspaceRole.MEMBER)])

        with pytest.raises(LastOwnerCannotLeaveError):
            await remove(repo, sole)

    async def test_the_refusal_leaves_the_membership_untouched(self) -> None:
        # A half-applied refusal would be worse than none: the row would say
        # somebody had left while they were still the only administrator.
        repo = FakeMembershipRepository()
        sole = member(WorkspaceRole.OWNER)
        repo.memberships.append(sole)

        with pytest.raises(LastOwnerCannotLeaveError):
            await remove(repo, sole)
        assert sole.is_live and sole.ended_by is None

    async def test_one_of_two_owners_can_be_removed(self) -> None:
        repo = FakeMembershipRepository()
        first, second = member(WorkspaceRole.OWNER), member(WorkspaceRole.OWNER)
        repo.memberships.extend([first, second])

        await remove(repo, second)

        assert second.ended_at == NOW and first.is_live

    async def test_the_last_member_can_be_removed_when_an_owner_remains(self) -> None:
        # The rule is about *administration*, not about being alone.
        repo = FakeMembershipRepository()
        owner, only_member = member(WorkspaceRole.OWNER), member(WorkspaceRole.MEMBER)
        repo.memberships.extend([owner, only_member])

        await remove(repo, only_member)

        assert only_member.ended_at == NOW

    async def test_an_already_ended_owner_does_not_count_toward_the_rule(self) -> None:
        # Otherwise a removed owner would keep protecting a workspace they had
        # left, and the last real owner could never be removed.
        repo = FakeMembershipRepository()
        gone, sole = member(WorkspaceRole.OWNER), member(WorkspaceRole.OWNER)
        repo.memberships.extend([gone, sole])
        await remove(repo, gone)

        with pytest.raises(LastOwnerCannotLeaveError):
            await remove(repo, sole)


class TestItRefusesWhatWouldClaimNothing:
    async def test_removing_twice_is_refused(self) -> None:
        # The second call would overwrite the moment the departure actually
        # happened, which is the one fact the record exists to hold.
        repo = FakeMembershipRepository()
        one, two = member(WorkspaceRole.OWNER), member(WorkspaceRole.MEMBER)
        repo.memberships.extend([one, two])
        await remove(repo, two)

        with pytest.raises(MembershipAlreadyEndedError):
            await remove(repo, two)

    async def test_an_unknown_membership_is_refused(self) -> None:
        repo = FakeMembershipRepository()

        with pytest.raises(MembershipNotFoundError):
            await remove(repo, member(WorkspaceRole.MEMBER))


class TestAnEndedMembershipStopsGrantingAnything:
    async def test_it_no_longer_resolves_as_membership(self) -> None:
        # **The security-relevant one.** This lookup is what verifies membership
        # on every request; an ended membership that still resolved would keep
        # somebody signed in to an organization they had been removed from.
        repo = FakeMembershipRepository()
        owner, leaver = member(WorkspaceRole.OWNER), member(WorkspaceRole.MEMBER, RAVI)
        repo.memberships.extend([owner, leaver])

        await remove(repo, leaver)

        assert await repo.get(WORKSPACE, RAVI) is None

    async def test_it_leaves_the_roster(self) -> None:
        repo = FakeMembershipRepository()
        owner, leaver = member(WorkspaceRole.OWNER), member(WorkspaceRole.MEMBER)
        repo.memberships.extend([owner, leaver])

        await remove(repo, leaver)
        listed = await repo.list_page_for_workspace(WORKSPACE, limit=10, after=None)

        assert [m.id for m in listed] == [owner.id]

    async def test_it_is_still_findable_by_id_for_the_audit_trail(self) -> None:
        repo = FakeMembershipRepository()
        owner, leaver = member(WorkspaceRole.OWNER), member(WorkspaceRole.MEMBER)
        repo.memberships.extend([owner, leaver])

        await remove(repo, leaver)

        assert await repo.get_by_id(WORKSPACE, leaver.id) is not None
