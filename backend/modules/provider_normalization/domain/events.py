"""Domain events published by Provider Normalization.

Cataloged in docs/architecture/06-events.md. Published through the
transactional outbox, in the same transaction as the claims themselves — a
consumer must never be told evidence exists before it is durable.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Final
from uuid import UUID

EVENT_VERSION: Final = 1


@dataclass(frozen=True, slots=True)
class ClaimRecorded:
    """Evidence was produced from one raw record.

    Carries identity and counts, **not the claims themselves**. Embedding
    claim bodies would make every vocabulary addition an event contract
    change, and would let a consumer read evidence without the provenance
    the read port carries. A consumer that needs the claims reads them
    through `provider_normalization.public.ClaimReader`.

    One event per raw record rather than one per claim: the claims from a
    record are a single unit of evidence about a single subject, and
    resolving identity once per record rather than once per attribute is
    the difference between one decision and fifteen identical ones.
    """

    event_id: UUID
    workspace_id: UUID
    occurred_at: datetime
    raw_record_id: UUID
    provider: str
    subject_external_id: str
    claim_count: int
    mapper_version: str
    causation_id: UUID | None = None
    event_type: str = "claim.recorded"
    event_version: int = EVENT_VERSION

    def to_payload(self) -> dict[str, Any]:
        return {
            "raw_record_id": str(self.raw_record_id),
            "provider": self.provider,
            "subject_external_id": self.subject_external_id,
            "claim_count": self.claim_count,
            "mapper_version": self.mapper_version,
        }
