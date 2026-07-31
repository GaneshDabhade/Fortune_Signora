"""HTTP response schemas for the Opportunity Engine.

Deliberately separate from the domain entities, even where field-identical:
coupling the wire contract to the domain model makes a domain refactor a
client-breaking change (19-api-conventions.md).

**Every field here answers a question a salesperson would ask.** The test for
inclusion was *"would someone selling understand why this is present?"* — and
several domain fields did not survive it:

- `generation` — how many opportunities this account has had. A uniqueness
  device that stops two concurrent qualifications both succeeding. Nobody
  selling has ever wanted to know it.
- `policy_version` — which qualification policy admitted this account. Real,
  auditable, and a support question rather than a sales one.
- `originating_buying_score_id` — the provenance link. It belongs on the
  account brief, where a citation can be *followed*; on a list row it is an
  opaque identifier nobody can act on.
- `contested_at_creation` — superseded by the live `contested`, which is what
  a seller is actually deciding on today.

None of them are secret and none are hidden — they are simply not part of
*this* answer, and a row that carries them teaches a reader that the fields on
it are not worth reading.

**Descriptions are `Field(description=…)`, not `#:` comments.** The first draft
used comments, which document the class for a Python reader and reach the
generated OpenAPI as nothing at all — so every field arrived on the wire
undocumented while the source looked thorough. A test now asserts the schema
itself, because that is what a client actually receives.
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from modules.opportunity_engine.application.queries import TrackedOpportunity
from modules.opportunity_engine.domain.opportunity import EvidenceState, Stage


class AccountAttentionResponse(BaseModel):
    """One account on the attention list — a row a seller decides from."""

    model_config = ConfigDict(frozen=True)

    id: UUID = Field(
        description="The opportunity. Use this to open the account's full brief."
    )
    account_id: UUID = Field(
        description=(
            "The company this opportunity is about. Resolve its name from the "
            "accounts endpoint of the Knowledge Graph: no single module may reach both "
            "workflow and entity names, so the two are composed by the caller."
        )
    )

    score: int | None = Field(
        description=(
            "Commercial attention, 0–100. An ordering, not a probability and not a "
            "prediction. Null when the evidence behind it has expired — the opportunity "
            "is still open and the number that justified it is no longer current."
        )
    )
    trend: str | None = Field(
        description="Which way the score last moved: rising, falling, or steady."
    )
    score_change: int | None = Field(
        description=(
            "Signed movement against the previous reading. Distinguishes an account that "
            "has sat at 70 for a month from one that reached 70 last night."
        )
    )
    trigger: str | None = Field(
        description=(
            "Why this account rose to attention now — a new signal, a superseded one, a "
            "changed scoring model or profile, or evidence ageing out."
        )
    )
    contested: bool = Field(
        description=(
            "Whether opposing readings are both live. A contested account is not a less "
            "certain one; it ranks above a quiet account at the same score, because a "
            "fought-over account warrants more attention rather than average attention."
        )
    )

    evidence: EvidenceState = Field(
        description=(
            "How the intelligence behind this opportunity is holding up: current, cooling, "
            "or stale. Computed when you ask and never stored, so you can see that an "
            "account went cold without Signora closing it for you."
        )
    )
    stage: Stage = Field(description="Where this sits in your workflow.")
    owner_id: UUID | None = Field(
        description="Who holds this account, or null if nobody has taken it."
    )

    opened_at: datetime = Field(
        description=(
            "When the opportunity was opened. Also half of the pagination keyset, which "
            "is why it appears on the row rather than only inside the cursor."
        )
    )

    @classmethod
    def from_domain(cls, tracked: TrackedOpportunity) -> "AccountAttentionResponse":
        score = tracked.current_score
        return cls(
            id=tracked.opportunity.id,
            account_id=tracked.opportunity.entity_id,
            score=score.value if score else None,
            trend=score.trend.value if score else None,
            score_change=score.delta if score else None,
            trigger=score.trigger.value if score else None,
            contested=score.contested if score else False,
            evidence=tracked.evidence_state,
            stage=tracked.state.stage,
            owner_id=tracked.state.owner_id,
            opened_at=tracked.opportunity.created_at,
        )


__all__ = ["AccountAttentionResponse"]
