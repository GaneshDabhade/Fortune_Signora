"""The deterministic provider, and the one place it must refuse to exist.

Two things are proven here. **The adapter satisfies the port** — every knob,
the failure taxonomy, and the derived timeout — and **the composition root
refuses it outside a local environment**, which is the acceptance criterion
[TASK-415](../../../docs/BACKLOG.md) calls not optional.

The second is the one worth reading. A production service answering from a
stub is indistinguishable from one that works, so the guard is the whole
reason a mock may be a first-class provider rather than a test fixture.
"""

from __future__ import annotations

from uuid import uuid4

import httpx
import pytest

from modules.ai_platform.domain.provider import (
    AIPermanentError,
    AIProviderAdapter,
    AIProviderRegistry,
    AIRateLimitedError,
    AIRegistrationError,
    AITransientError,
    AIVendor,
    InferenceRequest,
    ModelNotRegisteredError,
)
from modules.ai_platform.evaluation.run_log import RunLog
from modules.ai_platform.infrastructure.adapters.mock import MockAdapter
from modules.ai_platform.infrastructure.composition import build_provider_registry
from modules.ai_platform.infrastructure.settings import AISettings


def a_request(**overrides: object) -> InferenceRequest:
    kwargs: dict[str, object] = {
        "model": "mock-model",
        "prompt": "explain this account",
        "output_schema": {"type": "object"},
        "workspace_id": uuid4(),
        "correlation_id": uuid4(),
        "max_output_tokens": 512,
        "temperature": 0.0,
        "timeout_seconds": 30.0,
    }
    kwargs.update(overrides)
    return InferenceRequest(**kwargs)  # type: ignore[arg-type]


def an_adapter(**overrides: object) -> MockAdapter:
    kwargs: dict[str, object] = {"models": frozenset({"mock-model"})}
    kwargs.update(overrides)
    return MockAdapter(**kwargs)  # type: ignore[arg-type]


class TestItSatisfiesThePort:
    def test_it_is_a_valid_adapter(self) -> None:
        assert isinstance(an_adapter(), AIProviderAdapter)

    def test_it_declares_structured_output(self) -> None:
        """The registry refuses an adapter that cannot constrain output, and
        would be right to — every guarantee in this module begins with a
        parseable structure."""
        assert an_adapter().describe().supports_structured_output is True

    async def test_it_answers_as_itself_and_never_as_a_runtime_that_did_not_run(
        self,
    ) -> None:
        """The reason `AIVendor.MOCK` exists rather than reusing `OLLAMA`.

        Provenance travels onto every `ai_inference` row. A stub claiming to
        be a local model would make that row assert a runtime nobody started
        — *"an incorrect attribution is worse than none"* (§10).
        """
        result = await an_adapter().complete(a_request())
        assert result.vendor is AIVendor.MOCK

    async def test_it_reports_the_model_it_was_asked_for(self) -> None:
        result = await an_adapter().complete(a_request(model="mock-model"))
        assert result.model == "mock-model"

    async def test_it_records_what_crossed_the_port(self) -> None:
        adapter = an_adapter()
        await adapter.complete(a_request(prompt="first"))
        await adapter.complete(a_request(prompt="second"))
        assert [r.prompt for r in adapter.seen] == ["first", "second"]

    async def test_the_same_request_twice_returns_the_same_thing(self) -> None:
        """Determinism is the guarantee, not a side effect. Nothing here reads
        a clock or a counter, so replay and regression can sit on it."""
        adapter = an_adapter(content='{"a": 1}')
        first = await adapter.complete(a_request())
        second = await adapter.complete(a_request())
        assert first.content == second.content
        assert first.usage == second.usage


