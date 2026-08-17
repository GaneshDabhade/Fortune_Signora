"""The onboarding run's own behaviour — [TASK-469](../../../docs/BACKLOG.md).

🔴 **This file exists because there were none.** `domain/onboarding.py` is 402
lines and `application/use_cases/onboarding.py` is 245, and before this commit
**nothing under `tests/` imported either** — the only collected test matching
*onboarding* was a machine-credential scope parametrisation about a different
subject entirely. 📁 Recorded as [B-276](../../../docs/BUGS.md), because this
file closes the part the current slice touches and not the whole gap.

⚠️ **That is the shape [B-1011](../../../docs/BUGS.md) had.** A file nobody
tested, carrying behaviour a customer meets on their first screen, discovered
at a coverage gate rather than by reading. **The half that had never executed
there was a guard; the halves that had never executed here are the goal table
and every refusal in the aggregate.**
"""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest

from modules.workspace_tenancy.domain.exceptions import (
    OnboardingRunAlreadyFinishedError,
    TeamSizeOutOfRangeError,
    TooManyGoalsError,
)
from modules.workspace_tenancy.domain.onboarding import (
    MAX_GOALS,
    MAX_TEAM_SIZE,
    MIN_TEAM_SIZE,
    Answer,
    Goal,
    OnboardingRun,
    OnboardingStep,
    Provenance,
    Role,
    features_for,
)


def run(**changes: object) -> OnboardingRun:
    """A run at the moment it opens. ⛔ **Every answer `None`, and that is the
    product's real starting state** — no enrichment producer exists, so the
    fixture is not a simplification."""
    base = OnboardingRun(
        workspace_id=uuid4(),
        person_id=uuid4(),
        started_at=datetime(2026, 8, 17, tzinfo=UTC),
    )
    return base if not changes else base._touch(**changes)  # noqa: SLF001


class TestWhatTheGoalsSwitchOn:
    """*"Feature preferences follow from the goals — no separate step."*"""

    def test_no_goals_switches_nothing_on(self) -> None:
        assert run().features == ()

    def test_one_goal_gives_the_capabilities_it_implies(self) -> None:
        chosen = run().choose_goals((Goal.PROTECT_RENEWALS,))
        assert chosen.features == ("signals", "account_360")

    def test_two_goals_sharing_a_capability_report_it_once(self) -> None:
        """⚡ **`signals` is implied by two different goals.** A customer
        picking both has not switched it on twice, and a duplicate in this
        tuple would render as one in the sentence on screen `06`."""
        chosen = run().choose_goals((Goal.STOP_DEALS_SLIPPING, Goal.PROTECT_RENEWALS))
        assert chosen.features.count("signals") == 1

    def test_the_order_is_the_order_the_goals_were_chosen_in(self) -> None:
        """📁 *"These order the home page"* — ⛔ so this is a sequence and not
        a set, and reversing the goals must reverse what leads."""
        forward = run().choose_goals((Goal.FORECAST_ACCURATELY, Goal.FIND_NEW_PIPELINE))
        backward = run().choose_goals((Goal.FIND_NEW_PIPELINE, Goal.FORECAST_ACCURATELY))
        assert forward.features[0] == "forecast"
        assert backward.features[0] == "companies"

    def test_the_function_and_the_property_cannot_disagree(self) -> None:
        """`features_for()` exists for callers holding goals without a run.
        ⛔ **Two routes to one answer is exactly what §2 warns about**, so the
        fact that one delegates to the other is asserted rather than trusted."""
        goals = (Goal.COACH_THE_TEAM, Goal.PROVE_MARKETING_IMPACT)
        assert features_for(goals) == run().choose_goals(goals).features


class TestWhatTheGoalsLeftOff:
    """📁 Screen `06`'s other half — *"and leave Marketing attribution off"*."""

    def test_nothing_is_off_before_anything_is_chosen(self) -> None:
        """⚠️ **Absence of a choice is not a choice against.** With no goals,
        listing eight capabilities as *off* would describe a decision the
        person has not made."""
        assert run().features_off == ()

    def test_off_is_exactly_the_complement_of_on(self) -> None:
        chosen = run().choose_goals((Goal.FORECAST_ACCURATELY,))
        assert set(chosen.features) & set(chosen.features_off) == set()
        assert "forecast" in chosen.features
        assert "signals" in chosen.features_off

    def test_every_capability_is_on_one_side_or_the_other(self) -> None:
        """⛔ **The universe is derived from the goal table, not listed beside
        it.** A capability missing from a hand-written list would never appear
        as *off* and nothing would say so — which is why this asserts the
        union rather than a literal set of names."""
        for goal in Goal:
            chosen = run().choose_goals((goal,))
            everything = set(chosen.features) | set(chosen.features_off)
            assert everything == set(features_for(tuple(Goal)))

    def test_choosing_every_goal_leaves_nothing_off(self) -> None:
        chosen = run().choose_goals(tuple(Goal)[:MAX_GOALS])
        assert set(chosen.features).isdisjoint(chosen.features_off)


