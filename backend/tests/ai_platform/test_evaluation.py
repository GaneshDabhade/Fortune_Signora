"""The harness, its dataset, its rubric, and the release it produces.

Every test here is **offline**. That is not a convenience — it is the two-tier
split holding: the harness's *mechanics* are deterministic engineering
behaviour and are verified against fakes, while the thing the harness measures
is probabilistic and is verified by running it (`make eval`). Testing the
mechanics against a real model would make this file slow and flaky and would
still not measure the model.
"""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Any
from uuid import UUID, uuid4

import pytest

from modules.ai_platform.application.infer import Infer, InferencePolicy
from modules.ai_platform.domain.narration import Narration
from modules.ai_platform.domain.prompt import (
    MINIMUM_COVERAGE,
    Evaluation,
    PromptNotReleasableError,
    PromptRegistry,
)
from modules.ai_platform.domain.provider import AIProviderRegistry, AITransientError, AIVendor
from modules.ai_platform.domain.record import InferenceOutcome
from modules.ai_platform.evaluation.dataset import (
    DatasetError,
    GoldenCase,
    GoldenDataset,
    fingerprint_of,
    load_dataset,
)
from modules.ai_platform.evaluation.harness import EvaluationAbandonedError, Harness
from modules.ai_platform.evaluation.release import ReleaseError, record
from modules.ai_platform.evaluation.report import CaseResult, EvaluationReport
from modules.ai_platform.evaluation.rubric import RUBRIC_VERSION, coverage, criteria
from modules.ai_platform.infrastructure.prompt_loader import load_prompt_registry
from tests.ai_platform.fakes import FakeAdapter
from tests.ai_platform.test_infer import FakeRecorder, a_prompt

MODEL = "fake-model"
TODAY = date(2026, 7, 30)
DATASET_PATH = (
    Path(__file__).resolve().parents[2]
    / "modules"
    / "ai_platform"
    / "evaluation"
    / "datasets"
    / "explanation_narration@1.json"
)


# --------------------------------------------------------------------------
# The shipped dataset


class TestTheShippedGoldenSet:
    def test_it_loads_and_matches_its_own_fingerprint(self) -> None:
        dataset = load_dataset("explanation_narration", 1)
        assert len(dataset) >= 1
        assert dataset.seeded_from.startswith("signora_platform/simulation/scenarios")

    def test_every_case_declares_facts_its_own_evidence_contains(self) -> None:
        """Guaranteed by ``GoldenCase``; asserted here against the real file,
        because a case demanding a fact the model is never shown cannot be
        passed by any output and would fail the prompt forever."""
        dataset = load_dataset("explanation_narration", 1)
        for case in dataset.cases:
            resolvable = {fact.ref.token for fact in case.evidence}
            assert set(case.load_bearing) <= resolvable

    def test_an_edited_expectation_fails_to_load(self, tmp_path: Path) -> None:
        """The property that makes the dataset an engineering asset: history
        is never modified silently. Revising a case is a version bump."""
        document = json.loads(DATASET_PATH.read_text())
        document["cases"][0]["load_bearing"] = document["cases"][0]["load_bearing"][:1]
        (tmp_path / "explanation_narration@1.json").write_text(json.dumps(document))

        with pytest.raises(DatasetError, match="fingerprint"):
            load_dataset("explanation_narration", 1, directory=tmp_path)

    def test_a_dataset_that_misnames_itself_is_refused(self, tmp_path: Path) -> None:
        document = json.loads(DATASET_PATH.read_text())
        document["version"] = 2
        (tmp_path / "explanation_narration@1.json").write_text(json.dumps(document))

        with pytest.raises(DatasetError, match="declares itself"):
            load_dataset("explanation_narration", 1, directory=tmp_path)

    def test_reformatting_is_not_an_edit(self) -> None:
        """The fingerprint covers the expectations, not the whitespace around
        them — otherwise every reformat would read as a revision and the
        signal would be ignored within a month."""
        cases = json.loads(DATASET_PATH.read_text())["cases"]
        reordered = json.loads(json.dumps(cases, indent=8))
        assert fingerprint_of(cases) == fingerprint_of(reordered)

    def test_the_note_is_not_part_of_what_the_dataset_asserts(self) -> None:
        document = json.loads(DATASET_PATH.read_text())
        before = fingerprint_of(document["cases"])
        document["_comment"] = "changed"
        assert fingerprint_of(document["cases"]) == before

    def test_a_missing_dataset_is_refused_rather_than_defaulted(self, tmp_path: Path) -> None:
        with pytest.raises(DatasetError, match="no golden dataset"):
            load_dataset("explanation_narration", 99, directory=tmp_path)


