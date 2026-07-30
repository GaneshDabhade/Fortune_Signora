"""How strongly the evidence backs a conclusion — computed, never asserted.

**No model touches this file.** Support is derived entirely from facts the
platform already owns: which providers said it, whether the intelligence is
still current, and whether anything disagrees. A model-emitted confidence
number would be uncalibrated, incomparable between runs and between models,
moved by a vendor's checkpoint update, and self-referential — asking the
thing that might be wrong how confident it is yields a high number precisely
when it is most fluently wrong (ADR-0030, Ruling 1).

**A customer must always be able to see why Support reads as it does.** So
the level is never returned alone: it travels with the `SupportBasis` that
produced it, and the derivation is two yes/no questions a person can check
against the evidence in front of them.

Two deliberate exclusions, and both are the point.

**Contested does not lower Support.** *The Buying Score Engine prioritizes;
it never resolves* (ratified 2026-07-29) — a fought-over account warrants
more attention, not average attention, which is why opposing hypotheses never
cancel arithmetically in the ledger. Netting a contradiction into a weaker
support level would resolve, one stage later, exactly what six stages
preserved. Contention is **carried and shown**, never folded in.

**Event count does not enter the level either.** More events feel like more
support, but *how many is enough* is a threshold nobody can justify — and a
magic number nobody can justify will be trusted by four modules within a
year. Corroboration is used instead, because *"two independent providers say
this"* is a **definition** rather than a tuned value. The count is still
shown; it simply does not decide anything.

The result: **Support introduces no new threshold at all.** Both inputs to
the level already existed and were already derived elsewhere.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from modules.opportunity_engine.public import EvidenceState

_NOT_A_NUMBER = (
    "SupportLevel is a semantic category, not a score. Converting it to a number invites "
    "averaging, weighting and thresholding — and a support figure that can be averaged "
    "across accounts will be, by someone who never reads this message."
)
_NOT_ORDERED = (
    "SupportLevel does not order. Two levels differ in *why* the evidence is weaker — an "
    "aging conclusion and a single-sourced one are different problems with different fixes, "
    "and ranking them hides which one a reader is looking at."
)

#: Corroboration means **independent** sources agreeing. One provider
#: repeating itself across ten events is one source, however many rows it
#: produced — which is why this counts distinct providers rather than events,
#: the same distinction `ReasonedOutput.premises` draws for citations.
MINIMUM_CORROBORATING_PROVIDERS = 2


class SupportLevel(StrEnum):
    """How well the evidence backs the conclusion. **Never a number.**

    Three values derived from two independent yes/no facts, so a reader can
    reconstruct the level from the basis without trusting the arithmetic.
    """

    CORROBORATED = "corroborated"
    """Independent providers agree, and the intelligence is current. The
    strongest thing Signora can say without a human checking."""

    QUALIFIED = "qualified"
    """One of the two holds. Either a single source, or evidence that has
    begun to age — and the basis says which, because the two call for
    different responses."""

    LIMITED = "limited"
    """A single source, and the intelligence is no longer current. The
    conclusion may still be right; nothing here independently supports it."""

    def __int__(self) -> int:
        raise TypeError(_NOT_A_NUMBER)

    def __float__(self) -> float:
        raise TypeError(_NOT_A_NUMBER)

    def __lt__(self, other: object) -> bool:
        raise TypeError(_NOT_ORDERED)

    def __le__(self, other: object) -> bool:
        raise TypeError(_NOT_ORDERED)

    def __gt__(self, other: object) -> bool:
        raise TypeError(_NOT_ORDERED)

    def __ge__(self, other: object) -> bool:
        raise TypeError(_NOT_ORDERED)


@dataclass(frozen=True, slots=True)
class SupportBasis:
    """The facts that produced a level, so the level never stands alone.

    Every field is something the pipeline already computed and already
    records. Nothing here is new information — it is existing information
    made visible at the point a customer is deciding whether to believe a
    conclusion.
    """

    #: Distinct providers that independently corroborate the contributing
    #: events. **Names, not a count**, so a reader sees *who* agrees — and so
    #: "two providers" cannot silently become the same provider twice.
    corroborating_providers: frozenset[str]

    #: How many business events contribute. Shown because a customer asked
    #: *"how much is behind this?"*, and deliberately **not** an input to the
    #: level: see the module docstring.
    contributing_events: int

    #: Already derived by the Opportunity Engine, reused rather than
    #: recomputed. A second definition of "is this still current" would
    #: disagree with the first within a year.
    evidence_state: EvidenceState

    #: Carried, shown, and **never netted into the level**. A contested
    #: account is not a weakly-supported one; it is one where something
    #: disagrees, and the reader is entitled to know that rather than to
    #: receive its average.
    contested: bool
    #: The outweighed reading, **named rather than counted** — a consumer told
    #: only "contested" learns something disagrees while being denied the
    #: means to look. Mirrors `BuyingScore.dissenting_signal_ids`.
    dissenting_signals: int = 0

    def __post_init__(self) -> None:
        if self.contributing_events < 0 or self.dissenting_signals < 0:
            raise ValueError("support cannot rest on a negative number of anything.")
        if self.contested and self.dissenting_signals < 1:
            raise ValueError(
                "a contested basis names no dissenting signal. Contradiction is named, never "
                "merely counted — the same rule the buying score ledger enforces."
            )
        if self.contributing_events == 0 and self.corroborating_providers:
            raise ValueError(
                "providers corroborate no events. A provider that contributed nothing cannot "
                "be corroborating anything."
            )

    @property
    def is_corroborated(self) -> bool:
        """Independent sources agree. A **definition**, not a threshold."""
        return len(self.corroborating_providers) >= MINIMUM_CORROBORATING_PROVIDERS

    @property
    def is_current(self) -> bool:
        """Reused from the Opportunity Engine's own derivation."""
        return self.evidence_state is EvidenceState.CURRENT

    @property
    def level(self) -> SupportLevel:
        """Two yes/no questions, and nothing else.

        Both were already derived elsewhere, so this adds no threshold and no
        weighting — which is what makes the answer explainable to a customer
        rather than merely reported to one.
        """
        if self.is_corroborated and self.is_current:
            return SupportLevel.CORROBORATED
        if self.is_corroborated or self.is_current:
            return SupportLevel.QUALIFIED
        return SupportLevel.LIMITED

    def explain(self) -> tuple[str, ...]:
        """Why the level reads as it does, in a customer's terms.

        Rendered from the same fields the level is derived from, so the
        explanation cannot drift from the value it explains — the alternative,
        a stored sentence, would be a second representation of one fact.
        """
        sources = sorted(self.corroborating_providers)
        reasons = [
            f"{self.contributing_events} contributing business event(s)",
            (
                f"corroborated by {len(sources)} independent providers ({', '.join(sources)})"
                if self.is_corroborated
                else f"a single source ({sources[0]})"
                if sources
                else "no corroborating provider recorded"
            ),
            (
                "the intelligence behind it is current"
                if self.is_current
                else f"the intelligence behind it is {self.evidence_state.value}"
            ),
        ]
        if self.contested:
            reasons.append(
                f"{self.dissenting_signals} signal(s) read the same evidence differently — "
                "this does not weaken the support, it is a separate thing to weigh"
            )
        return tuple(reasons)
