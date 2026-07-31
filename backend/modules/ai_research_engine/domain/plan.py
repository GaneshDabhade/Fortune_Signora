"""What the planner decides — and the narrow shape it is allowed to decide in.

**This is where the AI Research Engine becomes agentic**, and it is deliberately
the smallest possible place for that to happen. The planner answers exactly one
question — *which comparison is worth performing next?* — and it answers it by
naming a derivation from a closed catalog and the facts that derivation should
run over.

    The planner chooses work. Deterministic code performs it.

So there is **no field here for a conclusion**, no number, no finding, and no
place to put one. A model that tries to answer a question rather than select one
has nowhere to write the answer, and the schema refuses the output — the same
mechanical stop condition `ReasonedOutput` uses to keep M9 from recommending.

---

**A plan carries no epistemic origin, because it is not a knowledge object.**
By the Knowledge Contract's own test — *if this were wrong, could a customer be
misled?* — the answer is no: a bad plan produces a less useful brief, but it
asserts nothing about the customer's world. It is **model-authored operational
history**, the same category as `ResearchTask` and as `ai_inference`'s record of
a call, and the contract already classifies an agentic step that way.

That is a deliberate correction to an earlier draft of this file, which called a
plan INFERRED. Origin classifies *knowledge*; classifying machinery would make
the ladder mean less, and it would imply a plan is the kind of thing that could
be weighed against a finding.

**It is uncitable for a stronger reason than Rule 12.** It has no address at
all, and nothing that is not knowledge ever enters an evidence set — so no
derivation can rest on the reason a model gave for running it. What a plan
produces is *attention*, Rule 9, which is exactly what a model is permitted to
direct.

**It cites; it is not cited.** Each step's reason is a `GroundedStatement`, so
the facts a step concerns *are* its citations. One representation, and M8's
`check()` already refuses a citation that resolves to nothing — the model cannot
plan work over a fact it was never shown, and that closure is not reimplemented
here.

---

**Two limits, and neither is a tuned number.**

*One step per derivation.* A derivation is a comparison over a set of facts, so
two steps naming one derivation are one comparison split in half. Forbidding the
repeat makes the plan's length bounded by the catalog itself rather than by a
constant somebody would later raise.

*An empty plan is legal, and is the stop decision.* *"Enough evidence has already
been gathered"* is a planning answer, not a planning failure. An agent that
cannot decide to stop does not terminate, and requiring at least one step would
make stopping unrepresentable.

The **cost** budget and the timeout are not here. They govern a running agent
rather than a plan's shape, and they belong with the orchestrator that enforces
them.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Final

from pydantic import BaseModel, ConfigDict, model_validator

from modules.ai_platform.public import EvidenceError, EvidenceRef, GroundedOutput, GroundedStatement
from modules.ai_research_engine.domain.retrieval import BUSINESS_EVENT, DISSENTING_SIGNAL


class PlanError(ValueError):
    """A plan was proposed that could not be executed as written."""


class DerivationType(StrEnum):
    """Every comparison this module can perform. **Closed, and closed on
    purpose** — a planner that could name a derivation would be a planner that
    could invent one, and an invented name reaches the orchestrator as work
    nothing knows how to do.

    Each member is here because *retrieval already exposes what it needs*. The
    catalog below states which facts that is, and nothing was added because it
    sounded useful.
    """

    #: How many independent providers support each conclusion — and which rest
    #: on one. Provider agreement is visible on a business event and nowhere
    #: else, and nothing in the product surfaces it today.
    CORROBORATION = "corroboration"

    #: What the buying score preserved but outweighed. Carried through six
    #: stages precisely so it is not netted away, and read by nothing until now.
    DISSENT = "dissent"

    #: How old the evidence beneath a conclusion is, and how far apart its
    #: events fall. A score is a projection of a moment; this asks which moment.
    RECENCY = "recency"


@dataclass(frozen=True, slots=True)
class DerivationDefinition:
    """What a derivation answers, and what it needs in order to answer it.

    **Reviewed prose plus a machine-checkable input contract**, the same pairing
    the signal catalog uses: `question` is for a human deciding whether the
    comparison was worth making, `consumes` is what refuses a step aimed at
    facts the derivation cannot read.
    """

    derivation: DerivationType
    question: str
    #: Which retrieval fact kinds this derivation reads. A step targeting
    #: anything else is refused at construction rather than failing later with
    #: an empty result nobody can interpret.
    consumes: frozenset[str]


CATALOG: Final[dict[DerivationType, DerivationDefinition]] = {
    DerivationType.CORROBORATION: DerivationDefinition(
        derivation=DerivationType.CORROBORATION,
        question="Which conclusions rest on a single provider, and which are independently agreed?",
        consumes=frozenset({BUSINESS_EVENT}),
    ),
    DerivationType.DISSENT: DerivationDefinition(
        derivation=DerivationType.DISSENT,
        question="What reading did the score preserve but outweigh, and how strong was it?",
        consumes=frozenset({DISSENTING_SIGNAL}),
    ),
    DerivationType.RECENCY: DerivationDefinition(
        derivation=DerivationType.RECENCY,
        question="How old is the evidence beneath this conclusion, and how far apart does it fall?",
        consumes=frozenset({BUSINESS_EVENT}),
    ),
}


class PlannedStep(BaseModel):
    """One comparison the planner wants performed, and why.

    **Declarative throughout.** It names work; it does not do it. The facts the
    comparison should run over are the reason's citations, so there is exactly
    one place a target can be written and no way for the two to disagree.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    derivation: DerivationType
    #: Why this is worth doing, and — as its citations — what it should read.
    reason: GroundedStatement

    @property
    def targets(self) -> tuple[EvidenceRef, ...]:
        """The facts this step is aimed at. Raises on an unparseable citation
        rather than dropping it: a target nobody can address is a step nobody
        can execute."""
        return tuple(EvidenceRef.parse(token) for token in self.reason.evidence)

    @model_validator(mode="after")
    def _targets_are_readable_by_this_derivation(self) -> PlannedStep:
        definition = CATALOG[self.derivation]
        if not self.reason.evidence:
            raise PlanError(
                f"a {self.derivation.value} step names no facts, so there is nothing to "
                "compare. A step without targets is an intention, not work."
            )
        try:
            kinds = {ref.kind for ref in self.targets}
        except EvidenceError as exc:
            raise PlanError(f"a {self.derivation.value} step cites nothing addressable: {exc}") from exc
        unreadable = kinds - definition.consumes
        if unreadable:
            raise PlanError(
                f"a {self.derivation.value} step targets {sorted(unreadable)}, which it cannot "
                f"read — it consumes {sorted(definition.consumes)}. Aimed at the wrong facts, a "
                "derivation returns an empty result that reads like a finding of nothing."
            )
        return self


class ResearchPlan(GroundedOutput):
    """The planner's entire contribution: an ordered list of intentions.

    Nothing here is a result. Deliberately small, and small in the same way
    `ReasonedOutput` is: everything a customer will lean on is produced by
    deterministic code afterwards, because those are the parts that must be
    reproducible.
    """

    steps: tuple[PlannedStep, ...] = ()

    def statements(self) -> tuple[GroundedStatement, ...]:
        """Every reason, so `check()` verifies each step's targets resolve
        inside the evidence the planner was actually shown."""
        return tuple(step.reason for step in self.steps)

    @model_validator(mode="after")
    def _no_derivation_is_planned_twice(self) -> ResearchPlan:
        planned = [step.derivation for step in self.steps]
        if len(planned) != len(set(planned)):
            raise PlanError(
                "a derivation is planned twice. A derivation is one comparison over a set of "
                "facts, so two steps naming it are one comparison split in half — and both "
                "halves would derive findings with the same identity."
            )
        return self

    @property
    def is_complete(self) -> bool:
        """No further work is worth doing. **A decision, not a failure** — an
        agent that cannot stop does not terminate."""
        return not self.steps
