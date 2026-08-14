"""The bulk owner change, end to end — [TASK-1479](../../../docs/BACKLOG.md) ⓶a.

🔴 **This file exists because [B-201](../../../docs/BUGS.md) found the whole
batch path untested.** ⓶a shipped three use cases — propose, apply, reverse —
with **61% of `assignment_use_cases.py` covered**, and the uncovered 39% was
exactly the lifecycle a customer's *take it back* depends on.

⚠️ **Not a coverage exercise.** 📁 The gap was found by a repository-wide
number and the tests below are written from the behaviour, not from the missed
lines: **each one is a sentence about what a customer would see if it were
wrong**, and three of them describe outcomes nothing else in the suite asserts.

⚡ **The lesson is [§19](../../../CLAUDE.md)'s own bullet**, and it caught what
a slice-local check could not: *"no file the slice introduced sits at 0%"* was
satisfied — none did — **and the repository still went under the floor.**
"""

from __future__ import annotations

from datetime import timedelta
from uuid import UUID, uuid4

import pytest

from modules.commercial_profile.application.assignment_use_cases import (
    ApplyAssignmentBatch,
    NotAWorkspaceMemberError,
    ProposeAssignmentBatch,
    ProposeAssignmentBatchInput,
    ReverseAssignmentBatch,
)
from modules.commercial_profile.domain.account_assignment import (
    AccountAssignment,
    AccountRole,
    AssignmentBatch,
    AssignmentError,
    Reassignment,
)
from modules.workspace_tenancy.public.query_port import MembershipView


class _Proposer:
    """Records what was proposed, so a test can assert **the sentence a
    customer approves** rather than only that a call happened."""

    def __init__(self) -> None:
        self.proposals: list[dict[str, object]] = []

    async def propose(
        self,
        *,
        workspace_id: UUID,
        name: str,
        item_count: int,
        proposed_by: UUID,
        reversible_for: timedelta | None = None,
    ) -> UUID:
        batch_id = uuid4()
        self.proposals.append(
            {
                "workspace_id": workspace_id,
                "name": name,
                "item_count": item_count,
                "proposed_by": proposed_by,
                "reversible_for": reversible_for,
                "batch_id": batch_id,
            }
        )
        return batch_id


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


class _Batches:
    """The module's own row for a proposed batch."""

    def __init__(self, batch: AssignmentBatch | None = None) -> None:
        self._batch = batch
        self.applied: list[Reassignment] = []

    async def record(
        self, workspace_id: UUID, batch: AssignmentBatch, *, actor_id: UUID
    ) -> None:
        self._batch = batch

    async def by_id(self, workspace_id: UUID, batch_id: UUID) -> AssignmentBatch | None:
        if self._batch is None or self._batch.batch_id != batch_id:
            return None
        return self._batch

    async def record_applied(
        self, workspace_id: UUID, batch_id: UUID, moved: Reassignment, *, actor_id: UUID
    ) -> None:
        self.applied.append(moved)


class _Repository:
    def __init__(self, *, held_by: dict[UUID, UUID] | None = None) -> None:
        self._held_by = held_by or {}
        self.restored: list[tuple[tuple[UUID, UUID | None], ...]] = []
        self.restored_to: list[UUID | None] = []

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
        return Reassignment(
            role=role,
            assigned_to=member_user_id,
            previous=tuple(
                (account, self._held_by.get(account)) for account in account_ids
            ),
        )

    async def restore(
        self,
        workspace_id: UUID,
        previous: tuple[tuple[UUID, UUID | None], ...],
        *,
        role: AccountRole,
        assigned_to: UUID | None,
        actor_id: UUID,
    ) -> None:
        self.restored.append(previous)
        self.restored_to.append(assigned_to)


def _propose_input(member: UUID, accounts: tuple[UUID, ...]) -> ProposeAssignmentBatchInput:
    return ProposeAssignmentBatchInput(
        workspace_id=uuid4(),
        actor_id=uuid4(),
        account_ids=accounts,
        role=AccountRole.OWNER,
        member_user_id=member,
    )


