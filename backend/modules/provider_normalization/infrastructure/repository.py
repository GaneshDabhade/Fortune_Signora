"""Persistence for claims and normalization outcomes.

**There is no update method for claims, deliberately.** Immutability is
enforced at the database by the absent UPDATE grant; not offering the
method here means nobody writes code that would fail at runtime.
"""

from __future__ import annotations

from dataclasses import asdict, is_dataclass
from datetime import date, datetime
from enum import Enum
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from modules.provider_normalization.domain.claim import Claim
from modules.provider_normalization.domain.outcome import NormalizationOutcome
from modules.provider_normalization.infrastructure.models import (
    ClaimModel,
    NormalizationOutcomeModel,
)

SYSTEM_USER_ID = UUID("00000000-0000-0000-0000-000000000001")


def encode_value(value: Any) -> Any:
    """Serialise a claim value for JSONB.

    Dates become ISO strings and enums their values, so a stored claim is
    readable in a psql session during an incident — a pickled or opaque
    encoding would make the evidence chain unreadable exactly when someone
    needs to follow it.
    """
    if is_dataclass(value) and not isinstance(value, type):
        return {k: encode_value(v) for k, v in asdict(value).items()}
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    if isinstance(value, (list, tuple)):
        return [encode_value(v) for v in value]
    return value


class ClaimRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def store(self, claims: tuple[Claim, ...]) -> int:
        if not claims:
            return 0

        self._session.add_all(
            [
                ClaimModel(
                    id=claim.id,
                    workspace_id=claim.workspace_id,
                    raw_record_id=claim.source.raw_record_id,
                    provider=claim.source.provider,
                    attribute=claim.attribute.value,
                    claim_domain=claim.attribute.domain.value,
                    value={"v": encode_value(claim.value)},
                    observed_at=claim.observed_at,
                    subject_external_id=claim.subject.provider_external_id,
                    subject_domain=claim.subject.domain,
                    subject_legal_name=claim.subject.legal_name,
                    mapper_version=claim.source.mapper_version,
                    payload_provenance=claim.source.payload_provenance,
                    created_by=SYSTEM_USER_ID,
                    updated_by=SYSTEM_USER_ID,
                )
                for claim in claims
            ]
        )
        return len(claims)

    async def record_outcome(self, workspace_id: UUID, outcome: NormalizationOutcome) -> None:
        """Upsert on (record, mapper version).

        A re-run with the same mapper is idempotent; a re-run after a fix
        carries a new version and inserts, so the improvement is visible as
        a diff rather than an overwrite.
        """
        statement = (
            insert(NormalizationOutcomeModel)
            .values(
                id=uuid4(),
                workspace_id=workspace_id,
                raw_record_id=outcome.raw_record_id,
                provider=outcome.provider,
                mapper_version=outcome.mapper_version,
                claim_count=len(outcome.claims),
                rejections=[
                    {"reason": r.reason.value, "detail": r.detail} for r in outcome.rejections
                ],
                ignored_fields=list(outcome.ignored_fields),
                created_by=SYSTEM_USER_ID,
                updated_by=SYSTEM_USER_ID,
            )
            .on_conflict_do_update(
                constraint="uq_normalization_outcome_attempt",
                set_={
                    "claim_count": len(outcome.claims),
                    "rejections": [
                        {"reason": r.reason.value, "detail": r.detail} for r in outcome.rejections
                    ],
                },
            )
        )
        await self._session.execute(statement)
