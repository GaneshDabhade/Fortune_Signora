"""The synthesis port, satisfied through the AI Provider Abstraction Layer.

**The only file in this module that touches a model, and it still names no
vendor** (`CLAUDE.md` §10). It asks the registry `for_model(model)` and uses
whatever adapter answers — Ollama in development, a hosted commercial model in
production (ADR-0028), or one that does not exist yet.

### What this deliberately does not do

**It does not validate, ground, or repair.** The reply crosses the port as text
and is parsed and fenced above it. An adapter that quietly fixed a malformed
draft would be repairing the exact defect the evaluation exists to measure.

**It does not choose sampling policy in more than one place.** Temperature and
token budget are stated here, once, as the synthesis policy — the same rule
`InferenceRequest` documents about its own required fields.

### The stated limitation

**A synthesis does not yet write an `ai_inference` record.** `Infer` owns that
path and is shaped around an `EvidenceSet`, which a commercial synthesis never
has — it is shown a reasoning graph. Reshaping `Infer` to accept a second input
kind is `ai_platform`'s decision and not this lane's (§20e), so it folds into
[C-214](../../../../docs/LANE_COORDINATION.md) alongside the release-derivation
divergence.

**What that costs today is bounded and stated rather than hidden**: a refusal,
a malformed draft and a provider failure are all carried on `PassResult` with
their detail, so nothing is silent — but they are not yet durable beyond the
caller, and *observability is a product capability* (`CLAUDE.md` §2). It is
recorded as a limitation of this slice, not as a property of the design.
"""

from __future__ import annotations

import json
from typing import Any, Final
from uuid import UUID, uuid4

from modules.ai_platform.public import AIProviderRegistry, InferenceRequest
from modules.sales_engagement.application.ports import ModelReply
from modules.sales_engagement.domain.draft import SCHEMA

#: Synthesis sampling policy, decided once.
#:
#: **Low, and not because it makes the output reproducible.** Batching, hardware
#: and silent vendor-side model updates all move output at any temperature, and
#: no part of this design may claim reproducibility on the strength of this
#: number (ADR-0028). It is low because a strategist's summary should vary as
#: little as the closed set it is compiled from — and because *stability across
#: repeated runs* is one of the dimensions this pass is measured on.
TEMPERATURE: Final = 0.1

#: Enough for three short paragraphs and the JSON that carries them. A pass that
#: needs more than this has stopped being an executive summary.
MAX_OUTPUT_TOKENS: Final = 1200

TIMEOUT_SECONDS: Final = 90.0

_SCHEMA: Final[dict[str, Any]] = json.loads(SCHEMA)


class ProviderSynthesisModel:
    """Satisfies `SynthesisModel` through the AI Provider Abstraction Layer."""

    def __init__(self, registry: AIProviderRegistry) -> None:
        self._registry = registry

    async def complete(
        self, *, prompt: str, model: str, workspace_id: UUID, correlation_id: UUID
    ) -> ModelReply:
        adapter = self._registry.for_model(model)
        result = await adapter.complete(
            InferenceRequest(
                model=model,
                prompt=prompt,
                output_schema=_SCHEMA,
                workspace_id=workspace_id,
                correlation_id=correlation_id,
                max_output_tokens=MAX_OUTPUT_TOKENS,
                temperature=TEMPERATURE,
                timeout_seconds=TIMEOUT_SECONDS,
            )
        )
        # **Generated here, and the limitation above says why.** When a
        # synthesis becomes a durable `ai_inference` row, this id becomes that
        # row's — nothing above the port changes, because `Synthesis` already
        # carries an opaque `inference_id` it never interprets.
        return ModelReply(text=result.content, inference_id=uuid4())
