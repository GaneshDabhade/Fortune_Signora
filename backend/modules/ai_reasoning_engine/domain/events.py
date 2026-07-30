"""Domain events published by the AI Reasoning Engine.

Cataloged in docs/architecture/06-events.md.

**Exactly one.** `ai_reasoning.completed` announces that a conclusion now
exists — never what a consumer should do about it, which is the Recommendation
Engine's (M11).

**Identity and counts, never the prose.** `conclusion_count` says how many
statements; nothing here says what they are. *Events carry identity; ports
carry payload* — the rule that keeps claim bodies out of `claim.recorded` and
the contribution ledger out of `buying_score.updated`. A paragraph in an
envelope makes every wording change a contract change, and copies
customer-visible text into a queue whose retention nobody has reasoned about.

`support` and `contested` travel as **string categories**, exactly as
`MatchStrength` and `Relevance` do. A consumer given a number would average
it; a consumer given `contested` as a flag alongside `support` can see that
contention was preserved rather than netted away.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Final
from uuid import UUID

EVENT_VERSION: Final = 1


@dataclass(frozen=True, slots=True)
class ReasoningCompleted:
    """A Decision Package was produced and stored."""

    event_id: UUID
    workspace_id: UUID
    occurred_at: datetime
    reasoning_id: UUID
    subject_kind: str
    subject_id: UUID
    prompt_name: str
    prompt_version: int
    #: Content identity of the prompt, not merely its number. Two packages
    #: claiming version 1 with different fingerprints came from different text.
    prompt_fingerprint: str
    model: str
    #: Provenance only. **Never consulted for a decision** — vendor neutrality
    #: binds consumers as much as it binds the platform (CLAUDE.md §10).
    vendor: str
    evidence_digest: str
    #: A category, never a number. See `SupportLevel`.
    support: str
    #: Travels so no consumer rediscovers it by querying signals, which would
    #: put scoring logic in the wrong module.
    contested: bool
    conclusion_count: int
    inference_id: UUID
    payload_version: int
    causation_id: UUID | None = None
    event_type: str = "ai_reasoning.completed"
    event_version: int = EVENT_VERSION

    def to_payload(self) -> dict[str, Any]:
        return {
            "reasoning_id": str(self.reasoning_id),
            "subject_kind": self.subject_kind,
            "subject_id": str(self.subject_id),
            "prompt_name": self.prompt_name,
            "prompt_version": self.prompt_version,
            "prompt_fingerprint": self.prompt_fingerprint,
            "model": self.model,
            "vendor": self.vendor,
            "evidence_digest": self.evidence_digest,
            "support": self.support,
            "contested": self.contested,
            "conclusion_count": self.conclusion_count,
            "inference_id": str(self.inference_id),
            "payload_version": self.payload_version,
        }
