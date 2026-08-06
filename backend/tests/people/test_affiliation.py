"""An affiliation is an interval that closes, and a departure that cannot be
attributed closes nothing.
"""

from datetime import date
from uuid import uuid4

import pytest

from modules.people.domain.affiliation import Affiliation, AffiliationError, RoleInterval
from modules.people.domain.matching_rule import MatchOutcome, match_departure
from modules.people.domain.person import Person, PersonError

MARCH = date(2026, 3, 1)
SEPTEMBER = date(2026, 9, 1)
WORKSPACE = uuid4()
ACME = uuid4()


def _affiliation(*, title: str = "VP of Engineering", company: object = None,
                 ended: date | None = None) -> Affiliation:
    return Affiliation(
        id=uuid4(),
        workspace_id=WORKSPACE,
        person_id=uuid4(),
        company_id=company or ACME,  # type: ignore[arg-type]
        title=title,
        seniority="vp",
        interval=RoleInterval(started_on=MARCH, ended_on=ended),
    )


class TestALeavingIsAnIntervalClosing:
    def test_a_new_affiliation_has_no_end(self) -> None:
        assert _affiliation().is_current

    def test_ending_it_returns_a_new_value_and_leaves_the_original(self) -> None:
        """**Nothing is overwritten** — the ADR's load-bearing choice."""
        original = _affiliation()

        closed = original.ended(on=SEPTEMBER)

        assert closed.interval.ended_on == SEPTEMBER
        assert original.is_current
        assert closed.interval.started_on == MARCH

    def test_ending_it_twice_is_refused_rather_than_overwriting(self) -> None:
        """Two departures matched to one arrival is a matching defect, and
        keeping the later date would hide it."""
        closed = _affiliation().ended(on=SEPTEMBER)

        with pytest.raises(AffiliationError, match="already ended"):
            closed.ended(on=date(2026, 10, 1))

    def test_leaving_before_arriving_is_refused(self) -> None:
        with pytest.raises(AffiliationError, match="cannot end on"):
            RoleInterval(started_on=SEPTEMBER, ended_on=MARCH)

    def test_an_affiliation_with_no_title_is_refused(self) -> None:
        with pytest.raises(AffiliationError, match="no title"):
            _affiliation(title="   ")


class TestOpenMeansNoDepartureObserved:
    def test_an_open_interval_reports_itself_open(self) -> None:
        # Deliberately *not* "they still work there" — see the docstring. The
        # test names the claim the code is allowed to make.
        assert RoleInterval(started_on=MARCH).is_open

    def test_a_closed_one_does_not(self) -> None:
        assert not RoleInterval(started_on=MARCH, ended_on=SEPTEMBER).is_open


class TestADepartureNobodyCanAttributeClosesNothing:
    def test_one_open_role_with_that_title_is_matched(self) -> None:
        held = _affiliation()

        found = match_departure([held], company_id=ACME, title="VP of Engineering")

        assert found.outcome is MatchOutcome.MATCHED
        assert found.closes is held

    def test_two_people_holding_it_closes_neither(self) -> None:
        """**The rule this module exists to state.** Closing either is a guess,
        and a wrongly closed interval is indistinguishable from a real one."""
        first, second = _affiliation(), _affiliation()

        found = match_departure([first, second], company_id=ACME, title="VP of Engineering")

        assert found.outcome is MatchOutcome.AMBIGUOUS
        assert found.closes is None
        # The candidates travel with the refusal, so a consumer can say
        # "one of these two left" rather than nothing at all.
        assert set(found.candidates) == {first, second}

    def test_nobody_recorded_in_the_role_is_not_an_error(self) -> None:
        """Signora never saw the arrival. The departure still happened."""
        found = match_departure([], company_id=ACME, title="VP of Engineering")

        assert found.outcome is MatchOutcome.NONE_OPEN
        assert found.candidates == ()

    def test_an_already_closed_affiliation_is_not_a_candidate(self) -> None:
        found = match_departure(
            [_affiliation(ended=SEPTEMBER)], company_id=ACME, title="VP of Engineering"
        )

        assert found.outcome is MatchOutcome.NONE_OPEN

    def test_the_same_title_at_another_company_is_not_a_candidate(self) -> None:
        """A rule matching on title alone would close the wrong account's VP."""
        elsewhere = _affiliation(company=uuid4())

        found = match_departure([elsewhere], company_id=ACME, title="VP of Engineering")

        assert found.outcome is MatchOutcome.NONE_OPEN

    def test_case_and_spacing_are_folded_and_nothing_else_is(self) -> None:
        held = _affiliation(title="VP of Engineering")

        assert match_departure(
            [held], company_id=ACME, title="  vp   of engineering "
        ).outcome is MatchOutcome.MATCHED
        # A synonym is a reviewed catalog, not code — the same limitation
        # commercial_profile.evaluation carries, and for the same reason.
        assert match_departure(
            [held], company_id=ACME, title="VP, Engineering"
        ).outcome is MatchOutcome.NONE_OPEN


class TestAPersonBelongsToOneWorkspace:
    def test_a_person_is_an_identity_and_nothing_else(self) -> None:
        """Two customers tracking the same human hold two unrelated rows, and
        that is the tenancy model rather than duplication."""
        person = Person(id=uuid4(), workspace_id=WORKSPACE)

        assert person.workspace_id == WORKSPACE
        assert not hasattr(person, "name")
        assert not hasattr(person, "current_employer")

    def test_person_error_exists_for_a_tenantless_identity(self) -> None:
        assert issubclass(PersonError, ValueError)
