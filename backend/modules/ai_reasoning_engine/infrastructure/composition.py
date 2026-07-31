"""Composition root for the AI Reasoning Engine.

Wires the adapters into the use case. Everything concrete is constructed here
and nowhere else, so `application/` and `domain/` see only ports.

**`Infer` is a parameter, not a construction**, and that is a finding rather
than a preference. M9 owns its own prompts — `prompts/reasoning@1.md` and its
manifest — and `load_prompt_registry(directory)` is per-directory precisely so
each module can. But the loader lives in `ai_platform/infrastructure/`, and
`public/` sits *below* `infrastructure/` in the layering contract, so it cannot
be published there: a loader that reads the filesystem is infrastructure, and
publishing it would put an infrastructure dependency underneath every consumer
of the AI Platform's contract.

The contract was right to refuse. Binding a module's prompt directory to an
`Infer` is the **application** composition root's job — the one place that may
legitimately import both modules' infrastructure — which is the same place
M8's `build_narrate` is called from. So M9 names the prompt and the version it
ships, because those are the release-rule decisions and a caller free to choose
could route around the rule by naming an unevaluated version; and the caller
supplies an `Infer` bound to `PROMPT_DIR` below.

**`reasoning@1` is authored and unreleased.** `Infer.execute` will refuse it
until it earns a release against the model it is asked to serve, and that
refusal is the release rule working, not a wiring defect to route around.
"""

from __future__ import annotations

from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession

from modules.ai_platform.public import ExplanationSource, Infer
from modules.ai_reasoning_engine.application.reason import Reason
from modules.ai_reasoning_engine.infrastructure.context import PipelineReasoningContext
from modules.ai_reasoning_engine.infrastructure.repository import (
    SqlDecisionPackageRepository,
)
from modules.opportunity_engine.public import OpportunityQueries
from modules.signal_engine.public import SignalQueries
from signora_platform.event_bus import EventPublisher

#: Where M9's prompts live. Exported so the application composition root can
#: bind an `Infer` to them without knowing this module's internal layout.
PROMPT_DIR = Path(__file__).resolve().parent.parent / "prompts"

#: The prompt M9 ships. Named here rather than accepted from a caller: which
#: prompt reasons about an account is the module's decision, and a caller free
#: to choose one could name an unevaluated version and bypass the release rule.
REASONING_PROMPT = "reasoning"
REASONING_PROMPT_VERSION = 1


def build_reason(
    session: AsyncSession,
    *,
    infer: Infer,
    opportunities: OpportunityQueries,
    signals: SignalQueries,
    evidence: ExplanationSource,
    publisher: EventPublisher,
) -> Reason:
    """The only way to construct a producer of Decision Packages.

    The package and its event share the caller's `session`: they are one unit
    of work, so a rolled-back transaction leaves neither behind — a package
    nobody committed was never shown to anyone. Operational history is the
    opposite case and is handled inside `Infer`, whose recorder commits on its
    own transaction because the model call happened whatever became of the
    transaction that asked for it (ADR-0029).
    """
    return Reason(
        infer=infer,
        context=PipelineReasoningContext(
            opportunities=opportunities,
            signals=signals,
            evidence=evidence,
        ),
        repository=SqlDecisionPackageRepository(session),
        publisher=publisher,
        session=session,
        prompt_name=REASONING_PROMPT,
        prompt_version=REASONING_PROMPT_VERSION,
    )
