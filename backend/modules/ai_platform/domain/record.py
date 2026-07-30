"""What happened on one call to a model.

Written whether the call succeeded or not. **A table that records only
successes cannot report a failure rate**, and the ungrounded rate is the
single most important thing this platform can measure about itself — it is
how Risk R-10 stops being an open risk and becomes a number.

Everything here is a *fact about what happened*: which prompt, which model,
which evidence, how many tokens, how long, what outcome. No money, no
verdict, no judgement. Pricing is applied outside at reporting time, so a
rate change re-prices history correctly (CLAUDE.md §6).

Deliberately absent: the rendered prompt text. It is fully reconstructable
from ``prompt_version`` plus ``evidence_refs``, both stored — so nothing is
lost, and Signora avoids accumulating a large body of provider-sourced text
with no data classification behind it. **R-05 (prompt data classification)
is an open escalation requiring legal input**, and this design routes around
needing it resolved rather than pretending a coding session may decide it.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from uuid import UUID

from modules.ai_platform.domain.provider import AIVendor
from modules.ai_platform.domain.usage import InferenceUsage


class InferenceOutcome(StrEnum):
    """How a call ended. Five outcomes, deliberately not collapsed.

    Each names a different thing being wrong, with a different owner:
    ``ungrounded`` is a prompt or model problem, ``schema_invalid`` is a
    structure problem, ``transient`` is an infrastructure problem, and
    ``permanent`` is usually a configuration one. One "failed" bucket would
    say nothing useful about any of them.
    """

    OK = "ok"
    SCHEMA_INVALID = "schema_invalid"
    """The model's output did not parse as the declared structure."""

    UNGROUNDED = "ungrounded"
    """It parsed, and made a claim the evidence does not support."""

    TRANSIENT = "transient"
    """The vendor could not answer, and might next time."""

    PERMANENT = "permanent"
    """The vendor refused, and would refuse again."""


@dataclass(frozen=True, slots=True)
class InferenceRecord:
    """One row per model call. Immutable, like everything else it describes."""

    id: UUID
    workspace_id: UUID
    correlation_id: UUID

    prompt_name: str
    prompt_version: int
    #: Identity of the prompt text, not merely its number. Two results
    #: claiming version 1 with different fingerprints came from different
    #: prompts, and that is worth being able to see.
    prompt_fingerprint: str

    #: What was asked for, and what answered — not always the same, since a
    #: tag may resolve to a specific build.
    requested_model: str
    served_model: str | None
    vendor: AIVendor | None

    #: The reproducible half of the input. With ``prompt_version`` this is
    #: enough to reconstruct exactly what the model saw.
    evidence_digest: str
    evidence_refs: tuple[str, ...]

    outcome: InferenceOutcome
    usage: InferenceUsage
    #: Why it failed, for a caller that needs to say so. ``None`` on success.
    detail: str | None
    created_at: datetime

    @property
    def succeeded(self) -> bool:
        return self.outcome is InferenceOutcome.OK