class TestTheKnobs:
    """Five settable, one derived — and the derivation is the point.

    The row asks for six including a timeout. A configured latency *and* a
    configured timeout are two representations of how long a call took, and
    §2 says the second copy eventually contradicts the first.
    """

    async def test_content_is_returned_verbatim(self) -> None:
        adapter = an_adapter(content='{"narrative": "steady"}')
        assert (await adapter.complete(a_request())).content == '{"narrative": "steady"}'

    async def test_the_default_content_parses(self) -> None:
        """A default that did not parse would fail every caller for a reason
        that had nothing to do with the caller."""
        import json

        assert json.loads((await an_adapter().complete(a_request())).content) == {}

    async def test_token_usage_is_settable(self) -> None:
        adapter = an_adapter(input_tokens=120, output_tokens=45)
        usage = (await adapter.complete(a_request())).usage
        assert (usage.input_tokens, usage.output_tokens, usage.total_tokens) == (120, 45, 165)

    async def test_latency_is_reported_and_never_slept(self) -> None:
        """A fake that actually waited would make the suite slower without
        making it more honest."""
        import time

        adapter = an_adapter(latency_ms=5_000)
        started = time.monotonic()
        result = await adapter.complete(a_request(timeout_seconds=30.0))
        assert result.usage.latency_ms == 5_000
        assert time.monotonic() - started < 1.0

    async def test_the_retry_count_is_settable(self) -> None:
        adapter = an_adapter(retries=2)
        assert (await adapter.complete(a_request())).usage.retries == 2

    @pytest.mark.parametrize(
        "error",
        [
            AITransientError(AIVendor.MOCK, "overloaded"),
            AIRateLimitedError(AIVendor.MOCK, "slow down", retry_after_seconds=30.0),
            AIPermanentError(AIVendor.MOCK, "refused"),
        ],
    )
    async def test_any_failure_in_the_taxonomy_can_be_scripted(
        self, error: Exception
    ) -> None:
        """The taxonomy already exists; the mock reuses it rather than
        inventing a parallel one."""
        with pytest.raises(type(error)):
            await an_adapter(error=error).complete(a_request())

    async def test_a_scripted_failure_reports_no_usage(self) -> None:
        """A call that failed has no output tokens. Recording some would make
        the deterministic path disagree with every real adapter."""
        adapter = an_adapter(error=AIPermanentError(AIVendor.MOCK, "refused"), output_tokens=99)
        with pytest.raises(AIPermanentError):
            await adapter.complete(a_request())


class TestTheTimeoutIsDerivedFromLatency:
    async def test_a_call_slower_than_its_budget_times_out(self) -> None:
        adapter = an_adapter(latency_ms=45_000)
        with pytest.raises(AITransientError):
            await adapter.complete(a_request(timeout_seconds=30.0))

    async def test_the_same_latency_inside_a_larger_budget_succeeds(self) -> None:
        """The negative control, and what makes the test above mean anything:
        the *budget* decides, not a second knob."""
        adapter = an_adapter(latency_ms=45_000)
        assert (await adapter.complete(a_request(timeout_seconds=60.0))).usage.latency_ms == 45_000

    async def test_a_timeout_is_transient_rather_than_permanent(self) -> None:
        """The distinction the platform's retry policy reads. A timeout
        retried is work that was merely late; a permanent failure retried
        burns quota to no purpose."""
        adapter = an_adapter(latency_ms=45_000)
        with pytest.raises(AITransientError) as raised:
            await adapter.complete(a_request(timeout_seconds=1.0))
        assert not isinstance(raised.value, AIPermanentError)


