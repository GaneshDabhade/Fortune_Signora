"""*"What has Signora been doing?"* — the workspace's research, as a list.

**The module's other three reads are all about one account**, and this one is
not: Home's two agent cards ask about the agent rather than about a record
(`docs/design-snapshot/screens/Fortune Signora Home.dc.html`, `card.agentqueue`
and `card.agentruns`, both depending on `agents.runs`). A surface that had to
ask account by account could not ask it at all.

**Two properties are worth asserting and neither is obvious:**

| | |
|---|---|
| **The CURRENT state, per request** | history is append-only, so every run
still has its `requested` row behind it — a list reading the first row would
show every completed run as still queued |
| **A source counted once** | a piece of evidence two findings both cited is
one source, and counting the citations would report a run as having read twice
what it read |
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from modules.ai_platform.public import AIVendor, EvidenceRef, EvidenceValue, GroundedStatement
from modules.ai_research_engine.application.queries import ResearchQueries
from modules.ai_research_engine.domain.request import (
    ResearchRequest,
    ResearchRequestState,
    ResearchStatus,
    next_state,
    opening_state,
)
from modules.ai_research_engine.domain.research import (
    ResearchFinding,
    ResearchSynthesis,
    ResearchTask,
    research_finding_id,
)
from modules.ai_research_engine.infrastructure.repository import SqlResearchRepository
from modules.ai_research_engine.infrastructure.request_repository import (
    SqlResearchArtifactReader,
    SqlResearchRequestRepository,
)
from signora_platform.db import tenant_scoped_session

pytestmark = pytest.mark.integration

NOW = datetime(2026, 8, 18, 6, 0, tzinfo=UTC)


def _request(workspace_id: UUID, *, minutes_ago: int, asker: UUID) -> ResearchRequest:
    return ResearchRequest(
        id=uuid4(),
        workspace_id=workspace_id,
        entity_id=uuid4(),
        opportunity_id=uuid4(),
        requested_by=asker,
        requested_at=NOW - timedelta(minutes=minutes_ago),
    )


def _finding(
    workspace_id: UUID, task: ResearchTask, *, cited: tuple[EvidenceRef, ...]
) -> ResearchFinding:
    attributes: tuple[tuple[str, EvidenceValue], ...] = (("conclusions", 2),)
    return ResearchFinding(
        id=research_finding_id(
            workspace_id=workspace_id,
            subject=task.subject,
            derivation="corroboration",
            derivation_version=1,
            cited=cited,
        ),
        workspace_id=workspace_id,
        task_id=task.id,
        subject=task.subject,
        derivation="corroboration",
        derivation_version=1,
        attributes=attributes,
        cited=cited,
        created_at=NOW,
    )


def _task(workspace_id: UUID, request: ResearchRequest) -> ResearchTask:
    return ResearchTask(
        id=uuid4(),
        workspace_id=workspace_id,
        correlation_id=uuid4(),
        subject=EvidenceRef(kind="entity", id=request.entity_id),
        opportunity_id=request.opportunity_id,
        requested_at=request.requested_at,
    )


def _synthesis(
    workspace_id: UUID, task: ResearchTask, findings: tuple[ResearchFinding, ...]
) -> ResearchSynthesis:
    return ResearchSynthesis(
        id=uuid4(),
        workspace_id=workspace_id,
        task_id=task.id,
        statements=tuple(
            GroundedStatement(text=f"Statement {n}.", evidence=(finding.ref.token,))
            for n, finding in enumerate(findings)
        ),
        finding_ids=tuple(finding.id for finding in findings),
        prompt_name="research_synthesis",
        prompt_version=1,
        prompt_fingerprint="f" * 64,
        model="llama3.1:8b",
        vendor=AIVendor.OLLAMA,
        evidence_digest="d" * 64,
        inference_id=uuid4(),
        created_at=NOW,
    )


async def _open(
    session_factory: async_sessionmaker[AsyncSession], request: ResearchRequest
) -> ResearchRequestState:
    state = opening_state(request)
    async with tenant_scoped_session(
        session_factory, workspace_id=request.workspace_id, user_id=request.requested_by
    ) as session:
        await SqlResearchRequestRepository(session).open(request, state)
    return state


async def _advance(
    session_factory: async_sessionmaker[AsyncSession],
    request: ResearchRequest,
    state: ResearchRequestState,
    status: ResearchStatus,
    **kwargs: object,
) -> ResearchRequestState:
    moved = next_state(state, status, occurred_at=NOW, **kwargs)  # type: ignore[arg-type]
    async with tenant_scoped_session(
        session_factory, workspace_id=request.workspace_id, user_id=request.requested_by
    ) as session:
        await SqlResearchRequestRepository(session).record(moved)
    return moved


async def _runs(
    session_factory: async_sessionmaker[AsyncSession],
    workspace_id: UUID,
    reader: UUID,
    **kwargs: int,
) -> tuple[object, ...]:
    async with tenant_scoped_session(
        session_factory, workspace_id=workspace_id, user_id=reader
    ) as session:
        queries = ResearchQueries(
            requests=SqlResearchRequestRepository(session),
            artifacts=SqlResearchArtifactReader(session),
        )
        return await queries.recent_runs(workspace_id, **kwargs)


class TestTheListAnswersForTheWorkspaceRatherThanForAnAccount:
    async def test_every_account_asked_about_appears_once_newest_first(
        self, session_factory: async_sessionmaker[AsyncSession]
    ) -> None:
        workspace_id, asker = uuid4(), uuid4()
        older = _request(workspace_id, minutes_ago=90, asker=asker)
        newer = _request(workspace_id, minutes_ago=10, asker=asker)
        for request in (older, newer):
            await _open(session_factory, request)

        runs = await _runs(session_factory, workspace_id, asker)

        assert [run.request.id for run in runs] == [newer.id, older.id], (  # type: ignore[attr-defined]
            "runs are ordered by when somebody ASKED. Ordering by the state "
            "would put a long-finished run above a fresh one every time its "
            "history gained a row."
        )

    async def test_a_workspace_nobody_has_asked_in_answers_with_nothing(
        self, session_factory: async_sessionmaker[AsyncSession]
    ) -> None:
        """**An empty list is an answer.** A workspace that has never used
        research is an ordinary state, and the surface is what says so."""
        assert await _runs(session_factory, uuid4(), uuid4()) == ()

    async def test_another_workspaces_research_is_not_in_this_list(
        self, session_factory: async_sessionmaker[AsyncSession]
    ) -> None:
        """Through `signora_app`, so RLS is the control being asserted and not
        the `where` clause standing in front of it."""
        theirs, ours, asker = uuid4(), uuid4(), uuid4()
        await _open(session_factory, _request(theirs, minutes_ago=5, asker=asker))

        assert await _runs(session_factory, ours, asker) == ()

    async def test_the_limit_is_honoured(
        self, session_factory: async_sessionmaker[AsyncSession]
    ) -> None:
        workspace_id, asker = uuid4(), uuid4()
        for minutes in (30, 20, 10):
            await _open(session_factory, _request(workspace_id, minutes_ago=minutes, asker=asker))

        runs = await _runs(session_factory, workspace_id, asker, limit=2)

        assert len(runs) == 2


class TestEachRunCarriesWhereItGotToAndNotWhereItStarted:
    async def test_a_completed_run_does_not_read_as_still_queued(
        self, session_factory: async_sessionmaker[AsyncSession]
    ) -> None:
        """🔴 **The defect this test exists for.** History is append-only, so a
        completed request still has its `requested` row sitting behind it. A
        list reading any row but the highest `sequence` would show every
        finished run as waiting to start."""
        workspace_id, asker = uuid4(), uuid4()
        request = _request(workspace_id, minutes_ago=20, asker=asker)
        state = await _open(session_factory, request)
        state = await _advance(session_factory, request, state, ResearchStatus.RUNNING)
        await _advance(
            session_factory, request, state, ResearchStatus.COMPLETED, task_id=uuid4()
        )

        (run,) = await _runs(session_factory, workspace_id, asker)

        assert run.state.status is ResearchStatus.COMPLETED  # type: ignore[attr-defined]

    async def test_a_failure_carries_the_reason_it_failed(
        self, session_factory: async_sessionmaker[AsyncSession]
    ) -> None:
        """📁 *"Scheduled and triggered runs, failures first"* — a failure a
        surface cannot explain is one nobody can act on."""
        workspace_id, asker = uuid4(), uuid4()
        request = _request(workspace_id, minutes_ago=20, asker=asker)
        state = await _open(session_factory, request)
        state = await _advance(session_factory, request, state, ResearchStatus.RUNNING)
        await _advance(
            session_factory,
            request,
            state,
            ResearchStatus.FAILED,
            detail="The provider returned no evidence.",
        )

        (run,) = await _runs(session_factory, workspace_id, asker)

        assert run.state.detail == "The provider returned no evidence."  # type: ignore[attr-defined]
        assert run.sources is None, (  # type: ignore[attr-defined]
            "a failed run produced no artifact, so there is nothing it read. "
            "Reporting 0 would state that it read nothing, which is a "
            "different claim."
        )


class TestASourceIsCountedOnceHoweverManyFindingsCiteIt:
    async def test_two_findings_citing_one_event_between_them_read_three_sources(
        self, session_factory: async_sessionmaker[AsyncSession]
    ) -> None:
        """⚡ **Four citations, three sources.** A run that compared the same
        business event under two derivations read it once — counting the
        citations would report a run as having read twice what it read."""
        workspace_id, asker = uuid4(), uuid4()
        request = _request(workspace_id, minutes_ago=20, asker=asker)
        state = await _open(session_factory, request)
        state = await _advance(session_factory, request, state, ResearchStatus.RUNNING)

        task = _task(workspace_id, request)
        shared = EvidenceRef(kind="business_event", id=uuid4())
        findings = tuple(
            _finding(
                workspace_id,
                task,
                cited=(shared, EvidenceRef(kind="business_event", id=uuid4())),
            )
            for _ in range(2)
        )
        async with tenant_scoped_session(
            session_factory, workspace_id=workspace_id, user_id=asker
        ) as session:
            await SqlResearchRepository(session).save(
                task, findings, _synthesis(workspace_id, task, findings)
            )
        await _advance(
            session_factory, request, state, ResearchStatus.COMPLETED, task_id=task.id
        )

        (run,) = await _runs(session_factory, workspace_id, asker)

        assert run.sources == 3  # type: ignore[attr-defined]

    async def test_each_run_is_counted_against_its_own_findings(
        self, session_factory: async_sessionmaker[AsyncSession]
    ) -> None:
        """🔴 **The failure a single-run test cannot see.**

        ⛔ **`unnest` in `FROM` reading another `FROM` item's column is a
        LATERAL** — every row unnested against its own citations. **Written as
        an ordinary cross join it would unnest every finding against every
        other finding's citations**, and both runs below would report five
        sources. A test with one run in the workspace answers the same either
        way.
        """
        workspace_id, asker = uuid4(), uuid4()
        counted = []
        for minutes, citations in ((40, 2), (20, 3)):
            request = _request(workspace_id, minutes_ago=minutes, asker=asker)
            state = await _open(session_factory, request)
            state = await _advance(session_factory, request, state, ResearchStatus.RUNNING)
            task = _task(workspace_id, request)
            findings = (
                _finding(
                    workspace_id,
                    task,
                    cited=tuple(
                        EvidenceRef(kind="business_event", id=uuid4())
                        for _ in range(citations)
                    ),
                ),
            )
            async with tenant_scoped_session(
                session_factory, workspace_id=workspace_id, user_id=asker
            ) as session:
                await SqlResearchRepository(session).save(
                    task, findings, _synthesis(workspace_id, task, findings)
                )
            await _advance(
                session_factory, request, state, ResearchStatus.COMPLETED, task_id=task.id
            )
            counted.append(citations)

        runs = await _runs(session_factory, workspace_id, asker)

        assert [run.sources for run in runs] == [3, 2], (  # type: ignore[attr-defined]
            "each run read its own evidence. Five apiece would mean the "
            "citations were unnested across findings rather than within one."
        )

    async def test_a_run_that_found_nothing_worth_citing_read_zero_rather_than_nothing(
        self, session_factory: async_sessionmaker[AsyncSession]
    ) -> None:
        """⚠️ **`0` and `None` are different facts.** A completed run with no
        findings read nothing; a running one has read nothing *yet*, and a
        surface that collapsed them would tell somebody a run in progress had
        already come back empty."""
        workspace_id, asker = uuid4(), uuid4()
        request = _request(workspace_id, minutes_ago=20, asker=asker)
        state = await _open(session_factory, request)
        state = await _advance(session_factory, request, state, ResearchStatus.RUNNING)
        await _advance(
            session_factory, request, state, ResearchStatus.COMPLETED, task_id=uuid4()
        )

        (run,) = await _runs(session_factory, workspace_id, asker)

        assert run.sources == 0  # type: ignore[attr-defined]

    async def test_a_run_still_going_has_read_nothing_anybody_may_cite(
        self, session_factory: async_sessionmaker[AsyncSession]
    ) -> None:
        workspace_id, asker = uuid4(), uuid4()
        request = _request(workspace_id, minutes_ago=20, asker=asker)
        state = await _open(session_factory, request)
        await _advance(session_factory, request, state, ResearchStatus.RUNNING)

        (run,) = await _runs(session_factory, workspace_id, asker)

        assert run.sources is None  # type: ignore[attr-defined]
