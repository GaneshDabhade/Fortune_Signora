"""Domain events published by the AI Research Engine.

Cataloged in docs/architecture/06-events.md.

**Two, and they are opposite ends of one act.** `ai_research.requested` says a
person asked; `ai_research.completed` says the run finished. Nothing is
published in between — a *"started"* event would announce work that has changed
nothing, and the surface a customer watches reads the request's own state
history rather than a stream of announcements about it.

**`ai_research.requested` is a command carried on the bus, and that is
deliberate.** An API handler may not call a model (CLAUDE.md §7), so the
request commits with the outbox row that will start the work, and the relay
delivers it. Publishing directly to Redis would enqueue work whose cause might
never commit, which is the failure the outbox exists to prevent.

**`ai_research.completed` means the run finished.** It announces that a
research artifact exists — findings derived, synthesis written, all of it
stored. Not that planning finished, not that some steps executed. A consumer
treating it as *"work is available"* would read a partial run as a complete
one, and the AI Reasoning Engine consumes this
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

#: The wire names, as constants rather than only as dataclass defaults.
#: `slots=True` makes the class attribute a descriptor, so `Event.event_type`
#: reads the slot rather than the default — a subscription registered from it
#: would point at a repr nothing publishes. Found exactly that way.
RESEARCH_REQUESTED: Final = "ai_research.requested"
RESEARCH_COMPLETED: Final = "ai_research.completed"


@dataclass(frozen=True, slots=True)
class ResearchRequested:
    """A person asked for research on one account.

    **Identity only.** The handler reads the request row it names rather than
    trusting the payload — the same rule that keeps claim bodies out of
    `claim.recorded`, and here it also means a replayed event cannot start a
    run against an account the request no longer points at.

    `requested_by` is carried because it is what a later reader needs to
    explain a model call in their bill, and it is not derivable from anything
    else on the envelope.
    """

    event_id: UUID
    workspace_id: UUID
    occurred_at: datetime
    request_id: UUID
    entity_id: UUID
    opportunity_id: UUID
    requested_by: UUID
    payload_version: int
    causation_id: UUID | None = None
    event_type: str = RESEARCH_REQUESTED
    event_version: int = EVENT_VERSION

    def to_payload(self) -> dict[str, Any]:
        return {
            "request_id": str(self.request_id),
            "entity_id": str(self.entity_id),
            "opportunity_id": str(self.opportunity_id),
            "requested_by": str(self.requested_by),
            "payload_version": self.payload_version,
        }


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
    event_type: str = RESEARCH_COMPLETED
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
