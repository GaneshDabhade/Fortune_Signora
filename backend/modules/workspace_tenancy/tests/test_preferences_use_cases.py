"""Reading and changing preferences — [TASK-470](../../../../docs/BACKLOG.md).

⚡ **The case that matters is the partial write.** The design's profile is
several panels edited independently, so a request that mentions the theme must
leave the pronouns alone — and `None` cannot express *not mentioned*, because
clearing a field is a legitimate thing to ask for.
"""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest

from modules.workspace_tenancy.application.use_cases.preferences import (
    ChangePreferencesInput,
    ChangePreferencesUseCase,
    DismissFirstRunUseCase,
    GetPreferencesUseCase,
    SkipInviteUseCase,
)
from modules.workspace_tenancy.domain.preferences import (
    ScreenReaderVerbosity,
    TextSize,
    Density,
    PersonPreferences,
    Theme,
    TimeFormat,
)
from modules.workspace_tenancy.tests.fakes import FakePersonPreferencesRepository

pytestmark = pytest.mark.asyncio

#: ⚡ **The clock is injected, everywhere** — these use cases take `now`
#: precisely so a test never has to wait for one to move.
AT = datetime(2026, 8, 13, 9, 14, tzinfo=UTC)
LATER = datetime(2026, 8, 13, 11, 30, tzinfo=UTC)


class TestSomebodyWhoHasNeverOpenedTheScreen:
    async def test_reads_the_defaults_rather_than_nothing(self) -> None:
        """⛔ **The absence of a row is not the absence of an answer.** A port
        that could answer `None` would push that reasoning into every caller,
        and the first to forget it renders a blank profile to a new account."""
        prefs = await GetPreferencesUseCase(preferences=FakePersonPreferencesRepository()).execute(
            uuid4(), uuid4()
        )

        assert prefs.theme is Theme.SYSTEM
        assert prefs.timezone is None


class TestAPartialChange:
    async def test_changing_the_theme_leaves_everything_else_alone(self) -> None:
        repo = FakePersonPreferencesRepository()
        change = ChangePreferencesUseCase(preferences=repo)
        ws, person = uuid4(), uuid4()
        await change.execute(
            ChangePreferencesInput(
                workspace_id=ws, person_id=person, pronouns="she/her", timezone="Europe/Copenhagen"
            )
        )

        after = await change.execute(
            ChangePreferencesInput(workspace_id=ws, person_id=person, theme=Theme.DARK)
        )

        assert after.theme is Theme.DARK
        assert after.pronouns == "she/her"
        assert after.timezone == "Europe/Copenhagen"

    async def test_the_twelve_profile_locale_and_accessibility_fields_all_survive(
        self,
    ) -> None:
        """🔴 **[B-264](../../../../docs/BUGS.md)'s shape, asserted for the
        fields migration `0060` added.**

        ⚠️ **The defect was a use case that REBUILT `PersonPreferences` from
        named fields**, so every field added after it was written was silently
        dropped — *"every profile edit reset `last_entered_at`"*.

        ⛔ **A test asserting each new field's default would have passed against
        that defect.** ✅ **Setting all twelve, then changing something else
        entirely, is what catches it** — and it is the shape that keeps catching
        it for the thirteenth.
        """
        repo = FakePersonPreferencesRepository()
        change = ChangePreferencesUseCase(preferences=repo)
        ws, person = uuid4(), uuid4()

        await change.execute(
            ChangePreferencesInput(
                workspace_id=ws,
                person_id=person,
                job_title="Head of Revenue Operations",
                department="Revenue",
                mobile="+45 20 00 00 00",
                date_format="31 Dec 2026",
                number_format="1.234,56",
                week_starts_on="Monday",
                reduce_motion=True,
                increase_contrast=True,
                always_show_focus_ring=True,
                underline_links=False,
                text_size=TextSize.ONE_TWENTY_FIVE,
                screen_reader_verbosity=ScreenReaderVerbosity.CONCISE,
            )
        )

        after = await change.execute(
            ChangePreferencesInput(workspace_id=ws, person_id=person, theme=Theme.DARK)
        )

        assert after.theme is Theme.DARK
        assert after.job_title == "Head of Revenue Operations"
        assert after.department == "Revenue"
        assert after.mobile == "+45 20 00 00 00"
        assert after.date_format == "31 Dec 2026"
        assert after.number_format == "1.234,56"
        assert after.week_starts_on == "Monday"
        assert after.reduce_motion is True
        assert after.increase_contrast is True
        assert after.always_show_focus_ring is True
        assert after.underline_links is False
        assert after.text_size is TextSize.ONE_TWENTY_FIVE
        assert after.screen_reader_verbosity is ScreenReaderVerbosity.CONCISE

    async def test_clearing_a_field_is_possible_and_is_not_the_same_as_omitting_it(
        self,
    ) -> None:
        """**The whole reason `UNSET` exists.** With `None` meaning both, a
        panel that omitted a field it does not own would silently erase what
        another panel had set."""
        repo = FakePersonPreferencesRepository()
        change = ChangePreferencesUseCase(preferences=repo)
        ws, person = uuid4(), uuid4()
        await change.execute(
            ChangePreferencesInput(workspace_id=ws, person_id=person, pronouns="she/her")
        )

        cleared = await change.execute(
            ChangePreferencesInput(workspace_id=ws, person_id=person, pronouns=None)
        )

        assert cleared.pronouns is None

    async def test_a_change_persists_and_reads_back(self) -> None:
        repo = FakePersonPreferencesRepository()
        ws, person = uuid4(), uuid4()
        await ChangePreferencesUseCase(preferences=repo).execute(
            ChangePreferencesInput(
                workspace_id=ws,
                person_id=person,
                density=Density.COMPACT,
                time_format=TimeFormat.TWELVE_HOUR,
            )
        )

        reread = await GetPreferencesUseCase(preferences=repo).execute(ws, person)

        assert reread.density is Density.COMPACT
        assert reread.time_format is TimeFormat.TWELVE_HOUR

    async def test_one_persons_change_is_not_anothers(self) -> None:
        """🔴 **The Security Invariant this row names, at the layer above the
        policy.** A preference row must never become a route to another
        account's data — and the query predicate is the first of the two
        guards, the RLS policy being the one that holds regardless."""
        repo = FakePersonPreferencesRepository()
        ws, me, colleague = uuid4(), uuid4(), uuid4()
        await ChangePreferencesUseCase(preferences=repo).execute(
            ChangePreferencesInput(workspace_id=ws, person_id=me, theme=Theme.DARK)
        )

        theirs = await GetPreferencesUseCase(preferences=repo).execute(ws, colleague)

        assert theirs.theme is Theme.SYSTEM


