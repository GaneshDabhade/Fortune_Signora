"""Placing evidence into a prompt template.

**This module composes; it does not decide form.** The Prompt Rendering Protocol
(``domain/rendering.py``) owns what a fact looks like and how a citation is
presented; everything here is the template contract — where the evidence goes,
and refusing a prompt with nowhere to put it.

That division is the whole of ADR-0031's fix. Until M9.5 this file authored the
citation's display form while ``EvidenceRef.parse`` defined the grammar that had
to read it back, and nothing reconciled the two: **a protocol shared by two
components that neither owned.** The disagreement was invisible until a model
took its instructions literally, and it cost three prompts their release.

**Deterministic by construction.** The evidence set is already in canonical
order, attributes are already sorted, and neither this module nor the protocol
adds an ordering — so the same evidence always renders to the same text, and a
recorded ``evidence_digest`` identifies exactly what the model saw.
"""

from __future__ import annotations

from modules.ai_platform.domain.evidence import EvidenceSet
from modules.ai_platform.domain.prompt import PromptError, PromptVersion
from modules.ai_platform.domain.rendering import render_facts

#: Where the facts go in a prompt template.
FACTS_PLACEHOLDER = "{facts}"


def render(prompt: PromptVersion, evidence: EvidenceSet) -> str:
    """The complete prompt text for one inference."""
    if FACTS_PLACEHOLDER not in prompt.text:
        raise PromptError(
            f"prompt {prompt.reference} has no {FACTS_PLACEHOLDER} placeholder, so the "
            "evidence would never reach the model — which would make every statement it "
            "produced ungrounded by construction."
        )
    return prompt.text.replace(FACTS_PLACEHOLDER, render_facts(evidence))
