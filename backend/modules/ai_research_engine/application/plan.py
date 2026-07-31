"""Asking a model what is worth comparing — the module's only model call so far.

**One function, and everything it needs is injected.** `Infer` is the AI
Platform's single path to a model: it resolves the provider *by model*, renders
the evidence, validates the response against `ResearchPlan`'s schema, grounds it
against the evidence set, and records the call. None of that is repeated here,
and none of it can be bypassed from here.

**No vendor is named, and there is nowhere to name one.** This file knows a
model string and nothing else; which adapter serves it is `for_model`'s answer
and configuration's decision. `if vendor == …` is not merely forbidden here —
there is no vendor in scope to branch on.

---

**Grounding is not re-checked.** `Infer.execute` calls `verify()` before
returning, so a plan reaching this function's caller has already had every
target resolved inside the evidence the planner was shown. Re-checking would be
a second representation of one guarantee, and the second copy is the one that
eventually disagrees.

**The plan is returned exactly as the model produced it** — steps are not
reordered or normalised. Repository evidence settles this rather than
preference: `ai_reasoning.stated_reasoning` and `ai_narration.statements` both
round-trip in model order, and *a materialized AI artifact is a historical
fact*, so reordering one is editing it. Nothing downstream needs the order
canonical either — a finding's identity is derived from its derivation, its
version and its **sorted** citations, so two orderings of one plan execute to
identical findings with identical ids. The determinism is already where it has
to be, and imposing more would cost the only record of what the model actually
returned.
"""

from __future__ import annotations

from uuid import UUID

from modules.ai_platform.public import EvidenceSet, Infer, InferenceInput, InferenceOutput
from modules.ai_research_engine.domain.plan import ResearchPlan

PROMPT_NAME = "research_planning"
PROMPT_VERSION = 1


async def plan_research(
    infer: Infer,
    *,
    model: str,
    correlation_id: UUID,
    evidence: EvidenceSet,
) -> InferenceOutput[ResearchPlan]:
    """What is worth comparing about this account, and the record of the asking.

    A function rather than a class: there is exactly one thing to do and no
    state to hold. `InferenceOutput` is returned rather than the bare plan so a
    caller can record which model, which prompt and which evidence digest
    produced it without a second lookup — **for inferred knowledge,
    auditability is a property of the act**, and the act is only fully known
    here.
    """
    return await infer.execute(
        InferenceInput(
            prompt_name=PROMPT_NAME,
            prompt_version=PROMPT_VERSION,
            model=model,
            evidence=evidence,
            correlation_id=correlation_id,
        ),
        ResearchPlan,
    )
