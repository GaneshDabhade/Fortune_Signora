"""Domain events published by the AI Research Engine.

Cataloged in docs/architecture/06-events.md.

**Exactly one, and it means the run finished.** `ai_research.completed`
announces that a research artifact exists — findings derived, synthesis
written, all of it stored. Not that planning finished, not that some steps
executed. A consumer treating it as *"work is available"* would read a partial
run as a complete one, and the AI Reasoning Engine consumes this
opportunistically precisely because it may not arrive at all.

**Identity and counts, never the prose.** `finding_count` says how many
comparisons were performed; nothing here says what they found. *Events carry
identity; ports carry payload* — the rule that keeps claim bodies out of
`claim.recorded` and the contribution ledger out of `buying_score.updated`.

**This replaces the v2 placeholders.** The catalog reserved `artifact_ref` and
`model_provenance` for this event — the same two shapes M9 found and replaced
at T127, and for the same reason: neither is a field, both are categories of
field, and a consumer cannot be written against either.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Final
from uuid import UUID

EVENT_VERSION: Final = 1


@dataclass(frozen=True, slots=True)
class ResearchCompleted:
    """A research artifact was produced and stored."""

    event_id: UUID
    workspace_id: UUID
    occurred_at: datetime
    research_id: UUID
    opportunity_id: UUID
    subject_kind: str
    subject_id: UUID
    #: The synthesis's identity. Findings are addressed individually and are
    #: read through the module's own surface, never carried here.
    synthesis_id: UUID
    prompt_name: str
    prompt_version: int
    #: Content identity of the prompt, not merely its number. Two syntheses
    #: claiming version 1 with different fingerprints came from different text.
    prompt_fingerprint: str
    model: str
    #: Provenance only. **Never consulted for a decision** — vendor neutrality
    #: binds consumers as much as it binds the platform.
    vendor: str
    evidence_digest: str
    #: How many deterministic comparisons this run performed. A count, never a
    #: quality: a run with one finding is not worse than one with three, it
    #: looked at an account with less to compare.
    finding_count: int
    statement_count: int
    inference_id: UUID
    payload_version: int
    causation_id: UUID | None = None
    event_type: str = "ai_research.completed"
    event_version: int = EVENT_VERSION

    def to_payload(self) -> dict[str, Any]:
        return {
            "research_id": str(self.research_id),
            "opportunity_id": str(self.opportunity_id),
            "subject_kind": self.subject_kind,
            "subject_id": str(self.subject_id),
            "synthesis_id": str(self.synthesis_id),
            "prompt_name": self.prompt_name,
            "prompt_version": self.prompt_version,
            "prompt_fingerprint": self.prompt_fingerprint,
            "model": self.model,
            "vendor": self.vendor,
            "evidence_digest": self.evidence_digest,
            "finding_count": self.finding_count,
            "statement_count": self.statement_count,
            "inference_id": str(self.inference_id),
            "payload_version": self.payload_version,
        }
