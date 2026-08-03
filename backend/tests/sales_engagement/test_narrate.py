"""Narrating a brief — six views of one graph, and a brief that survives all six failing.

**Against fakes, and never a model.** What is under test is the *composition*:
which passes are attempted, what happens to the brief when one is refused, and
whether an unbuilt prompt is distinguishable from a misbehaving one.
"""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

from modules.ai_platform.public import (
    AITransientError,
    AIVendor,
    Evaluation,
    PromptRegistry,
    PromptVersion,
)
from modules.sales_engagement.application.approach import Approach
from modules.sales_engagement.application.narrate import NarrateBrief, NarratedBrief
from modules.sales_engagement.application.ports import ModelReply, SynthesisModel
from modules.sales_engagement.application.synthesise import PassOutcome, Synthesise
from modules.sales_engagement.domain.brief import Pass
from modules.sales_engagement.domain.context import COMMERCIAL_CONTEXT_PROTOCOL_VERSION
from modules.sales_engagement.public import CommitteeRoleRef, Evidence, reason

NOW = datetime(2026, 8, 3, tzinfo=UTC)
ACCOUNT = UUID("22222222-2222-4222-8222-222222222222")
WORKSPACE = UUID("11111111-1111-4111-8111-111111111111")
MODEL = "granite3.3:2b"
CHAMPION = CommitteeRoleRef(title="VP Engineering", part="champion")
PROMPT_TEXT = "Write.\n{schema}\n{context}"

APPOINTMENT = Evidence(
    event_id=UUID("5e000000-0000-4000-8000-000000000001"),
    type_key="leadership_appointed",
    summary="Appointed a new VP of Engineering",
    occurred_at=datetime(2026, 7, 14, tzinfo=UTC),
    corroborating_providers=2,
    names_title="VP of Engineering",
)

GOOD = '{"passages": [{"text": "Open on the appointment.", "cites": ["VP Engineering"]}]}'
INVENTED = '{"passages": [{"text": "They are leaving Databricks.", "cites": ["VP Engineering"]}]}'


def approach() -> Approach:
    return Approach(
        reasoning=reason(
            account_id=ACCOUNT, committee=(CHAMPION,), evidence=(APPOINTMENT,), now=NOW
        ),
        fits=(),
        product=None,
    )


def passing() -> Evaluation:
    return Evaluation(
        model=MODEL,
        dataset="approach",
        dataset_version=1,
        rubric_version=1,
        evaluated_on=NOW.date(),
        sample_size=10,
        grounding_failures=0,
        schema_failures=0,
        coverage=0.9,
        rendering_protocol_version=COMMERCIAL_CONTEXT_PROTOCOL_VERSION,
        retries=0,
    )


def registry(*released: Pass) -> PromptRegistry:
    """A registry where exactly the named passes have earned the model."""
    return PromptRegistry(
        versions=tuple(
            PromptVersion(
                name=one.value,
                version=1,
                owner="Sales Engagement",
                text=PROMPT_TEXT,
                evaluations=(passing(),) if one in released else (),
            )
            for one in Pass
        )
    )


class FakeModel:
    def __init__(self, reply: str) -> None:
        self._reply = reply
        self.calls = 0

    async def complete(
        self, *, prompt: str, model: str, workspace_id: UUID, correlation_id: UUID
    ) -> ModelReply:
        self.calls += 1
        return ModelReply(text=self._reply, inference_id=uuid4())


class BrokenModel:
    async def complete(
        self, *, prompt: str, model: str, workspace_id: UUID, correlation_id: UUID
    ) -> ModelReply:
        raise AITransientError(AIVendor.OLLAMA, "unreachable")


async def narrate(model: SynthesisModel, *released: Pass) -> NarratedBrief:
    return await NarrateBrief(
        synthesise=Synthesise(prompts=registry(*released), model=model, model_name=MODEL)
    ).execute(approach(), workspace_id=WORKSPACE, correlation_id=uuid4())


