"""Produce one Decision Package. **Orchestration, and nothing else.**

Five steps, no branches, no rules:

    assemble context → infer once → compose → store → publish

**This layer should be easy to read because every decision was made
elsewhere.** Whether the evidence is strong is `SupportBasis`. Why the
reading exists is `BuyingScore.trigger`. What the conclusion does not imply
is the signal catalog. Whether the output is grounded is the AI Platform. If
substantial business logic ever appears in this file, it belongs to one of
those owners and has been written in the wrong place.

**Exactly one inference per package.** Not a loop, not a refinement pass, not
a second call to check the first — the AI Reasoning Engine is the *structured
single-call* half of the M8/M9 split, deliberately distinct from M10's
agentic workload with its different latency, cost and failure profile
(CLAUDE.md §10). A second call here would quietly make this module the thing
the split exists to keep it from becoming.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from modules.ai_platform.public import (
    AIPlatformError,
    Infer,
    InferenceInput,
    InferenceRecord,
)
from modules.ai_reasoning_engine.application.ports import (
    DecisionPackageRepository,
    ReasoningContextSource,
)
from modules.ai_reasoning_engine.domain.context import ReasoningContext
from modules.ai_reasoning_engine.domain.decision import ReasonedOutput
from modules.ai_reasoning_engine.domain.events import ReasoningCompleted
from modules.ai_reasoning_engine.domain.package import PAYLOAD_VERSION, DecisionPackage
from signora_platform.event_bus import EventPublisher
from signora_platform.observability import get_logger

logger = get_logger(__name__)

PRODUCER_MODULE = "ai_reasoning_engine"

#: What a Decision Package is about, in this module's own addressing
#: vocabulary rather than the pipeline's.
SUBJECT_KIND = "account"


class NothingToReasonAboutError(AIPlatformError):
    """No context could be assembled, so no conclusion was attempted."""


@dataclass(frozen=True, slots=True)
class ReasonInput:
    workspace_id: UUID
    entity_id: UUID
    model: str
    correlation_id: UUID


class Reason:
    """The only way to produce a Decision Package."""

    def __init__(
        self,
        *,
        infer: Infer,
        context: ReasoningContextSource,
        repository: DecisionPackageRepository,
        publisher: EventPublisher,
        session: AsyncSession,
        prompt_name: str,
        prompt_version: int,
        clock: Callable[[], datetime] = lambda: datetime.now(UTC),
    ) -> None:
        self._infer = infer
        self._context = context
        self._repository = repository
        self._publisher = publisher
        self._session = session
        self._prompt_name = prompt_name
        self._prompt_version = prompt_version
        self._clock = clock

    async def execute(self, request: ReasonInput) -> DecisionPackage:
        context = await self._context.context_for(request.workspace_id, request.entity_id)
        if context is None:
            raise NothingToReasonAboutError(
                f"no reasoning context could be assembled for {request.entity_id}. Nothing was "
                "sent to a model: a conclusion with no evidence is a conclusion about nothing."
            )

        # `execute`, never `measure`. This is a request path, so the release
        # rule binds: a prompt that has not passed evaluation for this model
        # does not reach it (ADR-0028).
        result = await self._infer.execute(
            InferenceInput(
                prompt_name=self._prompt_name,
                prompt_version=self._prompt_version,
                model=request.model,
                evidence=context.evidence,
                correlation_id=request.correlation_id,
            ),
            ReasonedOutput,
        )

        package = _compose(result.output, result.record, context, request, at=self._clock())
        await self._repository.save(package)
        await self._publisher.publish(
            # See provider_normalization's handler: the platform's
            # PublishableEvent Protocol declares settable members, which a
            # frozen domain event cannot satisfy. A finding, not fixed here.
            [_completed(package)],  # type: ignore[list-item]
            session=self._session,
            producer_module=PRODUCER_MODULE,
            correlation_id=request.correlation_id,
        )

        logger.info(
            "decision package produced",
            extra={
                "workspace_id": str(package.workspace_id),
                "correlation_id": str(package.correlation_id),
                "package_id": str(package.id),
                "subject_id": str(package.subject_id),
                "support": package.support.level.value,
                "contested": package.support.contested,
                "premises": len(package.supporting_evidence),
                "inference_id": str(package.inference_id),
            },
        )
        return package


def _compose(
    output: ReasonedOutput,
    record: InferenceRecord,
    context: ReasoningContext,
    request: ReasonInput,
    *,
    at: datetime,
) -> DecisionPackage:
    """Assemble the fifteen parts. **Three come from `output`.**

    A function rather than a method because it decides nothing and depends on
    no collaborator — it is the shape of the artifact written down once.
    """
    if record.vendor is None or record.served_model is None:
        raise AIPlatformError(
            f"inference {record.id} succeeded without complete provenance, which the "
            "ai_inference constraint should have refused. Provenance on a customer-visible "
            "artifact is never invented to fill a gap."
        )

    return DecisionPackage(
        id=uuid4(),
        workspace_id=request.workspace_id,
        correlation_id=request.correlation_id,
        subject_kind=SUBJECT_KIND,
        subject_id=context.subject_id,
        summary=output.summary,
        proposition=output.proposition,
        stated_reasoning=output.stated_reasoning,
        supporting_evidence=tuple(sorted(output.premises)),
        support=context.support,
        temporal=context.temporal,
        alternative_readings=context.alternative_readings,
        limitations=context.limitations,
        suggested_validation=context.suggested_validation,
        catalog_version=context.catalog_version,
        prompt_name=record.prompt_name,
        prompt_version=record.prompt_version,
        prompt_fingerprint=record.prompt_fingerprint,
        model=record.served_model,
        vendor=record.vendor,
        evidence_digest=record.evidence_digest,
        inference_id=record.id,
        originating_buying_score_id=context.originating_buying_score_id,
        created_at=at,
    )


def _completed(package: DecisionPackage) -> ReasoningCompleted:
    return ReasoningCompleted(
        event_id=uuid4(),
        workspace_id=package.workspace_id,
        occurred_at=package.created_at,
        reasoning_id=package.id,
        subject_kind=package.subject_kind,
        subject_id=package.subject_id,
        prompt_name=package.prompt_name,
        prompt_version=package.prompt_version,
        prompt_fingerprint=package.prompt_fingerprint,
        model=package.model,
        vendor=package.vendor.value,
        evidence_digest=package.evidence_digest,
        support=package.support.level.value,
        contested=package.support.contested,
        conclusion_count=len(package.statements),
        inference_id=package.inference_id,
        payload_version=PAYLOAD_VERSION,
    )
