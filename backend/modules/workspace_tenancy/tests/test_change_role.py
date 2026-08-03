"""Changing what somebody is allowed to do.

**Organizational authority, not a field.** The rules asserted here are the ones
that can strand an organization or lose the answer to *"who made Ravi an
owner?"*.
"""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest

from modules.workspace_tenancy.application.use_cases.change_role import (
    ChangeRole,
    ChangeRoleCommand,
)
from modules.workspace_tenancy.application.use_cases.remove_member import (
    MembershipNotFoundError,
)
from modules.workspace_tenancy.domain.entities import (
    LastOwnerCannotLeaveError,
    Membership,
    MembershipAlreadyEndedError,
    RoleUnchangedError,
    WorkspaceRole,
)
from modules.workspace_tenancy.tests.fakes import FakeMembershipRepository, FakeRoleChangeLog

NOW = datetime(2026, 8, 3, 9, 0, tzinfo=UTC)
WORKSPACE = uuid4()
ANA = uuid4()


def member(role: WorkspaceRole, user_id: UUID | None = None) -> Membership:
    membership, _ = Membership.create(
        workspace_id=WORKSPACE, user_id=user_id or uuid4(), role=role, created_by=ANA
    )
    return membership


async def change(
    repo: FakeMembershipRepository,
    log: FakeRoleChangeLog,
    membership: Membership,
    to: WorkspaceRole,
) -> Membership:
    return await ChangeRole(memberships=repo, history=log).execute(
        ChangeRoleCommand(
            workspace_id=WORKSPACE,
            membership_id=membership.id,
            new_role=to,
            changed_by=ANA,
        ),
        now=NOW,
    )


def setup(*roles: WorkspaceRole) -> tuple[FakeMembershipRepository, FakeRoleChangeLog, list[Membership]]:
    repo, log = FakeMembershipRepository(), FakeRoleChangeLog()
    people = [member(role) for role in roles]
    repo.memberships.extend(people)
    return repo, log, people


class TestAuthorityChanges:
    async def test_a_member_can_be_promoted(self) -> None:
        repo, log, (owner, colleague) = setup(WorkspaceRole.OWNER, WorkspaceRole.MEMBER)

        await change(repo, log, colleague, WorkspaceRole.OWNER)

        assert colleague.role is WorkspaceRole.OWNER

    async def test_an_owner_can_be_demoted_when_another_remains(self) -> None:
        repo, log, (first, second) = setup(WorkspaceRole.OWNER, WorkspaceRole.OWNER)

        await change(repo, log, second, WorkspaceRole.MEMBER)

        assert second.role is WorkspaceRole.MEMBER and first.role is WorkspaceRole.OWNER

    async def test_an_owner_may_demote_themselves(self) -> None:
        # Refusing it would mean an administrator handing over could not then
        # step back, and the last-owner rule already protects what matters.
        repo, log, (me, other) = setup(WorkspaceRole.OWNER, WorkspaceRole.OWNER)

        await ChangeRole(memberships=repo, history=log).execute(
            ChangeRoleCommand(
                workspace_id=WORKSPACE,
                membership_id=me.id,
                new_role=WorkspaceRole.MEMBER,
                changed_by=me.user_id,
            ),
            now=NOW,
        )

        assert me.role is WorkspaceRole.MEMBER


