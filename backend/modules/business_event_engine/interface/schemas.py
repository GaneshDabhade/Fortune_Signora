"""HTTP response schemas for the Business Event Engine's evidence surface.

**Where a citation stops being a claim and becomes a record.** Every AI
statement and every ledger line names the business event beneath it; this is
what that name opens to.

**The fact a customer came for is not the summary — it is the observations.**
*"Grew headcount 17% over 38 days"* is Signora's sentence. `29,000 → 34,000,
observed by CoreSignal on 25 July` is the provider's, and it is the only thing
here that Signora did not write. A viewer that showed the summary and hid the
readings would be asking to be trusted at exactly the moment the customer came
to stop trusting and start checking.

**Corroboration is stated, never implied.** Which providers reported this, and
whether more than one did. A single-source fact is not a weaker fact — it is a
differently-supported one, and a screen that omitted the distinction would let
a reader assume agreement that was never measured.
"""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from modules.business_event_engine.application.queries import BusinessEventEvidence
from modules.business_event_engine.domain.taxonomy import BusinessEventType
from modules.observation_engine.public import Observation


class ObservationResponse(BaseModel):
    """One provider's reading — the fact under the fact."""

    model_config = ConfigDict(frozen=True)

    provider: str = Field(
        description="Who reported this. Named rather than counted, so a reader who "
        "distrusts one source can see when it is the one talking."
    )
    attribute: str = Field(description="What was measured — headcount, revenue band, a "
        "technology, a funding round.")
    previous_value: Any | None = Field(
        description=(
            "What it was before, or null when this is the first reading. **The half that "
            "makes a change checkable**: a current value alone cannot be argued with."
        )
    )
    current_value: Any = Field(description="What it is now, as the provider reported it.")
    direction: str = Field(
        description="Which way it moved — increased, decreased, or appeared for the first time."
    )
    observed_at: datetime = Field(
        description=(
            "When the provider observed it. **Not when Signora stored it** — the "
            "distinction is what lets a reader judge whether a fact is stale independently "
            "of when the pipeline happened to run."
        )
    )

    @classmethod
    def from_domain(cls, observation: Observation) -> "ObservationResponse":
        return cls(
            provider=observation.provider,
            attribute=observation.attribute.value,
            previous_value=observation.previous_value,
            current_value=observation.current_value,
            direction=observation.direction.value,
            observed_at=observation.observed_at,
        )


class BusinessEventEvidenceResponse(BaseModel):
    """What happened, and every reading that says so."""

    model_config = ConfigDict(frozen=True)

    id: UUID = Field(description="The business event. This is what a citation names.")
    type_key: BusinessEventType = Field(
        description="What kind of thing happened, in Signora's business vocabulary."
    )
    summary: str = Field(
        description=(
            "What happened, in one sentence. **Signora's words, not a provider's** — "
            "rendered from the same fields the readings below carry, so the sentence and "
            "the evidence cannot drift apart."
        )
    )
    occurred_at: datetime = Field(
        description="When it happened, derived from the evidence rather than from when "
        "the pipeline ran."
    )

    corroborating_providers: tuple[str, ...] = Field(
        description=(
            "Every provider whose readings independently support this. **One is not a "
            "weakness** — it is a differently-supported fact, and saying so is what stops "
            "a reader assuming an agreement that was never measured."
        )
    )
    observations: tuple[ObservationResponse, ...] = Field(
        description=(
            "The readings this rests on, oldest first. **The only content here Signora did "
            "not write.** A citation that resolved to a summary and no readings would be "
            "asking to be trusted at the moment somebody came to check."
        )
    )

    @classmethod
    def from_domain(cls, evidence: BusinessEventEvidence) -> "BusinessEventEvidenceResponse":
        return cls(
            id=evidence.event.id,
            type_key=evidence.event.type_key,
            summary=evidence.event.summary,
            occurred_at=evidence.event.occurred_at,
            corroborating_providers=evidence.event.corroborating_providers,
            observations=tuple(
                ObservationResponse.from_domain(observation)
                for observation in sorted(
                    evidence.observations, key=lambda o: (o.observed_at, str(o.id))
                )
            ),
        )


__all__ = ["BusinessEventEvidenceResponse", "ObservationResponse"]
