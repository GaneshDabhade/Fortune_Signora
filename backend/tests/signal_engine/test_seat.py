"""TASK-458 — the seat a decision-maker signal is about.

**The domain half, pure and with no database.** What is under test is the
refusal: `seat_for` names a seat when exactly one holder carried the title,
and names none when two did — which is `people.match_departure`'s discipline
read rather than written.
"""

from __future__ import annotations

from datetime import date

from modules.signal_engine.domain.seat import Seat, fold_title, seat_for

MARCH = date(2025, 3, 4)
SEPTEMBER = date(2026, 9, 1)


def _seat(title: str, *, ended: date | None = None) -> Seat:
    return Seat(title=title, seniority="vp", started_on=MARCH, ended_on=ended)


class TestFolding:
    def test_case_and_internal_space_only(self) -> None:
        assert fold_title("  VP   of  Engineering ") == fold_title("vp of engineering")

    def test_punctuation_is_not_normalised_and_that_is_deliberate(self) -> None:
        """*"VP of Engineering"* and *"VP, Engineering"* are one job to a
        person and two strings here — the limitation `match_departure` carries
        and states, rather than a second vocabulary invented in this module."""
        assert fold_title("VP of Engineering") != fold_title("VP, Engineering")


class TestTenure:
    def test_a_closed_interval_reads_as_a_period(self) -> None:
        assert _seat("VP", ended=SEPTEMBER).tenure == ("held from 4 March 2025 to 1 September 2026")

    def test_an_open_interval_states_the_absence_rather_than_implying_it_continues(
        self,
    ) -> None:
        """P-A. *"Held since March"* asserts they are still there; the People
        contract says only that no departure has been observed, and those are
        different claims."""
        assert _seat("VP").tenure == "held from 4 March 2025, with no departure recorded"

    def test_is_open_is_not_still_held(self) -> None:
        assert _seat("VP").is_open is True
        assert _seat("VP", ended=SEPTEMBER).is_open is False

    def test_the_date_does_not_depend_on_the_machine(self) -> None:
        """`%-d` is glibc-only; a rationale that read differently in a
        container than on a developer's laptop is §2's hidden input in its
        smallest form."""
        assert "4 March" in _seat("VP").tenure
        assert "04 March" not in _seat("VP").tenure


class TestSelection:
    def test_one_holder_names_the_seat(self) -> None:
        seats = (_seat("VP of Engineering"), _seat("CFO"))
        found = seat_for(seats, title="vp of engineering")
        assert found is not None and found.title == "VP of Engineering"

    def test_two_holders_of_one_title_name_none(self) -> None:
        """The refusal. A rationale picking one of two would assert something
        no evidence supports, and a rationale is what a customer argues with."""
        seats = (_seat("VP of Engineering"), _seat("VP of Engineering", ended=SEPTEMBER))
        assert seat_for(seats, title="VP of Engineering") is None

    def test_no_holder_names_none(self) -> None:
        assert seat_for((_seat("CFO"),), title="VP of Engineering") is None

    def test_an_empty_record_names_none(self) -> None:
        assert seat_for((), title="VP of Engineering") is None

    def test_a_closed_interval_still_counts_as_a_holder(self) -> None:
        """The whole reason `at_company` returns closed intervals: *"who left,
        and when"* is what `decision_maker_departed` exists to answer."""
        found = seat_for((_seat("VP of Engineering", ended=SEPTEMBER),), title="VP of Engineering")
        assert found is not None and found.ended_on == SEPTEMBER
