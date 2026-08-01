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
which are here — and, since **D42**, the facts those tokens address, together
with `evidence_unchanged`, which is the *comparison's* answer rather than the
hash itself.
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from modules.ai_platform.domain.evidence import EvidenceFact, EvidenceRef, EvidenceSet
from modules.ai_platform.domain.grounding import GroundedStatement
from modules.ai_platform.domain.narration import MaterializedNarration


class EvidenceFactResponse(BaseModel):
    """One fact a statement cites — **exactly what the model was given.**

    Not a record fetched from a table afterwards: the summary and attributes
    here are the ones assembled into the prompt, which is the strongest
    available form of *"here is what it was told."*

    The summary's language belongs to the module that owns the concept, so a
    citation resolves into the pipeline's own vocabulary rather than the
    substrate's paraphrase of it.
    """

    model_config = ConfigDict(frozen=True)

    token: str = Field(
        description="The citation this answers, exactly as it appears on a statement."
    )
    kind: str = Field(
        description=(
            "What sort of thing this is, in the pipeline's own words — `buying_score`, "
            "`signal_contribution`, `opportunity`. A reader is told which layer of the "
            "argument a sentence is standing on."
        )
    )
    summary: str = Field(
        description="The fact in one sentence, written by the module that owns the concept."
    )
    attributes: dict[str, str] = Field(
        description=(
            "The figures behind the summary, in canonical order. **Rendered as text**, "
            "because the evidence set canonicalises by type and the textual form is what the "
            "model was shown and what the digest covers — a number re-typed on the wire would "
            "be a different fact from the one that was cited."
        )
    )

    @classmethod
    def from_domain(cls, fact: EvidenceFact) -> "EvidenceFactResponse":
        return cls(
            token=fact.ref.token,
            kind=fact.ref.kind,
            summary=fact.summary,
            attributes={name: str(value) for name, value in fact.attributes},
        )


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

    facts: tuple[EvidenceFactResponse, ...] = Field(
        description=(
            "The facts the statements cite, each appearing **once** however many sentences "
            "rest on it. Looked up by token rather than repeated inside each statement: the "
            "citation is the token, and carrying the same fact three times would be three "
            "copies of one truth. Empty when the evidence could not be re-derived — which is "
            "an answer, not an error, and `evidence_unchanged` is false whenever it happens."
        )
    )
    evidence_unchanged: bool = Field(
        description=(
            "Whether the evidence behind this account is still **byte-identical** to what the "
            "model was shown, by comparing the re-derived set against the digest recorded when "
            "this was written. False means these sentences describe what was true then and the "
            "account has moved since — the narration is not wrong, it is dated, and it is never "
            "edited to catch up. The digest itself is not on the wire: a customer cannot verify "
            "a hash they cannot recompute, so what they get is the comparison's answer."
        )
    )

    @classmethod
    def from_domain(
        cls, narration: MaterializedNarration, evidence: EvidenceSet | None
    ) -> "AccountNarrationResponse":
        """Assemble the response, resolving each cited token against `evidence`.

        `evidence` is the set **re-derived now**, which is why nothing here
        trusts it without the digest: presenting today's facts as the ones a
        model saw is the quiet lie this method exists to refuse.
        """
        statements = tuple(
            NarrationStatementResponse.from_domain(s) for s in narration.statements
        )
        return cls(
            account_id=narration.subject.id,
            statements=statements,
            facts=_resolve(statements, evidence),
            evidence_unchanged=(
                evidence is not None and evidence.digest == narration.evidence_digest
            ),
            prompt=f"{narration.prompt_name}@{narration.prompt_version}",
            model=narration.model,
            vendor=narration.vendor.value,
            generated_at=narration.created_at,
        )


def _resolve(
    statements: tuple[NarrationStatementResponse, ...], evidence: EvidenceSet | None
) -> tuple[EvidenceFactResponse, ...]:
    """The facts the statements actually cite, in citation order, deduplicated.

    **Only what is cited.** The evidence set is everything the model was
    offered; the statements name what it used. Returning the difference would
    show a reader evidence no sentence rests on, which is the opposite of what
    a citation is for.

    A token that no longer resolves is simply absent — the set is re-derived,
    so a signal that has stopped contributing takes its fact with it. That case
    is always accompanied by `evidence_unchanged` being false, which is what
    explains it; a missing fact never has to explain itself alone.
    """
    if evidence is None:
        return ()

    seen: set[str] = set()
    resolved: list[EvidenceFactResponse] = []
    for statement in statements:
        for token in statement.evidence:
            if token in seen:
                continue
            seen.add(token)
            fact = evidence.resolve(EvidenceRef.parse(token))
            if fact is not None:
                resolved.append(EvidenceFactResponse.from_domain(fact))
    return tuple(resolved)


__all__ = [
    "AccountNarrationResponse",
    "EvidenceFactResponse",
    "NarrationStatementResponse",
]