class TestAuthorityCannotDisappear:
    async def test_the_last_owner_cannot_be_demoted(self) -> None:
        # **The same failure as removing them, reached a second way.** One
        # invariant, refused in one place.
        repo, log, (sole, _) = setup(WorkspaceRole.OWNER, WorkspaceRole.MEMBER)

        with pytest.raises(LastOwnerCannotLeaveError):
            await change(repo, log, sole, WorkspaceRole.MEMBER)

    async def test_the_refusal_leaves_the_role_untouched(self) -> None:
        repo, log, (sole, _) = setup(WorkspaceRole.OWNER, WorkspaceRole.MEMBER)

        with pytest.raises(LastOwnerCannotLeaveError):
            await change(repo, log, sole, WorkspaceRole.MEMBER)
        assert sole.role is WorkspaceRole.OWNER

    async def test_a_refused_change_writes_no_history(self) -> None:
        # A history containing changes that did not happen is one nobody trusts.
        repo, log, (sole, _) = setup(WorkspaceRole.OWNER, WorkspaceRole.MEMBER)

        with pytest.raises(LastOwnerCannotLeaveError):
            await change(repo, log, sole, WorkspaceRole.MEMBER)
        assert log.entries == []

    async def test_the_membership_set_is_locked_before_counting(self) -> None:
        # **Counting is not enough.** Two owners demoted concurrently each read
        # *two owners*, each compute *one remaining*, and both succeed. The
        # lock is what makes the check atomic across transactions.
        repo, log, (first, second) = setup(WorkspaceRole.OWNER, WorkspaceRole.OWNER)
        locked: list[UUID] = []
        original = repo.lock_membership_set

        async def watching(workspace_id: UUID) -> None:
            locked.append(workspace_id)
            await original(workspace_id)

        repo.lock_membership_set = watching  # type: ignore[method-assign]
        await change(repo, log, second, WorkspaceRole.MEMBER)

        assert locked == [WORKSPACE]


class TestTheChangeIsRecorded:
    async def test_it_writes_what_they_were_and_what_they_became(self) -> None:
        # Without this the previous value is gone, and *"who made Ravi an
        # owner?"* is unanswerable by anything — including replay.
        repo, log, (owner, colleague) = setup(WorkspaceRole.OWNER, WorkspaceRole.MEMBER)

        await change(repo, log, colleague, WorkspaceRole.OWNER)

        assert log.entries[0]["previous_role"] is WorkspaceRole.MEMBER
        assert log.entries[0]["new_role"] is WorkspaceRole.OWNER

    async def test_it_records_who_changed_it_and_when(self) -> None:
        repo, log, (owner, colleague) = setup(WorkspaceRole.OWNER, WorkspaceRole.MEMBER)

        await change(repo, log, colleague, WorkspaceRole.OWNER)

        assert log.entries[0]["changed_by"] == ANA
        assert log.entries[0]["at"] == NOW

    async def test_every_change_adds_an_entry_rather_than_replacing_one(self) -> None:
        repo, log, (owner, colleague) = setup(WorkspaceRole.OWNER, WorkspaceRole.MEMBER)

        await change(repo, log, colleague, WorkspaceRole.OWNER)
        await change(repo, log, colleague, WorkspaceRole.MEMBER)

        assert len(log.entries) == 2


class TestItRefusesWhatWouldRecordNothing:
    async def test_setting_the_role_somebody_already_has_is_refused(self) -> None:
        repo, log, (owner, colleague) = setup(WorkspaceRole.OWNER, WorkspaceRole.MEMBER)

        with pytest.raises(RoleUnchangedError):
            await change(repo, log, colleague, WorkspaceRole.MEMBER)
        assert log.entries == []

    async def test_an_ended_membership_cannot_be_promoted(self) -> None:
        # Somebody who has left cannot be given authority they could not use.
        repo, log, (owner, gone) = setup(WorkspaceRole.OWNER, WorkspaceRole.MEMBER)
        gone.end(by=ANA, at=NOW, reason=None, remaining_owners=1)

        with pytest.raises(MembershipAlreadyEndedError):
            await change(repo, log, gone, WorkspaceRole.OWNER)

    async def test_an_unknown_membership_is_refused(self) -> None:
        repo, log, _ = setup(WorkspaceRole.OWNER)

        with pytest.raises(MembershipNotFoundError):
            await change(repo, log, member(WorkspaceRole.MEMBER), WorkspaceRole.OWNER)