class TestACaseMustBeAbleToFail:
    def test_a_case_with_no_load_bearing_facts_is_refused(self) -> None:
        """Coverage over nothing is vacuously perfect, so such a case can only
        ever confirm what it assumes."""
        with pytest.raises(DatasetError, match="no load-bearing"):
            GoldenCase(name="empty", evidence=_evidence(), load_bearing=())

    def test_a_case_demanding_absent_evidence_is_refused(self) -> None:
        with pytest.raises(DatasetError, match="does not contain"):
            GoldenCase(name="impossible", evidence=_evidence(), load_bearing=("ghost:x",))

    def test_a_dataset_with_no_cases_is_refused(self) -> None:
        with pytest.raises(DatasetError, match="no cases"):
            GoldenDataset(name="d", version=1, fingerprint="x", seeded_from="y", cases=[])


# --------------------------------------------------------------------------
# The rubric


class TestTheRubricMeasuresAndTheDomainJudges:
    def test_coverage_is_the_share_of_load_bearing_facts_cited(self) -> None:
        output = _narration([(FUNDING,), (HIRING,)])
        assert coverage(output, (FUNDING, HIRING)) == 1.0
        assert coverage(output, (FUNDING, HIRING, "other:1")) == pytest.approx(2 / 3)

    def test_citing_facts_outside_the_load_bearing_set_earns_nothing(self) -> None:
        """Coverage measures whether the *argument* was carried, not how many
        citations were produced. A narrative that cited everything peripheral
        and nothing central must score zero."""
        assert coverage(_narration([("other:1",)]), (FUNDING,)) == 0.0

    def test_the_published_criteria_restate_no_number_of_their_own(self) -> None:
        """If this function ever contains a literal, that literal is a second
        representation of a release rule."""
        rendered = "\n".join(criteria())
        assert str(MINIMUM_COVERAGE) in rendered
        assert "coverage >=" in rendered

    @pytest.mark.parametrize(
        ("kwargs", "expected"),
        [
            ({}, True),
            ({"grounding_failures": 1}, False),
            ({"schema_failures": 1}, False),
            ({"coverage": MINIMUM_COVERAGE - 0.01}, False),
            ({"coverage": MINIMUM_COVERAGE}, True),
        ],
    )
    def test_release_is_derived_from_the_measurement(
        self, kwargs: dict[str, Any], expected: bool
    ) -> None:
        assert _evaluation(**kwargs).passed is expected

    def test_a_measurement_over_no_samples_is_refused(self) -> None:
        with pytest.raises(Exception, match="measured nothing"):
            _evaluation(sample_size=0)

    def test_a_measurement_must_name_its_dataset_revision_and_rubric(self) -> None:
        with pytest.raises(Exception, match="dataset revision"):
            _evaluation(dataset_version=0)


# --------------------------------------------------------------------------
# The harness


