"""Persistence for what happened on a model call, and for what it produced.

Write-only, deliberately. ``InferenceRecorder`` asks for one method and this
supplies one: the questions this table exists to answer — the ungrounded
rate, the retry trend — have no caller until the evaluation harness, and a
query method built before its consumer is a guess about the question.

``SqlInferenceRecorder`` writes on **its own transaction** (ADR-0029);
``SqlNarrationRepository`` writes on the caller's. That asymmetry is the
point: a narration nobody committed was never shown to anyone, while a model
call that happened, happened.

There is no update method and no delete method. Immutability is enforced at
the database by the absent ``UPDATE`` grant (migration 0015); the absent
delete is the weaker of the two statements here, since a workspace must
remain erasable — it simply is not this adapter's job.
"""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from modules.ai_platform.domain.grounding import GroundedStatement
from modules.ai_platform.domain.narration import MaterializedNarration, NarrationSubject
from modules.ai_platform.domain.provider import AIVendor
from modules.ai_platform.domain.record import InferenceRecord
from modules.ai_platform.infrastructure.metrics import RecordingMetrics, RecordingReporter
from modules.ai_platform.infrastructure.models import AIInferenceModel, AINarrationModel
from signora_platform.db import tenant_scoped_session
from signora_platform.observability import get_logger

logger = get_logger(__name__)

#: Machine-authored, like every derived row in the platform. An inference is
#: something Signora did, not something a person asked for by name.
SYSTEM_USER_ID = UUID("00000000-0000-0000-0000-000000000001")

#: Matches ``ai_inference.detail``. Kept here as well as in the migration
#: because the writer is what must fit the column, and a mismatch would
#: surface as a failed insert on the failure path — the worst possible place
#: for a second failure.
DETAIL_LIMIT = 1024


def _fit(detail: str | None) -> str | None:
    """Truncate rather than overflow.

    A grounding report grows with the number of violations, so the most
    thoroughly ungrounded output produces the longest message — and losing
    that row entirely to a length error would discard exactly the evidence
    the table exists to keep. The first characters carry the violation kinds,
    which is the part an engineer reads first.
    """
    if detail is None or len(detail) <= DETAIL_LIMIT:
        return detail
    return f"{detail[: DETAIL_LIMIT - 1]}…"


class SqlInferenceRecorder:
    """Writes one row per model call, whatever the outcome.

    **On its own transaction** (ADR-0029, ratified 2026-07-30). Operational
    history answers *"what happened?"*; business data answers *"what became
    true?"* Those are different categories of truth, and operational history
    takes the lifetime of the **operation**, not of the enclosing business
    transaction. Sharing the caller's session meant a grounding failure that
    propagated rolled the failure record back with it — so the ungrounded
    rate read 0% forever, and read it confidently.

    The independent session is an **implementation detail and stays one**.
    `Infer` depends on the `InferenceRecorder` port and knows nothing about
    transactions; nothing above this class can tell how the row is committed.

    A row therefore means *"this call was made and this is how it ended"*,
    deliberately independent of whether the business transaction that
    requested it survived. Tokens were spent and a vendor was called, and
    those facts do not un-happen because a later step failed.
    """

    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        *,
        metrics: RecordingReporter | None = None,
    ) -> None:
        self._session_factory = session_factory
        self._metrics = metrics or RecordingMetrics()

    async def record(self, record: InferenceRecord) -> None:
        """Persist the record, and **never** fail the caller if it cannot.

        Business success and operational persistence are intentionally
        decoupled: a narration that was produced correctly must not be thrown
        away because a log row could not be written. But **operational
        persistence failure must never become invisible** — losing the record
        silently would mean the ungrounded rate reads optimistically for the
        second time, by a different mechanism.

        So the exception is swallowed *loudly*: an ERROR line carrying enough
        to identify what was lost, and a counter an alert can bind to. This is
        the one place in the module where an exception is deliberately not
        propagated, and the reason is stated rather than assumed.
        """
        try:
            async with tenant_scoped_session(
                self._session_factory,
                # From the record, which took it from the verified evidence
                # set — never from anything a client supplied.
                workspace_id=record.workspace_id,
                user_id=SYSTEM_USER_ID,
            ) as session:
                await self._write(session, record)
        except Exception as exc:  # noqa: BLE001 -- see the docstring
            self._metrics.recording_failed()
            logger.error(
                "operational history lost: the inference record could not be persisted",
                extra={
                    "workspace_id": str(record.workspace_id),
                    "correlation_id": str(record.correlation_id),
                    "inference_id": str(record.id),
                    "outcome": record.outcome.value,
                    "prompt": f"{record.prompt_name}@{record.prompt_version}",
                    "error": str(exc),
                },
            )

    async def _write(self, session: AsyncSession, record: InferenceRecord) -> None:
        session.add(
            AIInferenceModel(
                id=record.id,
                workspace_id=record.workspace_id,
                correlation_id=record.correlation_id,
                prompt_name=record.prompt_name,
                prompt_version=record.prompt_version,
                prompt_fingerprint=record.prompt_fingerprint,
                requested_model=record.requested_model,
                served_model=record.served_model,
                vendor=record.vendor.value if record.vendor else None,
                evidence_digest=record.evidence_digest,
                evidence_refs=list(record.evidence_refs),
                outcome=record.outcome.value,
                input_tokens=record.usage.input_tokens,
                output_tokens=record.usage.output_tokens,
                latency_ms=record.usage.latency_ms,
                retries=record.usage.retries,
                detail=_fit(record.detail),
                created_at=record.created_at,
                updated_at=record.created_at,
                created_by=SYSTEM_USER_ID,
                updated_by=SYSTEM_USER_ID,
            )
        )
        await session.flush()


