"""Running a pass — every failure degrades to a brief without prose.

**Against fakes, and never a model.** Deterministic engineering behaviour is
verified against scripted adapters; AI quality is measured by the harness against
a real model. Merging the two would measure the fake — a scripted adapter never
invents a competitor unless it is told to.
"""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest

from modules.ai_platform.public import (
    AITransientError,
    AIVendor,
    Evaluation,
    PromptRegistry,
    PromptVersion,
)
from modules.sales_engagement.application.approach import Approach
from modules.sales_engagement.application.ports import ModelReply, SynthesisModel
from modules.sales_engagement.application.synthesise import (
    CONTEXT_PLACEHOLDER,
    PassOutcome,
    PassResult,
    Synthesise,
    render,
)
from modules.sales_engagement.domain.brief import Pass, assemble
from modules.sales_engagement.domain.context import (
    COMMERCIAL_CONTEXT_PROTOCOL_VERSION,
    CommercialContext,
)
from modules.sales_engagement.domain.synthesis import SynthesisSource
from modules.sales_engagement.public import CommitteeRoleRef, Evidence, reason

NOW = datetime(2026, 8, 3, tzinfo=UTC)
ACCOUNT = UUID("22222222-2222-4222-8222-222222222222")
WORKSPACE = UUID("11111111-1111-4111-8111-111111111111")
MODEL = "granite3.3:2b"
CHAMPION = CommitteeRoleRef(title="VP Engineering", part="champion")

APPOINTMENT = Evidence(
    event_id=UUID("5e000000-0000-4000-8000-000000000001"),
    type_key="leadership_appointed",
    summary="Appointed a new VP of Engineering",
    occurred_at=datetime(2026, 7, 14, tzinfo=UTC),
    corroborating_providers=2,
    names_title="VP of Engineering",
)

PROMPT_TEXT = "Summarise this.\n\n{schema}\n\n{context}"


def approach() -> Approach:
    return Approach(
        reasoning=reason(
            account_id=ACCOUNT, committee=(CHAMPION,), evidence=(APPOINTMENT,), now=NOW
        ),
        fits=(),
        product=None,
    )


def passing_measurement() -> Evaluation:
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


def registry(*, released: bool, version: int = 1) -> PromptRegistry:
    return PromptRegistry(
        versions=(
            PromptVersion(
                name=Pass.EXECUTIVE_SUMMARY.value,
                version=version,
                owner="Sales Engagement",
                text=PROMPT_TEXT,
                evaluations=(passing_measurement(),) if released else (),
            ),
        )
    )


class FakeModel:
    """Replies with whatever it was scripted to. **Records the prompt**, because
    what a model was shown is the input every other assertion depends on."""

    def __init__(self, reply: str) -> None:
        self._reply = reply
        self.saw: str | None = None
        self.calls = 0

    async def complete(
        self, *, prompt: str, model: str, workspace_id: UUID, correlation_id: UUID
    ) -> ModelReply:
        self.saw = prompt
        self.calls += 1
        return ModelReply(text=self._reply, inference_id=uuid4())


class BrokenModel:
    async def complete(
        self, *, prompt: str, model: str, workspace_id: UUID, correlation_id: UUID
    ) -> ModelReply:
        raise AITransientError(AIVendor.OLLAMA, "the runtime is unreachable")


GOOD = (
    '{"passages": [{"text": "The appointment points at leadership reshaping how this team '
    'builds.", "cites": ["VP Engineering"]}]}'
)


async def run(model: SynthesisModel, *, released: bool = True) -> PassResult:
    return await Synthesise(
        prompts=registry(released=released),
        model=model,
        model_name=MODEL,
    ).execute(approach(), Pass.EXECUTIVE_SUMMARY, workspace_id=WORKSPACE, correlation_id=uuid4())


