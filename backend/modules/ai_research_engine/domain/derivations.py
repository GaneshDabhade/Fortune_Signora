"""The comparisons themselves — deterministic, and the only author of a finding.

**One rule per derivation, one derivation per rule**, asserted at import time.
A declared derivation with no implementation is a promise the planner can make
and nothing can keep; an implementation nobody declared is a comparison the
catalog never described. The Business Event Engine's taxonomy asserts exactly
this pairing for the same reason, and the check below is that check.

---

**Every rule here is a pure function of the facts it is given.** No clock, no
database, no model, no configuration. That is what makes a `ResearchFinding`
DERIVED rather than merely labelled so: the same facts recompute the same
attributes forever, which is the property a customer relies on when they open
the cited rows and check the arithmetic themselves.

**No rule introduces a threshold.** Nothing here decides that three providers
are *enough*, or that ninety days is *stale*. Counting is a measurement;
sufficiency is a judgement, and a judgement compiled into a comparison is a
business rule nobody reviewed. The same restraint the signal catalog keeps.

**No rule ranks a category.** `relevance` is a category with no numeric meaning,
and a derivation that ordered it would reintroduce the scoring the Signal Engine
refuses — so relevance is reported as the set of values present, never as a
maximum.
"""

from __future__ import annotations

from datetime import date
from typing import Final, Protocol

from modules.ai_platform.public import EvidenceFact, EvidenceValue
from modules.ai_research_engine.domain.plan import CATALOG, DerivationType
from modules.ai_research_engine.domain.research import ResearchFinding
from modules.ai_research_engine.domain.retrieval import (
    OBSERVED_ON,
    OCCURRED_ON,
    PROVIDER_COUNT,
    PROVIDERS,
    RELEVANCE,
    SIGNAL_TYPE,
)

#: Separates joined multi-valued attributes. The same character retrieval uses,
#: because a derivation that split on a different one would silently read one
#: value where the pipeline wrote several.
JOIN: Final = ","

Attributes = tuple[tuple[str, EvidenceValue], ...]


class DerivationError(ValueError):
    """A derivation was asked to run over facts it cannot read."""


class Derivation(Protocol):
    """One comparison, and the version that identifies what it computes.

    `version` participates in a finding's identity, unlike a signal's profile
    version — because changing *how* a comparison is computed can change the
    answer from identical inputs, and a finding that ignored that would collide
    with the old one and silently keep the old value.
    """

    derives: DerivationType
    version: int

    def run(self, facts: tuple[EvidenceFact, ...]) -> Attributes: ...


def _attributes(fact: EvidenceFact) -> dict[str, EvidenceValue]:
    return dict(fact.attributes)


class Corroboration:
    """How many independent providers stand behind each conclusion.

    **The comparison nothing in the product performs today.** Provider
    agreement is visible on a business event and nowhere else, and M9's
    `SupportBasis` derives from *"at least two distinct corroborating
    providers"* — so a conclusion resting on one provider is materially
    different from one resting on three, and until now nobody could see which.

    Counts only. Whether the agreement is *sufficient* is a judgement, and this
    module does not make judgements.
    """

    derives = DerivationType.CORROBORATION
    version = 1

    def run(self, facts: tuple[EvidenceFact, ...]) -> Attributes:
        counts = [int(_attributes(fact)[PROVIDER_COUNT]) for fact in facts]  # type: ignore[arg-type]
        named: set[str] = set()
        for fact in facts:
            joined = str(_attributes(fact)[PROVIDERS])
            named.update(part for part in joined.split(JOIN) if part)
        return (
            ("conclusions", len(facts)),
            ("single_source", sum(1 for count in counts if count == 1)),
            ("independently_agreed", sum(1 for count in counts if count > 1)),
            ("distinct_providers", len(named)),
            ("providers", JOIN.join(sorted(named))),
        )


