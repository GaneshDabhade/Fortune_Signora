"""The onboarding use cases — [TASK-469](../../../../docs/BACKLOG.md).

⚡ **The interesting cases are the ones a person creates by being ordinary**:
starting twice because they came back from the resume banner, saving the same
step twice because the field blurred and then they advanced, and leaving
halfway through.
"""

from __future__ import annotations

from uuid import UUID, uuid4

import pytest

from modules.workspace_tenancy.application.use_cases.onboarding import (
    AdvanceOnboardingInput,
    AdvanceOnboardingUseCase,
    ChooseGoalsInput,
    ChooseGoalsUseCase,
    ConfirmCompanyInput,
    ConfirmCompanyUseCase,
    DescribePersonInput,
    DescribePersonUseCase,
    FinishOnboardingInput,
    FinishOnboardingUseCase,
    GetOnboardingUseCase,
    SkipOnboardingUseCase,
    StartOnboardingInput,
    StartOnboardingUseCase,
    inferred,
)
from modules.workspace_tenancy.domain.entities import Workspace
from modules.workspace_tenancy.domain.exceptions import (
    OnboardingRunNotFoundError,
    TooManyGoalsError,
    WorkspaceNotFoundError,
)
from modules.workspace_tenancy.domain.onboarding import (
    Answer,
    CompanySizeBand,
    Goal,
    OnboardingStep,
    Provenance,
    Role,
)
from modules.workspace_tenancy.tests.fakes import (
    FakeOnboardingRunRepository,
    FakeWorkspaceRepository,
)

pytestmark = pytest.mark.asyncio


async def _started() -> tuple[FakeWorkspaceRepository, FakeOnboardingRunRepository, UUID, UUID]:
    workspaces = FakeWorkspaceRepository()
    runs = FakeOnboardingRunRepository()
    # `create` returns the aggregate and the event it raised; only the first
    # is this helper's business.
    workspace, _event = Workspace.create(name="Northwind", created_by=uuid4())
    await workspaces.add(workspace)
    person = uuid4()
    await StartOnboardingUseCase(workspaces=workspaces, runs=runs).execute(
        StartOnboardingInput(workspace_id=workspace.id, person_id=person)
    )
    return workspaces, runs, workspace.id, person


class TestStarting:
    async def test_a_run_begins_at_welcome(self) -> None:
        _, runs, workspace_id, person = await _started()

        run = await GetOnboardingUseCase(runs=runs).execute(workspace_id, person)

        assert run.current_step is OnboardingStep.WELCOME
        assert not run.is_finished

    async def test_starting_twice_returns_the_run_in_progress(self) -> None:
        """⛔ **The person most likely to hit this came back from the resume
        banner**, and restarting would throw away the answers that made the
        banner worth showing."""
        workspaces, runs, workspace_id, person = await _started()
        await ChooseGoalsUseCase(runs=runs).execute(
            ChooseGoalsInput(
                workspace_id=workspace_id,
                person_id=person,
                goals=(Goal.PROTECT_RENEWALS,),
            ),
        )

        again = await StartOnboardingUseCase(workspaces=workspaces, runs=runs).execute(
            StartOnboardingInput(workspace_id=workspace_id, person_id=person)
        )

        assert again.goals == (Goal.PROTECT_RENEWALS,)

    async def test_two_people_in_one_workspace_have_two_runs(self) -> None:
        """⚠️ **The reason the key is composite.** A single run per workspace
        would let the second member resume the first member's, and the banner
        would offer the wrong person somebody else's half-finished answers."""
        workspaces, runs, workspace_id, first = await _started()
        second = uuid4()

        await StartOnboardingUseCase(workspaces=workspaces, runs=runs).execute(
            StartOnboardingInput(workspace_id=workspace_id, person_id=second)
        )
        await ChooseGoalsUseCase(runs=runs).execute(
            ChooseGoalsInput(
                workspace_id=workspace_id,
                person_id=first,
                goals=(Goal.COACH_THE_TEAM,),
            ),
        )

        assert (await GetOnboardingUseCase(runs=runs).execute(workspace_id, second)).goals == ()

    async def test_an_unknown_workspace_is_not_found_rather_than_forbidden(self) -> None:
        # 404, never 403 — a workspace the caller cannot see must be
        # indistinguishable from one that does not exist (18-authentication).
        with pytest.raises(WorkspaceNotFoundError):
            await StartOnboardingUseCase(
                workspaces=FakeWorkspaceRepository(), runs=FakeOnboardingRunRepository()
            ).execute(StartOnboardingInput(workspace_id=uuid4(), person_id=uuid4()))


