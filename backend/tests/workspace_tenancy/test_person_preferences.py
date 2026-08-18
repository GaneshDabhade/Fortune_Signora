"""`PersonPreferences`' one-time facts, as pure domain rules.

⚡ **Fast and databaseless on purpose.** The aggregate decides *whether* a moment
moves; the integration test decides *whether it persisted*. **Asserting the first
through HTTP would prove it slowly and locate the failure badly.**

📁 Home state 04 — *"a one-time strip"*, `AC-H03`'s *"shown exactly once"*.
"""

from dataclasses import replace
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest

from modules.workspace_tenancy.domain.exceptions import InvalidHomeCompositionError
from modules.workspace_tenancy.domain.preferences import HomeCardLayout, PersonPreferences

TOLD_AT = datetime(2026, 8, 18, 9, 0, tzinfo=UTC)


def _fresh() -> PersonPreferences:
    return PersonPreferences(workspace_id=uuid4(), person_id=uuid4())


class TestTheFirstEntryOfADay:
    """🔴 **Home state 13 and Entry rule 12's strip.**

    📁 State 13 · *"second or later entry on the same calendar day in this
    workspace"* → *"identical to state 06 with the workspace confirmation strip
    suppressed."* 📁 Entry rule 12's strip is *"gone on the second visit that day."*
    """

    def test_somebody_who_has_never_been_here_is_entering_for_the_first_time(self) -> None:
        """⛔ **`None` is *never entered*, not *entered long ago*.** ⚡ Somebody who
        has been nowhere has not been here today."""
        assert _fresh().first_entry_today(TOLD_AT) is True

    def test_a_second_entry_the_same_day_is_not_the_first(self) -> None:
        first = _fresh().entered(TOLD_AT)

        assert first.first_entry_today(TOLD_AT + timedelta(hours=6)) is False

    def test_the_next_day_is_a_first_entry_again(self) -> None:
        """📁 *"The same calendar day"* — ⛔ **a day, never twenty-four hours.**"""
        yesterday = _fresh().entered(TOLD_AT)

        assert yesterday.first_entry_today(TOLD_AT + timedelta(days=1)) is True

    def test_it_is_asked_before_the_entry_is_recorded(self) -> None:
        """🔴 **The ordering the use case depends on.**

        ⚡ Recording an entry sets `last_entered_at` to now, so asking afterwards
        answers `False` for the rest of the day. **This asserts that the trap is
        real**, so the use case's read-then-write order is load-bearing rather
        than incidental.
        """
        fresh = _fresh()

        assert fresh.first_entry_today(TOLD_AT) is True
        assert fresh.entered(TOLD_AT).first_entry_today(TOLD_AT) is False

    def test_the_day_boundary_is_this_persons_own(self) -> None:
        """⚠️ **A calendar day needs a zone, and it is the person's.**

        📁 `U-06`'s interim for the same question one card over is *"per person in
        profile timezone"*. ⚡ **23:00 in Auckland and 01:00 the next morning are
        the same UTC afternoon and different local days**, and the strip follows
        the person rather than the server.
        """
        auckland = replace(_fresh(), timezone="Pacific/Auckland")
        # 2026-08-18 09:00Z is 21:00 on the 18th in Auckland.
        evening = auckland.entered(datetime(2026, 8, 18, 9, 0, tzinfo=UTC))
        # 2026-08-18 13:00Z is 01:00 on the 19th in Auckland — a new local day.
        assert evening.first_entry_today(datetime(2026, 8, 18, 13, 0, tzinfo=UTC)) is True

    def test_an_unresolvable_zone_does_not_refuse_the_entry(self) -> None:
        """⛔ **The strip is a courtesy.** ⚡ Failing a whole entry over an
        unrecognised IANA string would make it a blocker."""
        nonsense = replace(_fresh(), timezone="Middle/Earth")

        assert nonsense.first_entry_today(TOLD_AT) is True