def _to_narration(row: AINarrationModel) -> MaterializedNarration:
    return MaterializedNarration(
        id=row.id,
        workspace_id=row.workspace_id,
        correlation_id=row.correlation_id,
        subject=NarrationSubject(kind=row.subject_kind, id=row.subject_id),
        prompt_name=row.prompt_name,
        prompt_version=row.prompt_version,
        prompt_fingerprint=row.prompt_fingerprint,
        model=row.model,
        vendor=AIVendor(row.vendor),
        evidence_digest=row.evidence_digest,
        evidence_refs=tuple(row.evidence_refs),
        inference_id=row.inference_id,
        statements=tuple(
            GroundedStatement(text=s["text"], evidence=tuple(s["evidence"]))
            for s in row.statements
        ),
        created_at=row.created_at,
        payload_version=row.payload_version,
    )


class SqlNarrationRepository:
    """Stores materialized narrations. **No update, no delete.**

    A narration is a historical fact: a better explanation is a new row.
    Immutability is enforced at the database by the absent ``UPDATE`` grant
    (migration 0016); the absent methods here mean no code path even asks.
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(self, narration: MaterializedNarration) -> None:
        self._session.add(
            AINarrationModel(
                id=narration.id,
                workspace_id=narration.workspace_id,
                correlation_id=narration.correlation_id,
                subject_kind=narration.subject.kind,
                subject_id=narration.subject.id,
                prompt_name=narration.prompt_name,
                prompt_version=narration.prompt_version,
                prompt_fingerprint=narration.prompt_fingerprint,
                model=narration.model,
                vendor=narration.vendor.value,
                evidence_digest=narration.evidence_digest,
                evidence_refs=list(narration.evidence_refs),
                inference_id=narration.inference_id,
                statements=[
                    {"text": s.text, "evidence": list(s.evidence)} for s in narration.statements
                ],
                payload_version=narration.payload_version,
                created_at=narration.created_at,
                updated_at=narration.created_at,
                created_by=SYSTEM_USER_ID,
                updated_by=SYSTEM_USER_ID,
            )
        )
        await self._session.flush()

    async def latest_for(
        self, workspace_id: UUID, subject_id: UUID
    ) -> MaterializedNarration | None:
        """The most recent narration for a subject.

        **Derived from the rows, never a stored "current" flag.** Narrations
        accumulate; a column marking one as current would be a second
        representation of a fact the timestamps already carry, and the two
        would eventually disagree.
        """
        row = (
            await self._session.execute(
                select(AINarrationModel)
                .where(
                    AINarrationModel.workspace_id == workspace_id,
                    AINarrationModel.subject_id == subject_id,
                )
                .order_by(AINarrationModel.created_at.desc())
                .limit(1)
            )
        ).scalar_one_or_none()
        return _to_narration(row) if row is not None else None