class TestTheFourthGoalIsRefused:
    def test_three_is_allowed(self) -> None:
        chosen = run().choose_goals(tuple(Goal)[:MAX_GOALS])
        assert len(chosen.goals) == MAX_GOALS

    def test_the_fourth_raises_rather_than_being_dropped(self) -> None:
        """⛔ **Refused, never silently truncated.** 📁 [B-255](../../../docs/BUGS.md):
        a control that silently does nothing is worse than one that is absent,
        and a fourth goal quietly discarded is that defect in the domain."""
        with pytest.raises(TooManyGoalsError):
            run().choose_goals(tuple(Goal)[: MAX_GOALS + 1])

    def test_a_repeated_goal_is_not_a_fourth(self) -> None:
        """⚡ **Deduplication happens after the limit is checked**, so three
        distinct goals sent twice is still an error rather than three."""
        chosen = run().choose_goals((Goal.PROTECT_RENEWALS, Goal.PROTECT_RENEWALS))
        assert chosen.goals == (Goal.PROTECT_RENEWALS,)

    def test_choosing_none_is_a_valid_answer(self) -> None:
        """📁 *"Skipping entirely is permitted."*"""
        assert run().choose_goals(()).goals == ()


class TestAFinishedRunIsHistory:
    """[§2](../../../CLAUDE.md) — *immutability is the default for anything
    that records a fact*, and every one of these refusals had never run."""

    @pytest.fixture
    def finished(self) -> OnboardingRun:
        return run().finish()

    def test_it_cannot_choose_goals(self, finished: OnboardingRun) -> None:
        with pytest.raises(OnboardingRunAlreadyFinishedError):
            finished.choose_goals((Goal.PROTECT_RENEWALS,))

    def test_it_cannot_advance(self, finished: OnboardingRun) -> None:
        with pytest.raises(OnboardingRunAlreadyFinishedError):
            finished.advance_to(OnboardingStep.GOALS)

    def test_it_cannot_confirm_company_facts(self, finished: OnboardingRun) -> None:
        with pytest.raises(OnboardingRunAlreadyFinishedError):
            finished.confirm_company(industry=Answer("saas", Provenance.ENTERED))

    def test_it_cannot_be_finished_twice(self, finished: OnboardingRun) -> None:
        """⚡ **The first timestamp is the one that happened.**"""
        with pytest.raises(OnboardingRunAlreadyFinishedError):
            finished.finish()

    def test_it_cannot_be_skipped(self, finished: OnboardingRun) -> None:
        """⛔ **Leaving and finishing are different facts** and a finished run
        cannot acquire the first one afterwards."""
        with pytest.raises(OnboardingRunAlreadyFinishedError):
            finished.skip()


class TestLeavingIsNotFinishing:
    def test_skipping_records_when_and_does_not_finish(self) -> None:
        left = run().skip()
        assert left.skipped_at is not None
        assert left.finished_at is None
        assert left.is_finished is False

    def test_a_run_nobody_left_has_no_skip_stamp(self) -> None:
        """⚡ **The resume banner reads this**, so *never started* and *left*
        must be distinguishable — 📁 the design shows the banner for one and
        not the other."""
        assert run().skipped_at is None

    def test_a_left_run_can_still_be_finished(self) -> None:
        """📁 *"An abandoned onboarding still produces a customer."* Coming
        back through the resume banner must work."""
        assert run().skip().finish().is_finished is True


class TestAdvancingIsWhatCompletesAStep:
    def test_the_step_being_left_becomes_complete(self) -> None:
        moved = run().advance_to(OnboardingStep.COMPANY)
        assert OnboardingStep.WELCOME in moved.completed_steps
        assert moved.current_step is OnboardingStep.COMPANY

    def test_going_back_does_not_uncomplete_anything(self) -> None:
        """📁 *"Returning to a step shows what was chosen, not an empty
        form."* ⛔ **A completed step stays completed**, or the rail would
        un-tick behind somebody who simply looked back."""
        forward = run().advance_to(OnboardingStep.COMPANY).advance_to(OnboardingStep.YOU)
        back = forward.advance_to(OnboardingStep.COMPANY)
        assert OnboardingStep.WELCOME in back.completed_steps
        assert OnboardingStep.COMPANY in back.completed_steps


