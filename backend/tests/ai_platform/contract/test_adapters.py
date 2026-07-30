"""Both adapters, against the same contract.

Ollama is the development runtime and Anthropic the production one
(ADR-0028), and below that sentence they are indistinguishable: the same
suite, unmodified, run against each. Where a vendor differs, the *adapter*
absorbs it — the only thing that varies here is the shape of the stubbed
response, which is precisely the vendor detail an adapter exists to hide.
"""

from __future__ import annotations

import json
from typing import Any

import httpx
import pytest

from modules.ai_platform.domain.provider import AIOutputUnusableError, AIVendor
from modules.ai_platform.infrastructure.adapters.anthropic import AnthropicAdapter
from modules.ai_platform.infrastructure.adapters.ollama import OllamaAdapter
from tests.ai_platform.contract.ai_provider_contract import AIProviderContractSuite, a_request

OLLAMA_MODEL = "llama3.1"
CLAUDE_MODEL = "claude-sonnet-4-5"


def client(handler: Any) -> httpx.AsyncClient:
    return httpx.AsyncClient(transport=httpx.MockTransport(handler))


class TestOllamaAdapter(AIProviderContractSuite):
    @pytest.fixture
    def model(self) -> str:
        return OLLAMA_MODEL

    @pytest.fixture
    def adapter(self) -> OllamaAdapter:
        return self.build(handler=self.responding(self.success_body()))

    def build(self, *, handler: Any) -> OllamaAdapter:
        return OllamaAdapter(client=client(handler), models=frozenset({OLLAMA_MODEL}))

    def success_body(self) -> dict[str, Any]:
        return {
            "model": OLLAMA_MODEL,
            "response": '{"answer": "they raised a Series B"}',
            "done": True,
            "done_reason": "stop",
            "prompt_eval_count": 120,
            "eval_count": 18,
        }

    def truncated_body(self) -> dict[str, Any]:
        return {**self.success_body(), "done_reason": "length"}

    async def test_an_empty_response_is_unusable(self) -> None:
        adapter = self.build(handler=self.responding({**self.success_body(), "response": "   "}))
        with pytest.raises(AIOutputUnusableError, match="no content"):
            await adapter.complete(a_request(OLLAMA_MODEL))

    async def test_the_served_model_is_recorded_over_the_requested_one(self) -> None:
        """A tag may resolve to a specific build. Provenance records what
        answered, so a behaviour change traces to a model change."""
        adapter = self.build(
            handler=self.responding({**self.success_body(), "model": "llama3.1:8b-q4"})
        )
        assert (await adapter.complete(a_request(OLLAMA_MODEL))).model == "llama3.1:8b-q4"


class TestAnthropicAdapter(AIProviderContractSuite):
    @pytest.fixture
    def model(self) -> str:
        return CLAUDE_MODEL

    @pytest.fixture
    def adapter(self) -> AnthropicAdapter:
        return self.build(handler=self.responding(self.success_body()))

    def build(self, *, handler: Any) -> AnthropicAdapter:
        return AnthropicAdapter(
            client=client(handler), api_key="test-key", models=frozenset({CLAUDE_MODEL})
        )

    def success_body(self) -> dict[str, Any]:
        return {
            "model": CLAUDE_MODEL,
            "stop_reason": "tool_use",
            "content": [
                {
                    "type": "tool_use",
                    "name": "respond",
                    "input": {"answer": "they raised a Series B"},
                }
            ],
            "usage": {"input_tokens": 120, "output_tokens": 18},
        }

    def truncated_body(self) -> dict[str, Any]:
        return {**self.success_body(), "stop_reason": "max_tokens"}

    async def test_prose_instead_of_a_tool_call_is_unusable(self) -> None:
        """Nothing is salvageable from a free-text reply when a structure
        was required."""
        adapter = self.build(
            handler=self.responding(
                {
                    **self.success_body(),
                    "content": [{"type": "text", "text": "I can't help with that."}],
                }
            )
        )
        with pytest.raises(AIOutputUnusableError, match="prose"):
            await adapter.complete(a_request(CLAUDE_MODEL))

    async def test_the_api_version_is_pinned_and_the_key_is_sent(self) -> None:
        """An unpinned version turns a vendor-side change into a behaviour
        change nobody can trace to a commit."""
        seen: list[httpx.Request] = []

        def handler(request: httpx.Request) -> httpx.Response:
            seen.append(request)
            return httpx.Response(200, json=self.success_body())

        await self.build(handler=handler).complete(a_request(CLAUDE_MODEL))
        assert seen[0].headers["anthropic-version"] == "2023-06-01"
        assert seen[0].headers["x-api-key"] == "test-key"

    async def test_the_model_is_forced_to_return_the_structure(self) -> None:
        seen: list[dict[str, Any]] = []

        def handler(request: httpx.Request) -> httpx.Response:
            seen.append(json.loads(request.content))
            return httpx.Response(200, json=self.success_body())

        await self.build(handler=handler).complete(a_request(CLAUDE_MODEL))
        assert seen[0]["tool_choice"] == {"type": "tool", "name": "respond"}


class TestTheTwoAdaptersAreIndistinguishableAboveThePort:
    """Vendor neutrality, demonstrated rather than asserted in prose."""

    async def test_both_produce_the_same_shaped_result_for_the_same_request(self) -> None:
        ollama = TestOllamaAdapter()
        anthropic = TestAnthropicAdapter()

        from_ollama = await ollama.build(handler=ollama.responding(ollama.success_body())).complete(
            a_request(OLLAMA_MODEL)
        )
        from_claude = await anthropic.build(
            handler=anthropic.responding(anthropic.success_body())
        ).complete(a_request(CLAUDE_MODEL))

        assert json.loads(from_ollama.content) == json.loads(from_claude.content)
        assert from_ollama.usage.input_tokens == from_claude.usage.input_tokens
        assert from_ollama.usage.output_tokens == from_claude.usage.output_tokens
        assert {from_ollama.vendor, from_claude.vendor} == {AIVendor.OLLAMA, AIVendor.ANTHROPIC}

    async def test_the_same_failure_crosses_as_the_same_platform_error(self) -> None:
        """A 429 means one thing whoever sent it. Retryability, timeouts,
        authentication and truncation are platform concepts before they
        cross the port."""
        ollama = TestOllamaAdapter()
        anthropic = TestAnthropicAdapter()

        for status in (429, 401, 503, 400):
            errors = []
            for suite, model in ((ollama, OLLAMA_MODEL), (anthropic, CLAUDE_MODEL)):
                try:
                    await suite.build(handler=suite.failing(status)).complete(a_request(model))
                except Exception as exc:
                    errors.append(type(exc))
            assert len(set(errors)) == 1, f"status {status} classified differently per vendor"
