"""The evaluation layer — datasets, rubric, harness and the recorded result.

**The harness itself is exercised against a fake here, and that is not a
contradiction.** What is being tested is the *harness*: that it iterates, that a
transport failure abandons a run rather than lowering its score, that one bad
attempt fails a case. What may never be tested against a fake is the *prompt*,
and nothing here claims to.
"""

from __future__ import annotations

from datetime import date
from uuid import UUID, uuid4

import pytest

from modules.ai_platform.public import AITransientError, AIVendor, PromptRegistry, PromptVersion
from modules.sales_engagement.application.ports import ModelReply
from modules.sales_engagement.application.synthesise import PassOutcome, Synthesise
from modules.sales_engagement.domain.brief import Pass
from modules.sales_engagement.domain.context import COMMERCIAL_CONTEXT_PROTOCOL_VERSION
from modules.sales_engagement.domain.release import earns_release, released_for
from modules.sales_engagement.domain.synthesis import Passage, Synthesis
from modules.sales_engagement.evaluation.dataset import DATASET_DIR, DatasetError, load_dataset
from modules.sales_engagement.evaluation.harness import EvaluationAbandonedError, Harness
from modules.sales_engagement.evaluation.report import CaseResult, EvaluationReport
from modules.sales_engagement.evaluation.rubric import RUBRIC_VERSION, coverage, stability
from modules.sales_engagement.infrastructure.prompts import prompts

MODEL = "granite3.3:2b"
PROMPT_TEXT = "Summarise.\n{schema}\n{context}"


class ScriptedModel:
    """Returns each scripted reply in turn, repeating the last."""

    def __init__(self, *replies: str) -> None:
        self._replies = list(replies)
        self.calls = 0

    async def complete(
        self, *, prompt: str, model: str, workspace_id: UUID, correlation_id: UUID
    ) -> ModelReply:
        reply = self._replies[min(self.calls, len(self._replies) - 1)]
        self.calls += 1
        return ModelReply(text=reply, inference_id=uuid4())


class BrokenModel:
    async def complete(
        self, *, prompt: str, model: str, workspace_id: UUID, correlation_id: UUID
    ) -> ModelReply:
        raise AITransientError(AIVendor.OLLAMA, "unreachable")


def cites(*tokens: str) -> str:
    listed = ", ".join(f'"{one}"' for one in tokens)
    return f'{{"passages": [{{"text": "A summary.", "cites": [{listed}]}}]}}'


def registry() -> PromptRegistry:
    return PromptRegistry(
        versions=(
            PromptVersion(
                name=Pass.EXECUTIVE_SUMMARY.value,
                version=1,
                owner="Sales Engagement",
                text=PROMPT_TEXT,
                evaluations=(),
            ),
        )
    )


def harness(model: object) -> Harness:
    return Harness(
        synthesise=Synthesise(
            prompts=registry(),
            model=model,  # type: ignore[arg-type]
            model_name=MODEL,
        ),
        prompts=registry(),
        today=lambda: date(2026, 8, 3),
    )


class TestTheGoldenSetIsAnEngineeringAsset:
    def test_it_loads_and_every_case_is_reachable(self) -> None:
        dataset = load_dataset("approach", 1)

        assert len(dataset) == 10
        assert dataset.reference == "approach@1"

    def test_every_case_declares_load_bearing_conclusions_its_graph_produces(self) -> None:
        """A case demanding a conclusion the model is never shown cannot be
        passed by any output, so it would measure nothing but itself. The loader
        enforces it; this asserts the shipped file satisfies it."""
        for case in load_dataset("approach", 1).cases:
            assert set(one.casefold() for one in case.load_bearing) <= case.source.citable()

    def test_the_set_covers_the_cases_where_the_honest_answer_is_small(self) -> None:
        """**The valuable half.** A rich graph is easy; a fluent model is most
        tempted where the evidence is thin, contradictory, stale or tied."""
        names = {one.name for one in load_dataset("approach", 1).cases}

        assert {
            "nothing-observed-wait",
            "stale-evidence-wait",
            "contradiction-unresolved",
            "product-tie-unknown",
            "single-source-verify",
            "champion-departed-verify",
        } <= names

    def test_an_edited_expectation_without_a_version_bump_fails_to_load(
        self, tmp_path: object
    ) -> None:
        """Revising a case is a version bump and a review, not an edit nobody
        sees — otherwise every historical result claiming this version is
        silently re-scored."""
        import json
        import pathlib

        directory = pathlib.Path(str(tmp_path))
        source = json.loads((DATASET_DIR / "approach@1.json").read_text())
        source["cases"][0]["load_bearing"] = ["recommendation"]
        (directory / "approach@1.json").write_text(json.dumps(source))

        with pytest.raises(DatasetError, match="fingerprint"):
            load_dataset("approach", 1, directory=directory)