class _CountingPreferences(FakePersonPreferencesRepository):
    """The fake, plus the one fact these tests are about: **did a write happen?**

    ⛔ **Asserting the VALUE is unchanged does not test this guard.** The
    domain already refuses to move — `dismissed_first_run` returns `self` when
    a moment is recorded, and `test_first_run_dismissal.py` covers that. **A
    use case that called `save` anyway would pass every value assertion and
    still write a row per click**, which is precisely the defect the guard
    exists to prevent and precisely what nothing observed.
    """

    def __init__(self) -> None:
        super().__init__()
        self.writes = 0

    async def save(self, preferences: PersonPreferences) -> None:
        self.writes += 1
        await super().save(preferences)


class TestASecondDismissalWritesNothing:
    """📁 [B-196](../../../../docs/BUGS.md) — QE, cycle 220.

    ⚡ **The behaviour was designed, stated in a comment, and asserted
    nowhere**: *"a write that stores no new fact is a row created for
    nothing."* ⛔ **Ten uncovered statements in this file took the repository
    under the coverage floor**, and the honest half of that row is that the
    branch genuinely had no test.
    """

    async def test_the_first_dismissal_writes_once(self) -> None:
        repo = _CountingPreferences()
        ws, person = uuid4(), uuid4()

        await DismissFirstRunUseCase(preferences=repo).execute(ws, person, now=AT)

        assert repo.writes == 1

    async def test_a_second_dismissal_writes_nothing_at_all(self) -> None:
        repo = _CountingPreferences()
        ws, person = uuid4(), uuid4()
        first = await DismissFirstRunUseCase(preferences=repo).execute(ws, person, now=AT)

        again = await DismissFirstRunUseCase(preferences=repo).execute(ws, person, now=LATER)

        # ⚡ **The first moment wins**, which is the fact a customer would
        # notice, and the row count is the fact only this assertion can see.
        assert again.first_run_dismissed_at == first.first_run_dismissed_at == AT
        assert repo.writes == 1


class TestUnskippingSomethingNeverSkipped:
    """⛔ **The same guard on the other use case**, and the case is real rather
    than defensive: 📁 the design puts *"Show the skipped step"* on the
    activation progress line, and **the line renders for everybody** — so a
    person who never skipped can reach the control that un-skips."""

    async def test_a_skip_writes_once(self) -> None:
        repo = _CountingPreferences()
        ws, person = uuid4(), uuid4()

        await SkipInviteUseCase(preferences=repo).execute(ws, person, skip=True, now=AT)

        assert repo.writes == 1

    async def test_un_skipping_a_record_that_was_never_skipped_writes_nothing(self) -> None:
        repo = _CountingPreferences()
        ws, person = uuid4(), uuid4()

        after = await SkipInviteUseCase(preferences=repo).execute(
            ws, person, skip=False, now=AT
        )

        assert after.invite_skipped_at is None
        assert repo.writes == 0

    async def test_but_a_real_un_skip_does_write(self) -> None:
        """✅ **The half that must not regress.** A guard that became *never
        write* would ship a hide with no way back — 📁 the exact failure
        `SkipInviteUseCase`'s docstring says two use cases would produce."""
        repo = _CountingPreferences()
        ws, person = uuid4(), uuid4()
        await SkipInviteUseCase(preferences=repo).execute(ws, person, skip=True, now=AT)

        after = await SkipInviteUseCase(preferences=repo).execute(
            ws, person, skip=False, now=LATER
        )

        assert after.invite_skipped_at is None
        assert repo.writes == 2
