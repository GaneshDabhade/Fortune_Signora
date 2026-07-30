"""Domain events published by the AI Platform.

Cataloged in docs/architecture/06-events.md.

**Exactly one**, and that restraint is the design. A substrate emitting events
nobody consumes is speculative by definition, and `ai_reasoning.completed`
(M9) and `ai_research.completed` (M10) are already reserved for the modules
that will actually produce them.

`ai.narration_completed` carries **identity and counts, never the prose**.
Events carry identity; ports carry payload — the same rule that keeps claim
bodies out of `claim.recorded` and the contribution ledger out of
`buying_score.updated`. Putting a paragraph of model output in an envelope
would make every wording change an event-contract change, and would copy
customer-visible text into a queue whose retention nobody has reasoned about.

There is deliberately **no `ai.narration_failed`**. A failed inference is
already recorded in `ai_inference` with its outcome and detail, and an event
whose information is fully contained elsewhere is a contract nobody keeps —
the same reasoning that removed `signal.scored` and `opportunity.closed`.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Final
from uuid import UUID

EVENT_VERSION: Final = 1


@dataclass(frozen=True, slots=True)
class NarrationCompleted:
    """A grounded explanation was produced and stored.

    **Announces language, not a conclusion.** Every statement in the narration
    restates something the deterministic pipeline had already computed, so a
    consumer learns that an explanation now exists — never that Signora has
    decided anything new.
    """

    event_id: UUID
    workspace_id: UUID
    occurred_at: datetime
    narration_id: UUID
    #: The subject in the AI Platform's own addressing vocabulary, so a
    #: consumer resolves it without this module naming the pipeline's concepts.
    subject_kind: str
    subject_id: UUID
    prompt_name: str
    prompt_version: int
    #: Content identity of the prompt, not merely its number. Two narrations
    #: claiming version 1 with different fingerprints came from different text.
    prompt_fingerprint: str
    model: str
    #: Provenance only. **Never consulted for a decision** — vendor neutrality
    #: applies to consumers as much as to this module (CLAUDE.md §10).
    vendor: str
    evidence_digest: str
    #: How many statements, not what they say.
    statement_count: int
    inference_id: UUID
    payload_version: int
    causation_id: UUID | None = None
    event_type: str = "ai.narration_completed"
    event_version: int = EVENT_VERSION

    def to_payload(self) -> dict[str, Any]:
        return {
            "narration_id": str(self.narration_id),
            "subject_kind": self.subject_kind,
            "subject_id": str(self.subject_id),
            "prompt_name": self.prompt_name,
            "prompt_version": self.prompt_version,
            "prompt_fingerprint": self.prompt_fingerprint,
            "model": self.model,
            "vendor": self.vendor,
            "evidence_digest": self.evidence_digest,
            "statement_count": self.statement_count,
            "inference_id": str(self.inference_id),
            "payload_version": self.payload_version,
        }
