"""The Prompt Rendering Protocol, and what binding a release to it means.

Four experimental inputs decide what an evaluation measured: the prompt text,
the rendered evidence, the model, and the dataset. Until M9.5 three were bound
to every measurement and the fourth — **the bytes the model actually read** —
was not recorded anywhere, so a change to it altered the experiment without
altering any artifact describing it.

These tests assert the fourth input now behaves like the other three.

**Nothing here calls a model**, and nothing here changes what any prompt
renders: Step B is deliberately behaviour-neutral, so the specimen below pins
the form that has shipped since M8, defect included.
"""

from __future__ import annotations

from dataclasses import replace
from datetime import UTC, date, datetime
from pathlib import Path
from uuid import UUID

import pytest

from modules.ai_platform.application.render import render
from modules.ai_platform.domain.evidence import EvidenceFact, EvidenceRef, EvidenceSet
from modules.ai_platform.domain.prompt import (
    Evaluation,
    PromptError,
    PromptNotReleasableError,
    PromptVersion,
)
from modules.ai_platform.domain.rendering import PROMPT_RENDERING_PROTOCOL_VERSION
from modules.ai_platform.infrastructure.prompt_loader import load_prompt_registry

MODEL = "llama3.1:8b"
WORKSPACE = UUID("00000000-0000-0000-0000-0000000000aa")
NOW = datetime(2026, 7, 31, tzinfo=UTC)

#: Every manifest the repository ships. Named rather than discovered, so a new
#: module's prompts are added here deliberately instead of silently escaping
#: the assertions below.
MANIFEST_DIRS = (
    "modules/ai_platform/prompts",
    "modules/ai_reasoning_engine/prompts",
    "modules/ai_research_engine/prompts",
)


def _evaluation(**overrides: object) -> Evaluation:
    defaults: dict[str, object] = {
        "model": MODEL,
        "dataset": "golden",
        "dataset_version": 1,
        "rubric_version": 1,
        "evaluated_on": date(2026, 7, 31),
        "sample_size": 2,
        "grounding_failures": 0,
        "schema_failures": 0,
        "coverage": 1.0,
        "rendering_protocol_version": PROMPT_RENDERING_PROTOCOL_VERSION,
    }
    return Evaluation(**{**defaults, **overrides})  # type: ignore[arg-type]


def _prompt(*evaluations: Evaluation) -> PromptVersion:
    return PromptVersion(
        name="specimen",
        version=1,
        owner="ai-platform@signora",
        text="A prompt. {facts}",
        evaluations=evaluations,
    )


class TestEveryMeasurementNamesItsProtocol:
    def test_an_evaluation_cannot_be_built_without_one(self) -> None:
        """**No default, and that is the point.** A default would let a
        measurement whose conditions nobody recorded present itself as valid —
        which is precisely the hidden input this field removes."""
        with pytest.raises(TypeError, match="rendering_protocol_version"):
            Evaluation(  # type: ignore[call-arg]
                model=MODEL,
                dataset="golden",
                dataset_version=1,
                rubric_version=1,
                evaluated_on=date(2026, 7, 31),
                sample_size=2,
                grounding_failures=0,
                schema_failures=0,
                coverage=1.0,
            )

    @pytest.mark.parametrize("version", [0, -1])
    def test_a_protocol_version_below_one_is_refused(self, version: int) -> None:
        with pytest.raises(PromptError, match="rendering protocol"):
            _evaluation(rendering_protocol_version=version)

    def test_a_manifest_entry_without_one_is_rejected(self, tmp_path: Path) -> None:
        """A repository that could load an unversioned measurement would let one
        earn a release, which is the failure this whole step exists to close."""
        (tmp_path / "specimen@1.md").write_text("A prompt. {facts}")
        prompt = _prompt()
        (tmp_path / "manifest.json").write_text(
            f"""{{"prompts": [{{"name": "specimen", "version": 1,
            "owner": "ai-platform@signora", "fingerprint": "{prompt.fingerprint}",
            "evaluations": [{{"model": "{MODEL}", "dataset": "golden", "dataset_version": 1,
            "rubric_version": 1, "evaluated_on": "2026-07-31", "sample_size": 2,
            "grounding_failures": 0, "schema_failures": 0, "coverage": 1.0,
            "retries": 0}}]}}]}}"""
        )

        load_prompt_registry.cache_clear()
        with pytest.raises(PromptError, match="rendering_protocol_version"):
            load_prompt_registry(tmp_path)
        load_prompt_registry.cache_clear()


