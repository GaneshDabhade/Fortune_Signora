"""The Ollama adapter — Signora's development runtime.

**Development only.** Never a production dependency, never a fallback,
never a cost tier (ADR-0028). Nothing above this file knows it exists: the
registry resolves a *model* to an adapter, so no caller can ask for Ollama
even deliberately.

Everything Ollama-shaped stops here. The `/api/generate` endpoint, the
`format` field carrying a JSON Schema, `eval_count` meaning output tokens,
`done_reason` signalling truncation — none of that vocabulary crosses the
port. What leaves is an ``InferenceResult`` identical in shape to the one
Anthropic's adapter returns, which is the whole point of the contract suite
running against both.
"""

from __future__ import annotations

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

VENDOR = AIVendor.OLLAMA


class OllamaAdapter:
    """Satisfies ``AIProviderAdapter`` against a local Ollama server."""

    def __init__(
        self,
        *,
        client: httpx.AsyncClient,
        models: frozenset[str],
        base_url: str = "http://localhost:11434",
    ) -> None:
        self._client = client
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
            "prompt": request.prompt,
            # Ollama's schema-constrained decoding. The platform's contract
            # is "output matching this schema"; how a vendor achieves it is
            # exactly what an adapter exists to hide.
            "format": dict(request.output_schema),
            "stream": False,
            "options": {
                "temperature": request.temperature,
                "num_predict": request.max_output_tokens,
            },
        }

        started = time.perf_counter_ns()
        try:
            response = await self._client.post(
                f"{self._base_url}/api/generate",
                json=payload,
                timeout=request.timeout_seconds,
            )
        except Exception as exc:
            raise classify_transport(VENDOR, exc) from exc
        # Measured locally rather than read from the vendor's own timing, so
        # the number means the same thing for every adapter.
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

    if body.get("done_reason") == "length":
        raise AIOutputUnusableError(
            VENDOR,
            "output was cut short by the token ceiling, so the structure is incomplete. "
            "Distinct from a grounding failure: nothing was claimed wrongly, the response "
            "simply stopped.",
        )

    content = body.get("response")
    if not isinstance(content, str) or not content.strip():
        raise AIOutputUnusableError(VENDOR, "response carried no content.")

    return InferenceResult(
        content=content,
        # What actually served the call, which is not always what was asked
        # for: a tag may resolve to a specific build.
        model=body.get("model") or request.model,
        vendor=VENDOR,
        usage=InferenceUsage(
            input_tokens=int(body.get("prompt_eval_count") or 0),
            output_tokens=int(body.get("eval_count") or 0),
            latency_ms=latency_ms,
        ),
    )
