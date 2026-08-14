"""**Owner and CSM** — [ADR-0411](../../../docs/architecture/adr/0411-customer-organized-account-metadata.md), [TASK-1479](../../../docs/BACKLOG.md) slice ⓶.

🔴 **The subject is the inverse.** *"Set the owner on these forty accounts"* is
easy; **undoing it is where the customer notices whether anybody thought about
it**, and it is the half [ADR-0405](../../../docs/architecture/adr/0405-an-action-is-approved-before-it-is-effective.md)
says the consuming domain owns.
"""

from __future__ import annotations

from uuid import uuid4

import pytest

from modules.commercial_profile.domain.account_assignment import (
    AccountAssignment,
    AccountRole,
    AssignmentError,
    Reassignment,
)


class TestTheRolesAreTheOnesTheRulingNames:
    def test_there_are_exactly_two(self) -> None:
        """⛔ **Closed, and not because a third is unimaginable.** The ruling's
        scope line is *"Those three. Nothing else"* — a role arriving through a
        string would be scope entering by the back door."""
        assert {role.value for role in AccountRole} == {"owner", "csm"}

    def test_an_unapproved_role_cannot_be_constructed(self) -> None:
        with pytest.raises(ValueError):
            AccountRole("account_executive")


class TestAnAssignmentPointsAtAMemberRatherThanNamingOne:
    def test_it_carries_a_user_id(self) -> None:
        """📁 **The ruling's own words**: *"a reference to a workspace member,
        not free text. A person who leaves must not leave a dangling
        string."*"""
        assignment = AccountAssignment(
            workspace_id=uuid4(),
            account_id=uuid4(),
            role=AccountRole.OWNER,
            member_user_id=uuid4(),
        )

        assert isinstance(assignment.member_user_id, type(uuid4()))

    def test_it_is_frozen(self) -> None:
        """Reassigning is a new fact, not an edit to the old one."""
        assignment = AccountAssignment(
            workspace_id=uuid4(),
            account_id=uuid4(),
            role=AccountRole.CSM,
            member_user_id=uuid4(),
        )

        with pytest.raises(Exception):
            assignment.member_user_id = uuid4()  # type: ignore[misc]


class TestTheInverseRestoresWhoHeldItRatherThanNobody:
    def test_unassigning_is_not_the_inverse_of_assigning(self) -> None:
        """🔴 **The assertion this aggregate exists for.**

        An account that already had an owner must get **that owner** back. ⛔ A
        reversal that cleared the field would take an owner away from somebody
        who always had one — a change the customer never asked for and could
        not explain.
        """
        held, unheld, previous_owner = uuid4(), uuid4(), uuid4()
        reassignment = Reassignment(
            role=AccountRole.OWNER,
            previous=((held, previous_owner), (unheld, None)),
        )

        assert reassignment.inverse() == ((held, previous_owner), (unheld, None))

    def test_an_account_that_did_not_move_is_not_reversed(self) -> None:
        """⛔ **`previous`, never `unchanged`.** Reversing an account that
        already held the requested member would move somebody who never
        moved."""
        already = uuid4()
        reassignment = Reassignment(role=AccountRole.OWNER, unchanged=(already,))

        assert reassignment.inverse() == ()

    def test_nothing_moved_reverses_to_nothing(self) -> None:
        """⚠️ **Distinct from *"it was never applied"***, and the caller can
        tell: an empty `previous` beside a populated `unchanged` says the
        request ran and found every account already correct."""
        reassignment = Reassignment(role=AccountRole.CSM, unchanged=(uuid4(), uuid4()))

        assert reassignment.inverse() == ()
        assert len(reassignment.unchanged) == 2

    def test_an_account_cannot_be_both_changed_and_unchanged(self) -> None:
        """⛔ **Refused at construction rather than resolved at reversal.**

        A reversal built from a contradictory record would restore an owner to
        an account that never moved, and **nothing downstream could detect
        it** — the write would look exactly like a legitimate one.
        """
        account = uuid4()

        with pytest.raises(AssignmentError):
            Reassignment(
                role=AccountRole.OWNER,
                previous=((account, uuid4()),),
                unchanged=(account,),
            )
