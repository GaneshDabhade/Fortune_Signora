"""The only path to a model: lifecycle, retry semantics, recording.

Every case runs against a scripted adapter. Deterministic behaviour is
verified without a model, per the two-tier split — whether a model reasons
well is the harness's question (T120).
"""

from __future__ import annotations

import contextlib
import json
from dataclasses import dataclass, field
from datetime import UTC, date, datetime
from uuid import UUID, uuid4

import pytest

from modules.ai_platform.application.infer import (
    Infer,
    InferenceInput,
    InferencePolicy,
)
from modules.ai_platform.application.render import render
from modules.ai_platform.domain.evidence import EvidenceSetBuilder
from modules.ai_platform.domain.grounding import (
    GroundedOutput,
    GroundedStatement,
    SchemaViolationError,
    UngroundedOutputError,
)
from modules.ai_platform.domain.prompt import (
    Evaluation,
    PromptNotReleasableError,
    PromptRegistry,
    PromptVersion,
)
from modules.ai_platform.domain.provider import (
    AIPermanentError,
    AIProviderRegistry,
    AIRateLimitedError,
    AITransientError,
    AIVendor,
    ModelNotRegisteredError,
)
from modules.ai_platform.domain.record import InferenceOutcome, InferenceRecord
from tests.ai_platform.fakes import FakeAdapter

MODEL = "fake-model"
WORKSPACE = UUID(int=42)
NOW = datetime(2026, 7, 30, 12, 0, tzinfo=UTC)
FUNDING = "business_event:00000000-0000-0000-0000-000000000001"


class Narration(GroundedOutput):
    points: tuple[GroundedStatement, ...]

    def statements(self) -> tuple[GroundedStatement, ...]:
        return self.points


@dataclass
class FakeRecorder:
    written: list[InferenceRecord] = field(default_factory=list)

    async def record(self, record: InferenceRecord) -> None:
        self.written.append(record)


def evidence() -> object:
    builder = EvidenceSetBuilder(WORKSPACE)
    builder.add(
        kind="business_event",
        id=UUID(int=1),
        summary="Raised 24M USD in a Series B round",
        attributes={"amount": 24000000},
    )
    return builder.build(assembled_at=NOW)


def a_prompt(*, released_for: str | None = MODEL) -> PromptVersion:
    evaluations = (
        (
            Evaluation(
                model=released_for,
                dataset="baseline",
                dataset_version=1,
                rubric_version=1,
                evaluated_on=date(2026, 7, 30),
                sample_size=20,
                grounding_failures=0,
                schema_failures=0,
                coverage=1.0,
            ),
        )
        if released_for
        else ()
    )
    return PromptVersion(
        name="narration",
        version=1,
        owner="AI Platform",
        text="Restate these.\n\n{facts}",
        evaluations=evaluations,
    )


GOOD = json.dumps({"points": [{"text": "They raised 24M USD.", "evidence": [FUNDING]}]})
UNGROUNDED = json.dumps({"points": [{"text": "They grew 40%.", "evidence": [FUNDING]}]})
MALFORMED = "I'm afraid I can't help with that."


def build(
    *,
    content: str = GOOD,
    error: Exception | None = None,
    errors: list[Exception] | None = None,
    prompt: PromptVersion | None = None,
    policy: InferencePolicy | None = None,
) -> tuple[Infer, FakeRecorder, FakeAdapter, list[float]]:
    adapter = FakeAdapter(models=frozenset({MODEL}), content=content, error=error)
    if errors is not None:
        _script(adapter, errors, content)
    providers = AIProviderRegistry()
    providers.register(adapter)
    recorder = FakeRecorder()
    slept: list[float] = []

    async def sleep(seconds: float) -> None:
        slept.append(seconds)

    infer = Infer(
        providers=providers,
        prompts=PromptRegistry(versions=(prompt or a_prompt(),)),
        recorder=recorder,
        policy=policy or InferencePolicy(backoff_seconds=1.0),
        clock=lambda: NOW,
        sleep=sleep,
    )
    return infer, recorder, adapter, slept


def _script(adapter: FakeAdapter, errors: list[Exception], content: str) -> None:
    """Fail with each error in turn, then succeed."""
    queue = list(errors)
    original = adapter.complete

    async def complete(request: object) -> object:
        if queue:
            raise queue.pop(0)
        return await original(request)  # type: ignore[arg-type]

    adapter.complete = complete  # type: ignore[method-assign,assignment]


