"""Response shapes for the Provider Platform's one read surface.

Purpose-built rather than a domain entity returned directly (§7), and it
carries facts rather than sentences: what a customer reads is composed at the
frontend edge, where the customer's vocabulary lives (ADR-0034).
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from modules.provider_platform.domain.coverage import SubjectCoverage


class SubjectCoverageResponse(BaseModel):
    """When a provider last looked at one company, and whether it found
    anything.

    **Two nullable-independent fields rather than one status string.** A
    string would have to enumerate the states, and the enumeration would then
    exist twice — here and wherever it is rendered. These two carry all four
    (§2, *truth has exactly one authoritative representation*).
    """

    subject: str = Field(
        description=(
            "The company name exactly as the customer declared it. Unresolved "
            "by design (ADR-0036 §5) — it identifies a declaration entry, not "
            "an entity."
        )
    )
    last_attempt: datetime | None = Field(
        default=None,
        description=(
            "When a provider last completed a read of this company, whether "
            "or not anything came back. Null when no completed read is "
            "recorded — read `stored_anything` to tell *never checked* from "
            "*read before this was recorded*."
        ),
    )
    stored_anything: bool = Field(
        description=(
            "Whether any read of this company has ever stored evidence. False "
            "with a `last_attempt` present is the case that matters: somebody "
            "looked and there was nothing there."
        )
    )

    @classmethod
    def from_domain(cls, found: SubjectCoverage) -> SubjectCoverageResponse:
        return cls(
            subject=found.subject,
            last_attempt=found.last_attempt,
            stored_anything=found.stored_anything,
        )


__all__ = ["SubjectCoverageResponse"]
