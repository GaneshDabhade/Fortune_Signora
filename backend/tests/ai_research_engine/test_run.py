"""The whole loop: somebody asks, a worker runs it, the brief is readable.

The one test in the repository that covers **request → event → handler →
artifact → read**, and it exists because M12.4 is the first capability where
those are one story rather than five components.

The model adapter is scripted, deliberately, for the reason `test_pipeline.py`
gives: `make eval-research` is the only command that calls a model, a local
runtime is never a production dependency (ADR-0028), and a gate needing a GPU
is a gate people learn to skip. Everything else is real — the real retrieval,
the real derivations, the real orchestrator, the real repositories, the real
outbox, the real transition rules.
"""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from modules.ai_platform.public import AIProviderRegistry, Infer, InferencePolicy
from modules.ai_research_engine.application.queries import ResearchArtifactMissing
from modules.ai_research_engine.application.request import (
    NoOpportunityToResearch,
    RequestResearchInput,
)
from modules.ai_research_engine.application.run import RequestNotFound
from modules.ai_research_engine.domain.request import (
    ResearchRequest,
    ResearchRequestState,
    ResearchStatus,
    opening_state,
)
from modules.ai_research_engine.infrastructure.composition import (
    build_begin_research_run,
    build_finish_research_run,
    build_request_research,
    build_research_queries,
)
from modules.ai_research_engine.infrastructure.request_repository import (
    SqlResearchRequestRepository,
)
from signora_platform.db import tenant_scoped_session
from signora_platform.event_bus import PostgresOutboxEventPublisher
from tests.ai_research_engine.test_pipeline import (
    MODEL,
    _ScriptedModel,
    _released_registry,
)
from tests.opportunity_engine.test_opportunity_pipeline import _tracked
from tests.pipeline import opportunities

pytestmark = pytest.mark.integration


def _infer(
    session_factory: async_sessionmaker[AsyncSession], *, synthesis_released: bool = True
) -> Infer:
    from modules.ai_platform.infrastructure.repository import SqlInferenceRecorder

    providers = AIProviderRegistry()
    providers.register(_ScriptedModel())
    return Infer(
        providers=providers,
        prompts=_released_registry(synthesis_released=synthesis_released),
        recorder=SqlInferenceRecorder(session_factory),
        policy=InferencePolicy(),
    )


async def _asked(
    session_factory: async_sessionmaker[AsyncSession],
    admin_session_factory: async_sessionmaker[AsyncSession],
    name: str = "northwind",
) -> tuple[UUID, UUID, UUID, ResearchRequest]:
    """A qualified account with research asked for. Returns the ids."""
    workspace_id, user_id, entity_id, _ = await _tracked(
        session_factory, admin_session_factory, name
    )
    async with tenant_scoped_session(
        session_factory, workspace_id=workspace_id, user_id=user_id
    ) as session:
        result = await build_request_research(
            session,
            opportunities=opportunities(session, workspace_id),
            publisher=PostgresOutboxEventPublisher(),
        ).execute(
            RequestResearchInput(
                workspace_id=workspace_id, entity_id=entity_id, requested_by=user_id
            ),
            correlation_id=uuid4(),
        )
    return workspace_id, user_id, entity_id, result.request


async def _run(
    session_factory: async_sessionmaker[AsyncSession],
    workspace_id: UUID,
    user_id: UUID,
    request_id: UUID,
    *,
    synthesis_released: bool = True,
) -> ResearchRequestState:
    """What the worker does, in the two transactions the handler uses."""
    async with tenant_scoped_session(
        session_factory, workspace_id=workspace_id, user_id=user_id
    ) as session:
        request, running = await build_begin_research_run(session).execute(
            workspace_id, request_id
        )

    async with tenant_scoped_session(
        session_factory, workspace_id=workspace_id, user_id=user_id
    ) as session:
        return await build_finish_research_run(
            session,
            infer=_infer(session_factory, synthesis_released=synthesis_released),
            model=MODEL,
            opportunities=opportunities(session, workspace_id),
            publisher=PostgresOutboxEventPublisher(),
        ).execute(request, running, correlation_id=uuid4())