def an_input() -> InferenceInput:
    return InferenceInput(
        prompt_name="narration",
        prompt_version=1,
        model=MODEL,
        evidence=evidence(),  # type: ignore[arg-type]
        correlation_id=uuid4(),
    )


class TestTheLifecycle:
    async def test_a_grounded_call_returns_output_and_a_record(self) -> None:
        infer, recorder, _, _ = build()
        result = await infer.execute(an_input(), Narration)

        assert result.output.points[0].text == "They raised 24M USD."
        assert result.record.outcome is InferenceOutcome.OK
        assert recorder.written == [result.record]

    async def test_the_rendered_evidence_reaches_the_model(self) -> None:
        infer, _, adapter, _ = build()
        await infer.execute(an_input(), Narration)

        sent = adapter.seen[0].prompt
        assert FUNDING in sent, "the model was never shown how to cite the fact"
        assert "Raised 24M USD" in sent

    async def test_the_output_schema_is_derived_from_the_output_type(self) -> None:
        infer, _, adapter, _ = build()
        await infer.execute(an_input(), Narration)
        assert adapter.seen[0].output_schema["title"] == "Narration"

    async def test_the_policy_is_the_only_source_of_timeout_and_temperature(self) -> None:
        policy = InferencePolicy(timeout_seconds=12.5, temperature=0.25, max_output_tokens=99)
        infer, _, adapter, _ = build(policy=policy)
        await infer.execute(an_input(), Narration)

        call = adapter.seen[0]
        assert call.timeout_seconds == 12.5
        assert call.temperature == 0.25
        assert call.max_output_tokens == 99

    async def test_the_record_carries_full_provenance(self) -> None:
        infer, _, _, _ = build()
        record = (await infer.execute(an_input(), Narration)).record

        assert record.prompt_name == "narration"
        assert record.prompt_version == 1
        assert record.prompt_fingerprint
        assert record.requested_model == MODEL
        assert record.vendor is AIVendor.OLLAMA
        assert record.evidence_digest == evidence().digest  # type: ignore[attr-defined]
        assert record.evidence_refs == (FUNDING,)
        assert record.workspace_id == WORKSPACE


class TestTheReleaseRuleIsEnforcedAtTheCall:
    async def test_an_unreleased_prompt_never_reaches_a_model(self) -> None:
        infer, recorder, adapter, _ = build(prompt=a_prompt(released_for=None))
        with pytest.raises(PromptNotReleasableError):
            await infer.execute(an_input(), Narration)
        assert adapter.seen == []
        assert recorder.written == []

    async def test_a_prompt_released_for_another_model_is_refused(self) -> None:
        infer, _, adapter, _ = build(prompt=a_prompt(released_for="some-other-model"))
        with pytest.raises(PromptNotReleasableError, match="some-other-model"):
            await infer.execute(an_input(), Narration)
        assert adapter.seen == []

    async def test_an_unserved_model_fails_before_any_call(self) -> None:
        infer, _, _, _ = build()
        request = InferenceInput(
            prompt_name="narration",
            prompt_version=1,
            model="unknown",
            evidence=evidence(),  # type: ignore[arg-type]
            correlation_id=uuid4(),
        )
        with pytest.raises((ModelNotRegisteredError, PromptNotReleasableError)):
            await infer.execute(request, Narration)