class TestOneGraphManyViews:
    async def test_every_released_pass_reaches_the_brief(self) -> None:
        result = await narrate(FakeModel(GOOD), Pass.EXECUTIVE_SUMMARY, Pass.CONVERSATION_STRATEGY)

        assert set(result.brief.narration) == {
            Pass.EXECUTIVE_SUMMARY,
            Pass.CONVERSATION_STRATEGY,
        }

    async def test_the_narrated_sections_appear_in_reading_order(self) -> None:
        """`sections()` computes the brief's shape, so a seventh pass cannot be
        added to the object and forgotten by the screen."""
        result = await narrate(FakeModel(GOOD), Pass.EXECUTIVE_SUMMARY, Pass.CONVERSATION_STRATEGY)
        sections = result.brief.sections()

        assert sections.index("executive_summary") < sections.index("conversation_strategy")

    async def test_every_pass_is_attempted_without_being_configured(self) -> None:
        """**A pass becomes reachable the moment its prompt earns a release.**
        A caller naming which passes to run would put the release decision in
        two places, and the copy nobody maintains is the one that is read."""
        result = await narrate(FakeModel(GOOD), Pass.EXECUTIVE_SUMMARY)

        assert len(result.attempts) == len(Pass)

    async def test_an_unreleased_pass_never_reaches_a_model(self) -> None:
        """The release is resolved before anything is rendered, so attempting
        all six costs one model call when one is released."""
        model = FakeModel(GOOD)
        await narrate(model, Pass.EXECUTIVE_SUMMARY)

        assert model.calls == 1


class TestTheBriefSurvivesEveryFailure:
    async def test_a_brief_with_nothing_released_is_complete(self) -> None:
        """**The asymmetry ADR-0200 rests on.** Delete the synthesis and the
        product still works; delete the graph and there is nothing to
        synthesise."""
        result = await narrate(FakeModel(GOOD))

        assert not result.brief.is_narrated
        assert "recommendation" in result.brief.sections()
        assert "roles" in result.brief.sections()

    async def test_a_refused_pass_leaves_the_rest_of_the_brief_intact(self) -> None:
        result = await narrate(FakeModel(INVENTED), Pass.EXECUTIVE_SUMMARY)

        assert not result.brief.is_narrated
        assert result.brief.recommendation is not None

    async def test_a_provider_outage_is_not_counted_as_a_refusal(self) -> None:
        """**One is a defect, the other is an afternoon.** Conflating them lets
        an outage read as a quality regression."""
        result = await narrate(BrokenModel(), Pass.EXECUTIVE_SUMMARY)

        assert result.refused == ()
        assert any(one.outcome is PassOutcome.PROVIDER_FAILED for one in result.attempts)

    async def test_an_unbuilt_prompt_is_not_counted_as_a_refusal(self) -> None:
        """**One is a backlog item, the other is a defect.** A pass with no
        artifact never ran, and counting it as refused would make an unbuilt
        prompt look like a misbehaving one."""
        result = await narrate(FakeModel(GOOD), Pass.EXECUTIVE_SUMMARY)

        assert result.refused == ()

    async def test_a_refusal_is_reported_with_the_claim_that_caused_it(self) -> None:
        result = await narrate(FakeModel(INVENTED), Pass.EXECUTIVE_SUMMARY)
        refused = result.refused

        assert len(refused) == 1
        assert refused[0].detail is not None
        assert "databricks" in refused[0].detail.lower()


class TestTheShippedArtifacts:
    def test_the_second_pass_exists_and_is_unreleased(self) -> None:
        """It has an artifact, so it is *reachable*; it has no passing
        evaluation, so it is not *reached*."""
        from modules.sales_engagement.domain.release import released_for
        from modules.sales_engagement.infrastructure.prompts import prompts

        prompt = prompts().get(Pass.CONVERSATION_STRATEGY.value, 1)

        assert "{context}" in prompt.text
        assert not released_for(prompt, MODEL)

    def test_both_artifacts_answer_different_questions_over_one_graph(self) -> None:
        """**The graph stays identical; only the perspective changes.** Two
        prompts asking the same question would be one prompt with a duplicate."""
        from modules.sales_engagement.infrastructure.prompts import prompts

        registry_ = prompts()
        summary = registry_.get(Pass.EXECUTIVE_SUMMARY.value, 1).text
        strategy = registry_.get(Pass.CONVERSATION_STRATEGY.value, 1).text

        assert summary != strategy
        assert "first conversation" in strategy
