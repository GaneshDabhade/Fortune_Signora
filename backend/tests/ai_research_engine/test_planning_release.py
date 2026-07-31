"""The release rule, and the plan-ordering ruling, asserted where they bind.

M10 requests `research_planning@2` and `research_synthesis@2`, both **released
for `llama3.1:8b` and refused for every other model**, because that is the only
pairing anything has measured under rendering protocol 2. The `@1` versions are
still on disk, still hold the measurements they earned under protocol 1, and
earn nothing today. Both directions are asserted — a release nobody can lose is
not a rule.

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
from modules.ai_research_engine.application.research import SYNTHESIS_PROMPT, SYNTHESIS_VERSION
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


class TestTheRequestPathUsesTheProtocol2Prompts:
    """M10 asks for `@2`, and `@2` is what earned a release under protocol 2."""

    def test_both_prompts_the_pipeline_requests_are_released(self) -> None:
        registry = load_prompt_registry(PROMPT_DIR)

        assert (PROMPT_NAME, PROMPT_VERSION) == ("research_planning", 2)
        assert (SYNTHESIS_PROMPT, SYNTHESIS_VERSION) == ("research_synthesis", 2)

        registry.get(PROMPT_NAME, PROMPT_VERSION).require_model(CERTIFIED_MODEL)
        registry.get(SYNTHESIS_PROMPT, SYNTHESIS_VERSION).require_model(CERTIFIED_MODEL)

    def test_an_unmeasured_model_is_refused(self) -> None:
        """**Including one certified for a different prompt.** `granite3.3:2b`
        carries M9's reasoning release and failed this prompt's schema in three
        of three runs — a release is a fact about a pairing, never about a
        model."""
        prompt = load_prompt_registry(PROMPT_DIR).get(PROMPT_NAME, PROMPT_VERSION)

        with pytest.raises(PromptNotReleasableError):
            prompt.require_model("granite3.3:2b")

    def test_no_prompt_the_pipeline_uses_instructs_a_transformation(self) -> None:
        """**The success criterion of M9.5, asserted on the artifacts.**

        A prompt author must never again compensate for parser behaviour. Both
        `@1` prompts told the model to remove characters; both `@2` prompts ask
        only that the reference be copied. This reads the shipped files, so a
        future author reintroducing the workaround fails here.
        """
        for name in (PROMPT_NAME, SYNTHESIS_PROMPT):
            text = (PROMPT_DIR / f"{name}@2.md").read_text().lower()

            assert "exactly as shown" in text
            for compensation in ("without the brackets", "square bracket", "strip", "remove the"):
                assert compensation not in text, (
                    f"{name}@2 instructs the model to edit a citation ('{compensation}'). "
                    "Rendering protocol 2 shows the reference as the parser accepts it, so "
                    "copying is the winning strategy and no prompt needs to describe surgery."
                )


class TestTheProtocol1PromptsKeepTheirHistoryAndEarnNothing:
    """Immutable, still on disk, still recording what they measured."""

    @pytest.mark.parametrize(
        ("name", "grounding_failures"),
        [("research_planning", 0), ("research_synthesis", 1)],
    )
    def test_version_1_records_its_protocol_1_measurement(
        self, name: str, grounding_failures: int
    ) -> None:
        manifest = json.loads((PROMPT_DIR / "manifest.json").read_text())
        record = next(
            p for p in manifest["prompts"] if p["name"] == name and p["version"] == 1
        )
        (measurement,) = record["evaluations"]

        assert measurement["model"] == CERTIFIED_MODEL
        assert measurement["rendering_protocol_version"] == 1
        assert measurement["grounding_failures"] == grounding_failures

        prompt = load_prompt_registry(PROMPT_DIR).get(name, 1)
        assert not prompt.is_released
        with pytest.raises(PromptNotReleasableError):
            prompt.require_model(CERTIFIED_MODEL)

    def test_the_two_versions_are_different_artifacts(self) -> None:
        """Content identity outranks version identity: `@2` is a new prompt,
        never an edit of `@1`, and the fingerprints prove it."""
        registry = load_prompt_registry(PROMPT_DIR)

        for name in ("research_planning", "research_synthesis"):
            first, second = registry.get(name, 1), registry.get(name, 2)
            assert first.fingerprint != second.fingerprint
            assert first.text != second.text


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
