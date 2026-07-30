"""Test doubles for the AI Provider Port.

A scripted fake, and deliberately so. Deterministic engineering behaviour —
the port contract, the failure taxonomy, routing, registration guards — is
verified here and **never against a model** (CLAUDE.md §10). Grounding,
prompt evaluation and output quality are the other tier: those need a real
model, because the failures they exist to catch are ones a fake would never
produce unless told to.

That the port is satisfiable by a ~30-line fake is itself the evidence that
it is a real boundary — the M5B ``SignalReader`` finding, applied forward
rather than discovered under pressure.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from modules.ai_platform.domain.provider import (
    AIProviderDescriptor,
    AIVendor,
    InferenceRequest,
    InferenceResult,
)
from modules.ai_platform.domain.usage import InferenceUsage


@dataclass
class FakeAdapter:
    """A scripted adapter. Returns what it was given, records what it saw."""

    vendor: AIVendor = AIVendor.OLLAMA
    models: frozenset[str] = field(default_factory=lambda: frozenset({"fake-model"}))
    supports_structured_output: bool = True
    content: str = "{}"
    error: Exception | None = None
    #: Every request this adapter received, in order. Lets a test assert
    #: what crossed the port without reaching inside the adapter.
    seen: list[InferenceRequest] = field(default_factory=list)

    def describe(self) -> AIProviderDescriptor:
        return AIProviderDescriptor(
            models=self.models,
            supports_structured_output=self.supports_structured_output,
            vendor=self.vendor,
        )

    async def complete(self, request: InferenceRequest) -> InferenceResult:
        self.seen.append(request)
        if self.error is not None:
            raise self.error
        return InferenceResult(
            content=self.content,
            model=request.model,
            vendor=self.vendor,
            usage=InferenceUsage(input_tokens=10, output_tokens=5, latency_ms=42),
        )