class TestAReleaseIsBoundToTheProtocolItWasMeasuredUnder:
    def test_a_current_measurement_earns_its_release(self) -> None:
        prompt = _prompt(_evaluation())

        assert prompt.is_released
        prompt.require_model(MODEL)
        prompt.require(model=MODEL, dataset="golden")

    def test_a_measurement_from_another_protocol_earns_nothing(self) -> None:
        prompt = _prompt(_evaluation(rendering_protocol_version=99))

        assert not prompt.is_released
        assert not prompt.is_released_for(MODEL)
        assert not prompt.supports(model=MODEL, dataset="golden")

    def test_the_run_it_describes_is_still_recorded_as_having_passed(self) -> None:
        """**The distinction the whole design rests on.** A protocol change does
        not retroactively make a clean run a failing one — that is not what
        happened, and a manifest that said so would lie about its own history.
        The measurement stays true; it stops *applying*."""
        stale = _evaluation(rendering_protocol_version=99)

        assert stale.passed
        assert not stale.measured_under_current_protocol
        assert not stale.earns_release

    def test_the_refusal_says_re_evaluate_rather_than_re_author(self) -> None:
        """Told only *"has not passed for this model"*, an engineer re-writes a
        prompt that was already correct. The two failures have opposite
        remedies, so they must not share a message."""
        prompt = _prompt(_evaluation(rendering_protocol_version=99))

        with pytest.raises(PromptNotReleasableError, match="protocol") as refusal:
            prompt.require_model(MODEL)

        assert "do not re-author" in str(refusal.value)

    def test_a_model_never_measured_still_reports_that_instead(self) -> None:
        """The stale-protocol message must not swallow the ordinary one — a
        model nothing ever evaluated is a different problem."""
        prompt = _prompt(_evaluation())

        with pytest.raises(PromptNotReleasableError, match="has not passed evaluation"):
            prompt.require_model("some-model-nobody-ran")


class TestTwoProtocolsAreTwoMeasurements:
    def test_the_same_run_under_a_new_protocol_is_an_addition(self) -> None:
        """**Without this, Step C could not be recorded.** Re-evaluating on the
        same model, dataset and day is exactly what a protocol change requires,
        and treating it as a duplicate would refuse the one run that proves the
        change was safe."""
        under_one = _evaluation(rendering_protocol_version=1)
        under_two = _evaluation(rendering_protocol_version=2)

        prompt = _prompt(under_one, under_two)

        assert len(prompt.evaluations) == 2

    def test_a_genuine_duplicate_is_still_refused(self) -> None:
        evaluation = _evaluation()

        with pytest.raises(PromptError, match="same evaluation twice"):
            _prompt(evaluation, replace(evaluation, coverage=0.9))


class TestTheProtocolVersionIdentifiesAForm:
    def test_protocol_1_renders_exactly_this(self) -> None:
        """**The specimen that gives the version a referent.**

        A bare integer nobody can check is worse than none: it makes bumping a
        matter of discipline, and discipline is what already failed here. This
        pins what protocol 1 *is*, so changing what a model sees without
        bumping the version fails a test rather than passing silently — the
        same guarantee `PINNED_FINGERPRINTS` gives prompt text.

        The bracket below is ADR-0031's defect, pinned deliberately. Step B
        changes no behaviour; Step C changes this specimen and the version
        together, in one reviewable diff.
        """
        prompt = _prompt()
        evidence = EvidenceSet(
            workspace_id=WORKSPACE,
            facts=(
                EvidenceFact(
                    ref=EvidenceRef(
                        kind="signal_contribution",
                        id=UUID("3f40f486-98e5-5ff7-812d-feca5aa54af7"),
                    ),
                    workspace_id=WORKSPACE,
                    summary="A retired system suggests displacement.",
                    attributes=(("contribution", 30), ("relevance", "primary")),
                ),
            ),
            assembled_at=NOW,
        )

        assert PROMPT_RENDERING_PROTOCOL_VERSION == 1
        assert render(prompt, evidence) == (
            "A prompt. "
            "[signal_contribution:3f40f486-98e5-5ff7-812d-feca5aa54af7] "
            "A retired system suggests displacement.\n"
            "  contribution: 30\n"
            "  relevance: primary"
        )


class TestEveryShippedReleaseSurvivesThisStep:
    """Step B must change no outcome. These read the real manifests."""

    @pytest.mark.parametrize("directory", MANIFEST_DIRS)
    def test_every_recorded_measurement_names_protocol_1(self, directory: str) -> None:
        load_prompt_registry.cache_clear()
        registry = load_prompt_registry(Path(__file__).resolve().parents[2] / directory)

        evaluations = [e for version in registry.versions for e in version.evaluations]

        assert evaluations, f"{directory} records no measurements at all."
        assert all(e.rendering_protocol_version == 1 for e in evaluations)
        assert all(e.measured_under_current_protocol for e in evaluations)

    def test_the_three_prompts_that_were_released_still_are(self) -> None:
        """Named individually rather than derived, so this states what is true
        today and fails loudly in Step C when it stops being true."""
        load_prompt_registry.cache_clear()
        root = Path(__file__).resolve().parents[2]

        released = {
            ("modules/ai_platform/prompts", "explanation_narration", "llama3.1:8b"),
            ("modules/ai_reasoning_engine/prompts", "reasoning", "granite3.3:2b"),
            ("modules/ai_research_engine/prompts", "research_planning", "llama3.1:8b"),
        }
        for directory, name, model in released:
            prompt = load_prompt_registry(root / directory).get(name, 1)
            assert prompt.is_released, f"{name}@1 lost its release."
            prompt.require_model(model)
