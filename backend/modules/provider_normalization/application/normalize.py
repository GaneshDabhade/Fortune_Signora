"""Normalize one raw provider record into canonical claims.

**An Evidence Translation Layer, not a data mapping layer.** It translates
faithfully and never interprets: no identity resolution, no reconciliation,
no confidence, no business decisions. Truth belongs downstream.

Every record produces an outcome, always — including a record that yielded
nothing. A missing outcome and an empty one mean different things, and
only one of them is a bug.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID, uuid4

from modules.provider_normalization.domain.claim import Claim, ClaimError
from modules.provider_normalization.domain.mapper import MappedClaim, ProviderMapper
from modules.provider_normalization.domain.outcome import (
    NormalizationOutcome,
    Rejection,
    RejectionReason,
)
from signora_platform.observability import get_logger

logger = get_logger(__name__)


@dataclass(frozen=True, slots=True)
class RawRecordInput:
    """The record to translate. Provider payloads arrive untyped and are
    treated as untrusted, exactly as a real vendor's would be."""

    raw_record_id: UUID
    workspace_id: UUID
    provider: str
    payload: dict[str, object]
    occurred_at: datetime
    payload_provenance: str


class NormalizeRawRecord:
    def __init__(self, *, mappers: dict[str, ProviderMapper]) -> None:
        self._mappers = mappers

    def execute(self, record: RawRecordInput) -> NormalizationOutcome:
        mapper = self._mappers.get(record.provider)
        if mapper is None:
            # A typed failure, never an empty result. An unmapped provider
            # must not look like a provider with nothing to say.
            return NormalizationOutcome(
                raw_record_id=record.raw_record_id,
                provider=record.provider,
                mapper_version="none",
                rejections=(
                    Rejection(
                        RejectionReason.UNSUPPORTED_CAPABILITY,
                        f"no mapper registered for provider '{record.provider}'",
                    ),
                ),
            )

        rejections: list[Rejection] = list(mapper.unexpected_fields(record.payload))
        claims: list[Claim] = []

        try:
            subject = mapper.subject(record.payload)
        except ClaimError as exc:
            # An unattributable claim is noise. Without a subject there is
            # nothing to attach evidence to, so translation stops here —
            # but the unknown-field rejections above are still reported,
            # because they diagnose the same shape change.
            rejections.append(Rejection(RejectionReason.UNRESOLVABLE_SUBJECT, str(exc)))
            return self._outcome(record, mapper, claims, rejections)

        source = mapper.source(record.raw_record_id, record.payload_provenance)

        for result in mapper.translate(record.payload, record.occurred_at):
            if isinstance(result, Rejection):
                rejections.append(result)
                continue
            claims.append(self._to_claim(record, subject, source, result, rejections))

        return self._outcome(record, mapper, [c for c in claims if c is not None], rejections)

    @staticmethod
    def _to_claim(
        record: RawRecordInput,
        subject: object,
        source: object,
        mapped: MappedClaim,
        rejections: list[Rejection],
    ) -> Claim:
        """Build a Claim, letting construction enforce the invariants.

        A mapper emitting a mistyped value fails here rather than three
        modules downstream, where the cause is no longer visible.
        """
        return Claim(
            id=uuid4(),
            workspace_id=record.workspace_id,
            subject=subject,  # type: ignore[arg-type]
            attribute=mapped.attribute,
            value=mapped.value,
            observed_at=mapped.observed_at,
            source=source,  # type: ignore[arg-type]
        )

    @staticmethod
    def _outcome(
        record: RawRecordInput,
        mapper: ProviderMapper,
        claims: list[Claim],
        rejections: list[Rejection],
    ) -> NormalizationOutcome:
        outcome = NormalizationOutcome(
            raw_record_id=record.raw_record_id,
            provider=record.provider,
            mapper_version=mapper.version,
            claims=tuple(claims),
            rejections=tuple(rejections),
            ignored_fields=tuple(sorted(k for k in record.payload if k in mapper.ignored_fields)),
        )

        if outcome.rejections:
            # Logged at WARNING with everything needed to diagnose without
            # reading source: provider, mapper version, and each reason.
            # A vendor shape change surfaces as a rising rejection rate.
            logger.warning(
                "normalization rejections",
                extra={
                    "provider": record.provider,
                    "mapper_version": mapper.version,
                    "raw_record_id": str(record.raw_record_id),
                    "rejection_count": len(outcome.rejections),
                    "reasons": sorted({r.reason.value for r in outcome.rejections}),
                    "has_missing_fields": outcome.has_missing_fields,
                },
            )

        return outcome