class TestTheHarness:
    async def test_a_clean_run_earns_the_release(self) -> None:
        harness, _ = _harness(content=_json([[FUNDING]]))
        report = await harness.evaluate(
            prompt_name="narration",
            prompt_version=1,
            model=MODEL,
            dataset=_dataset(),
            output_type=Narration,
        )

        assert report.grounding_failures == 0
        assert report.schema_failures == 0
        assert report.coverage == 1.0
        assert report.as_evaluation().passed

    async def test_the_report_names_everything_needed_to_repeat_the_run(self) -> None:
        """Signora's view of an evaluation is deterministic even though the
        model is not: the output cannot be re-derived, but everything about
        the run can be."""
        harness, _ = _harness(content=_json([[FUNDING]]))
        report = await harness.evaluate(
            prompt_name="narration",
            prompt_version=1,
            model=MODEL,
            dataset=_dataset(),
            output_type=Narration,
        )

        assert report.prompt_fingerprint == a_prompt().fingerprint
        assert (report.dataset_name, report.dataset_version) == ("golden", 1)
        assert report.dataset_fingerprint
        assert report.rubric_version == RUBRIC_VERSION
        assert report.evaluated_on == TODAY
        assert report.model == MODEL

    async def test_an_unreleased_prompt_can_still_be_measured(self) -> None:
        """The whole point. A prompt is usable once it has passed evaluation
        for a model, and evaluating it requires calling it — so the harness
        takes the one named exception to the release rule."""
        harness, _ = _harness(content=_json([[FUNDING]]), prompt=a_prompt(released_for=None))
        report = await harness.evaluate(
            prompt_name="narration",
            prompt_version=1,
            model=MODEL,
            dataset=_dataset(),
            output_type=Narration,
        )
        assert report.sample_size == 1

    async def test_the_request_path_still_refuses_that_prompt(self) -> None:
        """The control that keeps the exception an exception."""
        harness, infer = _harness(content=_json([[FUNDING]]), prompt=a_prompt(released_for=None))
        with pytest.raises(PromptNotReleasableError):
            await infer.execute(_request(), Narration)

    async def test_an_ungrounded_case_fails_rather_than_scoring_low(self) -> None:
        """Grounding is deterministic, so a failure is a defect. It must not
        be averaged away by a good case beside it."""
        harness, _ = _harness(content=_json([[FUNDING]], text="They grew 40%."))
        report = await harness.evaluate(
            prompt_name="narration",
            prompt_version=1,
            model=MODEL,
            dataset=_dataset(),
            output_type=Narration,
        )

        assert report.grounding_failures == 1
        assert not report.as_evaluation().passed
        assert report.results[0].detail, "a failure that does not say how leaves nothing to fix"

    async def test_a_malformed_case_is_counted_separately_from_an_ungrounded_one(self) -> None:
        """A model that cannot hold a structure and a model that invents facts
        are different problems with different fixes."""
        harness, _ = _harness(content="I'm afraid I can't help with that.")
        report = await harness.evaluate(
            prompt_name="narration",
            prompt_version=1,
            model=MODEL,
            dataset=_dataset(),
            output_type=Narration,
        )

        assert (report.schema_failures, report.grounding_failures) == (1, 0)

    async def test_a_transport_failure_abandons_the_run_rather_than_scoring_it(self) -> None:
        """A vendor being down says nothing about a prompt. A partial average
        recorded as a result would grant a release on the cases that happened
        to succeed."""
        harness, _ = _harness(error=AITransientError(AIVendor.OLLAMA, "down"))
        with pytest.raises(EvaluationAbandonedError, match="never reached a verdict"):
            await harness.evaluate(
                prompt_name="narration",
                prompt_version=1,
                model=MODEL,
                dataset=_dataset(),
                output_type=Narration,
            )

    async def test_every_case_is_traceable_and_traceable_identically_across_runs(self) -> None:
        harness, infer = _harness(content=_json([[FUNDING]]))
        recorder = infer._recorder  # noqa: SLF001 -- asserting what was recorded
        for _ in range(2):
            await harness.evaluate(
                prompt_name="narration",
                prompt_version=1,
                model=MODEL,
                dataset=_dataset(),
                output_type=Narration,
            )

        assert isinstance(recorder, FakeRecorder)
        first, second = recorder.written
        assert first.correlation_id == second.correlation_id, (
            "two runs of the same case must trace under the same id, or they cannot be "
            "diffed row by row"
        )


# --------------------------------------------------------------------------
# Recording the release


