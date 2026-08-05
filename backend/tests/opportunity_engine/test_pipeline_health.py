"""The dashboard's arithmetic, tested where it has no database.

**Every rule here is one a customer could dispute**, so every one of them is a
pure function and every test below reads like the sentence a CRO would say.
"""

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest

from modules.opportunity_engine.domain.opportunity import Stage
from modules.opportunity_engine.domain.pipeline_health import (
    FUNNEL,
    OwnerLoad,
    StageAgeing,
    StageConversion,
    funnel,
    median,
    stage_ageing,
)

NOW = datetime(2026, 8, 5, 12, 0, tzinfo=UTC)


class TestARateOverNothingIsNotZero:
    """The discipline the whole module inherits."""

    def test_a_stage_nobody_reached_has_no_conversion_rate(self) -> None:
        step = StageConversion(
            from_stage=Stage.TRACKING, to_stage=Stage.ENGAGED, entered=0, advanced=0
        )
        # Not 0.0. A new workspace reading "0% conversion" would act on a
        # number measured from no evidence at all.
        assert step.rate is None

    def test_a_stage_everybody_left_reports_zero_which_is_a_real_answer(self) -> None:
        step = StageConversion(
            from_stage=Stage.TRACKING, to_stage=Stage.ENGAGED, entered=9, advanced=0
        )
        assert step.rate == 0.0

    def test_a_rate_is_the_proportion_that_advanced(self) -> None:
        step = StageConversion(
            from_stage=Stage.TRACKING, to_stage=Stage.ENGAGED, entered=8, advanced=2
        )
        assert step.rate == 0.25

    def test_more_advanced_than_entered_is_refused_rather_than_reported(self) -> None:
        with pytest.raises(ValueError, match="only 3 ever entered"):
            StageConversion(
                from_stage=Stage.TRACKING, to_stage=Stage.ENGAGED, entered=3, advanced=4
            )


class TestTheFunnelKeepsItsShape:
    def test_every_step_is_returned_even_in_an_empty_workspace(self) -> None:
        steps = funnel({}, {})
        # The same three rows on the first day as on the hundredth, so a
        # surface does not have to render two different layouts.
        assert [(s.from_stage, s.to_stage) for s in steps] == list(zip(FUNNEL, FUNNEL[1:]))
        assert all(step.rate is None for step in steps)

    def test_the_steps_are_the_funnel_and_the_exits_are_not_in_it(self) -> None:
        assert Stage.CLOSED_LOST not in FUNNEL
        assert Stage.DISMISSED not in FUNNEL

    def test_counts_come_from_the_pair_not_from_two_independent_totals(self) -> None:
        # Twelve reached engaged, but only seven of them ever passed through
        # tracking. A rate built from the two totals would say 7/12; the
        # honest answer is over the accounts that actually entered.
        steps = funnel(
            {Stage.TRACKING: 10, Stage.ENGAGED: 12},
            {(Stage.TRACKING, Stage.ENGAGED): 7},
        )
        tracking_to_engaged = steps[0]
        assert tracking_to_engaged.entered == 10
        assert tracking_to_engaged.advanced == 7
        assert tracking_to_engaged.rate == 0.7


class TestAMedianSaysWhatItMeasured:
    def test_nothing_measured_is_none_rather_than_zero(self) -> None:
        # Zero days is a real answer meaning "arrived this morning".
        assert median([]) is None

    def test_an_odd_count_takes_the_middle(self) -> None:
        assert median([9.0, 1.0, 5.0]) == 5.0

    def test_an_even_count_averages_the_two_middle(self) -> None:
        assert median([1.0, 2.0, 4.0, 10.0]) == 3.0

    def test_it_does_not_depend_on_the_order_it_was_given(self) -> None:
        assert median([10.0, 1.0, 4.0, 2.0]) == median([1.0, 2.0, 4.0, 10.0])


class TestAgeingMeasuresWorkInProgress:
    def test_an_empty_stage_reports_no_median_and_no_oldest(self) -> None:
        ageing = stage_ageing(Stage.ENGAGED, (), now=NOW)
        assert ageing.open_count == 0
        assert ageing.median_days is None
        assert ageing.oldest_days is None

    def test_the_oldest_is_reported_beside_the_median(self) -> None:
        ageing = stage_ageing(
            Stage.ENGAGED,
            (NOW - timedelta(days=1), NOW - timedelta(days=3), NOW - timedelta(days=90)),
            now=NOW,
        )
        assert ageing.open_count == 3
        assert ageing.median_days == 3.0
        # The median says the stage is healthy; the oldest is the account
        # somebody forgot, and it is the reason both are returned.
        assert ageing.oldest_days == 90.0

    def test_now_is_supplied_by_the_caller_so_the_answer_replays(self) -> None:
        entered = (NOW - timedelta(days=2),)
        assert stage_ageing(Stage.TRACKING, entered, now=NOW).median_days == 2.0
        later = NOW + timedelta(days=5)
        assert stage_ageing(Stage.TRACKING, entered, now=later).median_days == 7.0

    def test_a_terminal_stage_cannot_age(self) -> None:
        # A closed opportunity has a duration, not an age — and letting one
        # through would put finished work on a list of things to chase.
        with pytest.raises(ValueError, match="is terminal and cannot age"):
            StageAgeing(
                stage=Stage.CLOSED_WON, open_count=1, median_days=3.0, oldest_days=3.0
            )

    def test_a_populated_stage_must_report_a_median(self) -> None:
        with pytest.raises(ValueError, match="exactly when it has open opportunities"):
            StageAgeing(stage=Stage.ENGAGED, open_count=4, median_days=None, oldest_days=None)


class TestAnOwnerRowIsCountsAndNothingElse:
    def test_unassigned_is_a_real_owner_row(self) -> None:
        # The column most worth looking at, because nobody is working it.
        load = OwnerLoad(owner_id=None, open_count=6, won=0, lost=0)
        assert load.owner_id is None
        assert load.open_count == 6

    def test_a_negative_count_is_refused(self) -> None:
        with pytest.raises(ValueError, match="cannot hold -1 won"):
            OwnerLoad(owner_id=uuid4(), open_count=0, won=-1, lost=0)
