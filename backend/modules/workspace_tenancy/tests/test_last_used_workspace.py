"""Last-used workspace — [TASK-1422](../../../../docs/BACKLOG.md).

🔴 **The hazard [D-196](../../../../docs/DECISION_REGISTER.md) named**: *"a
stored preference that OUTLIVES membership… an authorization failure wearing a
convenience feature's clothes."*

⚡ **The row's own distinction is kept, and the tests state both halves
separately**: ⛔ **a stale preference cannot ROUTE anybody — the engine asserts
that over 2,880 session/intent pairs — but it CAN cost a person their real
destination**, which is a correctness defect rather than a security one.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import UUID

import pytest

from modules.workspace_tenancy.application.use_cases.last_used_workspace import (
    ForgetWorkspaceEntry,
    RecordWorkspaceEntry,
    ResolveLastUsedWorkspace,
)
from modules.workspace_tenancy.domain.preferences import PersonPreferences

NOW = datetime(2026, 8, 10, 9, 0, tzinfo=UTC)
PERSON = UUID("11111111-1111-1111-1111-111111111111")
NORTH = UUID("22222222-2222-2222-2222-222222222222")
SOUTH = UUID("33333333-3333-3333-3333-333333333333")
THEIRS = UUID("44444444-4444-4444-4444-444444444444")


class FakePreferences:
    """⚡ **Returns defaults for an unknown key**, exactly as the real one does —
    *the absence of a row is not the absence of an answer.*"""

    def __init__(self) -> None:
        self.rows: dict[tuple[UUID, UUID], PersonPreferences] = {}
        self.writes = 0

    async def get(self, workspace_id: UUID, person_id: UUID) -> PersonPreferences:
        return self.rows.get(
            (workspace_id, person_id),
            PersonPreferences(workspace_id=workspace_id, person_id=person_id),
        )

    async def save(self, preferences: PersonPreferences) -> None:
        self.rows[(preferences.workspace_id, preferences.person_id)] = preferences
        self.writes += 1


@pytest.fixture
def preferences() -> FakePreferences:
    return FakePreferences()


class TestEnteringAWorkspace:
    async def test_entering_records_the_moment(self, preferences: FakePreferences) -> None:
        await RecordWorkspaceEntry(preferences).execute(NORTH, PERSON, now=NOW)

        assert (await preferences.get(NORTH, PERSON)).last_entered_at == NOW

    async def test_a_later_entry_wins(self, preferences: FakePreferences) -> None:
        record = RecordWorkspaceEntry(preferences)
        await record.execute(NORTH, PERSON, now=NOW)
        await record.execute(NORTH, PERSON, now=NOW + timedelta(hours=1))

        assert (await preferences.get(NORTH, PERSON)).last_entered_at == NOW + timedelta(hours=1)

    async def test_an_older_entry_is_ignored_and_writes_nothing(
        self, preferences: FakePreferences
    ) -> None:
        """⛔ **Monotonic, because entries arrive out of order.**

        ⚡ **A retried request or a clock that stepped back would otherwise move
        somebody's last-used workspace BACKWARDS** — which is precisely the
        wrong answer at the one moment it matters.
        """
        record = RecordWorkspaceEntry(preferences)
        await record.execute(NORTH, PERSON, now=NOW)
        writes_after_first = preferences.writes

        await record.execute(NORTH, PERSON, now=NOW - timedelta(hours=1))

        assert (await preferences.get(NORTH, PERSON)).last_entered_at == NOW
        # ⚡ And it costs a read rather than a write.
        assert preferences.writes == writes_after_first

    async def test_entering_does_not_disturb_the_other_preferences(
        self, preferences: FakePreferences
    ) -> None:
        # ⛔ **The aggregate is shared with the profile screen.** An entry that
        # reset somebody's theme would be a far more visible defect than the one
        # this row fixes.
        from modules.workspace_tenancy.domain.preferences import Theme

        await preferences.save(
            PersonPreferences(workspace_id=NORTH, person_id=PERSON, theme=Theme.DARK)
        )

        await RecordWorkspaceEntry(preferences).execute(NORTH, PERSON, now=NOW)

        stored = await preferences.get(NORTH, PERSON)
        assert stored.theme is Theme.DARK
        assert stored.last_entered_at == NOW


class TestResolvingIt:
    async def test_the_most_recent_of_the_workspaces_they_may_enter(
        self, preferences: FakePreferences
    ) -> None:
        record = RecordWorkspaceEntry(preferences)
        await record.execute(NORTH, PERSON, now=NOW)
        await record.execute(SOUTH, PERSON, now=NOW + timedelta(hours=1))

        answer = await ResolveLastUsedWorkspace(preferences).execute(
            PERSON, frozenset({NORTH, SOUTH})
        )

        assert answer == SOUTH

    async def test_never_entered_is_none_rather_than_the_beginning_of_time(
        self, preferences: FakePreferences
    ) -> None:
        """⛔ **`None` is *never entered*, not *entered long ago*.**

        ⚡ **Rule 12 `LAST_USED` must not fire for somebody who has been
        nowhere** — 📁 rule 13 `AMBIGUOUS` is the designed destination, so
        answering *nothing* is an answer rather than a failure.
        """
        answer = await ResolveLastUsedWorkspace(preferences).execute(
            PERSON, frozenset({NORTH, SOUTH})
        )

        assert answer is None

    async def test_an_unentered_workspace_never_wins_over_an_entered_one(
        self, preferences: FakePreferences
    ) -> None:
        await RecordWorkspaceEntry(preferences).execute(SOUTH, PERSON, now=NOW)

        answer = await ResolveLastUsedWorkspace(preferences).execute(
            PERSON, frozenset({NORTH, SOUTH})
        )

        assert answer == SOUTH


class TestTheHazardItself:
    """🔴 **[D-196](../../../../docs/DECISION_REGISTER.md), asserted.**"""

    async def test_a_workspace_they_no_longer_belong_to_can_never_be_the_answer(
        self, preferences: FakePreferences
    ) -> None:
        """⛔ **The whole row in one assertion.**

        ⚡ **The row for `THEIRS` is untouched — nothing cleared it** — and it
        holds the most recent entry of the three. ✅ **It still cannot win,
        because the derivation reads only the workspaces they may enter.**
        **That is what makes the clearing provable rather than diligent: there
        is nothing to forget to clear.**
        """
        record = RecordWorkspaceEntry(preferences)
        await record.execute(NORTH, PERSON, now=NOW)
        await record.execute(THEIRS, PERSON, now=NOW + timedelta(days=1))

        # ⚡ Membership ended. **The stored row is deliberately left in place.**
        answer = await ResolveLastUsedWorkspace(preferences).execute(PERSON, frozenset({NORTH}))

        assert answer == NORTH
        assert (await preferences.get(THEIRS, PERSON)).last_entered_at is not None

    async def test_and_it_bites_the_same_row_wins_while_the_membership_is_live(
        self, preferences: FakePreferences
    ) -> None:
        """⛔ **A test that only ever asserts an exclusion passes when the
        derivation is deleted and everything returns `None`.** ✅ **This is the
        discriminating case**: put the membership back and the same row wins.
        """
        record = RecordWorkspaceEntry(preferences)
        await record.execute(NORTH, PERSON, now=NOW)
        await record.execute(THEIRS, PERSON, now=NOW + timedelta(days=1))

        answer = await ResolveLastUsedWorkspace(preferences).execute(
            PERSON, frozenset({NORTH, THEIRS})
        )

        assert answer == THEIRS

    async def test_a_person_with_no_live_memberships_gets_nothing(
        self, preferences: FakePreferences
    ) -> None:
        await RecordWorkspaceEntry(preferences).execute(NORTH, PERSON, now=NOW)

        answer = await ResolveLastUsedWorkspace(preferences).execute(PERSON, frozenset())

        assert answer is None


class TestForgetting:
    """⚡ **Hygiene, and the tests say so** — 🔴 the control is the derivation."""

    async def test_it_clears_the_moment_without_touching_anything_else(
        self, preferences: FakePreferences
    ) -> None:
        from modules.workspace_tenancy.domain.preferences import Theme

        await preferences.save(
            PersonPreferences(
                workspace_id=NORTH, person_id=PERSON, theme=Theme.DARK, last_entered_at=NOW
            )
        )

        await ForgetWorkspaceEntry(preferences).execute(NORTH, PERSON)

        stored = await preferences.get(NORTH, PERSON)
        assert stored.last_entered_at is None
        # ⛔ **A membership ending is not a reason to forget somebody's theme.**
        # They may be invited back, and the preference was never the
        # workspace's to hold.
        assert stored.theme is Theme.DARK

    async def test_forgetting_what_was_never_recorded_writes_nothing(
        self, preferences: FakePreferences
    ) -> None:
        # ⚡ Every membership that ends calls this, and most people have never
        # entered most of their workspaces.
        await ForgetWorkspaceEntry(preferences).execute(NORTH, PERSON)

        assert preferences.writes == 0