class TestRecordingTheMeasurement:
    def test_a_run_is_appended_to_the_manifest(self, tmp_path: Path) -> None:
        """**Appended**, so the assertion is relative rather than absolute.

        Written first as `len(entries) == 1`, which passed only while the
        shipped manifest held no evaluations — it broke the moment a real run
        recorded one. Counting from the starting point is what the word
        *append* actually claims.
        """
        manifest = _manifest_copy(tmp_path)
        before = len(json.loads(manifest.read_text())["prompts"][0]["evaluations"])

        written = record(_report(), manifest=manifest)

        entries = json.loads(manifest.read_text())["prompts"][0]["evaluations"]
        assert len(entries) == before + 1
        assert entries[-1]["rubric_version"] == RUBRIC_VERSION
        assert entries[-1]["dataset_version"] == 1
        assert written.passed

    def test_the_written_manifest_still_loads(self, tmp_path: Path) -> None:
        """A file that saves cleanly and refuses to start is worse than one
        that refuses to save."""
        manifest = _manifest_copy(tmp_path)
        record(_report(), manifest=manifest)
        load_prompt_registry.cache_clear()

        registry = load_prompt_registry(manifest.parent)
        assert registry.get("explanation_narration", 1).is_released_for(MODEL)

    def test_a_failing_run_is_recorded_too(self, tmp_path: Path) -> None:
        """A manifest holding only passes shows a prompt with a clean history
        and no sign it was measured and found wanting."""
        manifest = _manifest_copy(tmp_path)
        written = record(_report(outcome=InferenceOutcome.UNGROUNDED), manifest=manifest)

        assert not written.passed
        load_prompt_registry.cache_clear()
        registry = load_prompt_registry(manifest.parent)
        assert not registry.get("explanation_narration", 1).is_released_for(MODEL)

    def test_the_same_measurement_twice_is_refused_rather_than_overwritten(
        self, tmp_path: Path
    ) -> None:
        """Evaluations accumulate. Overwriting one is how a result nobody
        liked stops existing."""
        manifest = _manifest_copy(tmp_path)
        record(_report(), manifest=manifest)
        with pytest.raises(ReleaseError, match="accumulate"):
            record(_report(), manifest=manifest)

    def test_a_run_measuring_different_text_is_refused(self, tmp_path: Path) -> None:
        manifest = _manifest_copy(tmp_path)
        with pytest.raises(ReleaseError, match="no longer there"):
            record(_report(fingerprint="0" * 64), manifest=manifest)


# --------------------------------------------------------------------------
# helpers

FUNDING = "business_event:00000000-0000-0000-0000-000000000001"
HIRING = "business_event:00000000-0000-0000-0000-000000000002"


def _evidence() -> Any:
    from modules.ai_platform.domain.evidence import EvidenceSetBuilder

    builder = EvidenceSetBuilder(UUID(int=42))
    builder.add(
        kind="business_event",
        id=UUID(int=1),
        summary="Raised 24M USD in a Series B round",
        attributes={"amount": "24000000"},
    )
    from datetime import UTC, datetime

    return builder.build(assembled_at=datetime(2026, 7, 30, tzinfo=UTC))


def _dataset() -> GoldenDataset:
    return GoldenDataset(
        name="golden",
        version=1,
        fingerprint="f" * 64,
        seeded_from="a test",
        cases=[GoldenCase(name="one", evidence=_evidence(), load_bearing=(FUNDING,))],
    )


def _narration(citations: list[tuple[str, ...]]) -> Narration:
    from modules.ai_platform.domain.grounding import GroundedStatement

    return Narration(
        points=tuple(
            GroundedStatement(text="They raised 24M USD.", evidence=refs) for refs in citations
        )
    )


def _json(citations: list[list[str]], *, text: str = "They raised 24M USD.") -> str:
    return json.dumps({"points": [{"text": text, "evidence": refs} for refs in citations]})


