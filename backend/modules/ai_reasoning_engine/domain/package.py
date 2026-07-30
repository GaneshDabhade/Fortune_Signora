"""The Decision Package — what a customer inspects, challenges and validates.

**It owns almost nothing.** Fifteen parts, and the module that assembles them
authored three. The rest is immutable history read from the pipeline,
deterministic derivations, and reviewed catalog content — each already owned
by a module better placed to be right about it (ADR-0030).

    Every field has the least powerful author capable of producing it
    correctly.

So this type is a **composition**, not a source of truth. The question it
answers is not *"what does M9 know?"* but *"what does a customer need in
front of them to reach their own judgement?"*

**Two snapshot rules, and the difference between them matters.**

*Catalog content is snapshotted.* `limitations` and `suggested_validation`
are copied onto the package at creation. A reviewed artifact changes by
version, and a package holding only a reference would silently change what it
appears to have said when the catalog is next revised — which is precisely
what immutability forbids.

*Immutable history is referenced, never copied.* Everything derived from the
buying score is recoverable forever from `originating_buying_score_id`,
because a score is never edited. Copying it would be duplicating a fact that
cannot drift, which is duplicate truth for no benefit.

The precedent is `ContributionLedger.ceiling`, carried on the ledger *"so the
ledger reproduces its score with no reference to current configuration"*.
Same reasoning, drawn at the same line: **the catalog is authoritative for
new packages; the package is authoritative for what was shown.**
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Final
from uuid import UUID

from modules.ai_platform.public import AIVendor, GroundedStatement
from modules.ai_reasoning_engine.domain.support import SupportBasis
from modules.ai_reasoning_engine.domain.temporal import TemporalExplanation

PAYLOAD_VERSION: Final = 1


class DecisionPackageError(ValueError):
    """A package was constructed that a customer could not act on."""


@dataclass(frozen=True, slots=True)
class AlternativeReading:
    """A hypothesis the evidence was tested against and did not support.

    Snapshotted from `SignalQueries.unsupported_types()` rather than
    referenced, because the *rules* that produced the reason are versioned
    code — a package explaining today's rejection with next quarter's rule
    would misreport what was considered.
    """

    signal_type: str
    reason: str


@dataclass(frozen=True, slots=True)
class DecisionPackage:
    """One conclusion, and everything needed to disagree with it."""

    id: UUID
    workspace_id: UUID
    correlation_id: UUID
    #: The account this concerns, in the AI Platform's addressing vocabulary.
    subject_kind: str
    subject_id: UUID

    # ---- authored by the model, and grounded (3 of 15)
    summary: GroundedStatement
    proposition: GroundedStatement
    stated_reasoning: tuple[GroundedStatement, ...]

    # ---- derived from facts the pipeline already owns
    supporting_evidence: tuple[str, ...]
    support: SupportBasis
    temporal: TemporalExplanation
    alternative_readings: tuple[AlternativeReading, ...]

    # ---- composed from the signal catalog, snapshotted
    limitations: tuple[str, ...]
    suggested_validation: tuple[str, ...]
    #: Which revision of the catalog the two fields above were taken from, so
    #: a reader can find the reviewed text this package actually used.
    catalog_version: int

    # ---- provenance, complete and denormalized
    prompt_name: str
    prompt_version: int
    prompt_fingerprint: str
    model: str
    vendor: AIVendor
    evidence_digest: str
    inference_id: UUID
    #: The immutable reading every derived answer is recoverable from.
    originating_buying_score_id: UUID

    created_at: datetime
    payload_version: int = PAYLOAD_VERSION

    def __post_init__(self) -> None:
        if not self.supporting_evidence:
            raise DecisionPackageError(
                f"package {self.id} cites nothing. Grounding refuses an uncited statement; "
                "an uncited conclusion is the same defect at rest."
            )
        if not self.limitations or not self.suggested_validation:
            raise DecisionPackageError(
                f"package {self.id} states no limitations or no way to check it. Both come "
                "from the signal catalog, where they are required — an empty one here means "
                "the catalog was not consulted."
            )

    @property
    def statements(self) -> tuple[GroundedStatement, ...]:
        """Every sentence a model wrote, which is every sentence grounding
        checked."""
        return (self.summary, self.proposition, *self.stated_reasoning)

    # **No contested-dissent guard here, deliberately.** One was written and
    # removed at T127: `SupportBasis` already refuses a contested basis that
    # names no dissenting signal, so a package-level repeat of that check
    # could never fire — a guard that cannot fail is documentation pretending
    # to be code, and the only way to reach it was to defeat the type system
    # from a test.
    #
    # The property genuinely worth protecting is different and is not
    # structural: *does the conclusion the model wrote actually acknowledge
    # the contradiction?* Citations alone cannot answer that, so it stays the
    # rubric's dissent-acknowledgement measure at evaluation time, where
    # ADR-0030 placed it.

    def answers(self) -> dict[str, tuple[str, ...]]:
        """The ten questions a customer asks, and this package's answers.

        **This is M9's acceptance criterion for customer-facing value**
        (ADR-0030). A package that cannot populate a row has a defect, and
        eight of the ten are answerable without a model having said anything.
        """
        return {
            "What is the conclusion?": (self.proposition.text,),
            "Why did Signora reach it?": tuple(s.text for s in self.stated_reasoning),
            "Which evidence supports it?": self.supporting_evidence,
            "Which evidence challenges it?": self._challenges(),
            "How recent is the evidence?": (self.temporal.freshness(),),
            "Why did this appear now?": (self.temporal.why_now(),),
            "Why not earlier?": (self.temporal.why_not_earlier(),),
            "What changed?": (self.temporal.what_changed(),),
            "What does it assume?": self.support.explain(),
            "What are its limitations?": self.limitations,
            "How do I validate it independently?": self.suggested_validation,
        }

    def _challenges(self) -> tuple[str, ...]:
        """Contradiction and the readings that were set aside.

        *"Nothing contradicts this"* is stated explicitly rather than left as
        an empty list — an absent answer reads as an unanswered question.
        """
        challenges: list[str] = []
        if self.support.contested:
            challenges.append(
                f"{self.support.dissenting_signals} signal(s) read the same evidence "
                "differently, and were not netted away"
            )
        challenges.extend(f"{r.signal_type}: {r.reason}" for r in self.alternative_readings)
        return tuple(challenges) or ("Nothing in the evidence contradicts this conclusion.",)