class TestWhatTheCustomerIsAskedToApprove:
    async def test_the_batch_is_named_in_the_customer_s_words(self) -> None:
        """📁 **ADR-0034**: the approval screen shows a sentence a person can
        read. ⛔ **Never the member's NAME** — this module holds none by
        ADR-0411's own design, and inventing one here would be the duplicated
        identity the reference exists to avoid.
        """
        member = uuid4()
        proposer = _Proposer()
        use_case = ProposeAssignmentBatch(
            workspaces=_Workspaces(members={member}), proposer=proposer
        )

        await use_case.execute(_propose_input(member, (uuid4(), uuid4())))

        name = str(proposer.proposals[0]["name"])
        assert "2" in name
        assert str(member) not in name

    async def test_the_count_is_of_companies_and_not_of_clicks(self) -> None:
        """🔴 **De-duplicated BEFORE the count is taken.**

        ⚠️ A table offering *Select all 312* on top of an existing selection is
        exactly how one row arrives twice — and **the customer would approve
        *"3 companies"* while the batch touched two.**
        """
        member, repeated, other = uuid4(), uuid4(), uuid4()
        proposer = _Proposer()
        use_case = ProposeAssignmentBatch(
            workspaces=_Workspaces(members={member}), proposer=proposer
        )

        await use_case.execute(_propose_input(member, (repeated, other, repeated)))

        assert proposer.proposals[0]["item_count"] == 2

    async def test_a_reversal_window_travels_with_the_proposal(self) -> None:
        """⚡ **The window is `action_batch`'s to enforce and this module's to
        state.** ⛔ Proposing without one would make the batch permanent by
        omission."""
        member = uuid4()
        proposer = _Proposer()
        use_case = ProposeAssignmentBatch(
            workspaces=_Workspaces(members={member}), proposer=proposer
        )

        await use_case.execute(_propose_input(member, (uuid4(),)))

        assert proposer.proposals[0]["reversible_for"] is not None

    async def test_a_stranger_cannot_even_be_proposed(self) -> None:
        """⚠️ **The FIRST of two membership checks, and it is not redundant.**
        A proposal a customer cannot act on is worth refusing now rather than
        at approval, when they have already decided."""
        proposer = _Proposer()
        use_case = ProposeAssignmentBatch(
            workspaces=_Workspaces(members=set()), proposer=proposer
        )

        with pytest.raises(NotAWorkspaceMemberError):
            await use_case.execute(_propose_input(uuid4(), (uuid4(),)))

        assert proposer.proposals == []

    async def test_an_empty_selection_is_refused_before_membership_is_asked(self) -> None:
        """The caller's own defect, answered without a cross-module read."""
        use_case = ProposeAssignmentBatch(
            workspaces=_Workspaces(members=set()), proposer=_Proposer()
        )

        with pytest.raises(AssignmentError) as refusal:
            await use_case.execute(_propose_input(uuid4(), ()))

        assert not isinstance(refusal.value, NotAWorkspaceMemberError)


