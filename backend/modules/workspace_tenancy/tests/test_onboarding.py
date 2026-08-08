"""**The Onboarding Run** — [TASK-469](../../../../docs/BACKLOG.md), Workflow 8.

⚡ **Most of these assert what the aggregate REFUSES**, because the design's
promises are all refusals underneath: *nothing already known is asked again*,
*consent is never inferred*, *the fourth selection is disabled not silently
ignored*, *free numbers are not accepted*.
"""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest

from modules.workspace_tenancy.domain.exceptions import (
    OnboardingRunAlreadyFinishedError,
    TeamSizeOutOfRangeError,
    TooManyGoalsError,
)
from modules.workspace_tenancy.domain.onboarding import (
    MAX_GOALS,
    MAX_TEAM_SIZE,
    Answer,
    CompanySizeBand,
    Goal,
    OnboardingRun,
    OnboardingStep,
    Provenance,
    Role,
    features_for,
)


def _run() -> OnboardingRun:
    return OnboardingRun(
        workspace_id=uuid4(),
        person_id=uuid4(),
        started_at=datetime.now(UTC),
    )


class TestAValueCarriesWhereItCameFrom:
    """*"Every inferred value marked as inferred and correctable."*"""

    def test_confirming_keeps_the_value_and_changes_only_its_standing(self) -> None:
        # Screen `04` is four confirmations and no typing. The value being
        # unchanged is the point: the person agreed rather than answered.
        inferred = Answer(value="Logistics & transport", provenance=Provenance.INFERRED)

        confirmed = inferred.confirmed()

        assert confirmed.value == inferred.value
        assert confirmed.provenance is Provenance.CONFIRMED

    def test_correcting_makes_it_theirs(self) -> None:
        inferred = Answer(value="Software", provenance=Provenance.INFERRED)

        assert inferred.corrected("Manufacturing") == Answer(
            value="Manufacturing", provenance=Provenance.ENTERED
        )

    def test_provenance_has_no_default_so_a_guess_cannot_pass_as_an_answer(self) -> None:
        """⛔ **The one assertion that protects the badge.**

        A default would let a caller store an inferred value that renders
        without its marking — and a screen cannot mark what the record did not
        keep.
        """
        with pytest.raises(TypeError):
            Answer(value="Software")  # type: ignore[call-arg]


class TestSkippingIsSafe:
    """*"An abandoned onboarding still produces a customer."*"""

    def test_a_new_run_answers_nothing_and_is_valid(self) -> None:
        run = _run()

        assert run.industry is None
        assert run.role is None
        assert run.goals == ()
        assert not run.is_finished

    def test_skipping_is_recorded_and_is_not_finishing(self) -> None:
        # ⛔ The two are different facts and the resume banner reads the
        # difference: a skipped run is resumable, a finished one is not.
        skipped = _run().skip()

        assert skipped.skipped_at is not None
        assert skipped.finished_at is None
        assert not skipped.is_finished

    def test_a_run_nobody_touched_is_distinguishable_from_one_they_left(self) -> None:
        assert _run().skipped_at is None


class TestProgressIsNamedStepsAndGoingBackIsNotDestructive:
    def test_advancing_completes_the_step_being_left(self) -> None:
        run = _run().advance_to(OnboardingStep.COMPANY)

        assert run.current_step is OnboardingStep.COMPANY
        assert OnboardingStep.WELCOME in run.completed_steps

    def test_returning_to_a_step_does_not_uncomplete_it(self) -> None:
        """*"Back is always available, never destructive."*"""
        forward = _run().advance_to(OnboardingStep.COMPANY).advance_to(OnboardingStep.YOU)

        back = forward.advance_to(OnboardingStep.COMPANY)

        assert back.current_step is OnboardingStep.COMPANY
        assert {OnboardingStep.WELCOME, OnboardingStep.COMPANY} <= back.completed_steps

    def test_answers_survive_going_back(self) -> None:
        # *"Returning to a step shows what was chosen, not an empty form."*
        run = (
            _run()
            .confirm_company(industry=Answer("Software", Provenance.CONFIRMED))
            .advance_to(OnboardingStep.YOU)
            .advance_to(OnboardingStep.COMPANY)
        )

        assert run.industry == Answer("Software", Provenance.CONFIRMED)


class TestTheCompanyStepAnswersPartially:
    def test_omitting_a_field_leaves_it_alone(self) -> None:
        """⛔ **The defect this prevents is silent data loss.**

        A call meaning to change the timezone must not clear the industry the
        person confirmed two fields earlier.
        """
        run = _run().confirm_company(
            industry=Answer("Logistics & transport", Provenance.CONFIRMED),
            company_size=Answer(CompanySizeBand.LARGE, Provenance.INFERRED),
        )

        later = run.confirm_company(timezone=Answer("Europe/Berlin", Provenance.CONFIRMED))

        assert later.industry == run.industry
        assert later.company_size == run.company_size
        assert later.timezone == Answer("Europe/Berlin", Provenance.CONFIRMED)

    def test_size_is_a_band_and_a_free_number_will_not_type_check(self) -> None:
        """*"Free numbers are not accepted; bands are what benchmarks are
        computed against."* ⚡ **Enforced by the type, asserted here so the
        reason survives** — a reviewer seeing `CompanySizeBand` should find
        the sentence that made it an enum."""
        run = _run().confirm_company(
            company_size=Answer(CompanySizeBand.ENTERPRISE, Provenance.CONFIRMED)
        )

        assert run.company_size is not None
        assert run.company_size.value.value == "1001-5000"