class TestBeingToldSetupIsComplete:
    def test_a_new_person_has_not_been_told(self) -> None:
        """⛔ **`None` is the absence**, and it is what makes the strip render."""
        assert _fresh().setup_complete_seen_at is None

    def test_being_told_records_the_moment(self) -> None:
        told = _fresh().saw_setup_complete(TOLD_AT)

        assert told.setup_complete_seen_at == TOLD_AT

    def test_the_first_moment_wins(self) -> None:
        """🔴 **The rule *"exactly once"* rests on this.**

        ⚡ A second render, a retry or a second tab must not move the timestamp
        forward. ⛔ **Overwriting it would lose the only fact the column carries**
        — when this person was told — which is precisely what somebody asks for
        when a strip appears twice.
        """
        later = TOLD_AT + timedelta(days=3)

        told = _fresh().saw_setup_complete(TOLD_AT)
        again = told.saw_setup_complete(later)

        assert again.setup_complete_seen_at == TOLD_AT

    def test_a_second_call_returns_the_same_object(self) -> None:
        """⚡ **Identity, not equality**, because the use case branches on it:
        *"only when something changed"* is what stops a second acknowledgement
        writing a row for nothing."""
        told = _fresh().saw_setup_complete(TOLD_AT)

        assert told.saw_setup_complete(TOLD_AT) is told

    def test_it_does_not_disturb_its_neighbours(self) -> None:
        """⛔ **Three one-time facts share this table** and they are independent:
        being told setup finished is not dismissing the first-run overlay and is
        not skipping the invite card. ⚠️ A `replace` that touched a sibling would
        be invisible until somebody's overlay came back."""
        told = _fresh().saw_setup_complete(TOLD_AT)

        assert told.first_run_dismissed_at is None
        assert told.invite_skipped_at is None


class TestArrangingHomesCards:
    """🔴 **Home §10's *Customise* panel** — 📁 `3.2.3`: *"card order within a
    composition is **stable across visits**."* 📁 `U-05`'s interim: *"**reorder and
    remove only.**"*
    """

    def test_nobody_has_arranged_anything_to_begin_with(self) -> None:
        """⛔ **An empty map is *never customised***, which renders the registry's
        own order — not *customised to nothing*, which would be an empty Home."""
        assert _fresh().home_layout == {}

    def test_an_arrangement_is_kept(self) -> None:
        layout = HomeCardLayout(order=("recents", "needs-you-today"), hidden=("meetings",))

        chosen = _fresh().choose_home_layout("seller", layout)

        assert chosen.home_layout["seller"] == layout

    def test_one_composition_at_a_time(self) -> None:
        """🔴 **The rule the use case depends on.**

        ⚡ The panel shows the composition the person is looking at. ⛔ **A write
        that replaced the whole map would wipe an arrangement they cannot see**,
        which they would meet the next time they switched with no way to know
        what happened.
        """
        seller = HomeCardLayout(order=("recents",))
        executive = HomeCardLayout(order=("top-risks",))

        both = _fresh().choose_home_layout("seller", seller).choose_home_layout(
            "executive", executive
        )

        assert both.home_layout["seller"] == seller
        assert both.home_layout["executive"] == executive

    def test_arranging_again_replaces_that_composition(self) -> None:
        first = HomeCardLayout(order=("recents", "meetings"))
        second = HomeCardLayout(order=("meetings", "recents"))

        chosen = _fresh().choose_home_layout("seller", first).choose_home_layout("seller", second)

        assert chosen.home_layout["seller"] == second

    def test_a_composition_home_cannot_render_is_refused(self) -> None:
        """⛔ **Refused rather than stored.** ⚡ An arrangement filed under a name
        Home does not know is one nobody would ever see, and the person would go
        on customising a screen that never changes."""
        with pytest.raises(InvalidHomeCompositionError):
            _fresh().choose_home_layout("dashboard", HomeCardLayout())

    def test_it_does_not_disturb_its_neighbours(self) -> None:
        chosen = _fresh().choose_home_layout("seller", HomeCardLayout(order=("recents",)))

        assert chosen.home_composition is None
        assert chosen.setup_complete_seen_at is None
