"""Identity resolution — the first decision Signora makes.

**The Knowledge Graph resolves identity. The Knowledge Graph does not
resolve truth.** (Permanent invariant, ratified 2026-07-28.) Identity is
irreducible: Apollo's `acme-corp` and BuiltWith's `acme.example` either
are the same company or they are not, and only this module is positioned
to answer it. Attribute conflict is *not* irreducible — it is carried
forward intact, because every downstream module has more context to weigh
it than the graph does.

Everything here is built around one asymmetry:

**Under-merging and over-merging are not equally bad.** Two entities for
one company is visible, reported, and fixable. Two companies collapsed
into one silently contaminates one customer's intelligence with another's,
looks perfectly clean, and corrupts every downstream signal. So the graph
is deliberately biased toward *not* merging.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime
from enum import StrEnum
from typing import Final
from uuid import UUID, uuid4


class EntityKind(StrEnum):
    """What kinds of thing the graph knows about.

    Person is deliberately absent: claims carry role changes but no person
    *identifier*, so there is no identity to resolve. Adding people now
    would mean inventing one.
    """

    COMPANY = "company"
    TECHNOLOGY = "technology"


class IdentityState(StrEnum):
    """The resolution state of a provider identity — explicit, so each
    downstream module *decides* how to treat it rather than silently
    treating everything as identified."""

    IDENTIFIED = "identified"
    """Bound to exactly one entity. Use it."""

    AMBIGUOUS = "ambiguous"
    """Two or more candidates matched and **nothing was merged**. The
    entity may be one of several; a score built on it is provisional."""

    UNRESOLVED = "unresolved"
    """No rule matched and no entity was created. Ignore until resolved."""


class MatchStrength(StrEnum):
    """How strong a match was — **a property of the rule, not a belief**.

    Named `MatchStrength` rather than `confidence` deliberately.
    "Confidence" invites probabilistic thinking; this is a statement about
    the match, not about the world.

    Declared once per rule and never computed, combined, or scored. A pure
    function of the rule adds no information beyond the rule itself, and a
    field that *looks* computed attracts pressure to make it "smarter" —
    which is exactly how a hidden heuristic is born.

    **Permanent invariant (ratified 2026-07-29): a semantic category, never
    a number.** It must never become a numeric score, never participate in a
    weighted calculation, and never become the basis of heuristic identity
    resolution. The two doors into that drift are numeric conversion and
    ordering comparison, so both are closed below rather than left to
    review. Asserted structurally in the Security Invariants suite.
    """

    CERTAIN = "certain"
    STRONG = "strong"
    MODERATE = "moderate"

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


_NOT_A_NUMBER: Final = (
    "MatchStrength is a semantic category, not a score. Converting it to a number is "
    "the first step of a weighted heuristic, which identity resolution must not have."
)

_NOT_ORDERED: Final = (
    "MatchStrength does not order. Comparing two strengths implies they can be ranked and "
    "combined; they cannot. Compare for equality, or select by RULE_PRECEDENCE."
)


class ResolutionRule(StrEnum):
    """Deterministic rules only. No fuzzy or probabilistic matching.

    A similarity threshold is a magic number nobody can justify, and
    identity is the worst possible place to start guessing.
    """

    SAME_PROVIDER_ID = "same_provider_id"
    EXACT_DOMAIN = "exact_domain"
    LEGAL_NAME_AND_COUNTRY = "legal_name_and_country"


#: Declared strength per rule, denormalized onto each decision at decision
#: time so the audit record is self-describing. Revising a rule's strength
#: produces new decisions superseding the old — never an edit.
RULE_STRENGTH: Final[dict[ResolutionRule, MatchStrength]] = {
    # The provider's own key. It cannot be wrong about its own identifiers.
    ResolutionRule.SAME_PROVIDER_ID: MatchStrength.CERTAIN,
    # Very reliable, not certain: subsidiaries and agencies share domains.
    ResolutionRule.EXACT_DOMAIN: MatchStrength.STRONG,
    # Two unrelated "Acme Ltd" in one country is a real scenario.
    ResolutionRule.LEGAL_NAME_AND_COUNTRY: MatchStrength.MODERATE,
}

#: Evaluation order. Stronger rules first, so a certain match is never
#: passed over for a weaker one.
RULE_PRECEDENCE: Final[tuple[ResolutionRule, ...]] = (
    ResolutionRule.SAME_PROVIDER_ID,
    ResolutionRule.EXACT_DOMAIN,
    ResolutionRule.LEGAL_NAME_AND_COUNTRY,
)


class ResolutionOutcome(StrEnum):
    BOUND = "bound"
    CREATED = "created"
    AMBIGUOUS = "ambiguous"


@dataclass(frozen=True, slots=True)
class ResolutionReason:
    """What actually matched.

    Carries the **value**, not just the rule. An engineer or an auditor
    reading this months later needs to see that `domain=acme.example`
    matched, not merely that "a domain rule fired". Future explainability
    depends entirely on these surviving.
    """

    rule: ResolutionRule
    field: str
    value: str

    @property
    def strength(self) -> MatchStrength:
        return RULE_STRENGTH[self.rule]

    def describe(self) -> str:
        return f"matched by {self.field}={self.value!r} ({self.rule}, {self.strength})"


@dataclass(frozen=True, slots=True)
class Entity:
    """A canonical thing in the business world.

    **Carries no attribute values.** An entity is an *identity*, not a
    record. Its name, headcount, and industry live in claims; a `name`
    column here would be truth-resolution in miniature, and it would
    immediately disagree with the claims underneath it.
    """

    id: UUID
    workspace_id: UUID
    kind: EntityKind
    created_at: datetime

    @classmethod
    def create(cls, *, workspace_id: UUID, kind: EntityKind, now: datetime) -> Entity:
        return cls(id=uuid4(), workspace_id=workspace_id, kind=kind, created_at=now)


@dataclass(frozen=True, slots=True)
class ResolutionDecision:
    """Why a binding exists. Immutable; corrected by supersession.

    A resolution decision is itself evidence, and knowledge should have
    history. A decision that can be edited is a decision whose history
    cannot be trusted — the same reasoning that makes claims immutable.
    """

    id: UUID
    workspace_id: UUID
    provider: str
    provider_external_id: str
    outcome: ResolutionOutcome
    reasons: tuple[ResolutionReason, ...]
    entity_id: UUID | None
    #: Populated on AMBIGUOUS: every entity that matched. Recorded so an
    #: operator can see what the graph could not choose between.
    candidate_entity_ids: tuple[UUID, ...]
    evidence_claim_ids: tuple[UUID, ...]
    decided_at: datetime

    #: The decision this one corrects, if any. **Points backwards, and that
    #: is forced by immutability**: a forward `superseded_by` would have to
    #: be written onto the older row, which needs an `UPDATE` grant this
    #: table deliberately does not have. A correction is therefore a new
    #: row naming its predecessor, and the current decision is the one no
    #: other decision names.
    supersedes: UUID | None = None

    @property
    def strength(self) -> MatchStrength | None:
        """The strength of the rule that decided this — not an aggregate.

        A decision is made by exactly one rule (the engine stops at the
        first rule that matches anything), so every reason on it shares one
        strength and there is nothing to combine. Stated as an invariant
        rather than quietly reduced with `min`/`max`, because a reduction
        would be the seam through which "two moderate matches make a strong
        one" eventually arrives.
        """
        if not self.reasons:
            return None
        strengths = {reason.strength for reason in self.reasons}
        if len(strengths) > 1:
            raise ValueError(
                f"decision {self.id} mixes match strengths {sorted(s.value for s in strengths)}. "
                "A decision is made by one rule; combining strengths is the probabilistic "
                "scoring this model exists to avoid."
            )
        return strengths.pop()

    def correcting(self, previous_decision_id: UUID) -> ResolutionDecision:
        return replace(self, supersedes=previous_decision_id)

    def resolved_to(self, entity_id: UUID) -> ResolutionDecision:
        """Attach the entity a CREATED decision produced.

        The rule engine cannot know it — it is pure and allocates nothing —
        so the entity is created by the use case and named here, before the
        decision is ever persisted.
        """
        return replace(self, entity_id=entity_id, candidate_entity_ids=(entity_id,))

    def explain(self) -> str:
        """Human-readable, for audit output and operator diagnosis."""
        if self.outcome is ResolutionOutcome.CREATED:
            return (
                "created a new entity: no rule matched for "
                f"{self.provider}:{self.provider_external_id}"
            )
        if self.outcome is ResolutionOutcome.AMBIGUOUS:
            return (
                f"ambiguous: {len(self.candidate_entity_ids)} candidates matched for "
                f"{self.provider}:{self.provider_external_id} — nothing merged "
                f"({'; '.join(r.describe() for r in self.reasons)})"
            )
        return f"bound to {self.entity_id}: {'; '.join(r.describe() for r in self.reasons)}"


@dataclass(frozen=True, slots=True)
class IdentityBinding:
    """A provider identity, and the entity it resolved to.

    `state` is carried rather than inferred from decision history, so a
    consumer never has to reconstruct it — and so treating an ambiguous
    identity as identified becomes a visible choice rather than an
    accident.
    """

    id: UUID
    workspace_id: UUID
    provider: str
    provider_external_id: str
    state: IdentityState
    entity_id: UUID | None
    decision_id: UUID
    created_at: datetime

    #: The identity hints this binding was made from — what the provider
    #: said, carried forward so resolving a later identity compares against
    #: stored values rather than re-reading another module's claims. These
    #: are *hints*, scoped to one provider identity and never merged across
    #: providers; they are not the entity's attributes, which remain claims.
    domain: str | None = None
    legal_name: str | None = None
    country: str | None = None

    superseded_by: UUID | None = None

    @property
    def is_usable(self) -> bool:
        return self.state is IdentityState.IDENTIFIED and self.entity_id is not None


@dataclass(frozen=True, slots=True)
class Relationship:
    """An edge between entities, derived from claims and citing them.

    `valid_to` is what makes a *removal* first-class: a technology that
    stopped being detected ends its relationship rather than deleting it.
    The history of what a company used and stopped using is precisely what
    a competitive-displacement signal reads.
    """

    id: UUID
    workspace_id: UUID
    kind: str
    source_entity_id: UUID
    target_entity_id: UUID
    valid_from: datetime
    evidence_claim_ids: tuple[UUID, ...]
    valid_to: datetime | None = None
    superseded_by: UUID | None = None

    @property
    def is_current(self) -> bool:
        return self.valid_to is None and self.superseded_by is None

    def ended(self, *, at: datetime, evidence: tuple[UUID, ...]) -> Relationship:
        return replace(self, valid_to=at, evidence_claim_ids=self.evidence_claim_ids + evidence)


USES_TECHNOLOGY: Final = "uses_technology"