class TestTeamSizeIsRefusedRatherThanCorrected:
    @pytest.mark.parametrize("size", [0, -1, MAX_TEAM_SIZE + 1])
    def test_out_of_range_raises(self, size: int) -> None:
        with pytest.raises(TeamSizeOutOfRangeError):
            _run().describe_person(team_size=Answer(size, Provenance.ENTERED))

    def test_zero_is_not_quietly_turned_into_one(self) -> None:
        """⚠️ **The whole reason this refuses instead of clamping.** Somebody
        typing `0` is telling the product something; storing `1` answers them
        by overwriting it."""
        with pytest.raises(TeamSizeOutOfRangeError):
            _run().describe_person(team_size=Answer(0, Provenance.ENTERED))

    @pytest.mark.parametrize("size", [1, MAX_TEAM_SIZE])
    def test_the_boundaries_are_inclusive(self, size: int) -> None:
        run = _run().describe_person(team_size=Answer(size, Provenance.ENTERED))

        assert run.team_size is not None
        assert run.team_size.value == size


class TestGoalsStopAtThree:
    def test_the_fourth_is_refused_not_ignored(self) -> None:
        with pytest.raises(TooManyGoalsError):
            _run().choose_goals(
                (
                    Goal.FORECAST_ACCURATELY,
                    Goal.STOP_DEALS_SLIPPING,
                    Goal.PROTECT_RENEWALS,
                    Goal.COACH_THE_TEAM,
                )
            )

    def test_choosing_none_is_permitted(self) -> None:
        """*"Skipping entirely is permitted."*"""
        assert _run().choose_goals(()).goals == ()

    def test_selection_order_is_kept_because_it_orders_the_home_page(self) -> None:
        chosen = (Goal.PROTECT_RENEWALS, Goal.FORECAST_ACCURATELY)

        assert _run().choose_goals(chosen).goals == chosen

    def test_a_repeated_goal_counts_once(self) -> None:
        run = _run().choose_goals((Goal.FORECAST_ACCURATELY, Goal.FORECAST_ACCURATELY))

        assert run.goals == (Goal.FORECAST_ACCURATELY,)

    def test_three_is_exactly_the_limit(self) -> None:
        chosen = (Goal.FORECAST_ACCURATELY, Goal.STOP_DEALS_SLIPPING, Goal.PROTECT_RENEWALS)

        assert len(_run().choose_goals(chosen).goals) == MAX_GOALS


class TestGoalsReplaceTheFeatureMenu:
    """*"Three outcomes map deterministically onto modules, so the
    feature-preferences step disappears."*"""

    def test_features_are_derived_from_the_goals(self) -> None:
        run = _run().choose_goals((Goal.FORECAST_ACCURATELY,))

        assert run.features == ("forecast", "executive_dashboard")

    def test_a_feature_two_goals_imply_appears_once_in_selection_order(self) -> None:
        run = _run().choose_goals((Goal.PROVE_MARKETING_IMPACT, Goal.FORECAST_ACCURATELY))

        assert run.features == ("reports", "executive_dashboard", "forecast")

    def test_no_goals_implies_no_features_rather_than_all_of_them(self) -> None:
        # ⛔ A skipped goals step must not read as "give me everything" — the
        # home page would then be identical for a person who chose nothing and
        # a person who chose all three, which makes the step decorative.
        assert _run().choose_goals(()).features == ()

    def test_every_goal_maps_to_something(self) -> None:
        """⛔ **A goal with no features would be a choice that does nothing** —
        the design's case against a feature menu applies to its replacement."""
        for goal in Goal:
            assert features_for((goal,)), goal

    def test_the_mapping_is_derived_and_not_a_stored_column(self) -> None:
        # Two runs with the same goals cannot disagree, because neither stores
        # the answer — §2, truth has one authoritative representation.
        goals = (Goal.COACH_THE_TEAM, Goal.FIND_NEW_PIPELINE)

        assert _run().choose_goals(goals).features == features_for(goals)


class TestAFinishedRunIsHistory:
    def test_finishing_records_when(self) -> None:
        run = _run().advance_to(OnboardingStep.CONNECT).finish()

        assert run.is_finished
        assert run.finished_at is not None

    @pytest.mark.parametrize(
        "change",
        [
            lambda r: r.choose_goals((Goal.PROTECT_RENEWALS,)),
            lambda r: r.confirm_company(industry=Answer("Software", Provenance.ENTERED)),
            lambda r: r.describe_person(role=Answer(Role.MARKETING, Provenance.ENTERED)),
            lambda r: r.advance_to(OnboardingStep.YOU),
            lambda r: r.skip(),
            lambda r: r.finish(),
        ],
    )
    def test_nothing_edits_it_afterwards(self, change: object) -> None:
        """⚡ **Onboarding answers become settings when the run ends.** Leaving
        this path open would give one fact two writers."""
        finished = _run().finish()

        with pytest.raises(OnboardingRunAlreadyFinishedError):
            change(finished)  # type: ignore[operator]

    def test_the_first_finish_is_the_one_that_happened(self) -> None:
        finished = _run().finish()

        with pytest.raises(OnboardingRunAlreadyFinishedError):
            finished.finish()


class TestTheAggregateIsFrozen:
    def test_a_caller_cannot_reach_through_it(self) -> None:
        """⛔ **The limit that refuses a fourth goal is worth nothing if the
        field is writable.**"""
        run = _run()

        with pytest.raises(AttributeError):
            run.goals = tuple(Goal)  # type: ignore[misc]
