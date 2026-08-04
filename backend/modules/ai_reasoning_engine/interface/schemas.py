"""HTTP response schemas for the Decision Package read path.

**ADR-0030's split is the shape of this response, not a note beside it.** Of
the package's fifteen parts a model authored three; the rest were computed from
facts the pipeline already owned or copied from a reviewed catalog. So the
authored parts are grouped and carry their citations, and the derived parts are
returned as the facts they are.

Three rules shaped every field.

**A statement and its citations are inseparable.** The grounding guarantee is
that every sentence rests on evidence the deterministic pipeline computed, and
a wire format able to carry the prose without the tokens would make the
guarantee unobservable to the only party it exists for. Same rule as
`ai_platform`'s narration schema, and for the same reason.

**Facts travel; sentences are the frontend's.** `SupportBasis.explain()` and
`TemporalExplanation.why_now()` phrase things for a reader, and
`DecisionPackage.answers()` composes the ten questions out of them — **that is
presentation, and ADR-0034 puts presentation at the frontend edge.** This
response therefore carries `contested`, `dissenting_signals`,
`alternative_readings`, `trend` and `delta` rather than the sentences built
from them, and nothing here re-implements a phrasing the domain already owns.

**What is deliberately absent**, following the precedent the narration schema
set: `id`, `correlation_id`, `inference_id` and `prompt_fingerprint` are how an
engineer traces a call, not how a seller decides anything. `evidence_digest` is
absent for a different reason — a customer cannot verify a hash they cannot
recompute, and the verifiable form of *"which evidence"* is the citation tokens
on each statement, which are here.
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from modules.ai_platform.public import GroundedStatement
from modules.ai_reasoning_engine.domain.package import AlternativeReading, DecisionPackage


class ReasonedStatementResponse(BaseModel):
    """One sentence a model wrote, and the evidence it rests on."""

    model_config = ConfigDict(frozen=True)

    text: str = Field(
        description=(
            "One statement, in plain language. The platform never limits what a model "
            "writes, only what it may reference."
        )
    )
    evidence: tuple[str, ...] = Field(
        description=(
            "The facts this sentence rests on, as citation tokens (`kind:id`). Never "
            "empty: an uncited statement is refused before the package is stored."
        )
    )

    @classmethod
    def from_domain(cls, statement: GroundedStatement) -> "ReasonedStatementResponse":
        return cls(text=statement.text, evidence=statement.evidence)


class AlternativeReadingResponse(BaseModel):
    """A hypothesis the evidence was tested against and did not support."""

    model_config = ConfigDict(frozen=True)

    signal_type: str = Field(description="The reading that was considered.")
    reason: str = Field(
        description=(
            "Why the evidence did not support it, in the words of the rules that were "
            "actually applied — snapshotted, so a package explains today's rejection "
            "with today's rule rather than next quarter's."
        )
    )

    @classmethod
    def from_domain(cls, reading: AlternativeReading) -> "AlternativeReadingResponse":
        return cls(signal_type=reading.signal_type, reason=reading.reason)


class SupportResponse(BaseModel):
    """How much weight the conclusion can carry, and why.

    **`level` is derived, never stored.** The table keeps a copy for operator
    queries and the repository deliberately does not read it, so a drift
    between the two cannot reach a customer.
    """

    model_config = ConfigDict(frozen=True)

    level: str = Field(
        description=(
            "`corroborated`, `qualified` or `limited` — derived from two yes/no facts in "
            "the basis below rather than declared, so a reader can reconstruct it without "
            "trusting the arithmetic and it cannot disagree with what it stands on."
        )
    )
    corroborating_providers: tuple[str, ...] = Field(
        description=(
            "Which independent sources saw this, in a stable order. One source is a "
            "reading; two that never spoke to each other is corroboration."
        )
    )
    contributing_events: int = Field(
        description="How many observed events the conclusion ultimately rests on."
    )
    evidence_state: str = Field(
        description="Whether the evidence beneath the conclusion is still current."
    )
    contested: bool = Field(
        description=(
            "Whether signals read the same evidence differently. **Stated rather than "
            "netted away** — a disagreement averaged into silence is a disagreement a "
            "customer never got to weigh."
        )
    )
    dissenting_signals: int = Field(
        description="How many signals disagreed, when the reading is contested."
    )


class TemporalResponse(BaseModel):
    """Why this conclusion appeared now, and what it is a reading of.

    Every field is derived from the buying score the package names. The
    sentences a customer reads — *why now*, *why not earlier*, *what changed* —
    are composed from exactly these, at the frontend edge.
    """

    model_config = ConfigDict(frozen=True)

    trigger: str = Field(description="What caused the score to be computed at all.")
    basis_at: datetime = Field(description="The moment the evidence beneath this was true.")
    computed_at: datetime = Field(description="When the reading was taken.")
    delta: int = Field(description="How far the score moved, signed. Zero on a first reading.")
    trend: str = Field(description="Which way it is moving.")
    evidence_state: str = Field(description="Whether the reading is still current.")
    valid_until: datetime | None = Field(
        default=None, description="When the reading stops being current, where that is knowable."
    )
    supersedes: UUID | None = Field(
        default=None,
        description="The earlier reading this replaces. Absent on a first reading.",
    )


class DecisionPackageResponse(BaseModel):
    """One conclusion, and everything needed to disagree with it.

    **The order of the fields is the order of the argument**: what Signora
    concluded, why, what it rests on, what argues against it, what it assumes,
    what it cannot see, how to check it, and who produced it.
    """

    model_config = ConfigDict(frozen=True)

    account_id: UUID = Field(description="The company this concerns.")

    # ---- authored by a model, and grounded (3 of 15)
    proposition: ReasonedStatementResponse = Field(
        description="The conclusion itself, with the evidence it rests on."
    )
    summary: ReasonedStatementResponse = Field(
        description="The conclusion in one sentence, cited like any other."
    )
    stated_reasoning: tuple[ReasonedStatementResponse, ...] = Field(
        description="How the conclusion was reached, one cited step at a time."
    )

    # ---- derived from facts the pipeline already owned
    supporting_evidence: tuple[str, ...] = Field(
        description="What the conclusion stands on, in the pipeline's own words."
    )
    support: SupportResponse
    temporal: TemporalResponse
    alternative_readings: tuple[AlternativeReadingResponse, ...] = Field(
        description=(
            "Readings that were considered and set aside. **Empty is a real answer** — "
            "it means nothing else was tested, not that nothing else was possible."
        )
    )

    # ---- copied from a reviewed catalog, snapshotted at creation
    limitations: tuple[str, ...] = Field(
        description=(
            "What this conclusion cannot see. Written by a domain expert in the signal "
            "catalog, and copied onto the package so a later catalog revision cannot "
            "change what a customer was told."
        )
    )
    suggested_validation: tuple[str, ...] = Field(
        description="How to check this independently, without taking Signora's word for it."
    )
    catalog_version: int = Field(
        description="Which catalog revision the two fields above were taken from."
    )

    # ---- provenance, on the response rather than reachable from it
    model: str = Field(description="Which model authored the three statements above.")
    vendor: str = Field(description="Who served the call.")
    prompt_name: str = Field(description="Which prompt produced it.")
    prompt_version: int = Field(description="Which version of that prompt.")
    created_at: datetime = Field(description="When this conclusion was reached.")

    @classmethod
    def from_domain(cls, package: DecisionPackage) -> "DecisionPackageResponse":
        return cls(
            account_id=package.subject_id,
            proposition=ReasonedStatementResponse.from_domain(package.proposition),
            summary=ReasonedStatementResponse.from_domain(package.summary),
            stated_reasoning=tuple(
                ReasonedStatementResponse.from_domain(s) for s in package.stated_reasoning
            ),
            supporting_evidence=package.supporting_evidence,
            support=SupportResponse(
                level=package.support.level.value,
                # Sorted rather than iterated: the basis holds a frozenset, and
                # set iteration order is a hidden input (§2).
                corroborating_providers=tuple(sorted(package.support.corroborating_providers)),
                contributing_events=package.support.contributing_events,
                evidence_state=package.support.evidence_state.value,
                contested=package.support.contested,
                dissenting_signals=package.support.dissenting_signals,
            ),
            temporal=TemporalResponse(
                trigger=package.temporal.trigger.value,
                basis_at=package.temporal.basis_at,
                computed_at=package.temporal.computed_at,
                delta=package.temporal.delta,
                trend=package.temporal.trend.value,
                evidence_state=package.temporal.evidence_state.value,
                valid_until=package.temporal.valid_until,
                supersedes=package.temporal.supersedes,
            ),
            alternative_readings=tuple(
                AlternativeReadingResponse.from_domain(r) for r in package.alternative_readings
            ),
            limitations=package.limitations,
            suggested_validation=package.suggested_validation,
            catalog_version=package.catalog_version,
            model=package.model,
            vendor=package.vendor.value,
            prompt_name=package.prompt_name,
            prompt_version=package.prompt_version,
            created_at=package.created_at,
        )


__all__ = [
    "AlternativeReadingResponse",
    "DecisionPackageResponse",
    "ReasonedStatementResponse",
    "SupportResponse",
    "TemporalResponse",
]