class Dissent:
    """What the buying score preserved but outweighed.

    The Buying Score Engine carries dissent through six stages precisely so it
    is **not netted away**, and nothing has read it until now. Reported as
    counts and the sets of values present — never as a strongest reading,
    because relevance is a category and ordering one is how a category becomes
    a score.
    """

    derives = DerivationType.DISSENT
    version = 1

    def run(self, facts: tuple[EvidenceFact, ...]) -> Attributes:
        attributes = [_attributes(fact) for fact in facts]
        types = sorted({str(a[SIGNAL_TYPE]) for a in attributes})
        relevances = sorted({str(a[RELEVANCE]) for a in attributes})
        return (
            ("dissenting_signals", len(facts)),
            ("signal_types", JOIN.join(types)),
            ("relevances", JOIN.join(relevances)),
        )


class Recency:
    """When the evidence beneath a conclusion actually happened.

    A buying score is a projection of a moment; this asks which moment. The
    span between the oldest and newest event is a measurement, not a verdict —
    nothing here decides that an interval is too long, because that is the kind
    of threshold this module leaves to the reader.
    """

    derives = DerivationType.RECENCY
    version = 1

    def run(self, facts: tuple[EvidenceFact, ...]) -> Attributes:
        days = sorted(_as_date(_attributes(fact)[OCCURRED_ON]) for fact in facts)
        return (
            ("oldest_on", days[0]),
            ("newest_on", days[-1]),
            ("span_days", (days[-1] - days[0]).days),
        )


def _as_date(value: EvidenceValue) -> date:
    if not isinstance(value, date):
        raise DerivationError(
            f"expected a date, received {type(value).__name__}. Retrieval writes typed "
            "attributes precisely so a comparison never has to parse one back out of text."
        )
    return value


DERIVATIONS: tuple[Derivation, ...] = (Corroboration(), Dissent(), Recency())
"""Declared here rather than discovered, so a rule that exists but is never
registered is a visible omission rather than a silent one."""


def validate_complete(derivations: tuple[Derivation, ...] = DERIVATIONS) -> None:
    """Every catalog entry has a rule, and every rule has a catalog entry.

    Run at import time, below. A declared derivation with no rule is work the
    planner can select and the orchestrator cannot perform; a rule with no
    declaration is a comparison whose question nobody wrote down, and whose
    input contract nothing checks.
    """
    implemented = {derivation.derives for derivation in derivations}
    declared = set(CATALOG)

    if orphan_types := declared - implemented:
        raise DerivationError(
            f"declared with no derivation to compute them: "
            f"{sorted(t.value for t in orphan_types)}. The planner can select work nothing "
            "knows how to perform."
        )
    if orphan_rules := implemented - declared:
        raise DerivationError(
            f"computed but not declared: {sorted(t.value for t in orphan_rules)}. A comparison "
            "with no catalog entry has no stated question and no checked input contract."
        )
    if len(implemented) != len(derivations):
        raise DerivationError(
            "two derivations claim one type. Which one runs would then depend on registry "
            "order, and a finding's content would depend on where a rule was declared."
        )


validate_complete()


def as_evidence(finding: ResearchFinding) -> EvidenceFact:
    """A finding, addressed as evidence a narrator may cite.

    **This is the only bridge from a derivation to a prompt**, and it carries
    no new information: the summary is the catalog's own reviewed question and
    the attributes are exactly what the rule computed. Nothing is rephrased,
    ranked, or explained on the way through — a finding that acquired meaning
    here would be a second author nobody reviewed.

    **The summary is the question, not an answer.** A narrator is shown *"which
    conclusions rest on a single provider?"* alongside the counts that answer
    it, so the words framing the numbers are a domain expert's rather than a
    model's, and they cannot drift from what was computed.
    """
    return EvidenceFact(
        ref=finding.ref,
        workspace_id=finding.workspace_id,
        summary=CATALOG[DerivationType(finding.derivation)].question,
        attributes=finding.attributes,
    )


def for_type(derivation: DerivationType) -> Derivation:
    """The one rule that computes this. Total, because `validate_complete`
    already refused a catalog entry without one."""
    return next(rule for rule in DERIVATIONS if rule.derives is derivation)
