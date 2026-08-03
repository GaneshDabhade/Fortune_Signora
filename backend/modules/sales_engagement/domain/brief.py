"""The Approach Brief — a structured object, never a prompt's output.

**The distinction that keeps this extensible.** A brief assembled as markdown
is one shape forever: a second audience, a seventh section or an export format
would each mean a new prompt and a new parser. A brief assembled as *named
sections over one reasoning graph* means the graph is written once and every
future view is a different arrangement of it.

```
   Provider data → evidence → reasoning → ApproachBrief → many views
                                              │
                          deterministic sections ─┴─ narrated sections
```

### Sections are absent, never empty

**A brief with a `Contradictions` heading and nothing under it is a brief that
looks the same for every Target Account** — which is the defect R1-06 named on
the workflow line and D6 named on a filter: *a control that always shows the
same thing teaches people to ignore controls.*

So a section that has nothing to say **is not in the brief at all**, and a
reader who sees *Contradictions* knows before reading it that there is a
contradiction.

### Narration is optional by construction

Every narrated section is keyed by the `Pass` that produced it, and **a brief
with no narration at all is a complete, valid brief**. That is not a
degradation path bolted on — it is the same asymmetry ADR-0200 rests on:
delete the synthesis and the product still works.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum
from types import MappingProxyType
from uuid import UUID

from modules.sales_engagement.domain.fit import ProductFit, ProductRef
from modules.sales_engagement.domain.reasoning import (
    ApproachReasoning,
    RankedRole,
    Recommendation,
    Risk,
    Unknown,
)
from modules.sales_engagement.domain.synthesis import Synthesis


class Pass(StrEnum):
    """One specialized synthesis over the same closed reasoning graph.

    **Six passes, one graph.** Each answers a different question a seller has
    about the *same* facts, which is why they are passes rather than prompts on
    different data — and why adding a seventh costs an artifact rather than a
    pipeline.

    ### Why six values when no prompt exists yet

    This is deliberately **not** the `FitDimension` case. There, five values
    would have needed *reasoning that does not exist* — a declaration nobody
    has made — so the code could never have emitted them. **Here the code path
    is identical for every value**: a pass is validated, keyed and rendered by
    the same generic mechanism, and only the artifact behind it is outstanding.
    A brief with none of them is valid, and each becomes reachable the moment
    its prompt is released.
    """

    EXECUTIVE_SUMMARY = "executive_summary"
    """The account in thirty seconds."""

    CONVERSATION_STRATEGY = "conversation_strategy"
    """What the first conversation should be about."""

    EVIDENCE_NARRATION = "evidence_narration"
    """Why the recommendation exists, in connected prose."""

    RISK_NARRATION = "risk_narration"
    """What is uncertain, and what that means commercially."""

    QUESTIONS = "questions"
    """Discovery questions, from what the reasoning could not settle."""

    OBJECTIONS = "objections"
    """What to expect back, and which claims to avoid making."""


@dataclass(frozen=True, slots=True)
class ApproachBrief:
    """Everything Signora can say about approaching one Target Account.

    **Deterministic sections first, narration second**, and the order is the
    architecture: every field above `narration` exists without a model, and a
    brief whose narration is empty is complete rather than broken.

    **`reasoning_version` and the evidence identity are carried**, so a brief a
    seller acted on six months ago can be explained by what was true then —
    the insertion point Commercial Memory needs, without materializing
    anything yet.
    """

    account_id: UUID
    recommendation: Recommendation
    #: Absent when the seller overrode, when two products tie, or when the
    #: portfolio fits nothing. **Never guessed.**
    product: ProductRef | None
    #: Absent when a product was chosen by a person — an override is an
    #: answer, and a ranking beside it invites re-litigation.
    fits: tuple[ProductFit, ...]
    roles: tuple[RankedRole, ...]
    unknowns: tuple[Unknown, ...]
    risks: tuple[Risk, ...]
    narration: Mapping[Pass, Synthesis]

    def sections(self) -> tuple[str, ...]:
        """Which sections this brief actually has, in reading order.

        **Computed, not declared.** A renderer asking *"what is on this
        brief?"* gets the answer from the brief rather than checking six fields
        and remembering the rule — and the rule lives in one place, so a
        seventh section cannot be added to the object and forgotten by the
        screen.
        """
        present: list[str] = ["recommendation"]
        if self.product is not None:
            present.append("product")
        if self.fits:
            present.append("product_fit")
        if self.roles:
            present.append("roles")
        if self.unknowns:
            present.append("unknowns")
        if self.risks:
            present.append("risks")
        present.extend(one.value for one in Pass if one in self.narration)
        return tuple(present)

    @property
    def is_narrated(self) -> bool:
        """Whether any pass survived validation.

        **A brief is complete without one.** This exists so a caller can say
        *"prose was refused"* in the operational record rather than inferring
        it from an empty mapping.
        """
        return bool(self.narration)


def assemble(
    *,
    reasoning: ApproachReasoning,
    fits: tuple[ProductFit, ...],
    product: ProductRef | None,
    narration: Mapping[Pass, Synthesis] | None = None,
) -> ApproachBrief:
    """Compose one brief from reasoning that is already complete.

    **No judgement happens here.** Every value was decided by the deterministic
    graph; this arranges them and attaches whatever narration survived
    validation. A decision creeping into assembly would be commercial reasoning
    outside the layer that is tested for it.
    """
    return ApproachBrief(
        account_id=reasoning.account_id,
        recommendation=reasoning.recommendation,
        product=product,
        fits=fits,
        roles=reasoning.roles,
        unknowns=reasoning.unknowns,
        risks=reasoning.risks,
        # **Frozen at the boundary.** A caller holding the original mapping
        # could otherwise add a pass after validation, which is precisely the
        # hole the synthesis contract exists to close.
        narration=MappingProxyType(dict(narration or {})),
    )
