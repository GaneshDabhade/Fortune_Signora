"""The OpenAI adapter — [TASK-420](../../../../../docs/BACKLOG.md), Epic H slice one.

🔴 **This row exists to TEST a claim rather than to add a vendor.** 📁
[ADR-0012](../../../../../docs/architecture/adr/0012-ai-platform-architecture.md)
says a vendor integrates by describing what it supports, and **nothing had ever
tested that by adding one.** ⚡ *"If anything above the port must change, that
is the finding."*

## ✅ Nothing above the port changed, and the reason is worth recording

⚠️ **The two vendors obtain structured output by completely different
mechanisms**, and neither crosses:

**Anthropic** — ⛔ **a forced tool call.** `tools` + `tool_choice`, and the
arguments of the `tool_use` block ARE the answer.

**OpenAI** — ⛔ **a native `response_format`.** `json_schema` with
`strict: true`, and the answer is `choices[0].message.content` **as a string**.

⚡ **`AIProviderAdapter` needed no change, no new method and no optional
parameter.** ✅ **That is the epic's premise holding**, and it held because the
port asks for *one describe and one complete* rather than for a vendor's shape.

## 🔴 The one thing that DID need care, and it is the port's contract

📁 **The Anthropic adapter's own note**: *"Serialised here so the port's
contract is the same string-of-JSON every adapter returns. A caller that
received a dict from one vendor and a string from another would branch on
vendor."*

⚠️ **OpenAI already returns a string, so the tempting line is to pass it
through.** ⛔ **That would break the contract in a way nothing would catch**:
the two vendors would return the same content with **different key order and
different whitespace**, and anything that compared, hashed or diffed two
results would see a vendor difference. ⚡ **So it is parsed and re-serialised
with `sort_keys=True`, exactly as Anthropic's is** — 📁 [§2](../../../../../CLAUDE.md),
*hidden inputs are architecture defects*, and provider identity is the hidden
input this layer exists to remove.

## ⛔ What is deliberately not here

**Bedrock and Azure OpenAI.** 📁 The row's own words: they are *reserved*
rather than recognised, and `AIVendor` says why — *"a member here with no
ratified status is a speculative extension point."*

**The vendor SDK.** ⚡ Reached over `httpx` for the reason the Anthropic
adapter gives: a new dependency needs approval ([§6](../../../../../CLAUDE.md)),
and it would bring its own retry and timeout behaviour to argue with the
platform's. ✅ **One transport for all three adapters also makes the shared
contract suite mean more** — when they behave identically, that is the
*adapters* agreeing rather than three SDKs coincidentally agreeing.
"""

from __future__ import annotations

import json
import time
from typing import Any

import httpx

from modules.ai_platform.domain.provider import (
    AIOutputUnusableError,
    AIProviderDescriptor,
    AIVendor,
    InferenceRequest,
    InferenceResult,
)
from modules.ai_platform.domain.usage import InferenceUsage
from modules.ai_platform.infrastructure.adapters.transport import (
    classify_response,
    classify_transport,
)

VENDOR = AIVendor.OPENAI

#: The schema's name in the request. ⛔ **Arbitrary and never leaves this
#: file**, exactly as Anthropic's tool name is: what matters is that naming a
#: schema is how this vendor guarantees a response matching one.
_SCHEMA_NAME = "response"


