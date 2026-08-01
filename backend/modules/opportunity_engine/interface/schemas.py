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

from modules.opportunity_engine.application.queries import (
    OpportunityBrief,
    TrackedOpportunity,
)
from modules.opportunity_engine.domain.opportunity import (
    EvidenceState,
    OpportunityState,
    Qualification,
    Stage,
)


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


class WorkflowStateResponse(BaseModel):
    """One complete statement of workflow state, as it was recorded."""

    model_config = ConfigDict(frozen=True)

    stage: Stage = Field(description="Where this stood after the change.")
    owner_id: UUID | None = Field(
        description="Who held it at that point, or null if nobody had taken it."
    )
    decided_by: UUID | None = Field(
        description=(
            "The person who made this change. Null only on the opening entry — Signora may "
            "suggest tracking an account and may do nothing else, so that is the one state "
            "with no human behind it."
        )
    )
    reason: str = Field(
        description=(
            "Why it changed. Recorded on every entry, because workflow has to explain itself "
            "as thoroughly as the intelligence does — *'someone changed it'* is not an "
            "explanation."
        )
    )
    occurred_at: datetime = Field(description="When it changed.")

    @classmethod
    def from_domain(cls, state: OpportunityState) -> "WorkflowStateResponse":
        return cls(
            stage=state.stage,
            owner_id=state.owner_id,
            decided_by=state.actor_id,
            reason=state.reason,
            occurred_at=state.occurred_at,
        )


class AccountOpportunityResponse(BaseModel):
    """What Signora committed to about this account, and what has happened since.

    **The brief's *then and now*.** Every field is either a fact recorded when
    somebody committed, or the same fact today. A score of 50 means something
    different on an account opened at 20 than on one opened at 60, and the
    attention list cannot show that because it only knows about now.
    """

    model_config = ConfigDict(frozen=True)

    id: UUID = Field(description="The opportunity — Signora's record of a commitment.")
    account_id: UUID = Field(description="The company it is about.")

    stage: Stage = Field(
        description=(
            "Where this sits in your workflow. Only `tracking` can be reached without a "
            "person: Signora suggests, and every stage beyond that names who decided it."
        )
    )
    owner_id: UUID | None = Field(
        description="Who holds this account, or null if nobody has taken it."
    )
    opened_at: datetime = Field(description="When Signora started tracking this account.")
    opened_by: Qualification = Field(
        description=(
            "How it got here — `automatic` if Signora suggested it from the evidence, "
            "`manual` if a person opened it regardless of the score."
        )
    )

    score_at_open: int = Field(
        description=(
            "Commercial attention at the moment of commitment. A **fact about then**, never "
            "a cached copy of the current number — it is what justified opening this, and it "
            "does not change when the score does."
        )
    )
    contested_at_open: bool = Field(
        description=(
            "Whether opposing readings were already live when it opened. Read beside "
            "`contested` on the score: an account that has *become* contested is a different "
            "situation from one that always was."
        )
    )

    score: int | None = Field(
        description=(
            "Commercial attention now. Null when no score is live — the opportunity outlives "
            "the score that created it, so a commitment stays open after its justification "
            "expires."
        )
    )
    score_change_since_open: int | None = Field(
        description=(
            "Signed movement since the commitment was made. **The one number the attention "
            "list cannot show you**, because it only knows about today. Null rather than "
            "zero when no score is live: zero is a reading that has not moved."
        )
    )
    evidence: EvidenceState = Field(
        description=(
            "How the intelligence behind this commitment is holding up: current, cooling, or "
            "stale. Computed when you ask and never stored, so an account can go cold without "
            "Signora closing it for you."
        )
    )

    history: tuple[WorkflowStateResponse, ...] = Field(
        description=(
            "Every workflow state in order, oldest first. Append-only and never rewritten — "
            "the status *is* the audit trail rather than something kept beside it, so the two "
            "cannot disagree."
        )
    )

    @classmethod
    def from_domain(cls, brief: OpportunityBrief) -> "AccountOpportunityResponse":
        return cls(
            id=brief.opportunity.id,
            account_id=brief.opportunity.entity_id,
            stage=brief.state.stage,
            owner_id=brief.state.owner_id,
            opened_at=brief.opportunity.created_at,
            opened_by=brief.opportunity.qualification,
            score_at_open=brief.opportunity.score_at_creation,
            contested_at_open=brief.opportunity.contested_at_creation,
            score=brief.current_score.value if brief.current_score else None,
            score_change_since_open=brief.score_change_since_open,
            evidence=brief.evidence_state,
            history=tuple(WorkflowStateResponse.from_domain(s) for s in brief.history),
        )


__all__ = [
    "AccountAttentionResponse",
    "AccountOpportunityResponse",
    "WorkflowStateResponse",
]
