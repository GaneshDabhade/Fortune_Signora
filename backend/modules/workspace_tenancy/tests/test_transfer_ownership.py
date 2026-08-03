"""Handing an organization over.

**The scenarios the product owner asked about**, and most of them collapse
into the transaction and the lock — which is the useful result: it says the
design is right rather than that the questions were unnecessary.
"""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest

from modules.workspace_tenancy.application.use_cases.remove_member import (
    MembershipNotFoundError,
)
from modules.workspace_tenancy.application.use_cases.transfer_ownership import (
    TransferOwnership,
    TransferOwnershipCommand,
)
from modules.workspace_tenancy.domain.entities import (
    Membership,
    MembershipAlreadyEndedError,
    OwnershipTransferError,
    WorkspaceRole,
)
from modules.workspace_tenancy.tests.fakes import FakeMembershipRepository, FakeRoleChangeLog

NOW = datetime(2026, 8, 3, 9, 0, tzinfo=UTC)
WORKSPACE = uuid4()
ANA = uuid4()


def member(role: WorkspaceRole, workspace: UUID | None = None) -> Membership:
    membership, _ = Membership.create(
        workspace_id=workspace or WORKSPACE,
        user_id=uuid4(),
        role=role,
        created_by=ANA,
    )
    return membership


async def hand_over(
    repo: FakeMembershipRepository,
    log: FakeRoleChangeLog,
    outgoing: Membership,
    incoming: Membership,
) -> tuple[Membership, Membership]:
    return await TransferOwnership(memberships=repo, history=log).execute(
        TransferOwnershipCommand(
            workspace_id=WORKSPACE,
            from_membership_id=outgoing.id,
            to_membership_id=incoming.id,
            performed_by=ANA,
        ),
        now=NOW,
    )


def pair() -> tuple[FakeMembershipRepository, FakeRoleChangeLog, Membership, Membership]:
    repo, log = FakeMembershipRepository(), FakeRoleChangeLog()
    owner, colleague = member(WorkspaceRole.OWNER), member(WorkspaceRole.MEMBER)
    repo.memberships.extend([owner, colleague])
    return repo, log, owner, colleague


class TestItHappensAsOneAct:
    async def test_authority_moves_in_both_directions(self) -> None:
        repo, log, owner, colleague = pair()

        await hand_over(repo, log, owner, colleague)

        assert colleague.role is WorkspaceRole.OWNER
        assert owner.role is WorkspaceRole.MEMBER

    async def test_the_organization_is_never_left_with_two_owners(self) -> None:
        # **The reason this is one operation.** Promote-then-demote leaves a
        # window nobody asked for, permanent if the second step never runs.
        repo, log, owner, colleague = pair()

        await hand_over(repo, log, owner, colleague)
        owners = [m for m in repo.memberships if m.role is WorkspaceRole.OWNER]

        assert len(owners) == 1

    async def test_the_last_owner_rule_is_not_consulted(self) -> None:
        # It protects against ending with nobody. This ends with exactly one,
        # and checking it mid-operation would refuse the thing that satisfies it.
        repo, log, sole, colleague = pair()

        await hand_over(repo, log, sole, colleague)

        assert colleague.role is WorkspaceRole.OWNER

    async def test_the_membership_set_is_locked_first(self) -> None:
        repo, log, owner, colleague = pair()
        locked: list[UUID] = []
        original = repo.lock_membership_set

        async def watching(workspace_id: UUID) -> None:
            locked.append(workspace_id)
            await original(workspace_id)

        repo.lock_membership_set = watching  # type: ignore[method-assign]
        await hand_over(repo, log, owner, colleague)

        assert locked == [WORKSPACE]


class TestBothChangesAreRecorded:
    async def test_two_entries_because_two_people_changed(self) -> None:
        repo, log, owner, colleague = pair()

        await hand_over(repo, log, owner, colleague)

        assert len(log.entries) == 2

    async def test_it_records_the_promotion_and_the_step_back(self) -> None:
        repo, log, owner, colleague = pair()

        await hand_over(repo, log, owner, colleague)
        moves = {(e["previous_role"], e["new_role"]) for e in log.entries}

        assert moves == {
            (WorkspaceRole.MEMBER, WorkspaceRole.OWNER),
            (WorkspaceRole.OWNER, WorkspaceRole.MEMBER),
        }

    async def test_both_name_who_performed_it(self) -> None:
        repo, log, owner, colleague = pair()

        await hand_over(repo, log, owner, colleague)

        assert all(entry["changed_by"] == ANA for entry in log.entries)


class TestTheScenariosThatWouldStrandAnOrganization:
    async def test_a_recipient_removed_while_the_dialog_was_open_is_refused(self) -> None:
        # **Checked before anything is mutated.** Otherwise they would be
        # promoted and then found to have left.
        repo, log, owner, colleague = pair()
        colleague.end(by=ANA, at=NOW, reason=None, remaining_owners=1)

        with pytest.raises(MembershipAlreadyEndedError):
            await hand_over(repo, log, owner, colleague)

    async def test_the_refusal_leaves_both_roles_untouched(self) -> None:
        repo, log, owner, colleague = pair()
        colleague.end(by=ANA, at=NOW, reason=None, remaining_owners=1)

        with pytest.raises(MembershipAlreadyEndedError):
            await hand_over(repo, log, owner, colleague)
        assert owner.role is WorkspaceRole.OWNER
        assert log.entries == []

    async def test_somebody_who_lost_ownership_first_cannot_hand_it_over(self) -> None:
        # The race the lock exists for, seen from the losing side: a concurrent
        # demotion lands first, and this transaction finds a member rather than
        # an owner.
        repo, log, owner, colleague = pair()
        owner.role = WorkspaceRole.MEMBER

        with pytest.raises(OwnershipTransferError):
            await hand_over(repo, log, owner, colleague)

    async def test_handing_over_to_yourself_is_refused(self) -> None:
        repo, log, owner, _ = pair()

        with pytest.raises(OwnershipTransferError):
            await hand_over(repo, log, owner, owner)

    async def test_somebody_in_another_organization_is_simply_not_found(self) -> None:
        # **The domain guard for this was written, and removed.** Both
        # memberships are fetched scoped to one workspace and RLS scopes them
        # again beneath that, so the check could never fire — documentation
        # pretending to be code. This asserts the protection that is real.
        repo, log = FakeMembershipRepository(), FakeRoleChangeLog()
        owner = member(WorkspaceRole.OWNER)
        elsewhere = member(WorkspaceRole.MEMBER, workspace=uuid4())
        repo.memberships.extend([owner, elsewhere])

        with pytest.raises(MembershipNotFoundError):
            await hand_over(repo, log, owner, elsewhere)

    async def test_an_unknown_recipient_is_refused(self) -> None:
        repo, log, owner, _ = pair()

        with pytest.raises(MembershipNotFoundError):
            await hand_over(repo, log, owner, member(WorkspaceRole.MEMBER))
