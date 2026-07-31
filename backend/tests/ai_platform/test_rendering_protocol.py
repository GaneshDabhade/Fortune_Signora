"""The Prompt Rendering Protocol, and what binding a release to it means.

Four experimental inputs decide what an evaluation measured: the prompt text,
the rendered evidence, the model, and the dataset. Until M9.5 three were bound
to every measurement and the fourth — **the bytes the model actually read** —
was not recorded anywhere, so a change to it altered the experiment without
altering any artifact describing it.

These tests assert the fourth input now behaves like the other three.

**Nothing here calls a model.** Step B named the input and bound releases to it;
Step C moved the form into the protocol and bumped it to 2, which withdrew every
release earned under protocol 1 — by derivation, with no manifest edited and no
migration run. Both halves are asserted below.
"""

from __future__ import annotations

from dataclasses import replace
from datetime import UTC, date, datetime
from pathlib import Path
from uuid import UUID

import pytest

from modules.ai_platform.application.render import render
from modules.ai_platform.domain.evidence import (
    EvidenceError,
    EvidenceFact,
    EvidenceRef,
    EvidenceSet,
)
from modules.ai_platform.domain.prompt import (
    Evaluation,
    PromptError,
    PromptNotReleasableError,
    PromptVersion,
)
from modules.ai_platform.domain.rendering import PROMPT_RENDERING_PROTOCOL_VERSION, cite
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


def _specimen() -> EvidenceSet:
    return EvidenceSet(
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


class TestTheProtocolVersionIdentifiesAForm:
    def test_protocol_2_renders_exactly_this(self) -> None:
        """**The specimen that gives the version a referent.**

        A bare integer nobody can check is worse than none: it makes bumping a
        matter of discipline, and discipline is what already failed here. This
        pins what protocol 2 *is*, so changing what a model sees without
        bumping the version fails a test rather than passing silently — the
        same guarantee `PINNED_FINGERPRINTS` gives prompt text.

        Protocol 1 wrapped the citation in brackets that were not part of it.
        Here the token stands alone, bounded by the start of the line and by an
        em dash — a character `kind:uuid` cannot contain.
        """
        assert PROMPT_RENDERING_PROTOCOL_VERSION == 2
        assert render(_prompt(), _specimen()) == (
            "A prompt. "
            "signal_contribution:3f40f486-98e5-5ff7-812d-feca5aa54af7 — "
            "A retired system suggests displacement.\n"
            "  contribution: 30\n"
            "  relevance: primary"
        )

    def test_a_hyphen_would_not_have_done(self) -> None:
        """The delimiter must be a character the token cannot contain, and a
        UUID is full of hyphens. Asserted rather than assumed, because the
        reason for the em dash is not visible from the character itself."""
        rendered = render(_prompt(), _specimen())

        assert " — " in rendered
        assert "-" in cite(next(iter(_specimen())).ref)


class TestWhatIsRenderedIsWhatTheParserAccepts:
    """**ADR-0031 Option D, asserted where it binds.**

    `test_evidence.py` already asserts `parse(ref.token) == ref` — the round
    trip over the *token*. Nothing asserted it over what a model is actually
    shown, and that gap is precisely where the defect lived for two milestones.
    """

    def test_every_citation_in_a_rendered_prompt_parses_back(self) -> None:
        evidence = _specimen()
        body = render(_prompt(), evidence).removeprefix("A prompt. ")

        for block, fact in zip(body.split("\n\n"), evidence, strict=True):
            citation = block.splitlines()[0].split(" ")[0]

            assert EvidenceRef.parse(citation) == fact.ref

    def test_the_rendered_citation_is_the_token_and_nothing_more(self) -> None:
        """A renderer that decorated the token would still round-trip if the
        decoration happened to be strippable. This asserts the stronger thing:
        **no decoration exists.**"""
        fact = next(iter(_specimen()))
        body = render(_prompt(), _specimen()).removeprefix("A prompt. ")

        assert body.startswith(f"{fact.ref.token} ")
        assert "[" not in body and "]" not in body

    def test_the_parser_still_refuses_what_it_always_refused(self) -> None:
        """**Step C did not make the parser tolerant, and must not have.**
        The fix is entirely on the producing side; a parser that repaired its
        input would make the failure rate unmeasurable."""
        ref = next(iter(_specimen())).ref

        for malformed in (f"[{ref.token}]", str(ref.id), f"{ref.token}:relevance=primary"):
            with pytest.raises(EvidenceError):
                EvidenceRef.parse(malformed)


class TestTheProtocolBumpWithdrewEveryStaleRelease:
    """**The point of the whole design, demonstrated against the real manifests.**

    Nothing was edited to make this true: no manifest entry was removed, no
    release was withdrawn by hand, no migration ran. One constant changed, and
    three releases stopped being earned by derivation.
    """

    @pytest.mark.parametrize("directory", MANIFEST_DIRS)
    def test_no_protocol_1_measurement_was_touched_or_still_applies(self, directory: str) -> None:
        """Every protocol-1 record is still there, and none of them earns
        anything. Scoped to protocol 1 rather than to *all* evaluations,
        because Step D began adding protocol-2 measurements alongside them —
        which is the point: history accumulates, it is not replaced."""
        load_prompt_registry.cache_clear()
        registry = load_prompt_registry(Path(__file__).resolve().parents[2] / directory)

        legacy = [
            e
            for version in registry.versions
            for e in version.evaluations
            if e.rendering_protocol_version == 1
        ]

        assert legacy, f"{directory} lost the protocol-1 measurements it recorded."
        assert not any(e.measured_under_current_protocol for e in legacy)
        assert not any(e.earns_release for e in legacy)

    @pytest.mark.parametrize(
        ("directory", "name", "model"),
        [
            # `explanation_narration@1` is deliberately absent: M9.5 Step F
            # re-measured it under protocol 2 and it earned a release again, so
            # it is no longer an example of a withdrawn one. Its full sequence —
            # unreleased, released, withdrawn, released — is asserted in
            # `test_prompts.py`, which is where that story belongs.
            ("modules/ai_reasoning_engine/prompts", "reasoning", "granite3.3:2b"),
            ("modules/ai_research_engine/prompts", "research_planning", "llama3.1:8b"),
        ],
    )
    def test_a_prompt_that_passed_no_longer_earns_a_release(
        self, directory: str, name: str, model: str
    ) -> None:
        load_prompt_registry.cache_clear()
        prompt = load_prompt_registry(Path(__file__).resolve().parents[2] / directory).get(name, 1)

        # The measurement is intact: it passed, and it says so.
        (earned,) = [e for e in prompt.evaluations if e.passed and e.model == model]
        assert earned.grounding_failures == 0
        assert earned.rendering_protocol_version == 1

        # And it no longer applies.
        assert not prompt.is_released
        with pytest.raises(PromptNotReleasableError, match="protocol") as refusal:
            prompt.require_model(model)

        assert "do not re-author" in str(refusal.value)