class TestApplyingWhatSomebodyApproved:
    def _batch(self, member: UUID, accounts: tuple[UUID, ...]) -> AssignmentBatch:
        return AssignmentBatch(
            batch_id=uuid4(),
            role=AccountRole.OWNER,
            member_user_id=member,
            requested=accounts,
        )

    async def test_it_assigns_and_records_what_moved(self) -> None:
        member, account = uuid4(), uuid4()
        batch = self._batch(member, (account,))
        batches = _Batches(batch)

        await ApplyAssignmentBatch(
            repository=_Repository(),
            batches=batches,
            workspaces=_Workspaces(members={member}),
        ).execute(uuid4(), batch.batch_id, actor_id=uuid4())

        assert batches.applied[0].previous == ((account, None),)

    async def test_a_member_who_left_between_proposal_and_approval_is_refused(self) -> None:
        """🔴 **The SECOND check, and it is the one that earns its keep.**

        ⛔ **The answer can differ between the two moments** — somebody proposes
        on Monday, the colleague leaves on Tuesday, the manager approves on
        Wednesday. **Assigning on acceptance would put forty accounts in the
        hands of somebody who cannot open them.**
        """
        departed, account = uuid4(), uuid4()
        batch = self._batch(departed, (account,))
        batches = _Batches(batch)

        with pytest.raises(NotAWorkspaceMemberError):
            await ApplyAssignmentBatch(
                repository=_Repository(),
                batches=batches,
                # ⚡ **They were a member when it was proposed and are not now.**
                workspaces=_Workspaces(members=set()),
            ).execute(uuid4(), batch.batch_id, actor_id=uuid4())

        assert batches.applied == []

    async def test_another_domain_s_batch_is_ignored_rather_than_refused(self) -> None:
        """⛔ **Not an error.** 📁 `action_batch.applied` is a shared lifecycle
        and every consumer sees every one of them — **a batch this module never
        proposed is simply not this module's**, and raising would dead-letter a
        tag batch on the owner consumer's queue.
        """
        batches = _Batches(None)

        await ApplyAssignmentBatch(
            repository=_Repository(),
            batches=batches,
            workspaces=_Workspaces(members=set()),
        ).execute(uuid4(), uuid4(), actor_id=uuid4())

        assert batches.applied == []


class TestTakingItBack:
    async def test_it_restores_the_prior_holders(self) -> None:
        member, account, previous_owner = uuid4(), uuid4(), uuid4()
        batch = AssignmentBatch(
            batch_id=uuid4(),
            role=AccountRole.OWNER,
            member_user_id=member,
            requested=(account,),
            moved=Reassignment(
                role=AccountRole.OWNER,
                assigned_to=member,
                previous=((account, previous_owner),),
            ),
        )
        repository = _Repository()

        await ReverseAssignmentBatch(repository=repository, batches=_Batches(batch)).execute(
            uuid4(), batch.batch_id, actor_id=uuid4()
        )

        assert repository.restored == [((account, previous_owner),)]

    async def test_the_reversal_carries_what_the_batch_PUT_there(self) -> None:
        """🔴 **`assigned_to` is what makes the write conditional**, and it is
        the fix for the three defects QE found at `935cbbd5`.

        ⛔ **Without it `restore` would be *"make the world look like it used
        to"*** — which silently discards a colleague's later choice — **rather
        than *"undo my change"*, which is what the button says.**
        """
        member, account = uuid4(), uuid4()
        batch = AssignmentBatch(
            batch_id=uuid4(),
            role=AccountRole.OWNER,
            member_user_id=member,
            requested=(account,),
            moved=Reassignment(
                role=AccountRole.OWNER, assigned_to=member, previous=((account, None),)
            ),
        )
        repository = _Repository()

        await ReverseAssignmentBatch(repository=repository, batches=_Batches(batch)).execute(
            uuid4(), batch.batch_id, actor_id=uuid4()
        )

        assert repository.restored_to == [member]

    async def test_a_batch_that_never_applied_has_nothing_to_undo(self) -> None:
        """⛔ **`moved is None` is the state the store keeps distinct from an
        empty list**, and this is where the distinction pays: **an approved but
        unapplied batch must not write anything on reversal.**"""
        batch = AssignmentBatch(
            batch_id=uuid4(),
            role=AccountRole.OWNER,
            member_user_id=uuid4(),
            requested=(uuid4(),),
        )
        repository = _Repository()

        await ReverseAssignmentBatch(repository=repository, batches=_Batches(batch)).execute(
            uuid4(), batch.batch_id, actor_id=uuid4()
        )

        assert repository.restored == []
        assert batch.to_reverse() == ()

    async def test_another_domain_s_reversal_is_ignored(self) -> None:
        repository = _Repository()

        await ReverseAssignmentBatch(repository=repository, batches=_Batches(None)).execute(
            uuid4(), uuid4(), actor_id=uuid4()
        )

        assert repository.restored == []