class TestTheRubric:
    def test_coverage_is_measured_over_citations(self) -> None:
        """Matching on the declaration rather than the words keeps this from
        rewarding a summary that happens to contain the right string in an
        unrelated sentence."""
        synthesis = Synthesis(
            passages=(Passage(text="Anything.", cites=("recommendation",)),),
            inference_id=uuid4(),
        )

        assert coverage(synthesis, ("recommendation", "vp engineering")) == 0.5

    def test_stability_compares_what_two_runs_chose_to_talk_about(self) -> None:
        """Two good summaries phrase things differently and that is not
        instability; two that disagree about which findings matter have not
        settled."""
        first = Synthesis(
            passages=(Passage(text="One phrasing.", cites=("recommendation",)),),
            inference_id=uuid4(),
        )
        same = Synthesis(
            passages=(Passage(text="A quite different phrasing.", cites=("recommendation",)),),
            inference_id=uuid4(),
        )
        other = Synthesis(
            passages=(Passage(text="One phrasing.", cites=("vp engineering",)),),
            inference_id=uuid4(),
        )

        assert stability(first, same) == 1.0
        assert stability(first, other) == 0.0


class TestTheHarness:
    async def test_a_clean_run_over_the_golden_set_produces_a_report(self) -> None:
        dataset = load_dataset("approach", 1)
        model = ScriptedModel(cites("recommendation"))

        report = await harness(model).evaluate(
            pass_=Pass.EXECUTIVE_SUMMARY,
            version=1,
            model=MODEL,
            dataset=dataset,
            runs_per_case=1,
        )

        assert report.sample_size == 10
        assert report.refusals == 0
        assert report.rubric_version == RUBRIC_VERSION

    async def test_it_runs_each_case_twice_by_default(self) -> None:
        """**Stability is the dimension this architecture guarantees most
        cheaply** — the input is a closed set, so two runs differ only by the
        model."""
        dataset = load_dataset("approach", 1)
        model = ScriptedModel(cites("recommendation"))

        report = await harness(model).evaluate(
            pass_=Pass.EXECUTIVE_SUMMARY, version=1, model=MODEL, dataset=dataset
        )

        assert model.calls == 20
        assert report.stability == 1.0

    async def test_one_bad_attempt_fails_the_case(self) -> None:
        """**A pass that fabricated on one of two attempts has fabricated.**
        Averaging would let a prompt earn a release on the run that happened to
        behave."""
        dataset = load_dataset("approach", 1)
        invented = '{"passages": [{"text": "They use Databricks.", "cites": ["recommendation"]}]}'
        model = ScriptedModel(cites("recommendation"), invented)

        report = await harness(model).evaluate(
            pass_=Pass.EXECUTIVE_SUMMARY, version=1, model=MODEL, dataset=dataset
        )

        assert report.refusals == 10

    async def test_a_transport_failure_abandons_the_run(self) -> None:
        """A vendor being down says nothing about a prompt. A partial average
        recorded as a result is how a release gets granted on the successes."""
        dataset = load_dataset("approach", 1)

        with pytest.raises(EvaluationAbandonedError, match="measured nothing"):
            await harness(BrokenModel()).evaluate(
                pass_=Pass.EXECUTIVE_SUMMARY, version=1, model=MODEL, dataset=dataset
            )