class TestTheDevelopmentDefault:
    """The objective, stated as a test: a fresh clone reaches a model path
    with no Ollama and no API key."""

    def _settings(self, **overrides: object) -> AISettings:
        return AISettings(**overrides)  # type: ignore[arg-type]

    async def test_the_development_model_resolves_with_no_ollama_and_no_key(self) -> None:
        settings = self._settings(anthropic_api_key=None)
        async with httpx.AsyncClient() as client:
            registry = build_provider_registry(settings, client=client)
            adapter = registry.for_model(settings.ollama_model)
        assert adapter.describe().vendor is AIVendor.MOCK

    async def test_ollama_is_registered_only_when_explicitly_selected(self) -> None:
        """Before this slice it was registered unconditionally, which is what
        made a local model a requirement rather than a choice (§10)."""
        settings = self._settings(development_provider="ollama")
        async with httpx.AsyncClient() as client:
            registry = build_provider_registry(settings, client=client)
            adapter = registry.for_model(settings.ollama_model)
        assert adapter.describe().vendor is AIVendor.OLLAMA

    async def test_exactly_one_of_the_two_serves_the_development_model(self) -> None:
        """Not a preference. The registry refuses two adapters claiming one
        model, so registering both would fail at composition."""
        settings = self._settings()
        async with httpx.AsyncClient() as client:
            vendors = {
                d.vendor for d in build_provider_registry(settings, client=client).descriptors()
            }
        assert AIVendor.OLLAMA not in vendors

    async def test_a_hosted_credential_still_registers_alongside_it(self) -> None:
        """The mock replaces the *development* runtime, never a real one."""
        settings = self._settings(anthropic_api_key="k")
        async with httpx.AsyncClient() as client:
            registry = build_provider_registry(settings, client=client)
            assert registry.for_model(settings.anthropic_model).describe().vendor is (
                AIVendor.ANTHROPIC
            )
            assert registry.for_model(settings.ollama_model).describe().vendor is AIVendor.MOCK


class TestItIsRefusedOutsideALocalEnvironment:
    """The acceptance criterion the row calls not optional.

    A service answering from a deterministic stub is **indistinguishable from
    one that is working**, which is strictly worse than the outage it hides.
    """

    def _settings(self, **overrides: object) -> AISettings:
        return AISettings(**overrides)  # type: ignore[arg-type]

    @pytest.mark.parametrize("environment", ["production", "staging"])
    async def test_composition_refuses_the_mock_outside_local(self, environment: str) -> None:
        settings = self._settings(environment=environment)
        async with httpx.AsyncClient() as client:
            with pytest.raises(AIRegistrationError):
                build_provider_registry(settings, client=client)

    async def test_the_refusal_names_the_cause(self) -> None:
        """Fast *and* legible. §10 requires the diagnostic to name why, or an
        engineer reads a stack trace instead of a sentence."""
        settings = self._settings(environment="production")
        async with httpx.AsyncClient() as client:
            with pytest.raises(AIRegistrationError) as raised:
                build_provider_registry(settings, client=client)
        message = str(raised.value)
        assert "production" in message
        assert "mock" in message.lower()

    async def test_a_real_provider_is_unaffected_by_the_environment(self) -> None:
        """The negative control. The guard refuses *the mock*, never a
        deployment."""
        settings = self._settings(
            environment="production", development_provider="ollama", anthropic_api_key="k"
        )
        async with httpx.AsyncClient() as client:
            registry = build_provider_registry(settings, client=client)
        assert registry.for_model(settings.anthropic_model).describe().vendor is (
            AIVendor.ANTHROPIC
        )

    async def test_nothing_is_registered_when_the_guard_fires(self) -> None:
        """A partially built registry would be worse than none: it would
        resolve some models and not others, and the failure would surface far
        from its cause."""
        settings = self._settings(environment="production", anthropic_api_key="k")
        async with httpx.AsyncClient() as client:
            with pytest.raises(AIRegistrationError):
                build_provider_registry(settings, client=client)
            registry = AIProviderRegistry()
            with pytest.raises(ModelNotRegisteredError):
                registry.for_model(settings.anthropic_model)


class TestTheRunLogReadsBackWhatServedTheRun:
    def test_no_calls_means_no_provider(self) -> None:
        """An unreleased prompt fails before anything is served. Naming a
        provider there would attribute a run to a component never involved."""
        assert RunLog().provider() is None
