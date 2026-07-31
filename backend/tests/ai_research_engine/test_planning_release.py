"""The release rule, and the plan-ordering ruling, asserted where they bind.

`research_planning@1` is **released for `llama3.1:8b` and refused for every
other model**, because that is the only pairing anything has measured. These
tests assert it in both directions — a release nobody can lose is not a rule.

Nothing here calls a model.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

import pytest

from modules.ai_platform.public import (
    EvidenceFact,
    EvidenceRef,
    EvidenceSet,
    GroundedStatement,
    PromptNotReleasableError,
)
from modules.ai_platform.infrastructure.prompt_loader import load_prompt_registry
from modules.ai_research_engine.application.plan import PROMPT_NAME, PROMPT_VERSION
from modules.ai_research_engine.application.orchestrate import execute
from modules.ai_research_engine.domain.plan import DerivationType, PlannedStep, ResearchPlan
from modules.ai_research_engine.domain.research import ResearchTask
from modules.ai_research_engine.domain.retrieval import (
    BUSINESS_EVENT,
    CORROBORATED,
    EVENT_TYPE,
    OCCURRED_ON,
    PROVIDER_COUNT,
    PROVIDERS,
)

PROMPT_DIR = Path(__file__).resolve().parents[2] / "modules/ai_research_engine/prompts"
CERTIFIED_MODEL = "llama3.1:8b"
WORKSPACE = uuid4()
SUBJECT = EvidenceRef(kind="entity", id=uuid4())
NOW = datetime(2026, 7, 31, 12, 0, tzinfo=UTC)


class TestTheReleaseRuleBindsTheRequestPath:
    def test_the_certified_model_resolves(self) -> None:
        prompt = load_prompt_registry(PROMPT_DIR).get(PROMPT_NAME, PROMPT_VERSION)
        prompt.require_model(CERTIFIED_MODEL)

    def test_an_unmeasured_model_is_refused(self) -> None:
        """**Including one certified for a different prompt.** `granite3.3:2b`
        carries M9's reasoning release and failed this prompt's schema in three
        of three runs — a release is a fact about a pairing, never about a
        model."""
        prompt = load_prompt_registry(PROMPT_DIR).get(PROMPT_NAME, PROMPT_VERSION)

        with pytest.raises(PromptNotReleasableError):
            prompt.require_model("granite3.3:2b")

    def test_the_manifest_holds_exactly_the_measurement_that_earned_it(self) -> None:
        """`passed` is derived from the failure counts rather than stored, so a
        release cannot be recorded by asserting it."""
        manifest = json.loads((PROMPT_DIR / "manifest.json").read_text())
        record = next(p for p in manifest["prompts"] if p["name"] == PROMPT_NAME)
        (evaluation,) = record["evaluations"]

        assert record["name"] == PROMPT_NAME
        assert evaluation["model"] == CERTIFIED_MODEL
        assert evaluation["dataset"] == "research_planning"
        assert evaluation["grounding_failures"] == 0
        assert evaluation["schema_failures"] == 0
        assert evaluation["coverage"] == 1.0

    def test_the_synthesis_prompt_has_earned_no_release(self) -> None:
        """**Authored and unreleased, and the manifest says so.** A release is
        recorded by a measurement, never by asserting one — so this states what
        is true today rather than what the milestone intends."""
        manifest = json.loads((PROMPT_DIR / "manifest.json").read_text())
        record = next(p for p in manifest["prompts"] if p["name"] == "research_synthesis")

        assert record["evaluations"] == []

        prompt = load_prompt_registry(PROMPT_DIR).get("research_synthesis", 1)
        with pytest.raises(PromptNotReleasableError):
            prompt.require_model(CERTIFIED_MODEL)


def _event() -> EvidenceFact:
    return EvidenceFact(
        ref=EvidenceRef(kind=BUSINESS_EVENT, id=uuid4()),
        workspace_id=WORKSPACE,
        summary="Started using CloudERP",
        attributes=(
            (EVENT_TYPE, "technology_adopted"),
            (OCCURRED_ON, NOW.date()),
            (PROVIDER_COUNT, 1),
            (PROVIDERS, "builtwith"),
            (CORROBORATED, False),
        ),
    )


class TestPlanOrderIsPreservedAndCostsNothing:
    """**The ordering ruling, made executable.**

    Two semantically equivalent plans that differ only in step order stay
    different records — no canonicalisation — because a materialized AI
    artifact is a historical fact and reordering one is editing it. That is
    safe precisely because order buys nothing downstream: a finding's identity
    is derived from its derivation, its version and its **sorted** citations.
    """

    def test_two_orderings_execute_to_the_same_findings(self) -> None:
        first, second = _event(), _event()
        evidence = EvidenceSet(
            workspace_id=WORKSPACE, facts=(first, second), assembled_at=NOW
        )
        task = ResearchTask(
            id=uuid4(),
            workspace_id=WORKSPACE,
            correlation_id=uuid4(),
            subject=SUBJECT,
            opportunity_id=uuid4(),
            requested_at=NOW,
        )

        def _step(derivation: DerivationType) -> PlannedStep:
            return PlannedStep(
                derivation=derivation,
                reason=GroundedStatement(
                    text="Worth checking.",
                    evidence=(first.ref.token, second.ref.token),
                ),
            )

        forward = ResearchPlan(
            steps=(_step(DerivationType.CORROBORATION), _step(DerivationType.RECENCY))
        )
        reverse = ResearchPlan(
            steps=(_step(DerivationType.RECENCY), _step(DerivationType.CORROBORATION))
        )

        one = execute(task, forward, evidence, now=NOW)
        two = execute(task, reverse, evidence, now=NOW)

        assert {f.id for f in one} == {f.id for f in two}
        assert {f.derivation: f.attributes for f in one} == {
            f.derivation: f.attributes for f in two
        }

    def test_citation_order_within_a_step_does_not_change_a_finding(self) -> None:
        """The other half: identity sorts its citations, so the order the model
        listed targets in is not a fact about the comparison."""
        first, second = _event(), _event()
        evidence = EvidenceSet(
            workspace_id=WORKSPACE, facts=(first, second), assembled_at=NOW
        )
        task = ResearchTask(
            id=uuid4(),
            workspace_id=WORKSPACE,
            correlation_id=uuid4(),
            subject=SUBJECT,
            opportunity_id=uuid4(),
            requested_at=NOW,
        )

        def _plan(*tokens: str) -> ResearchPlan:
            return ResearchPlan(
                steps=(
                    PlannedStep(
                        derivation=DerivationType.CORROBORATION,
                        reason=GroundedStatement(text="Worth checking.", evidence=tokens),
                    ),
                )
            )

        one = execute(task, _plan(first.ref.token, second.ref.token), evidence, now=NOW)
        two = execute(task, _plan(second.ref.token, first.ref.token), evidence, now=NOW)

        assert one[0].id == two[0].id
        assert one[0].attributes == two[0].attributes