class TestTheReport:
    def report(self, *, refusals: int = 0, coverage_: float = 0.9) -> EvaluationReport:
        results = tuple(
            CaseResult(
                case=f"case-{n}",
                outcome=PassOutcome.REFUSED if n < refusals else PassOutcome.OK,
                coverage=0.0 if n < refusals else coverage_,
            )
            for n in range(10)
        )
        return EvaluationReport(
            prompt_name="executive_summary",
            prompt_version=1,
            prompt_fingerprint="a" * 64,
            model=MODEL,
            dataset_name="approach",
            dataset_version=1,
            dataset_fingerprint="b" * 64,
            rubric_version=RUBRIC_VERSION,
            evaluated_on=date(2026, 8, 3),
            results=results,
        )

    def test_the_durable_record_names_the_commercial_context_protocol(self) -> None:
        """**Two fields carry this module's meaning**, and the manifest says so:
        `grounding_failures` counts syntheses the fence refused, and the protocol
        is the Commercial Context Protocol."""
        evaluation = self.report(refusals=3).as_evaluation()

        assert evaluation.grounding_failures == 3
        assert evaluation.rendering_protocol_version == COMMERCIAL_CONTEXT_PROTOCOL_VERSION

    def test_a_clean_report_earns_a_release(self) -> None:
        assert earns_release(self.report().as_evaluation())

    def test_a_report_with_a_refusal_does_not(self) -> None:
        assert not earns_release(self.report(refusals=1).as_evaluation())

    def test_unmeasured_stability_reads_as_unmeasured(self) -> None:
        """**Absent rather than 1.0.** A stability figure nobody measured must
        not read as perfect stability."""
        assert self.report().stability is None
        assert "not measured" in self.report().render()

    def test_the_report_states_its_experimental_conditions(self) -> None:
        """A run that cannot name its conditions is not a measurement, it is an
        anecdote."""
        rendered = self.report().render()

        for condition in ("prompt", "model", "dataset", "rubric", "context"):
            assert condition in rendered


class TestTheShippedArtifact:
    def test_the_prompt_loads_and_matches_its_recorded_fingerprint(self) -> None:
        """A prompt whose text has drifted from its hash makes every result
        claiming that version unreproducible, and there is no way to notice
        after the fact."""
        prompt = prompts().get(Pass.EXECUTIVE_SUMMARY.value, 1)

        assert prompt.owner == "Sales Engagement"
        assert "{context}" in prompt.text

    def test_it_ships_measured_and_unreleased(self) -> None:
        """**Release is earned, never declared.** The artifact has been measured
        against a real model and did not pass, so no pairing is earned — and the
        failing run stays on record, because a manifest holding only passes shows
        a prompt with a clean history and no way to see it was found wanting.
        """
        prompt = prompts().get(Pass.EXECUTIVE_SUMMARY.value, 1)

        assert prompt.evaluations, "the shipped manifest records no measurement at all"
        assert not any(released_for(prompt, one.model) for one in prompt.evaluations)

    def test_every_recorded_measurement_names_the_commercial_context_protocol(self) -> None:
        """A measurement that cannot say what the model was shown cannot be
        reproduced — and for this module that condition is never the AI
        Platform's evidence rendering protocol."""
        prompt = prompts().get(Pass.EXECUTIVE_SUMMARY.value, 1)

        for one in prompt.evaluations:
            assert one.rendering_protocol_version == COMMERCIAL_CONTEXT_PROTOCOL_VERSION

    def test_every_pass_the_enum_declares_can_be_asked_for(self) -> None:
        """A `Pass` with no artifact is refused by name rather than silently
        skipped — the brief simply renders without it."""
        registry_ = prompts()
        named = {one.name for one in registry_.versions}

        assert Pass.EXECUTIVE_SUMMARY.value in named
