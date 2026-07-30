"""Persistence for what happened on a model call, and for what it produced.

Write-only, deliberately. ``InferenceRecorder`` asks for one method and this
supplies one: the questions this table exists to answer — the ungrounded
rate, the retry trend — have no caller until the evaluation harness, and a
query method built before its consumer is a guess about the question.

There is no update method and no delete method. Immutability is enforced at
the database by the absent ``UPDATE`` grant (migration 0015); the absent
delete is the weaker of the two statements here, since a workspace must
remain erasable — it simply is not this adapter's job.
"""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from modules.ai_platform.domain.grounding import GroundedStatement
from modules.ai_platform.domain.narration import MaterializedNarration, NarrationSubject
from modules.ai_platform.domain.provider import AIVendor
from modules.ai_platform.domain.record import InferenceRecord
from modules.ai_platform.infrastructure.models import AIInferenceModel, AINarrationModel

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
    """Writes one row per model call, whatever the outcome."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def record(self, record: InferenceRecord) -> None:
        self._session.add(
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
        await self._session.flush()


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
