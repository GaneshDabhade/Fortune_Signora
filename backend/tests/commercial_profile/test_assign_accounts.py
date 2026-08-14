"""Who may be named as an owner — [TASK-1479](../../../docs/BACKLOG.md) slice ⓶.

🔴 **The membership check is what makes ADR-0411's *reference, not free text*
true.** An unverified reference is free text with a `UUID` type.
"""

from __future__ import annotations

from uuid import UUID, uuid4

import pytest

from modules.commercial_profile.application.assignment_use_cases import (
    AssignAccounts,
    AssignAccountsInput,
    NotAWorkspaceMemberError,
    ReverseAssignment,
)
from modules.commercial_profile.domain.account_assignment import (
    AccountAssignment,
    AccountRole,
    AssignmentError,
    Reassignment,
)
from modules.workspace_tenancy.public.query_port import MembershipView


class _Repository:
    """A fake that records what it was asked, so a test can assert that a
    refusal wrote **nothing** rather than merely returned an error."""

    def __init__(self) -> None:
        self.assigned: list[tuple[UUID, ...]] = []
        self.restored: list[tuple[tuple[UUID, UUID | None], ...]] = []

    async def for_accounts(
        self, workspace_id: UUID, account_ids: tuple[UUID, ...]
    ) -> tuple[AccountAssignment, ...]:
        return ()

    async def assign(
        self,
        workspace_id: UUID,
        account_ids: tuple[UUID, ...],
        *,
        role: AccountRole,
        member_user_id: UUID,
        actor_id: UUID,
    ) -> Reassignment:
        self.assigned.append(account_ids)
        return Reassignment(
            role=role, previous=tuple((account, None) for account in account_ids)
        )

    async def restore(
        self,
        workspace_id: UUID,
        previous: tuple[tuple[UUID, UUID | None], ...],
        *,
        role: AccountRole,
        actor_id: UUID,
    ) -> None:
        self.restored.append(previous)


class _Workspaces:
    def __init__(self, *, members: set[UUID]) -> None:
        self._members = members

    async def workspace_exists(self, workspace_id: UUID) -> bool:
        return True

    async def get_membership(
        self, workspace_id: UUID, user_id: UUID
    ) -> MembershipView | None:
        if user_id not in self._members:
            return None
        return MembershipView(workspace_id=workspace_id, user_id=user_id, role="member")


def _request(member: UUID, accounts: tuple[UUID, ...]) -> AssignAccountsInput:
    return AssignAccountsInput(
        workspace_id=uuid4(),
        account_ids=accounts,
        role=AccountRole.OWNER,
        member_user_id=member,
        actor_id=uuid4(),
    )


class TestAReferenceIsCheckedWhenItIsMade:
    async def test_a_member_can_be_assigned(self) -> None:
        member, account = uuid4(), uuid4()
        repository = _Repository()
        use_case = AssignAccounts(
            repository=repository, workspaces=_Workspaces(members={member})
        )

        outcome = await use_case.execute(_request(member, (account,)))

        assert outcome.previous == ((account, None),)

    async def test_somebody_who_is_not_a_member_is_refused(self) -> None:
        """📁 **The ruling's own reasoning**: *"a person who leaves must not
        leave a dangling string"* — ⛔ **which only holds if the reference is
        checked when it is made.**"""
        stranger, account = uuid4(), uuid4()
        use_case = AssignAccounts(
            repository=_Repository(), workspaces=_Workspaces(members=set())
        )

        with pytest.raises(NotAWorkspaceMemberError):
            await use_case.execute(_request(stranger, (account,)))

    async def test_a_refusal_writes_nothing(self) -> None:
        """🔴 **Membership first, and before any write.**

        ⛔ Verifying afterwards would mean a rejected assignment had already
        changed rows, and correctness would depend on a transaction rollback
        undoing something the domain should never have accepted.
        """
        repository = _Repository()
        use_case = AssignAccounts(repository=repository, workspaces=_Workspaces(members=set()))

        with pytest.raises(NotAWorkspaceMemberError):
            await use_case.execute(_request(uuid4(), (uuid4(),)))

        assert repository.assigned == []

    def test_the_refusal_says_which_person(self) -> None:
        """⚠️ **A distinct error, because the two ways this fails are answered
        by different people.** *"This account does not exist"* is the caller's
        mistake; *"this person is not on your team"* is something the customer
        can act on."""
        stranger = uuid4()

        assert str(stranger) in str(NotAWorkspaceMemberError(stranger))


class TestAnEmptySelectionIsADefectRatherThanANoOp:
    async def test_it_is_refused(self) -> None:
        """⛔ **A successful no-op would let a broken selection look like a
        completed action** — P-A's shape, one layer up: an absence must not
        render as a success."""
        member = uuid4()
        use_case = AssignAccounts(
            repository=_Repository(), workspaces=_Workspaces(members={member})
        )

        with pytest.raises(AssignmentError):
            await use_case.execute(_request(member, ()))

    async def test_it_is_refused_before_membership_is_even_asked(self) -> None:
        """The caller's defect is answered without a cross-module read."""
        repository = _Repository()
        use_case = AssignAccounts(repository=repository, workspaces=_Workspaces(members=set()))

        with pytest.raises(AssignmentError) as refusal:
            await use_case.execute(_request(uuid4(), ()))

        assert not isinstance(refusal.value, NotAWorkspaceMemberError)


class TestReversingDoesNotRecheckMembership:
    async def test_a_departed_member_is_still_restored(self) -> None:
        """⛔ **Deliberate, and it is the harder call.**

        The previous holders were members when they were assigned. **If one has
        since left, restoring them is still the correct reversal** — the
        alternative is an undo that silently declines to undo part of what it
        was asked to undo, and a customer who pressed *take it back* would find
        it partly taken back.
        """
        departed, account = uuid4(), uuid4()
        repository = _Repository()

        await ReverseAssignment(repository=repository).execute(
            uuid4(),
            Reassignment(role=AccountRole.OWNER, previous=((account, departed),)),
            actor_id=uuid4(),
        )

        assert repository.restored == [((account, departed),)]

    async def test_it_restores_what_moved_and_not_what_was_asked(self) -> None:
        moved, untouched = uuid4(), uuid4()
        repository = _Repository()

        await ReverseAssignment(repository=repository).execute(
            uuid4(),
            Reassignment(
                role=AccountRole.OWNER,
                previous=((moved, uuid4()),),
                unchanged=(untouched,),
            ),
            actor_id=uuid4(),
        )

        restored_accounts = [account for account, _ in repository.restored[0]]
        assert restored_accounts == [moved]