def _harness(
    *, content: str = "", error: Exception | None = None, prompt: Any = None
) -> tuple[Harness, Infer]:
    adapter = FakeAdapter(models=frozenset({MODEL}), content=content, error=error)
    providers = AIProviderRegistry()
    providers.register(adapter)
    prompts = PromptRegistry(versions=(prompt or a_prompt(),))
    infer = Infer(
        providers=providers,
        prompts=prompts,
        recorder=FakeRecorder(),
        policy=InferencePolicy(max_attempts=1),
    )
    return Harness(infer=infer, prompts=prompts, today=lambda: TODAY), infer


def _request() -> Any:
    from modules.ai_platform.application.infer import InferenceInput

    return InferenceInput(
        prompt_name="narration",
        prompt_version=1,
        model=MODEL,
        evidence=_evidence(),
        correlation_id=uuid4(),
    )


def _evaluation(**overrides: Any) -> Evaluation:
    defaults: dict[str, Any] = {
        "model": MODEL,
        "dataset": "golden",
        "dataset_version": 1,
        "rubric_version": RUBRIC_VERSION,
        "evaluated_on": TODAY,
        "sample_size": 4,
        "grounding_failures": 0,
        "schema_failures": 0,
        "coverage": 1.0,
    }
    return Evaluation(**{**defaults, **overrides})


def _report(
    *, outcome: InferenceOutcome = InferenceOutcome.OK, fingerprint: str | None = None
) -> EvaluationReport:
    shipped = load_prompt_registry().get("explanation_narration", 1)
    return EvaluationReport(
        prompt_name="explanation_narration",
        prompt_version=1,
        prompt_fingerprint=fingerprint or shipped.fingerprint,
        model=MODEL,
        dataset_name="golden",
        dataset_version=1,
        dataset_fingerprint="f" * 64,
        rubric_version=RUBRIC_VERSION,
        evaluated_on=TODAY,
        results=(
            CaseResult(
                case="one",
                outcome=outcome,
                coverage=1.0 if outcome is InferenceOutcome.OK else 0.0,
                detail=None if outcome is InferenceOutcome.OK else "it made something up",
            ),
        ),
    )


def _manifest_copy(tmp_path: Path) -> Path:
    """A real prompt directory, copied — so the fingerprint check under test
    runs against the shipped artifact rather than a fixture shaped to pass."""
    import shutil

    from modules.ai_platform.infrastructure.prompt_loader import PROMPT_DIR

    shutil.copytree(PROMPT_DIR, tmp_path / "prompts")
    load_prompt_registry.cache_clear()
    return tmp_path / "prompts" / "manifest.json"


# --------------------------------------------------------------------------
# The report, and the command


class TestTheReportIsReadable:
    def test_it_names_the_run_and_its_verdict(self) -> None:
        rendered = _report().render()
        for expected in (
            "explanation_narration@1",
            MODEL,
            "golden@1",
            f"rubric   v{RUBRIC_VERSION}",
            "release             EARNED",
        ):
            assert expected in rendered

    def test_it_prints_the_criteria_it_was_judged_by(self) -> None:
        """A number a reader cannot trace to a published criterion is a
        number they will either over-trust or ignore."""
        rendered = _report().render()
        for line in criteria():
            assert line in rendered

    def test_a_failing_case_says_how_it_failed(self) -> None:
        rendered = _report(outcome=InferenceOutcome.UNGROUNDED).render()
        assert "FAIL" in rendered
        assert "it made something up" in rendered
        assert "release             REFUSED" in rendered


