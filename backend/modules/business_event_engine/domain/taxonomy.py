"""The business event taxonomy — Signora's business language.

**A product asset, not an implementation detail.** These types are the
shared vocabulary the product, analytics, AI reasoning, recommendations,
customer interfaces, and future integrations all speak. Every one has to
pass a single test:

> *If a CRO opened Signora today, would they immediately understand what
> this event means?*

That rules out provider terminology, implementation terminology, and
engineering terminology. A type describes **what happened in the
customer's business**, never how Signora discovered it — which is why the
domains here (`capital`, `leadership`, `demand`) are business categories
rather than the claim vocabulary's data categories (`firmographic`,
`technographic`, `behavioural`). Those describe where data came from;
these describe what happened.

**The taxonomy defines language; rules define derivation.** Meaning should
stay stable while derivation improves — a better hiring-surge rule must
not change what a hiring surge *is*. So this file and
`domain/rules/` evolve on different clocks, and the taxonomy's should be
much slower.

**Every business threshold lives here.** A parameter is a claim about the
world that someone must be able to argue with; a constant in a rule is a
claim nobody can see. A Security Invariant enforces the distinction by
reading each rule module as a syntax tree.
"""

from __future__ import annotations

from enum import StrEnum
from typing import Any, Final

from pydantic import BaseModel, ConfigDict, Field

from modules.provider_normalization.public import ClaimAttribute


class BusinessDomain(StrEnum):
    """How a CRO groups what happens to an account.

    Deliberately **not** the claim vocabulary's `ClaimDomain`. That one
    categorises data by where it came from; this one categorises events by
    what they mean to a business.
    """

    CAPITAL = "capital"
    TECHNOLOGY = "technology"
    LEADERSHIP = "leadership"
    WORKFORCE = "workforce"
    GROWTH = "growth"
    DEMAND = "demand"


class BusinessEventType(StrEnum):
    """The types themselves. **Adding one is a product decision.**

    Each is split by direction wherever the two directions mean opposite
    things commercially: a leader joining and a leader leaving are not one
    event with a flag, and neither are revenue growth and contraction. A
    consumer that has to read a field to know whether the news is good has
    been handed the wrong vocabulary.
    """

    FUNDING_ROUND_CLOSED = "funding_round_closed"
    ACQUISITION_ANNOUNCED = "acquisition_announced"
    TECHNOLOGY_ADOPTED = "technology_adopted"
    TECHNOLOGY_RETIRED = "technology_retired"
    LEADERSHIP_APPOINTED = "leadership_appointed"
    LEADERSHIP_DEPARTED = "leadership_departed"
    HIRING_SURGE = "hiring_surge"
    HEADCOUNT_DECLINE = "headcount_decline"
    REVENUE_GROWTH = "revenue_growth"
    REVENUE_CONTRACTION = "revenue_contraction"
    BUYING_INTENT_SURGE = "buying_intent_surge"


class TaxonomyError(Exception):
    """The taxonomy artifact is malformed or incomplete.

    Raised at load time rather than at first detection: a taxonomy that is
    wrong should stop a deployment, not silently stop detecting one type.
    """


class TypeDefinition(BaseModel):
    """One type, as declared in the versioned artifact."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    key: BusinessEventType
    domain: BusinessDomain
    title: str
    description: str
    why_it_matters: str
    """Written for a customer, not an engineer. It exists so the taxonomy
    cannot grow a type nobody can justify — if the sentence is hard to
    write, the type probably should not exist."""

    evidence_attributes: tuple[ClaimAttribute, ...] = Field(min_length=1)
    """Which canonical attributes a detection may rest on. Declared so a
    vocabulary change that orphans a type is visible rather than silent."""

    parameters: dict[str, Any] = Field(default_factory=dict)
    """**The only place a business threshold may live.**"""


class Taxonomy(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid", populate_by_name=True)

    version: int
    types: tuple[TypeDefinition, ...]

    note: str = Field(default="", alias="_comment")
    """The artifact's own preamble, declared rather than tolerated.

    `extra="forbid"` is the point of this model — a typo'd key must fail a
    deployment rather than silently disable a type — so the one key that is
    prose has to be a field like any other.
    """

    def definition(self, key: BusinessEventType) -> TypeDefinition:
        for definition in self.types:
            if definition.key is key:
                return definition
        raise TaxonomyError(
            f"'{key}' is not declared in taxonomy v{self.version}. A rule detecting a type the "
            "taxonomy does not define is a rule nobody can review."
        )

    def parameters(self, key: BusinessEventType) -> Parameters:
        return Parameters(key, self.definition(key).parameters)

    def validate_complete(self, detected_keys: frozenset[BusinessEventType]) -> None:
        """Every declared type has a rule, and every rule has a declaration.

        A type with no rule is a promise nobody keeps — it appears in the
        product's vocabulary and never fires. A rule with no type is a
        detection nobody declared.
        """
        declared = {definition.key for definition in self.types}

        if orphan_types := declared - detected_keys:
            raise TaxonomyError(
                f"declared with no rule to detect them: {sorted(t.value for t in orphan_types)}. "
                "A type nobody detects is a promise the product cannot keep."
            )
        if orphan_rules := detected_keys - declared:
            raise TaxonomyError(
                f"detected but not declared: {sorted(t.value for t in orphan_rules)}. "
                "A rule with no declaration is a business threshold nobody reviewed."
            )


class Parameters:
    """Typed access to one type's declared parameters.

    Reading through this rather than indexing a dict is what makes an
    undeclared parameter a loud failure instead of a `KeyError` three
    stages into a pipeline run.
    """

    __slots__ = ("_key", "_values")

    def __init__(self, key: BusinessEventType, values: dict[str, Any]) -> None:
        self._key = key
        self._values = values

    def _get(self, name: str) -> Any:
        try:
            return self._values[name]
        except KeyError as exc:
            raise TaxonomyError(
                f"rule for '{self._key}' read undeclared parameter '{name}'. Every business "
                "threshold must be declared in the taxonomy, where it can be reviewed."
            ) from exc

    def number(self, name: str) -> float:
        return float(self._get(name))

    def count(self, name: str) -> int:
        return int(self._get(name))

    def strings(self, name: str) -> frozenset[str]:
        return frozenset(str(item) for item in self._get(name))

    def names(self) -> frozenset[str]:
        return frozenset(self._values)


CURRENT_TAXONOMY_VERSION: Final = 1
"""The version this build ships. Recorded on every business event, so a
replay under a later version is comparable to what came before rather than
indistinguishable from it."""
