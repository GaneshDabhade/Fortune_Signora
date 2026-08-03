"""Response shapes for a company's recorded changes.

**Purpose-built, never a domain entity** (§7). The wire shape is a contract
with the frontend; the domain is free to change without breaking it.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from modules.observation_engine.domain.observation import Observation


class AccountObservationResponse(BaseModel):
    """One recorded change to one attribute of one company, according to one
    provider.

    **Named `Account…` because `ObservationResponse` is already taken**, by the
    Business Event Engine's evidence drawer. Two response models sharing a
    class name share an OpenAPI component name: FastAPI qualifies both, the
    original key disappears, and **a shipped client contract is renamed by a
    change in an unrelated module.** Caught here only because a test happened
    to name the schema it cared about ([B-320](../../../../docs/BUGS.md)).

    **Everything needed to draw it is here**, because the alternative is a
    client re-deriving a transition from claim history — which would be every
    consumer reimplementing this module and diverging from it.

    **No rendered sentence.** *"Grew headcount 15%"* is the frontend edge's
    words ([ADR-0034](../../../../docs/architecture/adr/0034-ubiquitous-language.md)),
    and freezing one phrasing into the wire would put the translation inward,
    where the rule says it never travels.

    **No importance, score or threshold**, matching this module's public
    contract exactly: whether a move *matters* is the Business Event Engine's
    question, and a `significance` field here would be answered by whoever
    rendered it.
    """

    model_config = ConfigDict(frozen=True)

    id: UUID
    attribute: str = Field(
        description=(
            "What changed, in the canonical vocabulary. Clients map this to "
            "customer wording; the API deliberately does not."
        )
    )
    provider: str = Field(
        description=(
            "Who observed it. **Not decoration** — a change is only ever a change "
            "according to one source, and two sources reporting different values "
            "for the same week is disagreement rather than movement."
        )
    )
    kind: str = Field(description="Whether this is a transition between values or a one-off event.")
    direction: str = Field(description="Which way it moved, or that it did not move.")

    previous_value: Any | None = Field(
        description=(
            "What it was. Null when there is genuinely nothing it moved from — a first "
            "reading, or an occurrence rather than a transition. **Absence, not zero.**"
        )
    )
    current_value: Any = Field(description="What it became.")
    magnitude: float | None = Field(
        description=(
            "The arithmetic delta, for counts only. **Never a score, never normalized, "
            "and never comparable across attributes** — 15 more employees and 15 more "
            "job postings are not the same size of anything."
        )
    )

    observed_at: datetime = Field(description="When the provider says the new value was true.")
    previous_observed_at: datetime | None = Field(
        description=(
            "When the previous value was asserted. With `observed_at` this **bounds the "
            "window the change happened in** — the change occurred somewhere between the "
            "two, and never more precisely than that. A client drawing a point rather "
            "than an interval is claiming precision the evidence does not have."
        )
    )
    recorded_at: datetime = Field(
        description=(
            "When Signora learned it. The gap from `observed_at` is reporting lag, which "
            "is real — intent data arrives weeks late — and collapsing the two makes a "
            "backfill indistinguishable from a burst of activity."
        )
    )

    supersedes: UUID | None = Field(
        description=(
            "The coarser reading this one refined, when a late claim narrowed an earlier "
            "window. Present so a client that already drew the older one can replace it "
            "rather than draw both."
        )
    )

    @classmethod
    def from_domain(cls, observation: Observation) -> "AccountObservationResponse":
        return cls(
            id=observation.id,
            attribute=observation.attribute.value,
            provider=observation.provider,
            kind=observation.kind.value,
            direction=observation.direction.value,
            previous_value=observation.previous_value,
            current_value=observation.current_value,
            magnitude=observation.magnitude,
            observed_at=observation.observed_at,
            previous_observed_at=observation.previous_observed_at,
            recorded_at=observation.recorded_at,
            supersedes=observation.supersedes,
        )


__all__ = ["AccountObservationResponse"]
