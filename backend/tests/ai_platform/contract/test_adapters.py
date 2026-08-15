"""Every adapter, against the same contract.

Ollama is the development runtime and Anthropic the production one
(ADR-0028), and below that sentence they are indistinguishable: the same
suite, unmodified, run against each. Where a vendor differs, the *adapter*
absorbs it — the only thing that varies here is the shape of the stubbed
response, which is precisely the vendor detail an adapter exists to hide.

⚡ **OpenAI joined on 2026-08-15** — [TASK-420](../../../../docs/BACKLOG.md),
**and joining is the whole point of the row**: 📁
[ADR-0012](../../../../docs/architecture/adr/0012-ai-platform-architecture.md)
says a vendor integrates by describing what it supports, **and nothing had
ever tested that by adding one.** ✅ **It required no change to this suite, to
the port, or to anything above it** — only a third subclass and a third
stubbed body.

⚠️ **The three obtain structured output three different ways** — a JSON-mode
string, a forced tool call, and a native `response_format` — **and the
agreement tests below cannot tell.**
"""

from __future__ import annotations

import json
from typing import Any

import httpx
import pytest

from modules.ai_platform.domain.provider import AIOutputUnusableError, AIVendor
from modules.ai_platform.infrastructure.adapters.anthropic import AnthropicAdapter
from modules.ai_platform.infrastructure.adapters.ollama import OllamaAdapter
from modules.ai_platform.infrastructure.adapters.openai import OpenAIAdapter
from tests.ai_platform.contract.ai_provider_contract import AIProviderContractSuite, a_request

OLLAMA_MODEL = "llama3.1"
CLAUDE_MODEL = "claude-sonnet-4-5"
GPT_MODEL = "gpt-4.1"


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