class TestTheCommandRefusesToInventAResult:
    """The absence of a runtime must be *created*, never inherited.

    Corrected 2026-07-30, and the correction matters more than the tests. As
    first written these called ``main([])`` and relied on the developer's
    machine having no Ollama — which was true when they were written and
    stopped being true an hour later. They then failed, having silently been
    testing the ambient environment rather than the refusal.

    That is the worst possible shape for these two in particular: they assert
    the guarantee that the harness never substitutes a fake for a model, and
    a test that quietly changes meaning when a service starts cannot assert
    anything. The unreachable address is now injected.
    """

    #: Port 1 on the loopback. Privileged, unbound, and refused immediately —
    #: an *address*, not a timeout, so the test is fast and cannot pass
    #: because a connection was merely slow.
    NOWHERE = "http://127.0.0.1:1"

    @pytest.fixture(autouse=True)
    def _no_runtime(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("SIGNORA_OLLAMA_BASE_URL", self.NOWHERE)

    async def test_it_fails_rather_than_falling_back_to_a_fake(self, capsys: Any) -> None:
        """The single most important behaviour in the harness. A run against a
        scripted adapter would prove the grounding checker works and nothing
        about the model — and would earn a release on that basis.

        The message is asserted alongside the exit code deliberately: a run
        that failed for some *other* reason would also exit non-zero, and
        "it failed" is not evidence that it refused.
        """
        from modules.ai_platform.evaluation.__main__ import main

        exit_code = await main([])

        assert exit_code == 2
        printed = capsys.readouterr().err
        assert "No model runtime" in printed
        assert self.NOWHERE in printed, "the refusal must name the address it tried"

    async def test_the_refusal_says_how_to_fix_it(self, capsys: Any) -> None:
        """An engineer meeting this message should not have to read the
        source to learn what is missing."""
        from modules.ai_platform.evaluation.__main__ import main

        await main([])
        printed = capsys.readouterr().err
        assert "ollama pull" in printed
        assert "SIGNORA_OLLAMA_BASE_URL" in printed

    async def test_a_reachable_runtime_is_not_refused(self) -> None:
        """The positive control, and the reason the two tests above were
        wrong for an hour: without it, a refusal that fired unconditionally
        would satisfy both of them."""
        import httpx

        from modules.ai_platform.evaluation.__main__ import _reachable

        async def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(200, json={"models": []})

        transport = httpx.MockTransport(handler)
        async with httpx.AsyncClient(transport=transport) as client:
            assert await _reachable(client, "http://any-host") is True
            assert await _reachable(client, self.NOWHERE) is True

    async def test_an_unreachable_runtime_is_detected(self) -> None:
        import httpx

        from modules.ai_platform.evaluation.__main__ import _reachable

        async with httpx.AsyncClient() as client:
            assert await _reachable(client, self.NOWHERE) is False


class TestTheEvidenceTranslation:
    """`assemble` is the one place pipeline vocabulary becomes evidence.

    A defect here corrupts every golden dataset and every narration, silently,
    because the output would still be perfectly grounded — in the wrong facts.
    """

    def test_it_translates_and_never_derives(self) -> None:
        from modules.ai_platform.infrastructure.explanation import BUYING_SCORE, OPPORTUNITY

        dataset = load_dataset("explanation_narration", 1)
        kinds = {fact.ref.kind for case in dataset.cases for fact in case.evidence}
        assert {OPPORTUNITY, BUYING_SCORE} <= kinds

    def test_every_fact_carries_the_id_the_pipeline_minted(self) -> None:
        """A citation must resolve to a row a human can look at. A fact
        addressed by an id invented during assembly resolves to nothing."""
        dataset = load_dataset("explanation_narration", 1)
        for case in dataset.cases:
            for fact in case.evidence:
                assert fact.ref.id != UUID(int=0)

    def test_quantities_are_recorded_as_written(self) -> None:
        """Evidence canonicalises by type, so a number read back as a JSON
        float would digest differently from the same fact assembled in
        Python — and two identical inferences would look like two."""
        dataset = load_dataset("explanation_narration", 1)
        values = [v for case in dataset.cases for f in case.evidence for _, v in f.attributes]
        assert values and all(isinstance(value, str) for value in values)

    def test_the_opportunity_frame_is_not_load_bearing(self) -> None:
        """"An opportunity was opened" is the frame, not the content.
        Requiring it would let a narrative pass by restating the obvious."""
        from modules.ai_platform.infrastructure.explanation import OPPORTUNITY

        dataset = load_dataset("explanation_narration", 1)
        for case in dataset.cases:
            assert not any(ref.startswith(f"{OPPORTUNITY}:") for ref in case.load_bearing)
