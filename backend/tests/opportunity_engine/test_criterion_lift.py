"""Whether a declared criterion predicts anything — and refusing to say when
there is nothing to say.

**Every rule here is one a customer could dispute**, so every one is a pure
function with a test named for the sentence they would dispute.
"""

from __future__ import annotations

import pytest

from modules.commercial_profile.public import CriterionKind, Verdict
from modules.opportunity_engine.domain.criterion_lift import (
    DIRECTIONAL_BELOW,
    CriterionLift,
    Outcome,
    lift_for,
)
from modules.opportunity_engine.domain.opportunity import Stage

INDUSTRY = CriterionKind.INDUSTRY


def _outcomes(**counts: int) -> list[Outcome]:
    """`won_yes`, `lost_yes`, `won_no`, `lost_no`, `unmeasured`, `dismissed`."""
    made: list[Outcome] = []
    made += [Outcome(Stage.CLOSED_WON, Verdict.YES)] * counts.get("won_yes", 0)
    made += [Outcome(Stage.CLOSED_LOST, Verdict.YES)] * counts.get("lost_yes", 0)
    made += [Outcome(Stage.CLOSED_WON, Verdict.NO)] * counts.get("won_no", 0)
    made += [Outcome(Stage.CLOSED_LOST, Verdict.NO)] * counts.get("lost_no", 0)
    made += [Outcome(Stage.CLOSED_WON, Verdict.UNMEASURED)] * counts.get("unmeasured", 0)
    made += [Outcome(Stage.DISMISSED, Verdict.YES)] * counts.get("dismissed", 0)
    return made


class TestTheArithmetic:
    def test_a_criterion_that_predicts_nothing_measures_one(self) -> None:
        """Same win rate inside and outside the criterion — **1.0 is a real
        answer**, and it means *this told you nothing*."""
        found = lift_for(INDUSTRY, _outcomes(won_yes=5, lost_yes=5, won_no=5, lost_no=5))

        assert found.lift == 1.0

    def test_a_predictive_criterion_measures_above_one(self) -> None:
        found = lift_for(INDUSTRY, _outcomes(won_yes=8, lost_yes=2, won_no=2, lost_no=8))

        assert found.lift is not None and found.lift > 1.0

    def test_a_criterion_can_select_against_you(self) -> None:
        """**Below 1.0 is the most useful thing this can say** and the one
        nobody expects to see."""
        found = lift_for(INDUSTRY, _outcomes(won_yes=2, lost_yes=8, won_no=8, lost_no=2))

        assert found.lift is not None and found.lift < 1.0


class TestItRefusesToInventANumber:
    def test_nothing_satisfying_the_criterion_has_no_lift(self) -> None:
        assert lift_for(INDUSTRY, _outcomes(won_no=5, lost_no=5)).lift is None

    def test_no_decided_accounts_at_all_has_no_lift(self) -> None:
        assert lift_for(INDUSTRY, []).lift is None

    def test_a_workspace_with_no_wins_yet_has_no_lift(self) -> None:
        """**The case a young workspace hits.** `1.0` would read as *"this
        criterion is neutral"* when the truth is *"there are no wins to compare
        against."*"""
        assert lift_for(INDUSTRY, _outcomes(lost_yes=4, lost_no=4)).lift is None

    def test_it_never_returns_one_point_zero_from_no_evidence(self) -> None:
        """The row's own acceptance criterion: *a criterion no outcome data
        supports says so rather than reporting `1.0×`.*"""
        for outcomes in ([], _outcomes(won_no=3), _outcomes(lost_yes=3, lost_no=3)):
            assert lift_for(INDUSTRY, outcomes).lift is None


class TestUnmeasuredAccountsLeaveTheDenominator:
    def test_they_do_not_count_against_the_criterion(self) -> None:
        """**Counting them as not-satisfying would make a criterion look worse
        the less Signora knew** — the opposite of the truth."""
        known = lift_for(INDUSTRY, _outcomes(won_yes=5, lost_yes=5, won_no=5, lost_no=5))
        with_unknowns = lift_for(
            INDUSTRY, _outcomes(won_yes=5, lost_yes=5, won_no=5, lost_no=5, unmeasured=40)
        )

        assert with_unknowns.lift == known.lift

    def test_how_many_were_dropped_is_reported(self) -> None:
        """**Reported, never silently absorbed** — a lift over eleven accounts
        must not read as a lift over four hundred."""
        found = lift_for(INDUSTRY, _outcomes(won_yes=2, lost_no=2, unmeasured=7))

        assert found.unmeasured == 7
        assert found.measured == 4

    def test_a_dismissal_is_not_an_outcome_about_the_criterion(self) -> None:
        """**Feedback about Signora's own qualification**, not about whether
        the criterion predicts — folding it into losses would make a criterion
        look unpredictive because the platform surfaced the wrong accounts."""
        found = lift_for(INDUSTRY, _outcomes(won_yes=3, lost_no=3, dismissed=9))

        assert found.measured == 6
        assert found.unmeasured == 0


class TestEveryFigureCarriesItsSampleSize:
    def test_a_small_sample_is_visibly_small(self) -> None:
        found = lift_for(INDUSTRY, _outcomes(won_yes=2, lost_yes=1, won_no=1, lost_no=2))

        assert found.satisfied == 3
        assert found.is_directional

    def test_a_large_enough_sample_is_not(self) -> None:
        found = lift_for(
            INDUSTRY,
            _outcomes(won_yes=DIRECTIONAL_BELOW, lost_yes=0, won_no=5, lost_no=5),
        )

        assert not found.is_directional

    def test_the_threshold_is_the_approved_screens_own_sentence(self) -> None:
        """*"2.2× lift on only 22 deals; treat as directional, not settled."*
        **The screen and the measurement agree about what small means** rather
        than each carrying its own number."""
        assert DIRECTIONAL_BELOW == 22


class TestTheCountsCannotLie:
    def test_more_satisfied_than_measured_is_refused(self) -> None:
        with pytest.raises(ValueError, match="subset of the measured set"):
            CriterionLift(
                kind=INDUSTRY, satisfied=5, satisfied_won=1, measured=3, measured_won=1,
                unmeasured=0,
            )

    def test_more_won_than_existed_is_refused(self) -> None:
        with pytest.raises(ValueError, match="more accounts were won"):
            CriterionLift(
                kind=INDUSTRY, satisfied=3, satisfied_won=4, measured=3, measured_won=4,
                unmeasured=0,
            )
