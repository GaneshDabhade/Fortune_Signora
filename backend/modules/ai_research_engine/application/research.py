"""One research run, end to end. **Orchestration, and nothing else.**

    retrieve → plan → execute → synthesise → store → publish

Six steps, no branches, no rules. Every decision was made elsewhere: what is
worth comparing is the planner's, what a comparison computes is a derivation's,
whether the output is grounded is the AI Platform's, and what a finding *is* is
its own identity. If business logic ever appears in this file it belongs to one
of those owners and has been written in the wrong place.

**Two inferences, and exactly two.** Planning and synthesis — the module's whole
model budget. That is the shape M9's split anticipated: research is the agentic,
multi-call half, deliberately distinct from reasoning's single structured call.
A third call here would be a refinement pass nobody measured.

---

**The synthesis is grounded against findings, not facts.** The evidence set
handed to the narrator holds one entry per finding, each addressed by the id the
derivation minted and summarised by the catalog's reviewed question. So a
narrator cannot reach past a finding to reinterpret the business event beneath
it — the business event is not in the set it was given. That is what makes
*"explain, do not investigate"* structural rather than an instruction.

**Nothing is stored until everything succeeded.** A failed synthesis leaves no
task row and no findings: a run that stored its findings and then failed would
look, to every later reader, like a completed run that found things and said
nothing. Storing at the end costs a recomputation on failure — microseconds —
and buys a table where every row describes a run that finished.

**The event is published in the same transaction as the write**, through the
outbox. It announces completed work, never partial execution.
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from modules.ai_platform.public import (
    EvidenceRef,
    EvidenceSet,
    Infer,
    InferenceInput,
    InferenceRecord,
)
from modules.ai_research_engine.application.orchestrate import execute
from modules.ai_research_engine.application.ports import ResearchRepository
from modules.ai_research_engine.application.plan import plan_research
from modules.ai_research_engine.domain.derivations import as_evidence
from modules.ai_research_engine.domain.events import ResearchCompleted
from modules.ai_research_engine.domain.research import (
    PAYLOAD_VERSION,
    ResearchError,
    ResearchFinding,
    ResearchSynthesis,
    ResearchTask,
)
from modules.ai_research_engine.domain.retrieval import ResearchFactSource
from modules.ai_research_engine.domain.synthesis import SynthesisedResearch
from signora_platform.event_bus import EventPublisher

logger = logging.getLogger(__name__)

PRODUCER_MODULE = "ai_research_engine"

SYNTHESIS_PROMPT = "research_synthesis"
#: Version 2 since M9.5 Step D, and the version that first earned a release:
#: `@1` was refused four consecutive times, every failure a citation the model
#: had *edited* rather than copied.
SYNTHESIS_VERSION = 2

#: How a research subject is addressed. An account *is* a Knowledge Graph
#: entity, and naming it in the AI Platform's addressing vocabulary is what
#: lets a finding's subject and its citations be read the same way.
SUBJECT_KIND = "entity"


class Research:
    """Produce one research artifact for one account."""

    def __init__(
        self,
        *,
        facts: ResearchFactSource,
        infer: Infer,
        model: str,
        repository: ResearchRepository,
        publisher: EventPublisher,
        session: AsyncSession,
        clock: Callable[[], datetime] = lambda: datetime.now(UTC),
    ) -> None:
        self._facts = facts
        self._infer = infer
        self._model = model
        self._repository = repository
        self._publisher = publisher
        # The artifact and its event share the caller's session: they are one
        # unit of work, so a rolled-back transaction leaves neither behind.
        self._session = session
        self._clock = clock

    async def run(
        self, *, workspace_id: UUID, entity_id: UUID, opportunity_id: UUID, correlation_id: UUID
    ) -> ResearchTask | None:
        """The run, or `None` when the account has nothing to research.

        `None` rather than an empty artifact: research is invoked on qualified
        opportunities, and an account whose evidence a plan finds nothing worth
        comparing in has no brief to write. Publishing a completed event for it
        would tell the AI Reasoning Engine a research artifact exists.
        """
        facts = await self._facts.facts_for(workspace_id, entity_id)
        if not facts:
            return None

        now = self._clock()
        evidence = EvidenceSet(workspace_id=workspace_id, facts=facts, assembled_at=now)
        plan = await plan_research(
            self._infer, model=self._model, correlation_id=correlation_id, evidence=evidence
        )
        task = ResearchTask(
            id=uuid4(),
            workspace_id=workspace_id,
            correlation_id=correlation_id,
            subject=EvidenceRef(kind=SUBJECT_KIND, id=entity_id),
            opportunity_id=opportunity_id,
            requested_at=now,
        )
        findings = execute(task, plan.output, evidence, now=now)
        if not findings:
            return None

        synthesis, record = await self._synthesise(task, findings, now=now)
        await self._repository.save(task, findings, synthesis)
        await self._publisher.publish(
            # See M9's reason.py: the platform's PublishableEvent Protocol
            # declares settable members, which a frozen domain event cannot
            # satisfy. A finding (F-5), not fixed here.
            [ResearchCompleted(  # type: ignore[list-item]
                event_id=uuid4(),
                workspace_id=workspace_id,
                occurred_at=now,
                research_id=task.id,
                opportunity_id=opportunity_id,
                subject_kind=task.subject.kind,
                subject_id=task.subject.id,
                synthesis_id=synthesis.id,
                prompt_name=synthesis.prompt_name,
                prompt_version=synthesis.prompt_version,
                prompt_fingerprint=synthesis.prompt_fingerprint,
                model=synthesis.model,
                vendor=synthesis.vendor.value,
                evidence_digest=synthesis.evidence_digest,
                finding_count=len(findings),
                statement_count=len(synthesis.statements),
                inference_id=synthesis.inference_id,
                payload_version=PAYLOAD_VERSION,
                causation_id=correlation_id,
            )],
            session=self._session,
            producer_module=PRODUCER_MODULE,
            correlation_id=correlation_id,
        )

        logger.info(
            "research artifact produced",
            extra={
                "workspace_id": str(workspace_id),
                "correlation_id": str(correlation_id),
                "research_id": str(task.id),
                "finding_count": len(findings),
            },
        )
        return task

    async def _synthesise(
        self, task: ResearchTask, findings: tuple[ResearchFinding, ...], *, now: datetime
    ) -> tuple[ResearchSynthesis, InferenceRecord]:
        over = EvidenceSet(
            workspace_id=task.workspace_id,
            facts=tuple(as_evidence(finding) for finding in findings),
            assembled_at=now,
        )
        result = await self._infer.execute(
            InferenceInput(
                prompt_name=SYNTHESIS_PROMPT,
                prompt_version=SYNTHESIS_VERSION,
                model=self._model,
                evidence=over,
                correlation_id=task.correlation_id,
            ),
            SynthesisedResearch,
        )
        record = result.record
        if record.vendor is None or record.served_model is None:
            raise ResearchError(
                f"synthesis for task {task.id} returned without naming what served it. A "
                "materialized AI artifact whose provenance is incomplete cannot be attributed "
                "later, and attribution is the only thing auditable about inferred knowledge."
            )
        return (
            ResearchSynthesis(
                id=uuid4(),
                workspace_id=task.workspace_id,
                task_id=task.id,
                statements=result.output.statements(),
                finding_ids=tuple(finding.id for finding in findings),
                prompt_name=record.prompt_name,
                prompt_version=record.prompt_version,
                prompt_fingerprint=record.prompt_fingerprint,
                model=record.served_model,
                vendor=record.vendor,
                evidence_digest=record.evidence_digest,
                inference_id=record.id,
                created_at=now,
            ),
            record,
        )