class TestOpenAIAdapter(AIProviderContractSuite):
    """🔴 **The third vendor, and the row's actual subject.**

    ⛔ **Nothing above the port changed to admit it** — no new method, no
    optional parameter, no branch. ⚡ **That is
    [ADR-0012](../../../../docs/architecture/adr/0012-ai-platform-architecture.md)'s
    claim holding**, tested for the first time by exercising it.
    """

    @pytest.fixture
    def model(self) -> str:
        return GPT_MODEL

    @pytest.fixture
    def adapter(self) -> OpenAIAdapter:
        return self.build(handler=self.responding(self.success_body()))

    def build(self, *, handler: Any) -> OpenAIAdapter:
        return OpenAIAdapter(
            client=client(handler), api_key="test-key", models=frozenset({GPT_MODEL})
        )

    def success_body(self) -> dict[str, Any]:
        return {
            "model": GPT_MODEL,
            "choices": [
                {
                    "finish_reason": "stop",
                    # ⚡ **A STRING, where Anthropic returns a dict** — the
                    # difference the adapter absorbs.
                    #
                    # 🔴 **The spacing is DELIBERATELY NON-CANONICAL and must
                    # not be tidied.** ⛔ `json.dumps(…, sort_keys=True)` emits
                    # exactly one space after the colon, so a fixture written
                    # canonically makes a pass-through adapter produce the
                    # identical string — **and the byte-identical test below
                    # would pass against the defect it exists to catch.**
                    # ⚠️ **Found by fire-testing that test**, which passed with
                    # the re-serialisation removed until this string changed.
                    "message": {"content": '{"answer":   "they raised a Series B"}'},
                }
            ],
            "usage": {"prompt_tokens": 120, "completion_tokens": 18},
        }

    def truncated_body(self) -> dict[str, Any]:
        return {
            **self.success_body(),
            "choices": [
                {**self.success_body()["choices"][0], "finish_reason": "length"}
            ],
        }

    async def test_a_refusal_is_unusable_rather_than_retried(self) -> None:
        """⚡ **A refusal is its own FIELD on this vendor**, and neither of the
        other two has one. ⛔ **Reported as unusable rather than retried**: the
        model declined, and asking again is how a caller turns one refusal into
        several."""
        adapter = self.build(
            handler=self.responding(
                {
                    **self.success_body(),
                    "choices": [
                        {
                            "finish_reason": "stop",
                            "message": {"refusal": "I can't help with that."},
                        }
                    ],
                }
            )
        )
        with pytest.raises(AIOutputUnusableError, match="declined"):
            await adapter.complete(a_request(GPT_MODEL))

    async def test_json_that_is_not_an_object_is_unusable(self) -> None:
        """⛔ **`[1, 2, 3]` is valid JSON and satisfies nothing.** ⚡ The schema
        asks for an object, and a caller reads fields from it."""
        adapter = self.build(
            handler=self.responding(
                {
                    **self.success_body(),
                    "choices": [
                        {"finish_reason": "stop", "message": {"content": "[1, 2, 3]"}}
                    ],
                }
            )
        )
        with pytest.raises(AIOutputUnusableError, match="not an object"):
            await adapter.complete(a_request(GPT_MODEL))

    @pytest.mark.parametrize(
        ("choices", "expected"),
        [
            ([], "no choices"),
            (["not an object"], "not an object"),
            ([{"finish_reason": "stop", "message": "not an object"}], "no message"),
            ([{"finish_reason": "stop", "message": {"content": "   "}}], "no content"),
            ([{"finish_reason": "stop", "message": {"content": "{not json"}}], "not JSON"),
        ],
    )
    async def test_a_malformed_payload_is_unusable_rather_than_a_crash(
        self, choices: Any, expected: str
    ) -> None:
        """⚠️ **Five shapes a vendor should never send and might.**

        ⛔ **Each must become `AIOutputUnusableError` rather than a
        `TypeError` or a `KeyError`** — 📁 the port's own contract: *"Raises
        only `AIProviderError` subclasses."* ⚡ **A raw exception crossing the
        port would name Python rather than the vendor**, and an engineer
        reading an incident would have no idea which of three adapters
        produced it.

        ✅ **Written because the coverage gate said these five branches had no
        test**, which is a fair reading of *a guard nothing exercises*.
        """
        adapter = self.build(
            handler=self.responding({**self.success_body(), "choices": choices})
        )

        with pytest.raises(AIOutputUnusableError, match=expected):
            await adapter.complete(a_request(GPT_MODEL))

    async def test_the_key_is_a_bearer_token_and_the_schema_is_strict(self) -> None:
        """⛔ **`Authorization: Bearer`, not `x-api-key`** — and `strict` is
        what makes the schema a guarantee rather than a hint. ⚠️ **Without it
        the vendor treats the schema as advisory and the adapter would be
        validating hope.**"""
        seen: list[httpx.Request] = []

        def handler(request: httpx.Request) -> httpx.Response:
            seen.append(request)
            return httpx.Response(200, json=self.success_body())

        await self.build(handler=handler).complete(a_request(GPT_MODEL))

        assert seen[0].headers["authorization"] == "Bearer test-key"
        body = json.loads(seen[0].content)
        assert body["response_format"]["json_schema"]["strict"] is True


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

    async def test_all_three_return_a_byte_identical_body_for_the_same_answer(self) -> None:
        """🔴 **Byte-identical, not merely equal** — [TASK-420](../../../../docs/BACKLOG.md).

        ⚠️ **`json.loads(a) == json.loads(b)` passes for two strings with
        different key order**, and the test above uses exactly that. ⛔ **So it
        would not have caught an adapter that returned its vendor's string
        unchanged**, and OpenAI's arrives already serialised — **the tempting
        line is to pass it through.**

        ⚡ **A caller that hashes, diffs or caches a result would then see a
        difference that is purely the vendor's formatting** — 📁
        [§2](../../../../CLAUDE.md), *hidden inputs are architecture defects*,
        **and provider identity is the hidden input this layer removes.**
        """
        suites = (
            (TestOllamaAdapter(), OLLAMA_MODEL),
            (TestAnthropicAdapter(), CLAUDE_MODEL),
            (TestOpenAIAdapter(), GPT_MODEL),
        )

        bodies = set()
        for suite, model in suites:
            result = await suite.build(
                handler=suite.responding(suite.success_body())
            ).complete(a_request(model))
            bodies.add(result.content)

        assert len(bodies) == 1, f"three vendors returned {len(bodies)} different strings: {bodies}"

    async def test_the_third_vendor_needed_no_change_above_the_port(self) -> None:
        """⚡ **The epic's premise, as an assertion.** 📁 ADR-0012: a vendor
        integrates by *describing what it supports*. ⛔ **So a caller states a
        model and the descriptor answers** — and nothing in that sentence names
        a vendor."""
        openai = TestOpenAIAdapter()

        descriptor = openai.build(handler=openai.responding(openai.success_body())).describe()

        assert descriptor.vendor is AIVendor.OPENAI
        assert descriptor.supports_structured_output
        assert GPT_MODEL in descriptor.models

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
