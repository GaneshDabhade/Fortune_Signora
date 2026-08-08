"""Starting, saving, finishing and resuming an onboarding run.

**[TASK-469](../../../../../docs/BACKLOG.md) · Workflow 8**, against
`docs/design-snapshot/screens/Fortune Signora Onboarding.dc.html`.

### ⚡ Every use case here is *read, ask the aggregate, persist*

**Nothing decides anything `OnboardingRun` can decide.** The goal limit, the
team-size range, the refusal to edit a finished run — all of them live on the
aggregate, so a rule appearing here instead would be a rule the aggregate's
own tests could not reach.

### ⛔ What none of them do

**Enable a feature.** `features` is derived from the goals and returned so a
screen can say what it will get; **turning something on is the App Shell's and
Settings' work**, and a use case here that reached into another module's
configuration would make `workspace_tenancy` the owner of every capability the
product has.

**Infer anything.** *"Consent is never inferred"* — and the same discipline
applies one field earlier: an inferred company fact arrives from the caller
already marked `INFERRED`, because the enrichment that produced it is a
*provider* and enters through the Provider Simulation Framework
([20-provider-simulation.md](../../../../../docs/architecture/20-provider-simulation.md)),
never through a default in this layer.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID

from modules.workspace_tenancy.application.ports import (
    OnboardingRunRepository,
    WorkspaceRepository,
)
from modules.workspace_tenancy.domain.exceptions import (
    OnboardingRunNotFoundError,
    WorkspaceNotFoundError,
)
from modules.workspace_tenancy.domain.onboarding import (
    Answer,
    CompanySizeBand,
    Goal,
    OnboardingRun,
    OnboardingStep,
    Provenance,
    Role,
)


@dataclass(frozen=True)
class StartOnboardingInput:
    workspace_id: UUID
    person_id: UUID


@dataclass(frozen=True)
class AdvanceOnboardingInput:
    workspace_id: UUID
    person_id: UUID
    step: OnboardingStep


@dataclass(frozen=True)
class ConfirmCompanyInput:
    """Screen `04`. **Every field optional** — the step is skippable and
    partially answerable, and a call that meant to change the timezone must
    not clear the industry somebody confirmed two fields earlier."""

    workspace_id: UUID
    person_id: UUID
    industry: Answer[str] | None = None
    company_size: Answer[CompanySizeBand] | None = None
    region: Answer[str] | None = None
    timezone: Answer[str] | None = None


@dataclass(frozen=True)
class DescribePersonInput:
    workspace_id: UUID
    person_id: UUID
    role: Answer[Role] | None = None
    team_size: Answer[int] | None = None


@dataclass(frozen=True)
class ChooseGoalsInput:
    workspace_id: UUID
    person_id: UUID
    goals: tuple[Goal, ...]


@dataclass(frozen=True)
class FinishOnboardingInput:
    workspace_id: UUID
    person_id: UUID


class _OnboardingUseCase:
    """The load every one of them performs first.

    ⚡ **`ListWorkspaceMembersUseCase`'s shape rather than a new one** — this
    module's use cases are classes constructed with their ports, and a slice
    that introduced functions beside them would make the module look like two
    modules (§6, *match existing patterns in the module you are working in*).
    """

    def __init__(self, *, runs: OnboardingRunRepository) -> None:
        self._runs = runs

    async def _require_run(self, workspace_id: UUID, person_id: UUID) -> OnboardingRun:
        run = await self._runs.get(workspace_id, person_id)
        if run is None:
            raise OnboardingRunNotFoundError(
                "No onboarding run has been started in this workspace for this person."
            )
        return run


class StartOnboardingUseCase(_OnboardingUseCase):
    """Begin a run, or hand back the one already in progress.

    ⛔ **Starting twice never restarts.** *"Returning to a step shows what was
    chosen, not an empty form"* — and the person most likely to hit this is
    the one coming back from the resume banner, whose answers are the whole
    reason the banner exists.
    """

    def __init__(self, *, workspaces: WorkspaceRepository, runs: OnboardingRunRepository) -> None:
        super().__init__(runs=runs)
        self._workspaces = workspaces

    async def execute(self, input_: StartOnboardingInput) -> OnboardingRun:
        if await self._workspaces.get(input_.workspace_id) is None:
            # 404, never 403 — see `errors.py`. A workspace the caller cannot
            # see must be indistinguishable from one that does not exist.
            raise WorkspaceNotFoundError(input_.workspace_id)

        existing = await self._runs.get(input_.workspace_id, input_.person_id)
        if existing is not None:
            return existing

        run = OnboardingRun(
            workspace_id=input_.workspace_id,
            person_id=input_.person_id,
            started_at=datetime.now(UTC),
        )
        await self._runs.save(run)
        return run


class GetOnboardingUseCase(_OnboardingUseCase):
    """What the resume banner and every step read."""

    async def execute(self, workspace_id: UUID, person_id: UUID) -> OnboardingRun:
        return await self._require_run(workspace_id, person_id)


class AdvanceOnboardingUseCase(_OnboardingUseCase):
    """⚡ **This is autosave.** The step being left is completed and the
    transition is persisted, which is what makes *"you can leave at any
    point"* true rather than a promise the client keeps."""

    async def execute(self, input_: AdvanceOnboardingInput) -> OnboardingRun:
        run = (await self._require_run(input_.workspace_id, input_.person_id)).advance_to(
            input_.step
        )
        await self._runs.save(run)
        return run


