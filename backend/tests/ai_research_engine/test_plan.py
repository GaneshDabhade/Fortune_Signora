"""The planner: what it may decide, and everything it may not.

The planner is the one place in this module where a model chooses anything, so
these tests are mostly about the choices it **cannot** express. A schema that
refuses a conclusion is worth more than a rubric that scores one low.

Nothing here calls a model. The plans below are the structures a model would
have to return, checked directly.
"""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest
from pydantic import ValidationError

from modules.ai_platform.public import (
    EvidenceFact,
    EvidenceRef,
    EvidenceSet,
    GroundedStatement,
    ViolationKind,
    check,
)
from modules.ai_research_engine.domain.plan import (
    CATALOG,
    DerivationType,
    PlannedStep,
    ResearchPlan,
)
from modules.ai_research_engine.domain.retrieval import RESEARCH_FACT_KINDS

WORKSPACE = uuid4()
EVENT = EvidenceRef(kind="business_event", id=uuid4())
OTHER_EVENT = EvidenceRef(kind="business_event", id=uuid4())
DISSENT = EvidenceRef(kind="dissenting_signal", id=uuid4())


def _step(derivation: DerivationType, *refs: EvidenceRef, text: str = "Worth checking.") -> PlannedStep:
    return PlannedStep(
        derivation=derivation,
        reason=GroundedStatement(text=text, evidence=tuple(ref.token for ref in refs)),
    )


def _evidence(*refs: EvidenceRef) -> EvidenceSet:
    return EvidenceSet(
        workspace_id=WORKSPACE,
        facts=tuple(
            EvidenceFact(ref=ref, workspace_id=WORKSPACE, summary=f"A fact about {ref.kind}.")
            for ref in refs
        ),
        assembled_at=datetime(2026, 7, 31, tzinfo=UTC),
    )


class TestThePlannerCanDecideToStop:
    def test_an_empty_plan_is_legal(self) -> None:
        """*"Enough evidence has already been gathered"* is a planning answer,
        not a planning failure. An agent that cannot stop does not terminate."""
        plan = ResearchPlan()
        assert plan.steps == ()
        assert plan.is_complete

    def test_a_plan_with_work_is_not_complete(self) -> None:
        assert not ResearchPlan(steps=(_step(DerivationType.CORROBORATION, EVENT),)).is_complete


class TestThePlannerCannotAnswerItsOwnQuestion:
    def test_there_is_nowhere_to_put_a_conclusion(self) -> None:
        """**The mechanical stop condition.** A model that answers rather than
        selects has no field to answer in, and `extra="forbid"` refuses the
        output rather than letting a finding arrive from an INFERRED author."""
        with pytest.raises(ValidationError):
            ResearchPlan(steps=(), finding="two providers disagree")  # type: ignore[call-arg]

    def test_a_step_cannot_carry_a_result(self) -> None:
        with pytest.raises(ValidationError):
            PlannedStep(
                derivation=DerivationType.CORROBORATION,
                reason=GroundedStatement(text="x", evidence=(EVENT.token,)),
                provider_count=2,  # type: ignore[call-arg]
            )

    def test_a_plan_cannot_be_cited(self) -> None:
        """Rule 12, enforced by absence. A plan has no address, so no
        derivation can rest on the reason a model gave for running it."""
        plan = ResearchPlan()
        assert not hasattr(plan, "ref")
        assert not hasattr(plan, "token")


class TestAStepMustBeExecutable:
    def test_a_step_naming_no_facts_is_refused(self) -> None:
        with pytest.raises(ValidationError, match="names no facts"):
            PlannedStep(
                derivation=DerivationType.CORROBORATION,
                reason=GroundedStatement(text="Have a look.", evidence=()),
            )

    def test_a_step_aimed_at_facts_it_cannot_read_is_refused(self) -> None:
        """A `dissent` derivation over business events returns nothing, and an
        empty result reads exactly like a finding of nothing."""
        with pytest.raises(ValidationError, match="cannot read"):
            _step(DerivationType.DISSENT, EVENT)

    def test_a_step_aimed_at_the_right_kind_is_accepted(self) -> None:
        assert _step(DerivationType.DISSENT, DISSENT).targets == (DISSENT,)

    def test_a_malformed_citation_is_refused(self) -> None:
        with pytest.raises(ValidationError, match="nothing addressable"):
            PlannedStep(
                derivation=DerivationType.CORROBORATION,
                reason=GroundedStatement(text="x", evidence=("not-a-reference",)),
            )

    def test_targets_are_the_reasons_citations(self) -> None:
        """One representation. A separate `targets` field could disagree with
        the citations, and then the audit trail would not say what ran."""
        step = _step(DerivationType.CORROBORATION, EVENT, OTHER_EVENT)
        assert step.targets == (EVENT, OTHER_EVENT)


