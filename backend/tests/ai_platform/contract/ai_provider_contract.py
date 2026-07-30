"""The shared AI Provider contract suite.

**One suite, run against every adapter.** This is the keystone test of the
AI Platform, borrowed directly from the provider layer where it has held for
four milestones: it is the only mechanism that catches drift between the
development runtime and the production one, and drift there would quietly
invalidate every prompt evaluated locally.

The suite *is* the behavioural specification. When Ollama and Anthropic
disagree, the answer is to adapt the adapter — never to branch in shared
code, and never to relax the suite.

Written as a mixin rather than a parameterised module so each adapter gets a
real, named test class: *"the Anthropic adapter violates the contract"* is a
more useful failure than *"contract[3] failed"*.

    class TestOllama(AIProviderContractSuite):
        @pytest.fixture
        def adapter(self, ...) -> AIProviderAdapter: ...

An adapter without a contract suite is an adapter nobody has checked.

**Nothing here calls a model.** Every case runs against a stubbed transport,
so the suite is deterministic, offline, and fast — the deterministic tier of
the two-tier split. Whether a model *reasons well* is the harness's question
(T120); whether an adapter *translates correctly* is this one's, and they
must never be conflated.
"""

from __future__ import annotations

from typing import Any
from uuid import uuid4

import httpx
import pytest

from modules.ai_platform.domain.provider import (
    AIOutputUnusableError,
    AIPermanentError,
    AIProviderAdapter,
    AIProviderError,
    AIRateLimitedError,
    AITransientError,
    InferenceRequest,
)

SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {"answer": {"type": "string"}},
    "required": ["answer"],
    "additionalProperties": False,
}


def a_request(model: str, **overrides: Any) -> InferenceRequest:
    kwargs: dict[str, Any] = {
        "model": model,
        "prompt": "Restate the facts.",
        "output_schema": SCHEMA,
        "workspace_id": uuid4(),
        "correlation_id": uuid4(),
        "max_output_tokens": 256,
        "temperature": 0.0,
        "timeout_seconds": 30.0,
    }
    kwargs.update(overrides)
    return InferenceRequest(**kwargs)


