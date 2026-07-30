"""The Anthropic adapter — Signora's production runtime.

Reached over ``httpx`` rather than the vendor SDK, deliberately. Adding
``anthropic`` would be a new dependency requiring approval (CLAUDE.md §6),
and it would bring its own retry and timeout behaviour to argue with the
platform's. One transport for both adapters also makes the shared contract
suite mean more: when Ollama and Anthropic behave identically, that is the
*adapters* agreeing, not two SDKs coincidentally agreeing.

Everything Anthropic-shaped stops here. Structured output is obtained by
forcing a single tool call — a vendor convention nothing above the port has
heard of. The `x-api-key` header, the pinned API version, the content-block
list, `stop_reason`: none of it crosses.
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

VENDOR = AIVendor.ANTHROPIC

#: Pinned, never a floating alias. An unpinned version turns a vendor-side
#: change into a behaviour change nobody can trace to a commit.
API_VERSION = "2023-06-01"

#: The tool the model is forced to call. Its name is arbitrary and never
#: leaves this file; what matters is that requiring a tool call is how this
#: vendor guarantees a response matching a schema.
_TOOL = "respond"


class AnthropicAdapter:
    """Satisfies ``AIProviderAdapter`` against the Anthropic Messages API."""

    def __init__(
        self,
        *,
        client: httpx.AsyncClient,
        api_key: str,
        models: frozenset[str],
        base_url: str = "https://api.anthropic.com",
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
            "max_tokens": request.max_output_tokens,
            "temperature": request.temperature,
            "tools": [
                {
                    "name": _TOOL,
                    "description": "Return the response in the required structure.",
                    "input_schema": dict(request.output_schema),
                }
            ],
            "tool_choice": {"type": "tool", "name": _TOOL},
            "messages": [{"role": "user", "content": request.prompt}],
        }

        started = time.perf_counter_ns()
        try:
            response = await self._client.post(
                f"{self._base_url}/v1/messages",
                json=payload,
                headers={
                    "x-api-key": self._api_key,
                    "anthropic-version": API_VERSION,
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

    if body.get("stop_reason") == "max_tokens":
        raise AIOutputUnusableError(
            VENDOR,
            "output was cut short by the token ceiling, so the structure is incomplete. "
            "Distinct from a grounding failure: nothing was claimed wrongly, the response "
            "simply stopped.",
        )

    content = _tool_input(body)
    usage = body.get("usage") or {}
    return InferenceResult(
        # Serialised here so the port's contract is the same string-of-JSON
        # every adapter returns. A caller that received a dict from one
        # vendor and a string from another would branch on vendor, which is
        # the one thing the abstraction exists to prevent.
        content=json.dumps(content, sort_keys=True),
        model=body.get("model") or request.model,
        vendor=VENDOR,
        usage=InferenceUsage(
            input_tokens=int(usage.get("input_tokens") or 0),
            output_tokens=int(usage.get("output_tokens") or 0),
            latency_ms=latency_ms,
        ),
    )


def _tool_input(body: dict[str, Any]) -> dict[str, Any]:
    """The forced tool call's arguments — this vendor's structured output."""
    for block in body.get("content") or []:
        if isinstance(block, dict) and block.get("type") == "tool_use":
            arguments = block.get("input")
            if isinstance(arguments, dict):
                return arguments
    raise AIOutputUnusableError(
        VENDOR,
        "the model answered in prose rather than calling the required tool, so there is no "
        "structure to validate. Nothing is salvageable from a free-text reply here.",
    )
