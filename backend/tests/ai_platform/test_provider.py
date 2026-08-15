"""The AI Provider Port: routing, registration guards, and the failure taxonomy.

Covers the golden path and the failure paths that matter — a model nobody
serves, an adapter that cannot produce structured output, two adapters
claiming one model, and a request that could never be sent.
"""

from __future__ import annotations

from uuid import uuid4

import pytest

from modules.ai_platform.domain.errors import AIPlatformError
from modules.ai_platform.domain.provider import (
    AIProviderAdapter,
    AIProviderError,
    AIProviderRegistry,
    AIRateLimitedError,
    AIRegistrationError,
    AITransientError,
    AIVendor,
    InferenceRequest,
    InferenceRequestError,
    ModelNotRegisteredError,
)
from modules.ai_platform.domain.usage import InferenceUsage, UsageError
from modules.ai_platform.infrastructure.composition import build_provider_registry
from modules.ai_platform.infrastructure.settings import AISettings
from tests.ai_platform.fakes import FakeAdapter


def a_request(**overrides: object) -> InferenceRequest:
    kwargs: dict[str, object] = {
        "model": "fake-model",
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


class TestTheFakeSatisfiesThePort:
    def test_a_thirty_line_fake_is_a_valid_adapter(self) -> None:
        """If a fake cannot stand in for a dependency, the dependency was
        never really a boundary (the M5B finding). This asserts the port
        stayed small enough to remain one."""
        assert isinstance(FakeAdapter(), AIProviderAdapter)


class TestRoutingIsByModel:
    """A caller states the capability it needs. The registry answers who
    provides it — and there is no way to ask for a vendor by name."""

    def test_the_registry_resolves_a_model_to_its_adapter(self) -> None:
        registry = AIProviderRegistry()
        ollama = FakeAdapter(vendor=AIVendor.OLLAMA, models=frozenset({"llama3.1"}))
        claude = FakeAdapter(vendor=AIVendor.ANTHROPIC, models=frozenset({"claude-x"}))
        registry.register(ollama)
        registry.register(claude)

        assert registry.for_model("llama3.1") is ollama
        assert registry.for_model("claude-x") is claude

    def test_the_registry_exposes_no_vendor_keyed_lookup(self) -> None:
        """Vendor neutrality, made structural rather than documented.

        Business code that cannot *name* a vendor cannot branch on one. A
        `get(vendor)` here would be the first step back towards a dispatch
        table (CLAUDE.md §10, ADR-0028).
        """
        surface = {name for name in dir(AIProviderRegistry) if not name.startswith("_")}
        assert surface == {"adapters", "register", "for_model", "descriptors"}, (
            "The registry's public surface changed. Routing is by model; adding a "
            "vendor-keyed lookup would let a caller select a vendor deliberately."
        )

    def test_an_unserved_model_fails_loudly_and_names_what_is_registered(self) -> None:
        registry = AIProviderRegistry()
        registry.register(FakeAdapter(models=frozenset({"llama3.1"})))

        with pytest.raises(ModelNotRegisteredError) as caught:
            registry.for_model("gpt-9")
        assert "gpt-9" in str(caught.value)
        assert "llama3.1" in str(caught.value)

    def test_an_empty_registry_says_so_rather_than_listing_nothing(self) -> None:
        with pytest.raises(ModelNotRegisteredError, match="none"):
            AIProviderRegistry().for_model("anything")


class TestRegistrationRefusesMisconfiguration:
    """Caught at composition, where a human is present and a stack trace is
    cheap — not at 3am on a call that was supposed to explain an account."""

    def test_an_adapter_without_structured_output_is_refused(self) -> None:
        registry = AIProviderRegistry()
        with pytest.raises(AIRegistrationError, match="unusable"):
            registry.register(FakeAdapter(supports_structured_output=False))

    def test_an_adapter_serving_no_models_is_refused(self) -> None:
        registry = AIProviderRegistry()
        with pytest.raises(AIRegistrationError, match="serves no models"):
            registry.register(FakeAdapter(models=frozenset()))

    def test_two_adapters_claiming_one_model_are_refused(self) -> None:
        """Otherwise routing depends on registration order, and provenance
        records whichever adapter happened to win."""
        registry = AIProviderRegistry()
        registry.register(FakeAdapter(vendor=AIVendor.OLLAMA, models=frozenset({"shared"})))
        with pytest.raises(AIRegistrationError, match="already served by"):
            registry.register(
                FakeAdapter(vendor=AIVendor.ANTHROPIC, models=frozenset({"shared", "other"}))
            )

    def test_a_refused_adapter_is_not_registered(self) -> None:
        registry = AIProviderRegistry()
        with pytest.raises(AIRegistrationError):
            registry.register(FakeAdapter(supports_structured_output=False))
        assert registry.descriptors() == ()


class TestTheRequestRefusesWhatCannotBeSent:
    """A caller bug, caught before a vendor is chosen — which is why none of
    these name one."""

    @pytest.mark.parametrize(
        ("overrides", "expected"),
        [
            ({"model": "  "}, "names no model"),
            ({"prompt": ""}, "empty prompt"),
            ({"max_output_tokens": 0}, "must be positive"),
            ({"max_output_tokens": -1}, "must be positive"),
        ],
    )
    def test_a_malformed_request_is_refused(
        self, overrides: dict[str, object], expected: str
    ) -> None:
        with pytest.raises(InferenceRequestError, match=expected):
            a_request(**overrides)

    def test_request_errors_carry_no_vendor_attribution(self) -> None:
        """The request never reached a vendor. Naming one would put a false
        attribution in the first place an engineer looks."""
        with pytest.raises(InferenceRequestError) as caught:
            a_request(prompt="")
        assert not hasattr(caught.value, "vendor")
        for vendor in AIVendor:
            assert vendor.value not in str(caught.value)


class TestTheFailureTaxonomyIsSemantic:
    """A caller handles Signora concepts, never vendor error codes."""

    def test_every_failure_is_catchable_as_one_platform_error(self) -> None:
        for error in (
            InferenceRequestError("bad request"),
            AIRegistrationError(AIVendor.OLLAMA, "bad adapter"),
            ModelNotRegisteredError("no such model"),
            AIProviderError(AIVendor.ANTHROPIC, "boom"),
        ):
            assert isinstance(error, AIPlatformError)

    def test_a_rate_limit_is_a_transient_failure(self) -> None:
        """A caller backing off generically must not have to special-case
        rate limiting to get the backoff right."""
        error = AIRateLimitedError(AIVendor.ANTHROPIC, "slow down", retry_after_seconds=30.0)
        assert isinstance(error, AITransientError)
        assert error.retry_after_seconds == 30.0

    def test_a_rate_limit_without_a_stated_wait_says_so(self) -> None:
        """None means the vendor did not tell us — distinct from zero, which
        would mean retry immediately."""
        assert AIRateLimitedError(AIVendor.OLLAMA, "slow down").retry_after_seconds is None

    def test_a_vendor_failure_names_its_vendor(self) -> None:
        assert "anthropic" in str(AIProviderError(AIVendor.ANTHROPIC, "boom"))


class TestTheAdapterContract:
    async def test_a_completed_call_carries_provenance_and_usage(self) -> None:
        registry = AIProviderRegistry()
        registry.register(FakeAdapter(vendor=AIVendor.ANTHROPIC, models=frozenset({"claude-x"})))

        result = await registry.for_model("claude-x").complete(a_request(model="claude-x"))

        assert result.vendor is AIVendor.ANTHROPIC
        assert result.model == "claude-x"
        assert result.usage.total_tokens == 15

    async def test_a_vendor_failure_crosses_the_port_as_a_platform_error(self) -> None:
        adapter = FakeAdapter(error=AITransientError(AIVendor.OLLAMA, "overloaded"))
        with pytest.raises(AITransientError):
            await adapter.complete(a_request())

    async def test_the_adapter_receives_the_whole_request(self) -> None:
        """Statelessness at the port: nothing the adapter needs arrives by
        any route other than the request."""
        adapter = FakeAdapter()
        request = a_request()
        await adapter.complete(request)
        assert adapter.seen == [request]


class TestUsageRecordsFactsNotMoney:
    def test_usage_carries_no_currency_field(self) -> None:
        """A price is true for about a week; tokens are true forever.
        Pricing is applied outside the port at reporting time."""
        fields = set(InferenceUsage.__dataclass_fields__)
        assert fields == {"input_tokens", "output_tokens", "latency_ms", "retries"}
        assert not {f for f in fields if "cost" in f or "price" in f or "usd" in f}

    @pytest.mark.parametrize(
        "kwargs",
        [
            {"input_tokens": -1, "output_tokens": 0, "latency_ms": 0},
            {"input_tokens": 0, "output_tokens": -1, "latency_ms": 0},
            {"input_tokens": 0, "output_tokens": 0, "latency_ms": -1},
            {"input_tokens": 0, "output_tokens": 0, "latency_ms": 0, "retries": -1},
        ],
    )
    def test_negative_usage_is_refused(self, kwargs: dict[str, int]) -> None:
        with pytest.raises(UsageError, match="cannot be negative"):
            InferenceUsage(**kwargs)


class TestTheRegistryIsBuiltFromConfigurationAlone:
    """Which vendor serves an evaluation is a **setting**, never a code path.

    Ruled 2026-07-30, and asserted here because `build_provider_registry` had
    no test of its own — the composition root's registration rules were the
    thing every evaluation depends on and nothing checked. Both evaluation
    entry points now route through it, so these are the rules that decide
    whether `--model claude-sonnet-4-5` resolves.
    """

    def _settings(self, **overrides: object) -> AISettings:
        return AISettings(**overrides)  # type: ignore[arg-type]

    async def test_a_hosted_model_resolves_once_its_credential_is_present(self) -> None:
        """The whole of the provider-neutrality claim, in one assertion: a key
        in the environment is the only difference between a run that cannot
        reach a hosted model and one that can."""
        import httpx

        settings = self._settings(anthropic_api_key="k")
        async with httpx.AsyncClient() as client:
            registry = build_provider_registry(settings, client=client)
            adapter = registry.for_model(settings.anthropic_model)
        assert adapter.describe().vendor is AIVendor.ANTHROPIC

    async def test_without_the_credential_the_hosted_model_is_simply_unregistered(self) -> None:
        """The negative control, and the reason the test above means anything.

        The failure is *"no adapter serves this model"* at composition — legible
        and local — rather than a call that travels to a vendor and fails there
        with something an engineer has to decode.
        """
        import httpx

        settings = self._settings(anthropic_api_key=None)
        async with httpx.AsyncClient() as client:
            registry = build_provider_registry(settings, client=client)
            with pytest.raises(ModelNotRegisteredError):
                registry.for_model(settings.anthropic_model)

    async def test_a_second_hosted_vendor_registers_the_same_way(self) -> None:
        """🔴 **[TASK-420](../../../docs/BACKLOG.md), Epic H slice one — and the
        claim it exists to test.**

        📁 [ADR-0012](../../../docs/architecture/adr/0012-ai-platform-architecture.md)
        says a vendor integrates by *describing what it supports*. ⚡ **Adding
        one required no change to the registry, the port or the composition's
        shape** — **only a second `if key: register(...)`.**

        ⛔ **And the two are registered TOGETHER without either learning about
        the other**, which is what makes the registry's by-model resolution the
        thing that keeps callers vendor-blind.
        """
        import httpx

        settings = self._settings(anthropic_api_key="k", openai_api_key="k2")
        async with httpx.AsyncClient() as client:
            registry = build_provider_registry(settings, client=client)

            assert registry.for_model(settings.openai_model).describe().vendor is AIVendor.OPENAI
            assert (
                registry.for_model(settings.anthropic_model).describe().vendor
                is AIVendor.ANTHROPIC
            )

    async def test_the_second_vendor_is_absent_until_its_own_credential_exists(self) -> None:
        """⛔ **A deployment that has not configured OpenAI behaves exactly as
        it did before the adapter was written.** ⚠️ **Asserted with ANTHROPIC's
        key present**, so the test cannot pass merely because nothing is
        registered at all."""
        import httpx

        settings = self._settings(anthropic_api_key="k", openai_api_key=None)
        async with httpx.AsyncClient() as client:
            registry = build_provider_registry(settings, client=client)

            assert registry.for_model(settings.anthropic_model) is not None
            with pytest.raises(ModelNotRegisteredError):
                registry.for_model(settings.openai_model)

    async def test_no_adapter_is_registered_for_a_vendor_the_caller_named(self) -> None:
        """There is no vendor-keyed lookup to reach for, by construction. A
        caller that cannot *name* a vendor cannot branch on one."""
        assert not hasattr(AIProviderRegistry(), "for_vendor")
        assert not hasattr(AIProviderRegistry(), "get")