class TestTheLoopClosesEndToEnd:
    async def test_an_ask_becomes_a_readable_brief(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        workspace_id, user_id, entity_id, request = await _asked(
            session_factory, admin_session_factory
        )

        settled = await _run(session_factory, workspace_id, user_id, request.id)
        assert settled.status is ResearchStatus.COMPLETED

        async with tenant_scoped_session(
            session_factory, workspace_id=workspace_id, user_id=user_id
        ) as session:
            found = await build_research_queries(session).for_account(workspace_id, entity_id)

        assert found is not None
        assert found.artifact is not None
        assert found.artifact.synthesis.statements
        assert found.artifact.findings

    async def test_every_statement_cites_a_finding_on_the_same_response(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        """**Following a claim to its evidence is reading the payload you
        already have.** A statement citing something absent would be a promise
        the surface visibly could not keep — the exact defect R10-04 named."""
        workspace_id, user_id, entity_id, request = await _asked(
            session_factory, admin_session_factory
        )
        await _run(session_factory, workspace_id, user_id, request.id)

        async with tenant_scoped_session(
            session_factory, workspace_id=workspace_id, user_id=user_id
        ) as session:
            found = await build_research_queries(session).for_account(workspace_id, entity_id)

        assert found is not None and found.artifact is not None
        addressable = {finding.finding.ref.token for finding in found.artifact.findings}
        for statement in found.artifact.synthesis.statements:
            assert statement.evidence
            assert set(statement.evidence) <= addressable

    async def test_every_finding_carries_the_catalogs_question(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        """A client mapping `corroboration` to a sentence of its own would be a
        second copy of a reviewed vocabulary."""
        workspace_id, user_id, entity_id, request = await _asked(
            session_factory, admin_session_factory
        )
        await _run(session_factory, workspace_id, user_id, request.id)

        async with tenant_scoped_session(
            session_factory, workspace_id=workspace_id, user_id=user_id
        ) as session:
            found = await build_research_queries(session).for_account(workspace_id, entity_id)

        assert found is not None and found.artifact is not None
        for finding in found.artifact.findings:
            assert finding.question.endswith("?")
            assert finding.finding.derivation not in finding.question

    async def test_every_finding_cites_pipeline_rows_the_drawer_resolves(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        """The chain runs statement → finding → business event → providers, and
        this is the joint that makes the last two steps reachable."""
        workspace_id, user_id, entity_id, request = await _asked(
            session_factory, admin_session_factory
        )
        await _run(session_factory, workspace_id, user_id, request.id)

        async with tenant_scoped_session(
            session_factory, workspace_id=workspace_id, user_id=user_id
        ) as session:
            found = await build_research_queries(session).for_account(workspace_id, entity_id)

        assert found is not None and found.artifact is not None
        kinds = {
            ref.kind for finding in found.artifact.findings for ref in finding.finding.cited
        }
        assert kinds <= {"business_event", "dissenting_signal"}
        assert kinds


class TestAFailedRunSettlesRatherThanVanishing:
    async def test_the_reason_is_recorded_verbatim(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        """**Recorded, not re-raised.** The failures this stage produces — an
        unreleased prompt, a refused schema — are permanent within a redelivery
        window, and retrying them would spend the budget three times to record
        the same reason."""
        workspace_id, user_id, entity_id, request = await _asked(
            session_factory, admin_session_factory
        )

        settled = await _run(
            session_factory, workspace_id, user_id, request.id, synthesis_released=False
        )

        assert settled.status is ResearchStatus.FAILED
        assert settled.detail and "research_synthesis" in settled.detail

    async def test_a_failed_run_stores_no_artifact(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        workspace_id, user_id, entity_id, request = await _asked(
            session_factory, admin_session_factory
        )
        await _run(session_factory, workspace_id, user_id, request.id, synthesis_released=False)

        async with tenant_scoped_session(
            session_factory, workspace_id=workspace_id, user_id=user_id
        ) as session:
            found = await build_research_queries(session).for_account(workspace_id, entity_id)

        assert found is not None
        assert found.artifact is None

    async def test_the_account_can_be_asked_again(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        """A settled request never moves again — **a retry is a second
        request**, which keeps the first one's reason readable."""
        workspace_id, user_id, entity_id, request = await _asked(
            session_factory, admin_session_factory
        )
        await _run(session_factory, workspace_id, user_id, request.id, synthesis_released=False)

        async with tenant_scoped_session(
            session_factory, workspace_id=workspace_id, user_id=user_id
        ) as session:
            again = await build_request_research(
                session,
                opportunities=opportunities(session, workspace_id),
                publisher=PostgresOutboxEventPublisher(),
            ).execute(
                RequestResearchInput(
                    workspace_id=workspace_id, entity_id=entity_id, requested_by=user_id
                ),
                correlation_id=uuid4(),
            )

        assert again.already_running is False
        assert again.request.id != request.id


class TestRunningIsVisibleWhileItRuns:
    async def test_beginning_commits_on_its_own(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        """**The reason there are two methods rather than one.** A status
        written inside the transaction that runs the model becomes visible only
        once the model is done, which is when nobody needs it."""
        workspace_id, user_id, entity_id, request = await _asked(
            session_factory, admin_session_factory
        )

        async with tenant_scoped_session(
            session_factory, workspace_id=workspace_id, user_id=user_id
        ) as session:
            await build_begin_research_run(session).execute(workspace_id, request.id)

        async with tenant_scoped_session(
            session_factory, workspace_id=workspace_id, user_id=user_id
        ) as session:
            found = await build_research_queries(session).for_account(workspace_id, entity_id)

        assert found is not None
        assert found.state.status is ResearchStatus.RUNNING


class TestAskingAboutSomethingUnqualified:
    async def test_an_account_with_no_opportunity_is_refused(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        workspace_id, user_id, _, _ = await _tracked(
            session_factory, admin_session_factory, "northwind"
        )

        async with tenant_scoped_session(
            session_factory, workspace_id=workspace_id, user_id=user_id
        ) as session:
            with pytest.raises(NoOpportunityToResearch):
                await build_request_research(
                    session,
                    opportunities=opportunities(session, workspace_id),
                    publisher=PostgresOutboxEventPublisher(),
                ).execute(
                    RequestResearchInput(
                        workspace_id=workspace_id, entity_id=uuid4(), requested_by=user_id
                    ),
                    correlation_id=uuid4(),
                )


class TestARequestFromAnotherWorkspaceIsNotVisible:
    async def test_running_one_is_refused(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        first_ws, first_user, _, request = await _asked(
            session_factory, admin_session_factory, "northwind"
        )
        second_ws, second_user, _, _ = await _asked(
            session_factory, admin_session_factory, "contoso"
        )

        async with tenant_scoped_session(
            session_factory, workspace_id=second_ws, user_id=second_user
        ) as session:
            with pytest.raises(RequestNotFound):
                await build_begin_research_run(session).execute(second_ws, request.id)


class TestACompletedRequestAlwaysHasSomethingToRead:
    async def test_a_missing_artifact_raises_rather_than_reading_as_absence(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        """A completed run with nothing to read is a **storage fault**.
        Rendering it as *"no research yet"* would hide the loss of an AI
        artifact — the one category of row that cannot be recomputed."""
        workspace_id, user_id, entity_id, request = await _asked(
            session_factory, admin_session_factory
        )
        await _run(session_factory, workspace_id, user_id, request.id)

        async with admin_session_factory() as session:
            await session.execute(text("DELETE FROM research_synthesis"))
            await session.commit()

        async with tenant_scoped_session(
            session_factory, workspace_id=workspace_id, user_id=user_id
        ) as session:
            with pytest.raises(ResearchArtifactMissing):
                await build_research_queries(session).for_account(workspace_id, entity_id)


class TestTwoClicksResolveToOneRun:
    async def test_the_ordinary_repeat_is_answered_not_refused(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        workspace_id, user_id, entity_id, request = await _asked(
            session_factory, admin_session_factory
        )

        async with tenant_scoped_session(
            session_factory, workspace_id=workspace_id, user_id=user_id
        ) as session:
            second = await build_request_research(
                session,
                opportunities=opportunities(session, workspace_id),
                publisher=PostgresOutboxEventPublisher(),
            ).execute(
                RequestResearchInput(
                    workspace_id=workspace_id, entity_id=entity_id, requested_by=user_id
                ),
                correlation_id=uuid4(),
            )

        assert second.already_running is True
        assert second.request.id == request.id

    async def test_a_simultaneous_second_ask_loses_on_the_constraint(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        """**What holds when two clicks race** — asserted by going around the
        application check, which is the only way to reproduce a race
        deterministically. `generation` is `Opportunity`'s device, unchanged."""
        from sqlalchemy.exc import IntegrityError

        workspace_id, user_id, entity_id, request = await _asked(
            session_factory, admin_session_factory
        )

        with pytest.raises(IntegrityError):
            async with tenant_scoped_session(
                session_factory, workspace_id=workspace_id, user_id=user_id
            ) as session:
                await session.execute(
                    text(
                        "INSERT INTO research_request "
                        "(id, workspace_id, entity_id, opportunity_id, requested_by, "
                        " requested_at, generation, created_by, updated_by) "
                        "VALUES (gen_random_uuid(), :ws, :e, :o, :u, now(), 0, :u, :u)"
                    ),
                    {
                        "ws": str(workspace_id),
                        "e": str(entity_id),
                        "o": str(request.opportunity_id),
                        "u": str(user_id),
                    },
                )

    async def test_a_later_ask_takes_the_next_generation(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        """**The reason a partial index over status could not do this job.**
        History is append-only, so a constraint that refused a second
        `requested` row would refuse every legitimate later ask forever."""
        workspace_id, user_id, entity_id, request = await _asked(
            session_factory, admin_session_factory
        )
        await _run(session_factory, workspace_id, user_id, request.id)

        async with tenant_scoped_session(
            session_factory, workspace_id=workspace_id, user_id=user_id
        ) as session:
            again = await build_request_research(
                session,
                opportunities=opportunities(session, workspace_id),
                publisher=PostgresOutboxEventPublisher(),
            ).execute(
                RequestResearchInput(
                    workspace_id=workspace_id, entity_id=entity_id, requested_by=user_id
                ),
                correlation_id=uuid4(),
            )

        assert again.already_running is False
        assert again.request.generation == request.generation + 1


class TestTheRepositoryRefusesHistoryBelongingToNothing:
    async def test_a_state_for_an_unknown_request_is_refused(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        workspace_id, user_id, _, _ = await _tracked(
            session_factory, admin_session_factory, "northwind"
        )
        orphan = ResearchRequest(
            id=uuid4(),
            workspace_id=workspace_id,
            entity_id=uuid4(),
            opportunity_id=uuid4(),
            requested_by=user_id,
            requested_at=datetime.now(UTC),
        )

        async with tenant_scoped_session(
            session_factory, workspace_id=workspace_id, user_id=user_id
        ) as session:
            with pytest.raises(LookupError):
                await SqlResearchRequestRepository(session).record(opening_state(orphan))