class ConfirmCompanyUseCase(_OnboardingUseCase):
    """Screen `04` — four facts, each confirmed or corrected."""

    async def execute(self, input_: ConfirmCompanyInput) -> OnboardingRun:
        run = (await self._require_run(input_.workspace_id, input_.person_id)).confirm_company(
            industry=input_.industry,
            company_size=input_.company_size,
            region=input_.region,
            timezone=input_.timezone,
        )
        await self._runs.save(run)
        return run


class DescribePersonUseCase(_OnboardingUseCase):
    """Screen `05` — role and team size."""

    async def execute(self, input_: DescribePersonInput) -> OnboardingRun:
        run = (await self._require_run(input_.workspace_id, input_.person_id)).describe_person(
            role=input_.role, team_size=input_.team_size
        )
        await self._runs.save(run)
        return run


class ChooseGoalsUseCase(_OnboardingUseCase):
    """Screen `06` — up to three, and the fourth is refused here as well as
    disabled there. **A limit kept only in the client is a limit a request
    body does not have.**"""

    async def execute(self, input_: ChooseGoalsInput) -> OnboardingRun:
        run = (await self._require_run(input_.workspace_id, input_.person_id)).choose_goals(
            input_.goals
        )
        await self._runs.save(run)
        return run


class FinishOnboardingUseCase(_OnboardingUseCase):
    async def execute(self, input_: FinishOnboardingInput) -> OnboardingRun:
        run = (await self._require_run(input_.workspace_id, input_.person_id)).finish()
        await self._runs.save(run)
        return run


class SkipOnboardingUseCase(_OnboardingUseCase):
    """They chose to leave. ⛔ **Not a failure, and not a finish.**

    *"The dialog says what gets worse in product terms and lets them go. No
    second ask, no guilt copy."* **This records the leaving so the banner can
    do the remaining work quietly** — and so the product never asks again in
    the modal it already accepted an answer to.
    """

    async def execute(self, input_: FinishOnboardingInput) -> OnboardingRun:
        run = (await self._require_run(input_.workspace_id, input_.person_id)).skip()
        await self._runs.save(run)
        return run


def inferred[T](value: T) -> Answer[T]:
    """A convenience for callers holding an enrichment result.

    ⚡ **Generic, so `inferred("EU")` is an `Answer[str]`** rather than an
    `Answer[object]` that would not fit the field it was built for.

    ⚠️ **Named rather than defaulted.** `Answer` has no default provenance on
    purpose; this makes the common case short **without making it silent** —
    the word `inferred` is at the call site where a reviewer will see it.
    """
    return Answer(value=value, provenance=Provenance.INFERRED)
