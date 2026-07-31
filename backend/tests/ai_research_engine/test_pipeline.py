"""M10's demonstration: a provider payload becomes a research artifact.

Runs the **real** pipeline, the real retrieval, the real derivations, the real
orchestrator, the real repository and the real outbox publisher. The model
adapter is scripted, deliberately and for the same reason M8's and M9's are:
`make eval-research` is the only command that calls a model, a local runtime is
never a production dependency (ADR-0028), and a deployment gate needing a GPU is
a gate people learn to skip.

**What is proven here is the half that is deterministic** — and for M10 that is
every citable thing. The findings are computed from real pipeline rows by pure
functions; the model chooses which comparisons to run and writes the brief, and
neither of those produces a fact anyone may cite.
"""

from __future__ import annotations

import json
from datetime import date
from uuid import UUID, uuid4

import pytest
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from modules.ai_platform.domain.rendering import PROMPT_RENDERING_PROTOCOL_VERSION
from modules.ai_platform.infrastructure.prompt_loader import load_prompt_registry
from modules.ai_platform.infrastructure.repository import SqlInferenceRecorder
from modules.ai_platform.domain.evidence import EvidenceError, EvidenceRef
from modules.ai_platform.public import (
    AIProviderDescriptor,
    AIProviderRegistry,
    AIVendor,
    Evaluation,
    Infer,
    InferencePolicy,
    InferenceRequest,
    InferenceResult,
    InferenceUsage,
    PromptNotReleasableError,
    PromptRegistry,
    PromptVersion,
)
from modules.ai_research_engine.infrastructure.composition import PROMPT_DIR, build_research
from modules.ai_research_engine.infrastructure.models import (
    ResearchFindingModel,
    ResearchSynthesisModel,
    ResearchTaskModel,
)
from modules.ai_research_engine.infrastructure.repository import attributes_of, cited_of
from signora_platform.db import tenant_scoped_session
from signora_platform.event_bus import PostgresOutboxEventPublisher
from tests.opportunity_engine.test_opportunity_pipeline import _tracked
from tests.pipeline import _published, opportunities

pytestmark = pytest.mark.integration

MODEL = "llama3.1:8b"


def _plan_json(refs: list[str]) -> str:
    return json.dumps(
        {
            "steps": [
                {
                    "derivation": "corroboration",
                    "reason": {
                        "text": "These conclusions rest on different providers.",
                        "evidence": refs,
                    },
                },
                {
                    "derivation": "recency",
                    "reason": {"text": "The evidence spans a period.", "evidence": refs},
                },
            ]
        }
    )


def _brief_json(finding_refs: list[str]) -> str:
    return json.dumps(
        {
            "brief": [
                {
                    "text": "The account's conclusions rest on a single provider.",
                    "evidence": [finding_refs[0]],
                },
                {
                    "text": "The supporting events fall within one period.",
                    "evidence": [finding_refs[1]],
                },
            ]
        }
    )


def _parses(token: str) -> bool:
    try:
        EvidenceRef.parse(token)
    except EvidenceError:
        return False
    return True


class _ScriptedModel:
    """Answers each call with the refs it was actually shown.

    **Built from the prompt rather than from a fixture**, so the script cannot
    invent a citation and cannot keep passing against evidence the pipeline no
    longer emits. Which call it is answering is decided by what it sees: a
    prompt listing findings is the synthesis call, one listing facts is the
    planning call — the fake is never told the order.
    """

    def describe(self) -> AIProviderDescriptor:
        return AIProviderDescriptor(
            models=frozenset({MODEL}), supports_structured_output=True, vendor=AIVendor.OLLAMA
        )

    async def complete(self, request: InferenceRequest) -> InferenceResult:
        # **The fake succeeds the way protocol 2 intends a model to succeed:
        # by copying.** It takes the first token of each line and keeps the ones
        # that parse, which is exactly the protocol's promise — what is shown is
        # what the parser accepts. Under protocol 1 this read brackets off the
        # line, and a first attempt here matched prose in the prompt's own
        # derivation catalog: a delimiter is a weaker signal than parseability.
        refs = sorted(
            {
                token
                for line in request.prompt.splitlines()
                for token in [line.split(" ")[0]]
                if _parses(token)
            }
        )
        findings = [ref for ref in refs if ref.startswith("research_finding:")]
        content = _brief_json(findings) if findings else _plan_json(refs)
        return InferenceResult(
            content=content,
            model=request.model,
            vendor=AIVendor.OLLAMA,
            usage=InferenceUsage(input_tokens=10, output_tokens=5, latency_ms=42),
        )


def _version(name: str) -> PromptVersion:
    return PromptVersion(
        name=name,
        version=1,
        owner="ai-research@signora",
        text=(PROMPT_DIR / f"{name}@1.md").read_text(),
        evaluations=(
            Evaluation(
                model=MODEL,
                dataset=name,
                dataset_version=1,
                rubric_version=1,
                evaluated_on=date(2026, 7, 31),
                sample_size=2,
                grounding_failures=0,
                schema_failures=0,
                coverage=1.0,
                rendering_protocol_version=PROMPT_RENDERING_PROTOCOL_VERSION,
            ),
        ),
    )


def _released_registry() -> PromptRegistry:
    """Both of M10's prompts, **each with a passing evaluation**.

    A double for the registry, not for the release *rule*: the rule is the real
    one and is satisfied here by a measurement of the shape it demands. The
    shipped manifest is untouched, and `test_planning_release.py` asserts what
    it actually holds.
    """
    return PromptRegistry(
        versions=(_version("research_planning"), _version("research_synthesis"))
    )


