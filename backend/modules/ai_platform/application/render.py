"""Turning an evidence set into the text a model reads.

The one place language and evidence meet, and deliberately a small one. The
evidence domain says nothing about wording; the prompt artifact says nothing
about a particular account. This function joins them, and does nothing else.

**Deterministic by construction.** The evidence set is already in canonical
order, attributes are already sorted, and this adds no ordering of its own —
so the same evidence always renders to the same text, and a recorded
``evidence_digest`` identifies exactly what the model saw.

Every fact is rendered with its citation token, because a model cannot cite
what it was never shown how to name.
"""

from __future__ import annotations

from modules.ai_platform.domain.evidence import EvidenceFact, EvidenceSet
from modules.ai_platform.domain.prompt import PromptError, PromptVersion

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
    return prompt.text.replace(FACTS_PLACEHOLDER, _facts(evidence))


def _facts(evidence: EvidenceSet) -> str:
    return "\n\n".join(_fact(fact) for fact in evidence)


def _fact(fact: EvidenceFact) -> str:
    lines = [f"[{fact.ref.token}] {fact.summary}"]
    lines.extend(f"  {name}: {value}" for name, value in fact.attributes)
    return "\n".join(lines)