class TestTheHappyPath:
    async def test_a_grounded_draft_becomes_a_synthesis(self) -> None:
        result = await run(FakeModel(GOOD))

        assert result.outcome is PassOutcome.OK
        assert result.succeeded

    async def test_the_model_is_shown_the_rendered_graph(self) -> None:
        """**Not raw evidence.** The model is handed a fully constrained object
        and is not asked to infer any of it."""
        model = FakeModel(GOOD)
        await run(model)

        assert model.saw is not None
        assert "cite: VP Engineering" in model.saw
        assert CONTEXT_PLACEHOLDER not in model.saw

    async def test_the_synthesis_names_the_inference_that_produced_it(self) -> None:
        result = await run(FakeModel(GOOD))

        assert result.synthesis is not None
        assert result.synthesis.inference_id is not None


class TestEveryFailureDegradesToTheFacts:
    async def test_an_unreleased_prompt_produces_no_prose_and_no_exception(self) -> None:
        """**The state this module ships in**, and it is not a fault."""
        result = await run(FakeModel(GOOD), released=False)

        assert result.outcome is PassOutcome.NO_RELEASED_PROMPT
        assert not result.succeeded

    async def test_an_unreleased_prompt_is_never_sent_to_a_model(self) -> None:
        model = FakeModel(GOOD)
        await run(model, released=False)

        assert model.calls == 0

    async def test_a_malformed_reply_is_reported_as_malformed(self) -> None:
        result = await run(FakeModel("Here is your summary!"))

        assert result.outcome is PassOutcome.MALFORMED

    async def test_an_invented_claim_is_reported_as_refused(self) -> None:
        invented = (
            '{"passages": [{"text": "They are leaving Databricks.", "cites": ["VP Engineering"]}]}'
        )
        result = await run(FakeModel(invented))

        assert result.outcome is PassOutcome.REFUSED

    async def test_a_provider_failure_says_nothing_about_the_prompt(self) -> None:
        result = await run(BrokenModel())

        assert result.outcome is PassOutcome.PROVIDER_FAILED

    async def test_every_failure_names_the_specific_claim(self) -> None:
        """*"The synthesis was refused"* is not something an engineer can act
        on; *"it said Databricks and nothing derived Databricks"* is."""
        invented = (
            '{"passages": [{"text": "They are leaving Databricks.", "cites": ["VP Engineering"]}]}'
        )
        result = await run(FakeModel(invented))

        assert result.detail is not None
        assert "databricks" in result.detail.lower()

    async def test_a_brief_without_narration_is_still_complete(self) -> None:
        """**The asymmetry ADR-0200 rests on**, asserted rather than described."""
        result = await run(FakeModel("not json"), released=True)
        brief = assemble(reasoning=approach().reasoning, fits=(), product=None, narration=None)

        assert not result.succeeded
        assert not brief.is_narrated
        assert "recommendation" in brief.sections()
        assert "roles" in brief.sections()


class TestTheGateIsNotBypassable:
    async def test_measure_runs_an_unreleased_prompt(self) -> None:
        """**Named for what it is.** This is the run that *earns* a release, so
        it cannot itself require one — and a boolean flag on `execute` would
        have made the ungated path reachable from production code."""
        result = await Synthesise(
            prompts=registry(released=False),
            model=FakeModel(GOOD),
            model_name=MODEL,
        ).measure(
            approach(),
            Pass.EXECUTIVE_SUMMARY,
            version=1,
            workspace_id=WORKSPACE,
            correlation_id=uuid4(),
        )

        assert result.outcome is PassOutcome.OK


class TestRendering:
    def test_a_prompt_with_nowhere_to_put_the_graph_is_refused(self) -> None:
        """A prompt with no context placeholder would never show the model the
        graph, making every statement it produced an invention by
        construction."""
        context = CommercialContext(
            source=SynthesisSource(reasoning=approach().reasoning, fits=(), product=None)
        )

        with pytest.raises(Exception, match="placeholder"):
            render("Summarise this account.", context)

    def test_braces_in_the_schema_do_not_break_rendering(self) -> None:
        """**Replacement, not formatting.** `str.format` would read every brace
        in the JSON schema as a placeholder, so the prompt would fail to render
        for a reason having nothing to do with what it says."""
        context = CommercialContext(
            source=SynthesisSource(reasoning=approach().reasoning, fits=(), product=None)
        )

        rendered = render(PROMPT_TEXT, context)

        assert '"passages"' in rendered
        assert "── recommendation ──" in rendered