async def _run(
    session_factory: async_sessionmaker[AsyncSession],
    admin_session_factory: async_sessionmaker[AsyncSession],
) -> tuple[UUID, UUID, UUID]:
    workspace_id, user_id, entity_id, _ = await _tracked(
        session_factory, admin_session_factory, "northwind"
    )
    providers = AIProviderRegistry()
    providers.register(_ScriptedModel())
    correlation_id = uuid4()

    async with tenant_scoped_session(
        session_factory, workspace_id=workspace_id, user_id=user_id
    ) as session:
        tracked = await opportunities(session, workspace_id).tracked(workspace_id, entity_id)
        assert tracked is not None
        research = build_research(
            session,
            infer=Infer(
                providers=providers,
                prompts=_released_registry(),
                recorder=SqlInferenceRecorder(session_factory),
                policy=InferencePolicy(),
            ),
            model=MODEL,
            opportunities=opportunities(session, workspace_id),
            publisher=PostgresOutboxEventPublisher(),
        )
        task = await research.run(
            workspace_id=workspace_id,
            entity_id=entity_id,
            opportunity_id=tracked.opportunity.id,
            correlation_id=correlation_id,
        )

    assert task is not None
    return workspace_id, user_id, task.id


class TestTheResearchLifecycleCompletes:
    async def test_a_run_stores_a_task_its_findings_and_its_synthesis(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        workspace_id, user_id, task_id = await _run(session_factory, admin_session_factory)

        async with tenant_scoped_session(
            session_factory, workspace_id=workspace_id, user_id=user_id
        ) as session:
            tasks = (await session.execute(select(ResearchTaskModel))).scalars().all()
            findings = (await session.execute(select(ResearchFindingModel))).scalars().all()
            syntheses = (await session.execute(select(ResearchSynthesisModel))).scalars().all()

        assert [t.id for t in tasks] == [task_id]
        assert {f.derivation for f in findings} == {"corroboration", "recency"}
        assert len(syntheses) == 1
        assert syntheses[0].task_id == task_id

    async def test_it_announces_completed_work(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        """The event means the run finished — findings derived, brief written,
        all of it stored. Not that planning completed."""
        _, _, task_id = await _run(session_factory, admin_session_factory)

        published = await _published(admin_session_factory, "ai_research.completed")

        assert len(published) == 1
        announced = published[0]
        assert announced.producer_module == "ai_research_engine"
        assert announced.payload["research_id"] == str(task_id)
        assert announced.payload["finding_count"] == 2
        assert announced.payload["statement_count"] == 2
        # Identity and counts, never the prose: nothing in the envelope says
        # what the brief actually claimed.
        assert "brief" not in announced.payload
        assert "statements" not in announced.payload

    async def test_every_finding_round_trips_with_its_types_intact(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        """**A stored finding nobody can reconstruct is one nobody can
        recompute**, and recomputation is the only thing that makes a
        derivation checkable."""
        workspace_id, user_id, _ = await _run(session_factory, admin_session_factory)

        async with tenant_scoped_session(
            session_factory, workspace_id=workspace_id, user_id=user_id
        ) as session:
            rows = (await session.execute(select(ResearchFindingModel))).scalars().all()

        for row in rows:
            attributes = dict(attributes_of(row.attributes))
            assert cited_of(row.cited)
            if row.derivation == "corroboration":
                assert isinstance(attributes["conclusions"], int)
                assert isinstance(attributes["distinct_providers"], int)
            if row.derivation == "recency":
                assert not isinstance(attributes["span_days"], str)


class TestNothingIsStoredUntilEverythingSucceeded:
    async def test_an_unreleased_synthesis_prompt_stores_nothing(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        """**The release rule on the request path.** `research_synthesis@1` is
        authored and unreleased for this fake's model, so `Infer.execute`
        refuses it — and because storage happens at the end, the refusal leaves
        no task row and no findings rather than a run that found things and
        said nothing."""
        workspace_id, user_id, entity_id, _ = await _tracked(
            session_factory, admin_session_factory, "northwind"
        )
        providers = AIProviderRegistry()
        providers.register(_ScriptedModel())

        async with tenant_scoped_session(
            session_factory, workspace_id=workspace_id, user_id=user_id
        ) as session:
            tracked = await opportunities(session, workspace_id).tracked(workspace_id, entity_id)
            assert tracked is not None
            research = build_research(
                session,
                infer=Infer(
                    providers=providers,
                    prompts=load_prompt_registry(PROMPT_DIR),
                    recorder=SqlInferenceRecorder(session_factory),
                    policy=InferencePolicy(),
                ),
                model=MODEL,
                opportunities=opportunities(session, workspace_id),
                publisher=PostgresOutboxEventPublisher(),
            )
            with pytest.raises(PromptNotReleasableError):
                await research.run(
                    workspace_id=workspace_id,
                    entity_id=entity_id,
                    opportunity_id=tracked.opportunity.id,
                    correlation_id=uuid4(),
                )

        async with tenant_scoped_session(
            session_factory, workspace_id=workspace_id, user_id=user_id
        ) as session:
            stored = (await session.execute(text("SELECT count(*) FROM research_task"))).scalar()

        assert stored == 0
