"""HTTP response schemas for the AI Platform's narration read path.

**The first model-authored content in the product**, and the first response
whose provenance is part of the contract rather than an operational detail.

Two rules shape every field here:

**A statement and its citations are inseparable.** The grounding guarantee is
that every sentence rests on evidence the deterministic pipeline computed, and
a wire format that could carry the prose without the tokens would make the
guarantee unobservable to the only party it exists for. There is deliberately
no flattened `text` field holding the whole narration: a consumer that rendered
it would be rendering un-cited prose, which is exactly what the domain refuses
to produce.

**Provenance is on the response, not reachable from it.** *Which prompt · which
model · when* are answered without a second request, because a customer reading
generated language is entitled to know what generated it at the moment they
read it — not after following a link they will not follow.

**What is deliberately absent:** `id`, `correlation_id`, `inference_id` and
`prompt_fingerprint` — the operational record's identifiers. They are how an
engineer traces a call, not how a seller decides anything. `evidence_digest` is
absent for a different reason worth stating: it is a hash over the closed
evidence set, and a customer cannot verify a hash they cannot recompute. The
verifiable form of *"which evidence"* is the citation tokens on each statement,
which are here.
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from modules.ai_platform.domain.grounding import GroundedStatement
from modules.ai_platform.domain.narration import MaterializedNarration


class NarrationStatementResponse(BaseModel):
    """One sentence, and the evidence it rests on."""

    model_config = ConfigDict(frozen=True)

    text: str = Field(
        description=(
            "One statement, in plain language. Written by a model, and constrained to say "
            "nothing the evidence below does not support — the platform never limits what a "
            "model writes, only what it may reference."
        )
    )
    evidence: tuple[str, ...] = Field(
        description=(
            "The facts this sentence rests on, as citation tokens (`kind:id`). Never empty: "
            "an uncited statement is refused before it is stored, so a sentence you cannot "
            "check does not reach you."
        )
    )

    @classmethod
    def from_domain(cls, statement: GroundedStatement) -> "NarrationStatementResponse":
        return cls(text=statement.text, evidence=statement.evidence)


class AccountNarrationResponse(BaseModel):
    """The grounded explanation of one account, with what produced it."""

    model_config = ConfigDict(frozen=True)

    account_id: UUID = Field(description="The company this explains.")

    statements: tuple[NarrationStatementResponse, ...] = Field(
        description=(
            "The explanation, sentence by sentence, in the order it was written. Kept as "
            "separate statements rather than one paragraph **because each carries its own "
            "citations** — joining them into prose would discard the mapping from claim to "
            "evidence, which is the only reason to trust any of it."
        )
    )

    prompt: str = Field(
        description="Which prompt produced this, as `name@version`. A versioned, reviewed "
        "repository artifact — not a string somebody typed at runtime."
    )
    model: str = Field(
        description="Which model wrote it. Recorded because the same prompt on a different "
        "model is a different result, and a released prompt may only be used with pairings "
        "it has actually been measured against."
    )
    vendor: str = Field(
        description=(
            "Who served the call. **Provenance only** — no behaviour anywhere in Signora "
            "depends on which vendor answered, and this is recorded so a result can be "
            "attributed rather than so anything can branch on it."
        )
    )
    generated_at: datetime = Field(
        description=(
            "When this was written. It has not changed since: a better explanation is a new "
            "narration, never an edit — otherwise the record of what a customer was actually "
            "shown would be destroyed by improving it."
        )
    )

    @classmethod
    def from_domain(
        cls, narration: MaterializedNarration
    ) -> "AccountNarrationResponse":
        return cls(
            account_id=narration.subject.id,
            statements=tuple(
                NarrationStatementResponse.from_domain(s) for s in narration.statements
            ),
            prompt=f"{narration.prompt_name}@{narration.prompt_version}",
            model=narration.model,
            vendor=narration.vendor.value,
            generated_at=narration.created_at,
        )


__all__ = ["AccountNarrationResponse", "NarrationStatementResponse"]