class TestRetryIsSemanticAndNarrow:
    async def test_a_transient_failure_is_retried_and_can_succeed(self) -> None:
        infer, recorder, _, slept = build(errors=[AITransientError(AIVendor.OLLAMA, "overloaded")])
        result = await infer.execute(an_input(), Narration)

        assert result.record.outcome is InferenceOutcome.OK
        assert result.record.usage.retries == 1
        assert slept == [1.0]

    async def test_retries_back_off_exponentially(self) -> None:
        infer, _, _, slept = build(
            errors=[
                AITransientError(AIVendor.OLLAMA, "one"),
                AITransientError(AIVendor.OLLAMA, "two"),
            ],
            policy=InferencePolicy(max_attempts=3, backoff_seconds=2.0),
        )
        await infer.execute(an_input(), Narration)
        assert slept == [2.0, 4.0]

    async def test_a_vendor_stated_wait_wins_over_the_computed_backoff(self) -> None:
        """Guessing over a vendor's own answer is how an integration gets
        throttled harder."""
        infer, _, _, slept = build(
            errors=[AIRateLimitedError(AIVendor.OLLAMA, "slow down", retry_after_seconds=7.5)]
        )
        await infer.execute(an_input(), Narration)
        assert slept == [7.5]

    async def test_attempts_are_bounded(self) -> None:
        infer, recorder, _, slept = build(
            error=AITransientError(AIVendor.OLLAMA, "always down"),
            policy=InferencePolicy(max_attempts=2, backoff_seconds=0.5),
        )
        with pytest.raises(AITransientError):
            await infer.execute(an_input(), Narration)
        assert len(slept) == 1
        assert recorder.written[0].outcome is InferenceOutcome.TRANSIENT

    async def test_a_permanent_failure_is_never_retried(self) -> None:
        """Retrying one burns quota to no purpose and turns a configuration
        mistake into a burst of identical failures at the vendor."""
        infer, recorder, _, slept = build(error=AIPermanentError(AIVendor.OLLAMA, "bad key"))
        with pytest.raises(AIPermanentError):
            await infer.execute(an_input(), Narration)
        assert slept == []
        assert recorder.written[0].outcome is InferenceOutcome.PERMANENT

    async def test_a_grounding_failure_is_never_retried(self) -> None:
        """A content failure, not a transport failure. Re-rolling one would
        burn tokens and make the ungrounded rate unmeasurable."""
        infer, recorder, adapter, slept = build(content=UNGROUNDED)
        with pytest.raises(UngroundedOutputError):
            await infer.execute(an_input(), Narration)
        assert len(adapter.seen) == 1
        assert slept == []
        assert recorder.written[0].outcome is InferenceOutcome.UNGROUNDED

    async def test_a_schema_failure_is_never_retried(self) -> None:
        infer, recorder, adapter, slept = build(content=MALFORMED)
        with pytest.raises(SchemaViolationError):
            await infer.execute(an_input(), Narration)
        assert len(adapter.seen) == 1
        assert recorder.written[0].outcome is InferenceOutcome.SCHEMA_INVALID


class TestEveryOutcomeIsRecorded:
    """A table recording only successes cannot report a failure rate — and
    the ungrounded rate is the number this platform most needs about itself."""

    @pytest.mark.parametrize(
        ("kwargs", "expected"),
        [
            ({}, InferenceOutcome.OK),
            ({"content": UNGROUNDED}, InferenceOutcome.UNGROUNDED),
            ({"content": MALFORMED}, InferenceOutcome.SCHEMA_INVALID),
            (
                {"error": AITransientError(AIVendor.OLLAMA, "down")},
                InferenceOutcome.TRANSIENT,
            ),
            (
                {"error": AIPermanentError(AIVendor.OLLAMA, "bad key")},
                InferenceOutcome.PERMANENT,
            ),
        ],
    )
    async def test_the_outcome_is_recorded(
        self, kwargs: dict[str, object], expected: InferenceOutcome
    ) -> None:
        infer, recorder, _, _ = build(
            policy=InferencePolicy(max_attempts=1),
            **kwargs,  # type: ignore[arg-type]
        )
        with contextlib.suppress(Exception):
            await infer.execute(an_input(), Narration)
        assert len(recorder.written) == 1
        assert recorder.written[0].outcome is expected

    async def test_a_failure_record_explains_itself(self) -> None:
        infer, recorder, _, _ = build(content=UNGROUNDED)
        with pytest.raises(UngroundedOutputError):
            await infer.execute(an_input(), Narration)
        assert "40" in (recorder.written[0].detail or "")

    async def test_a_successful_record_carries_no_detail(self) -> None:
        infer, recorder, _, _ = build()
        await infer.execute(an_input(), Narration)
        assert recorder.written[0].detail is None

    async def test_a_transport_failure_records_zero_usage_rather_than_none(self) -> None:
        """A failed call still happened. A row with no usage is
        indistinguishable from one never attempted."""
        infer, recorder, _, _ = build(
            error=AIPermanentError(AIVendor.OLLAMA, "nope"),
            policy=InferencePolicy(max_attempts=1),
        )
        with pytest.raises(AIPermanentError):
            await infer.execute(an_input(), Narration)
        assert recorder.written[0].usage.total_tokens == 0

    async def test_a_provider_failure_still_names_the_vendor(self) -> None:
        """Nothing came back, and the vendor is known anyway — every
        ``AIProviderError`` names the one that raised it.

        Discarding it would leave a rate-limit incident attributable to
        nobody, which is the same defect as inventing an attribution, in the
        other direction.
        """
        infer, recorder, _, _ = build(
            error=AIRateLimitedError(AIVendor.OLLAMA, "slow down"),
            policy=InferencePolicy(max_attempts=1),
        )
        with pytest.raises(AITransientError):
            await infer.execute(an_input(), Narration)

        assert recorder.written[0].vendor is AIVendor.OLLAMA
        assert recorder.written[0].served_model is None, "nothing served this call"

    async def test_an_exhausted_retry_sequence_records_how_many_it_took(self) -> None:
        """R-01: a retry storm must be visible in ``retries`` long before it
        is visible on an invoice — and it is the *failed* rows that prove one
        happened."""
        infer, recorder, _, _ = build(
            error=AITransientError(AIVendor.OLLAMA, "always down"),
            policy=InferencePolicy(max_attempts=3, backoff_seconds=0.1),
        )
        with pytest.raises(AITransientError):
            await infer.execute(an_input(), Narration)

        assert recorder.written[0].usage.retries == 2

    async def test_a_permanent_failure_after_a_transient_one_records_the_retry(self) -> None:
        """Failing permanently on the second attempt is a different
        operational fact from failing on the first."""
        infer, recorder, _, _ = build(
            errors=[
                AITransientError(AIVendor.OLLAMA, "overloaded"),
                AIPermanentError(AIVendor.OLLAMA, "bad key"),
            ],
            policy=InferencePolicy(max_attempts=3, backoff_seconds=0.1),
        )
        with pytest.raises(AIPermanentError):
            await infer.execute(an_input(), Narration)

        assert recorder.written[0].outcome is InferenceOutcome.PERMANENT
        assert recorder.written[0].usage.retries == 1

    async def test_the_caller_never_sees_the_internal_retry_wrapper(self) -> None:
        """The count travels out of the retry loop inside a private
        exception. What the caller catches is still the vendor's failure."""
        infer, _, _, _ = build(
            error=AIPermanentError(AIVendor.OLLAMA, "bad key"),
            policy=InferencePolicy(max_attempts=1),
        )
        with pytest.raises(AIPermanentError) as caught:
            await infer.execute(an_input(), Narration)

        assert "bad key" in str(caught.value)
        assert caught.value.__suppress_context__, (
            "without `from None` the wrapper is printed as 'During handling of the above "
            "exception, another exception occurred' in every traceback a caller sees — an "
            "internal name in the first place an engineer looks"
        )