class TestOneDerivationIsOneComparison:
    def test_planning_a_derivation_twice_is_refused(self) -> None:
        """Two steps naming one derivation are one comparison split in half —
        and both halves would derive findings with the same identity."""
        with pytest.raises(ValidationError, match="planned twice"):
            ResearchPlan(
                steps=(
                    _step(DerivationType.CORROBORATION, EVENT),
                    _step(DerivationType.CORROBORATION, OTHER_EVENT),
                )
            )

    def test_distinct_derivations_are_accepted(self) -> None:
        plan = ResearchPlan(
            steps=(
                _step(DerivationType.CORROBORATION, EVENT),
                _step(DerivationType.DISSENT, DISSENT),
                _step(DerivationType.RECENCY, EVENT),
            )
        )
        assert len(plan.steps) == len(DerivationType)

    def test_the_plan_can_never_be_longer_than_the_catalog(self) -> None:
        """The length limit is **derived, not chosen**. Forbidding a repeated
        derivation bounds a plan by the catalog itself, so there is no constant
        for anyone to raise later."""
        assert len(CATALOG) == len(DerivationType)


class TestTheCatalogIsComplete:
    @pytest.mark.parametrize("derivation", list(DerivationType))
    def test_every_derivation_is_described(self, derivation: DerivationType) -> None:
        """A declared derivation with no definition is a promise the product
        cannot keep — the pairing the signal catalog asserts at load time."""
        definition = CATALOG[derivation]
        assert definition.derivation is derivation
        assert definition.question.strip().endswith("?")
        assert definition.consumes

    @pytest.mark.parametrize("derivation", list(DerivationType))
    def test_it_only_consumes_facts_retrieval_produces(
        self, derivation: DerivationType
    ) -> None:
        """A derivation reading a kind nothing retrieves would be planned,
        accepted, and then find nothing — a silent no-op wearing a step's
        clothes."""
        assert CATALOG[derivation].consumes <= RESEARCH_FACT_KINDS

    def test_no_definition_describes_a_derivation_that_does_not_exist(self) -> None:
        assert set(CATALOG) == set(DerivationType)


class TestClosureIsTheAiPlatformsAlready:
    """**Not reimplemented here.** A plan is a `GroundedOutput`, so `check()`
    already refuses a target the model was never shown."""

    def test_a_step_targeting_an_invented_fact_is_ungrounded(self) -> None:
        plan = ResearchPlan(steps=(_step(DerivationType.CORROBORATION, EVENT),))
        report = check(plan, _evidence(OTHER_EVENT))

        assert not report.is_grounded
        assert ViolationKind.UNRESOLVED_CITATION in report.kinds()

    def test_a_step_targeting_a_retrieved_fact_is_grounded(self) -> None:
        plan = ResearchPlan(steps=(_step(DerivationType.CORROBORATION, EVENT),))

        assert check(plan, _evidence(EVENT, OTHER_EVENT)).is_grounded

    def test_an_empty_plan_is_grounded(self) -> None:
        """Stopping cites nothing and must not be reported as ungrounded."""
        assert check(ResearchPlan(), _evidence(EVENT)).is_grounded

    def test_a_reason_inventing_a_figure_is_ungrounded(self) -> None:
        """The justification for doing work ends up in the audit trail. A
        planner that invents *"headcount fell 40%"* to justify a comparison has
        put a hallucination where a reviewer will read it as a reason."""
        plan = ResearchPlan(
            steps=(_step(DerivationType.CORROBORATION, EVENT, text="Headcount fell 40%."),)
        )
        report = check(plan, _evidence(EVENT))

        assert not report.is_grounded
        assert ViolationKind.UNGROUNDED_QUANTITY in report.kinds()