class TestEveryStepPersists:
    """*"Every step saves on advance and on blur."*"""

    async def test_advancing_is_saved_not_held_in_the_client(self) -> None:
        _, runs, workspace_id, person = await _started()

        await AdvanceOnboardingUseCase(runs=runs).execute(
            AdvanceOnboardingInput(
                workspace_id=workspace_id,
                person_id=person,
                step=OnboardingStep.COMPANY,
            ),
        )

        reloaded = await GetOnboardingUseCase(runs=runs).execute(workspace_id, person)
        assert reloaded.current_step is OnboardingStep.COMPANY
        assert OnboardingStep.WELCOME in reloaded.completed_steps

    async def test_a_partial_company_answer_does_not_clear_the_rest(self) -> None:
        _, runs, workspace_id, person = await _started()
        await ConfirmCompanyUseCase(runs=runs).execute(
            ConfirmCompanyInput(
                workspace_id=workspace_id,
                person_id=person,
                industry=Answer("Logistics & transport", Provenance.CONFIRMED),
                company_size=Answer(CompanySizeBand.LARGE, Provenance.INFERRED),
            ),
        )

        run = await ConfirmCompanyUseCase(runs=runs).execute(
            ConfirmCompanyInput(
                workspace_id=workspace_id,
                person_id=person,
                timezone=Answer("Europe/Berlin", Provenance.CONFIRMED),
            ),
        )

        assert run.industry is not None
        assert run.industry.value == "Logistics & transport"
        assert run.company_size is not None

    async def test_an_inferred_value_keeps_its_marking_through_a_save(self) -> None:
        """⛔ **The badge is only as good as the round trip.** A provenance
        lost between the request and the read is an inferred value rendering
        as a confirmed one."""
        _, runs, workspace_id, person = await _started()

        await ConfirmCompanyUseCase(runs=runs).execute(
            ConfirmCompanyInput(
                workspace_id=workspace_id,
                person_id=person,
                region=inferred("EU"),
            ),
        )

        run = await GetOnboardingUseCase(runs=runs).execute(workspace_id, person)
        assert run.region is not None
        assert run.region.provenance is Provenance.INFERRED

    async def test_the_role_and_team_size_land(self) -> None:
        _, runs, workspace_id, person = await _started()

        run = await DescribePersonUseCase(runs=runs).execute(
            DescribePersonInput(
                workspace_id=workspace_id,
                person_id=person,
                role=Answer(Role.REVENUE_LEADER, Provenance.ENTERED),
                team_size=Answer(24, Provenance.ENTERED),
            ),
        )

        assert run.role is not None
        assert run.role.value is Role.REVENUE_LEADER
        assert run.team_size is not None
        assert run.team_size.value == 24


class TestGoalsAndTheFeaturesTheyImply:
    async def test_the_goals_come_back_with_the_features_derived(self) -> None:
        _, runs, workspace_id, person = await _started()

        run = await ChooseGoalsUseCase(runs=runs).execute(
            ChooseGoalsInput(
                workspace_id=workspace_id,
                person_id=person,
                goals=(Goal.FORECAST_ACCURATELY,),
            ),
        )

        assert run.features == ("forecast", "executive_dashboard")

    async def test_a_fourth_goal_is_refused_at_this_layer_too(self) -> None:
        # ⛔ The screen disables it; this refuses it. A limit kept only in the
        # client is a limit a request body does not have.
        _, runs, workspace_id, person = await _started()

        with pytest.raises(TooManyGoalsError):
            await ChooseGoalsUseCase(runs=runs).execute(
                ChooseGoalsInput(
                    workspace_id=workspace_id,
                    person_id=person,
                    goals=(
                        Goal.FORECAST_ACCURATELY,
                        Goal.STOP_DEALS_SLIPPING,
                        Goal.PROTECT_RENEWALS,
                        Goal.FIND_NEW_PIPELINE,
                    ),
                ),
            )


class TestLeavingAndFinishing:
    async def test_skipping_records_that_they_left(self) -> None:
        _, runs, workspace_id, person = await _started()

        run = await SkipOnboardingUseCase(runs=runs).execute(
            FinishOnboardingInput(workspace_id=workspace_id, person_id=person),
        )

        assert run.skipped_at is not None
        assert not run.is_finished

    async def test_a_skipped_run_is_resumable_with_its_answers(self) -> None:
        """✅ **The banner's whole promise.** *"The resume banner does the
        remaining work quietly"* — quietly is only possible if what they had
        already done is still there."""
        workspaces, runs, workspace_id, person = await _started()
        await ChooseGoalsUseCase(runs=runs).execute(
            ChooseGoalsInput(
                workspace_id=workspace_id,
                person_id=person,
                goals=(Goal.FIND_NEW_PIPELINE,),
            ),
        )
        await SkipOnboardingUseCase(runs=runs).execute(
            FinishOnboardingInput(workspace_id=workspace_id, person_id=person),
        )

        resumed = await StartOnboardingUseCase(workspaces=workspaces, runs=runs).execute(
            StartOnboardingInput(workspace_id=workspace_id, person_id=person)
        )

        assert resumed.goals == (Goal.FIND_NEW_PIPELINE,)
        assert not resumed.is_finished

    async def test_finishing_is_persisted(self) -> None:
        _, runs, workspace_id, person = await _started()

        await FinishOnboardingUseCase(runs=runs).execute(
            FinishOnboardingInput(workspace_id=workspace_id, person_id=person),
        )

        assert (await GetOnboardingUseCase(runs=runs).execute(workspace_id, person)).is_finished


class TestReadingSomethingNobodyStarted:
    async def test_it_is_not_found_rather_than_an_empty_run(self) -> None:
        """⛔ **An empty run invented on read would make the banner permanent**
        — there would be no state in which nobody had started, so the product
        would forever offer to continue something that does not exist."""
        with pytest.raises(OnboardingRunNotFoundError):
            await GetOnboardingUseCase(runs=FakeOnboardingRunRepository()).execute(uuid4(), uuid4())