class OpenAIAdapter:
    """Satisfies ``AIProviderAdapter`` against the OpenAI Chat Completions API."""

    def __init__(
        self,
        *,
        client: httpx.AsyncClient,
        api_key: str,
        models: frozenset[str],
        base_url: str = "https://api.openai.com",
    ) -> None:
        self._client = client
        self._api_key = api_key
        self._models = models
        self._base_url = base_url.rstrip("/")

    def describe(self) -> AIProviderDescriptor:
        return AIProviderDescriptor(
            models=self._models,
            supports_structured_output=True,
            vendor=VENDOR,
        )

    async def complete(self, request: InferenceRequest) -> InferenceResult:
        payload: dict[str, Any] = {
            "model": request.model,
            "max_completion_tokens": request.max_output_tokens,
            "temperature": request.temperature,
            # ⚡ **`strict: true` is what makes this a guarantee rather than a
            # request.** ⛔ Without it the vendor treats the schema as a hint
            # and the adapter would be validating hope.
            "response_format": {
                "type": "json_schema",
                "json_schema": {
                    "name": _SCHEMA_NAME,
                    "strict": True,
                    "schema": dict(request.output_schema),
                },
            },
            "messages": [{"role": "user", "content": request.prompt}],
        }

        started = time.perf_counter_ns()
        try:
            response = await self._client.post(
                f"{self._base_url}/v1/chat/completions",
                json=payload,
                headers={
                    # ⛔ **`Authorization: Bearer`, not `x-api-key`.** One of
                    # several vendor conventions that stop at this file.
                    "Authorization": f"Bearer {self._api_key}",
                    "content-type": "application/json",
                },
                timeout=request.timeout_seconds,
            )
        except Exception as exc:
            raise classify_transport(VENDOR, exc) from exc
        latency_ms = (time.perf_counter_ns() - started) // 1_000_000

        failure = classify_response(VENDOR, response)
        if failure is not None:
            raise failure

        return _read(response, request, latency_ms)


def _read(response: httpx.Response, request: InferenceRequest, latency_ms: int) -> InferenceResult:
    try:
        body = response.json()
    except ValueError as exc:
        raise AIOutputUnusableError(VENDOR, f"response was not JSON: {exc}") from exc

    choice = _first_choice(body)

    if choice.get("finish_reason") == "length":
        raise AIOutputUnusableError(
            VENDOR,
            "output was cut short by the token ceiling, so the structure is incomplete. "
            "Distinct from a grounding failure: nothing was claimed wrongly, the response "
            "simply stopped.",
        )

    message = choice.get("message")
    if not isinstance(message, dict):
        raise AIOutputUnusableError(VENDOR, "the choice carried no message")

    # ⚡ **A refusal is its own field on this vendor, and it is NOT an error
    # about the request.** ⛔ Reported as unusable rather than retried: the
    # model declined, and asking again is how a caller turns one refusal into
    # several.
    refusal = message.get("refusal")
    if isinstance(refusal, str) and refusal.strip():
        raise AIOutputUnusableError(
            VENDOR,
            f"the model declined to answer, so there is no structure to validate: {refusal}",
        )

    usage = body.get("usage") or {}
    return InferenceResult(
        # 🔴 **Re-serialised rather than passed through.** This vendor returns
        # a string already, and returning it unchanged would give two vendors
        # different key order for identical content — a provider difference
        # visible to anything that compares or hashes a result.
        content=json.dumps(_content(message), sort_keys=True),
        model=body.get("model") or request.model,
        vendor=VENDOR,
        usage=InferenceUsage(
            input_tokens=int(usage.get("prompt_tokens") or 0),
            output_tokens=int(usage.get("completion_tokens") or 0),
            latency_ms=latency_ms,
        ),
    )


def _first_choice(body: dict[str, Any]) -> dict[str, Any]:
    choices = body.get("choices")
    if not isinstance(choices, list) or not choices:
        raise AIOutputUnusableError(VENDOR, "the response carried no choices")
    first = choices[0]
    if not isinstance(first, dict):
        raise AIOutputUnusableError(VENDOR, "the first choice was not an object")
    return first


def _content(message: dict[str, Any]) -> dict[str, Any]:
    """This vendor's structured output — **a JSON string, parsed here.**

    ⛔ **A string that is valid JSON but not an object is unusable.** ⚡ The
    schema asks for an object, and `[1, 2, 3]` would satisfy *"is JSON"* while
    satisfying nothing a caller can read a field from.
    """
    raw = message.get("content")
    if not isinstance(raw, str) or not raw.strip():
        raise AIOutputUnusableError(
            VENDOR,
            "the message carried no content, so there is no structure to validate",
        )
    try:
        parsed = json.loads(raw)
    except ValueError as exc:
        raise AIOutputUnusableError(
            VENDOR, f"the structured response was not JSON: {exc}"
        ) from exc
    if not isinstance(parsed, dict):
        raise AIOutputUnusableError(
            VENDOR,
            f"the structured response was {type(parsed).__name__}, not an object",
        )
    return parsed


__all__ = ["VENDOR", "OpenAIAdapter"]