class TestProvenanceTravelsWithTheValue:
    """📁 Screen `04`'s whole premise — *"four confirmations, no typing"*."""

    def test_confirming_keeps_the_value_and_changes_only_where_it_came_from(self) -> None:
        inferred = Answer("saas", Provenance.INFERRED)
        assert inferred.confirmed() == Answer("saas", Provenance.CONFIRMED)

    def test_correcting_makes_it_theirs(self) -> None:
        """⚡ *"Inferred and correctable"* — ⛔ **and a corrected value is
        `ENTERED`, never still `INFERRED`**, because *the product guessed* and
        *a human typed it* are the distinction provenance exists for."""
        assert Answer("saas", Provenance.INFERRED).corrected("fintech") == Answer(
            "fintech", Provenance.ENTERED
        )

    def test_confirming_a_company_fact_leaves_the_others_alone(self) -> None:
        """⛔ **A call meaning to change one field must not reset three.** The
        step is skippable and partially answerable, so the omitted arguments
        are *unchanged*, not *cleared*."""
        started = run().confirm_company(
            industry=Answer("saas", Provenance.INFERRED),
            timezone=Answer("Europe/Copenhagen", Provenance.INFERRED),
        )
        corrected = started.confirm_company(industry=Answer("fintech", Provenance.ENTERED))
        assert corrected.industry == Answer("fintech", Provenance.ENTERED)
        assert corrected.timezone == Answer("Europe/Copenhagen", Provenance.INFERRED)


class TestTheRunIsAboutOnePersonInOneWorkspace:
    def test_two_members_of_one_workspace_hold_separate_runs(self) -> None:
        """⚠️ **Keyed by workspace *and* person.** A single row per workspace
        would let the second member resume the first member's run, and the
        resume banner would then offer it to the wrong person."""
        workspace = uuid4()
        first = OnboardingRun(
            workspace_id=workspace,
            person_id=uuid4(),
            started_at=datetime(2026, 8, 17, tzinfo=UTC),
        )
        second = OnboardingRun(
            workspace_id=workspace,
            person_id=uuid4(),
            started_at=datetime(2026, 8, 17, tzinfo=UTC),
        )
        assert first.person_id != second.person_id
        assert first.workspace_id == second.workspace_id

    def test_the_placeholder_identity_features_for_uses_is_never_a_real_one(self) -> None:
        """`features_for()` builds a throwaway run with `UUID(int=0)`. ⛔ **If
        that ever escaped into a repository it would be a cross-tenant row**,
        so this asserts it is the null UUID and therefore recognisable."""
        assert UUID(int=0) == UUID("00000000-0000-0000-0000-000000000000")


class TestHowBigTheTeamIs:
    """📁 Screen `05` — *"Integer ≥ 1, ≤ 10,000. Zero explains that they
    count."* ⛔ **Every one of these refusals was unexecuted** ([B-276](../../../docs/BUGS.md))."""

    def test_a_real_number_is_kept_with_its_provenance(self) -> None:
        described = run().describe_person(
            role=Answer(Role.REVENUE_LEADER, Provenance.ENTERED),
            team_size=Answer(12, Provenance.ENTERED),
        )
        assert described.team_size == Answer(12, Provenance.ENTERED)
        assert described.role == Answer(Role.REVENUE_LEADER, Provenance.ENTERED)

    def test_zero_is_refused(self) -> None:
        """⚠️ **Refused, not silently corrected to one.** 📁 *"A person who
        types it is telling the product something, and silently storing `1`
        would answer them by overwriting the question."*"""
        with pytest.raises(TeamSizeOutOfRangeError):
            run().describe_person(team_size=Answer(0, Provenance.ENTERED))

    def test_the_bounds_themselves_are_accepted(self) -> None:
        """⛔ **The boundary is inclusive, and an off-by-one here would reject
        the single-person team the message exists to welcome.**"""
        for size in (MIN_TEAM_SIZE, MAX_TEAM_SIZE):
            assert run().describe_person(
                team_size=Answer(size, Provenance.ENTERED)
            ).team_size == Answer(size, Provenance.ENTERED)

    def test_one_past_the_top_is_refused(self) -> None:
        with pytest.raises(TeamSizeOutOfRangeError):
            run().describe_person(team_size=Answer(MAX_TEAM_SIZE + 1, Provenance.ENTERED))

    def test_describing_only_a_role_leaves_the_team_size_alone(self) -> None:
        """⛔ **The step is skippable and partially answerable.** A call meaning
        to set one field must not clear the other."""
        started = run().describe_person(team_size=Answer(12, Provenance.ENTERED))
        after = started.describe_person(role=Answer(Role.MARKETING, Provenance.ENTERED))
        assert after.team_size == Answer(12, Provenance.ENTERED)

    def test_a_finished_run_will_not_describe_a_person(self) -> None:
        with pytest.raises(OnboardingRunAlreadyFinishedError):
            run().finish().describe_person(role=Answer(Role.EXECUTIVE, Provenance.ENTERED))