class AIProviderContractSuite:
    """Behaviour every AI adapter must exhibit, whatever it is adapting."""

    # --- supplied by each adapter's own class -----------------------------

    @pytest.fixture
    def adapter(self) -> AIProviderAdapter:  # pragma: no cover - overridden
        raise NotImplementedError

    @pytest.fixture
    def model(self) -> str:  # pragma: no cover - overridden
        raise NotImplementedError

    def build(self, *, handler: Any) -> AIProviderAdapter:  # pragma: no cover - overridden
        """An adapter whose transport is the given handler."""
        raise NotImplementedError

    def success_body(self) -> dict[str, Any]:  # pragma: no cover - overridden
        """A well-formed success response in this vendor's shape."""
        raise NotImplementedError

    def truncated_body(self) -> dict[str, Any]:  # pragma: no cover - overridden
        """A response the vendor cut short at the token ceiling."""
        raise NotImplementedError

    # --- the contract -----------------------------------------------------

    def responding(self, body: dict[str, Any], status: int = 200) -> Any:
        def handler(_: httpx.Request) -> httpx.Response:
            return httpx.Response(status, json=body)

        return handler

    def failing(self, status: int, headers: dict[str, str] | None = None) -> Any:
        def handler(_: httpx.Request) -> httpx.Response:
            return httpx.Response(status, json={"error": "nope"}, headers=headers or {})

        return handler

    def test_it_describes_itself_without_being_called(
        self, adapter: AIProviderAdapter, model: str
    ) -> None:
        descriptor = adapter.describe()
        assert descriptor.serves(model)
        assert descriptor.supports_structured_output

    def test_it_satisfies_the_port(self, adapter: AIProviderAdapter) -> None:
        assert isinstance(adapter, AIProviderAdapter)

    async def test_a_successful_call_returns_content_provenance_and_usage(self, model: str) -> None:
        adapter = self.build(handler=self.responding(self.success_body()))
        result = await adapter.complete(a_request(model))

        assert result.content.strip()
        assert result.vendor is adapter.describe().vendor
        assert result.model
        assert result.usage.input_tokens > 0
        assert result.usage.output_tokens > 0
        assert result.usage.latency_ms >= 0

    async def test_content_is_a_string_whatever_the_vendor_returned(self, model: str) -> None:
        """A caller receiving a dict from one vendor and a string from
        another would have to branch on vendor — the one thing this
        abstraction exists to prevent."""
        adapter = self.build(handler=self.responding(self.success_body()))
        assert isinstance((await adapter.complete(a_request(model))).content, str)

    async def test_the_declared_schema_reaches_the_vendor(self, model: str) -> None:
        """Structured output is enforced identically across providers, so
        grounding behaves the same whichever served the call."""
        seen: list[dict[str, Any]] = []

        def handler(request: httpx.Request) -> httpx.Response:
            seen.append(__import__("json").loads(request.content))
            return httpx.Response(200, json=self.success_body())

        adapter = self.build(handler=handler)
        await adapter.complete(a_request(model))
        assert SCHEMA in _nested_values(seen[0]), "the output schema never reached the vendor"

    async def test_truncated_output_is_unusable_not_ungrounded(self, model: str) -> None:
        """The transport contract breaking, not the content contract.
        Merging them would hide a systemic ceiling problem inside a per-call
        quality metric."""
        adapter = self.build(handler=self.responding(self.truncated_body()))
        with pytest.raises(AIOutputUnusableError):
            await adapter.complete(a_request(model))

    async def test_a_non_json_response_is_unusable(self, model: str) -> None:
        def handler(_: httpx.Request) -> httpx.Response:
            return httpx.Response(200, text="<html>gateway</html>")

        adapter = self.build(handler=handler)
        with pytest.raises(AIOutputUnusableError):
            await adapter.complete(a_request(model))

    @pytest.mark.parametrize("status", [500, 502, 503, 504, 408])
    async def test_server_failures_are_transient(self, model: str, status: int) -> None:
        adapter = self.build(handler=self.failing(status))
        with pytest.raises(AITransientError):
            await adapter.complete(a_request(model))

    async def test_rate_limiting_is_transient_and_carries_the_stated_wait(self, model: str) -> None:
        adapter = self.build(handler=self.failing(429, {"retry-after": "30"}))
        with pytest.raises(AIRateLimitedError) as caught:
            await adapter.complete(a_request(model))
        assert isinstance(caught.value, AITransientError)
        assert caught.value.retry_after_seconds == 30.0

    async def test_rate_limiting_without_a_stated_wait_says_so(self, model: str) -> None:
        """None means the vendor did not tell us — distinct from zero, which
        would mean retry immediately."""
        adapter = self.build(handler=self.failing(429))
        with pytest.raises(AIRateLimitedError) as caught:
            await adapter.complete(a_request(model))
        assert caught.value.retry_after_seconds is None

    @pytest.mark.parametrize("status", [401, 403])
    async def test_authentication_failures_are_permanent(self, model: str, status: int) -> None:
        """A rejected credential does not improve with patience, and
        retrying one turns a configuration mistake into a burst of failed
        authentications against the vendor."""
        adapter = self.build(handler=self.failing(status))
        with pytest.raises(AIPermanentError):
            await adapter.complete(a_request(model))

    @pytest.mark.parametrize("status", [401, 403])
    async def test_an_authentication_failure_says_so(self, model: str, status: int) -> None:
        """A 401 is permanent under the default rule anyway, so the branch
        that recognises it exists purely to *name* the cause — and a
        misconfigured credential is the most common failure there is. The
        diagnostic is the property, so the diagnostic is what is asserted;
        an unasserted branch would be a guard that cannot fail.
        """
        adapter = self.build(handler=self.failing(status))
        with pytest.raises(AIPermanentError, match="authentication rejected"):
            await adapter.complete(a_request(model))

    async def test_a_bad_request_is_permanent(self, model: str) -> None:
        adapter = self.build(handler=self.failing(400))
        with pytest.raises(AIPermanentError):
            await adapter.complete(a_request(model))

    async def test_a_timeout_is_transient(self, model: str) -> None:
        def handler(_: httpx.Request) -> httpx.Response:
            raise httpx.ReadTimeout("too slow")

        adapter = self.build(handler=handler)
        with pytest.raises(AITransientError):
            await adapter.complete(a_request(model))

    async def test_a_refused_connection_is_transient(self, model: str) -> None:
        def handler(_: httpx.Request) -> httpx.Response:
            raise httpx.ConnectError("refused")

        adapter = self.build(handler=handler)
        with pytest.raises(AITransientError):
            await adapter.complete(a_request(model))

    async def test_no_vendor_exception_escapes_the_adapter(self, model: str) -> None:
        """A caller catching AIProviderError has caught everything. If an
        httpx exception reached them, every caller would end up importing
        httpx to handle it."""
        for handler in (
            self.failing(500),
            self.failing(400),
            self.responding({"nonsense": True}),
        ):
            adapter = self.build(handler=handler)
            try:
                await adapter.complete(a_request(model))
            except AIProviderError:
                pass
            except Exception as exc:  # pragma: no cover - the failure this guards
                pytest.fail(f"a non-platform exception escaped the adapter: {exc!r}")

    async def test_the_adapter_holds_nothing_between_calls(self, model: str) -> None:
        """Statelessness at the adapter: two identical calls are
        indistinguishable, and the second does not depend on the first."""
        adapter = self.build(handler=self.responding(self.success_body()))
        first = await adapter.complete(a_request(model))
        second = await adapter.complete(a_request(model))
        assert first.content == second.content
        assert first.usage.input_tokens == second.usage.input_tokens


def _nested_values(value: Any) -> list[Any]:
    """Every value anywhere in a nested structure, so the suite can assert
    the schema was sent without knowing where a vendor puts it."""
    found = [value]
    if isinstance(value, dict):
        for item in value.values():
            found.extend(_nested_values(item))
    elif isinstance(value, list):
        for item in value:
            found.extend(_nested_values(item))
    return found
