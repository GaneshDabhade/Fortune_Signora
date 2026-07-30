"""M8's one capability: turn deterministic intelligence into language.

**It composes; it does not reason.** Every collaborator here was built and
verified in T111–T120 — the explanation source assembles evidence, `Infer`
renders and calls and grounds and records, the repository stores, the
publisher announces. This use case adds sequencing and nothing else.

**The stop condition, restated at the place it binds** (ratified 2026-07-29):

> M8 may only generate language that restates deterministic intelligence
> already present in its input. It must never introduce a proposition absent
> from that input.

That rule is not enforced by this file's good intentions. It is enforced by
`verify()` inside `Infer`: every statement must cite evidence that resolves,
and every figure must appear in a fact that statement cited. A narration
containing a proposition the pipeline did not compute cannot cite anything
for it, so the call fails rather than returning it. **The guarantee is
mechanical, which is why the boundary between M8 and M9 is testable rather
than a matter of taste.**

If narrating ever *needs* a field holding a proposition
`OpportunityExplanation` does not already contain, that is not a schema
change — it is M9 arriving early, and the correct response is to halt.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from modules.ai_platform.application.infer import Infer, InferenceInput
from modules.ai_platform.application.ports import ExplanationSource, NarrationRepository
from modules.ai_platform.domain.errors import AIPlatformError
from modules.ai_platform.domain.events import NarrationCompleted
from modules.ai_platform.domain.narration import (
    PAYLOAD_VERSION,
    MaterializedNarration,
    Narration,
    NarrationSubject,
)
from signora_platform.event_bus import EventPublisher
from signora_platform.observability import get_logger

logger = get_logger(__name__)

PRODUCER_MODULE = "ai_platform"

#: What a narration produced by this use case is about. The AI Platform's own
#: addressing vocabulary — a subject kind, not the pipeline's `entity`.
SUBJECT_KIND = "account"


class NothingToNarrateError(AIPlatformError):
    """No evidence could be assembled for this subject.

    Distinct from a failed inference, and never silently satisfied with an
    empty set: an empty evidence set would reach a model and come back as a
    fluent paragraph about nothing, perfectly grounded in no facts at all.
    """


@dataclass(frozen=True, slots=True)
class NarrateInput:
    workspace_id: UUID
    entity_id: UUID
    model: str
    correlation_id: UUID


class Narrate:
    """Produce and store one grounded explanation."""

    def __init__(
        self,
        *,
        infer: Infer,
        source: ExplanationSource,
        repository: NarrationRepository,
        publisher: EventPublisher,
        session: AsyncSession,
        prompt_name: str,
        prompt_version: int,
        clock: Callable[[], datetime] = lambda: datetime.now(UTC),
    ) -> None:
        self._infer = infer
        self._source = source
        self._repository = repository
        self._publisher = publisher
        self._session = session
        self._prompt_name = prompt_name
        self._prompt_version = prompt_version
        self._clock = clock

    async def execute(self, request: NarrateInput) -> MaterializedNarration:
        evidence = await self._source.evidence_for(request.workspace_id, request.entity_id)
        if evidence is None:
            raise NothingToNarrateError(
                f"no evidence could be assembled for {request.entity_id}. Nothing was sent to a "
                "model: an empty evidence set produces a fluent paragraph about nothing."
            )

        # `execute`, never `measure`. This is a request path, so the release
        # rule binds: a prompt that has not passed evaluation for this model
        # does not reach it (ADR-0028).
        result = await self._infer.execute(
            InferenceInput(
                prompt_name=self._prompt_name,
                prompt_version=self._prompt_version,
                model=request.model,
                evidence=evidence,
                correlation_id=request.correlation_id,
            ),
            Narration,
        )

        record = result.record
        # Both `vendor` and `served_model` are non-None on success — the
        # database refuses an `ok` row that names neither, and a successful
        # InferenceOutput is exactly that row. Asserted rather than defaulted,
        # because a silent fallback here would put a fabricated vendor onto a
        # customer-visible artifact.
        if record.vendor is None:
            raise AIPlatformError(
                f"inference {record.id} succeeded without naming a vendor, which the "
                "ai_inference constraint should have refused. Provenance on a stored "
                "narration must never be invented to fill a gap."
            )

        narration = MaterializedNarration(
            id=uuid4(),
            workspace_id=request.workspace_id,
            correlation_id=request.correlation_id,
            subject=NarrationSubject(kind=SUBJECT_KIND, id=request.entity_id),
            prompt_name=record.prompt_name,
            prompt_version=record.prompt_version,
            prompt_fingerprint=record.prompt_fingerprint,
            model=record.served_model or record.requested_model,
            vendor=record.vendor,
            evidence_digest=record.evidence_digest,
            evidence_refs=record.evidence_refs,
            inference_id=record.id,
            statements=result.output.statements(),
            created_at=self._clock(),
        )

        await self._repository.save(narration)
        await self._publisher.publish(
            # See provider_normalization's handler: the platform's
            # PublishableEvent Protocol declares settable members, which a
            # frozen domain event cannot satisfy. A finding, not fixed here.
            [_completed(narration)],  # type: ignore[list-item]
            session=self._session,
            producer_module=PRODUCER_MODULE,
            correlation_id=request.correlation_id,
        )

        logger.info(
            "narration completed",
            extra={
                "workspace_id": str(narration.workspace_id),
                "correlation_id": str(narration.correlation_id),
                "narration_id": str(narration.id),
                "subject_id": str(narration.subject.id),
                "prompt": f"{narration.prompt_name}@{narration.prompt_version}",
                "model": narration.model,
                "vendor": narration.vendor.value,
                "statement_count": len(narration.statements),
                "inference_id": str(narration.inference_id),
            },
        )
        return narration


def _completed(narration: MaterializedNarration) -> NarrationCompleted:
    return NarrationCompleted(
        event_id=uuid4(),
        workspace_id=narration.workspace_id,
        occurred_at=narration.created_at,
        narration_id=narration.id,
        subject_kind=narration.subject.kind,
        subject_id=narration.subject.id,
        prompt_name=narration.prompt_name,
        prompt_version=narration.prompt_version,
        prompt_fingerprint=narration.prompt_fingerprint,
        model=narration.model,
        vendor=narration.vendor.value,
        evidence_digest=narration.evidence_digest,
        statement_count=len(narration.statements),
        inference_id=narration.inference_id,
        payload_version=PAYLOAD_VERSION,
    )
