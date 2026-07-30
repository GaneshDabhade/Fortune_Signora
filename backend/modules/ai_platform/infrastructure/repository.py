"""Persistence for what happened on a model call.

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

from sqlalchemy.ext.asyncio import AsyncSession

from modules.ai_platform.domain.record import InferenceRecord
from modules.ai_platform.infrastructure.models import AIInferenceModel

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