class TestInferIsStateless:
    async def test_two_identical_calls_produce_identical_requests(self) -> None:
        infer, _, adapter, _ = build()
        request = an_input()
        await infer.execute(request, Narration)
        await infer.execute(request, Narration)

        first, second = adapter.seen
        assert first.prompt == second.prompt
        assert first.output_schema == second.output_schema
        assert first.temperature == second.temperature

    async def test_a_failed_call_does_not_change_the_next_one(self) -> None:
        infer, _, adapter, _ = build(errors=[AITransientError(AIVendor.OLLAMA, "blip")])
        await infer.execute(an_input(), Narration)
        first_prompt = adapter.seen[-1].prompt

        await infer.execute(an_input(), Narration)
        assert adapter.seen[-1].prompt == first_prompt

    def test_infer_holds_no_mutable_state(self) -> None:
        infer, _, _, _ = build()
        held = {k: v for k, v in vars(infer).items()}
        assert not any(isinstance(v, list | dict | set) for v in held.values()), (
            "Infer is holding a mutable container — the beginning of a cache, "
            "and a hidden input to every later call."
        )


class TestRenderingIsDeterministicAndSeparate:
    def test_the_same_evidence_always_renders_identically(self) -> None:
        prompt = a_prompt()
        assert render(prompt, evidence()) == render(prompt, evidence())  # type: ignore[arg-type]

    def test_a_prompt_with_no_placeholder_is_refused(self) -> None:
        """Evidence would never reach the model, making every statement it
        produced ungrounded by construction."""
        prompt = PromptVersion(
            name="broken", version=1, owner="AI Platform", text="No placeholder here."
        )
        with pytest.raises(Exception, match="placeholder"):
            render(prompt, evidence())  # type: ignore[arg-type]


class TestThePolicyRefusesNonsense:
    @pytest.mark.parametrize(
        "kwargs",
        [{"max_attempts": 0}, {"timeout_seconds": 0.0}, {"backoff_seconds": -1.0}],
    )
    def test_an_unusable_policy_is_refused(self, kwargs: dict[str, object]) -> None:
        with pytest.raises(ValueError):
            InferencePolicy(**kwargs)  # type: ignore[arg-type]
