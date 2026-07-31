"""What research produces: an act, a derivation, and a narration.

Three objects, and **the reason there are three rather than one is the
Knowledge Contract's identity rule**:

    Identity is derived from content **iff** the object is reproducible from
    its inputs; otherwise it is minted. (Rule 1)

A computation repeated over identical inputs is the *same* object. An act
repeated is a *second* act, even when it produces identical words. So:

| Object | Origin | Identity | Because |
|---|---|---|---|
| `ResearchTask` | *not knowledge* | minted | A run happened. Running twice is twice |
| `ResearchFinding` | **DERIVED** | `uuid5` over content | Recomputing must insert nothing |
| `ResearchSynthesis` | **INFERRED** | minted | A model was called. Calling twice is twice |

That split is not designed here — it is the discipline four modules already
follow (`Observation`, `BusinessEvent`, `Signal` and `BuyingScore` derive;
`Claim`, `Opportunity` and `AINarration` mint), written down for the first time
in the Knowledge Contract and applied unchanged.

---

**The ruling that shapes this file.** M10 was ruled **Internal Research** on
2026-07-31: research explores, compares and synthesises knowledge Signora
already owns, and reaches no external source. Findings are therefore DERIVED —
and *DERIVED is a claim about how content was produced, not a label that can be
applied to it* (Rule 8: promotion does not exist).

**So a finding's content is computed, and the model never authors it.** The
model plans *which comparison is worth running* — attention, which Rule 9
permits — and deterministic code computes the answer over cited rows. A model
paraphrase of derived facts would be INFERRED no matter what field it sat in.

**This is why a finding has no free-text field.** Not an oversight and not a
limitation: it is the same shape every other DERIVED object in this repository
already has. `Signal`, `BusinessEvent` and `Observation` are typed data with no
prose; narration appears for the first time at M9, authored by a model and
grounded. A `summary: str` here would be a place for a model to write, and a
type that offers one has already lost the argument.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import ClassVar, Final
from uuid import UUID, uuid5

from modules.ai_platform.public import AIVendor, EvidenceRef, EvidenceValue, GroundedStatement
from modules.ai_research_engine.domain.knowledge import EpistemicOrigin

RESEARCH_FINDING_NAMESPACE: Final = UUID("3a02938f-4da2-4c51-8040-894b7520cee1")
"""Fixed namespace for deterministic finding identity. **Never change it** —
every finding in every workspace would acquire a new identity, and the next
research run would insert a duplicate of the entire table."""

#: The `EvidenceRef.kind` a finding addresses itself by. One constant rather
#: than a literal at each call site, because a citation whose kind varied by
#: caller would resolve for some readers and not others.
FINDING_KIND: Final = "research_finding"

PAYLOAD_VERSION: Final = 1

#: Identity is built by joining fields with this separator.
#:
#: **There is deliberately no guard forbidding it inside `derivation`.** One was
#: written, and removed when the test meant to prove it fires could not be
#: constructed: a version renders as digits and every citation token ends in a
#: UUID, so the boundary between the derivation field and the citation list can
#: only fall in one place. Two different findings cannot produce one identity
#: whatever text a derivation contains — the types already close the door, and a
#: guard that cannot fail is documentation pretending to be code. The property
#: is asserted directly instead, over adversarial derivations, in
#: `test_research.py`.
_SEPARATOR: Final = "|"


class ResearchError(ValueError):
    """A research object was constructed that could not be defended."""


@dataclass(frozen=True, slots=True)
class ResearchTask:
    """One act of researching an account. **Operational history, not knowledge.**

    It asserts nothing about a customer's world — it records that Signora
    looked. By the contract's own test (*if this were wrong, could a customer
    be misled?*) it is machinery, in the same category as `ai_inference`, and
    it carries no epistemic origin because there is nothing to classify.

    Deliberately a record rather than a state machine. Budget, deadline,
    planning and resumability are real and are this module's to own — they are
    not *this task's*, and building them before the orchestrator that uses them
    would freeze a guess about a shape nothing has exercised yet.
    """

    id: UUID
    workspace_id: UUID
    correlation_id: UUID
    #: The account under research, in the AI Platform's addressing vocabulary,
    #: so a finding's subject and its citations are read the same way.
    subject: EvidenceRef
    #: What made this account worth the cost. Research is invoked selectively,
    #: and the opportunity is the selection.
    opportunity_id: UUID
    requested_at: datetime


@dataclass(frozen=True, slots=True)
class ResearchFinding:
    """One thing research worked out, and the rows it worked it out from.

    **DERIVED, and checkable by recomputation** — the only class the contract
    calls fully verifiable. A customer disagreeing with a finding does not need
    to be persuaded: they open the cited rows and run the same comparison.
    """

    #: Declared once for the type, not per instance. Origin is immutable for an
    #: object's lifetime (Rule 5), and a field would let two findings of one
    #: kind disagree about how they must be checked.
    origin: ClassVar[EpistemicOrigin] = EpistemicOrigin.DERIVED

    id: UUID
    workspace_id: UUID
    #: The act that produced it. A finding outlives its task and stays readable
    #: through it — which run looked, when, under which correlation.
    task_id: UUID
    subject: EvidenceRef
    #: Names the deterministic computation that produced this. Not a topic and
    #: not a question: *which code derived it*, so a reader can find that code.
    derivation: str
    #: Bumped when the computation changes in a way that could change its
    #: answer. **Part of identity, unlike `Signal`'s profile version** — and the
    #: contrast is deliberate. A profile change that still yields the same
    #: signal type yields the same signal, because the type *is* the claim.
    #: A derivation change can yield a different value from identical inputs,
    #: so omitting it here would let new content collide with an old id and
    #: silently insert nothing.
    derivation_version: int
    #: What the computation produced, typed and in canonical order. Typed
    #: rather than rendered for the reason `EvidenceFact` gives: a value's type
    #: is part of its meaning, and text that has lost it cannot be compared.
    attributes: tuple[tuple[str, EvidenceValue], ...]
    #: The rows this rests on. A finding citing nothing is not derived from
    #: anything, whatever it claims.
    cited: tuple[EvidenceRef, ...]
    created_at: datetime
    payload_version: int = PAYLOAD_VERSION

    def __post_init__(self) -> None:
        if not self.derivation.strip():
            raise ResearchError(
                f"finding {self.id} names no derivation, so nothing identifies the code that "
                "produced it — and a derived fact nobody can recompute is not derived."
            )
        if self.derivation_version < 1:
            raise ResearchError(
                f"finding {self.id} has derivation version {self.derivation_version}. Versions "
                "start at 1, and identity keys on this — a zero would make the first revision "
                "indistinguishable from an unversioned finding."
            )
        if not self.cited:
            raise ResearchError(
                f"finding {self.id} cites nothing. Grounding refuses an uncited statement; an "
                "uncited derivation is the same defect at rest."
            )
        if not self.attributes:
            raise ResearchError(
                f"finding {self.id} states nothing. A finding with no attributes records that a "
                "comparison ran, which is the task's job, not a finding's."
            )
        names = [name for name, _ in self.attributes]
        if len(names) != len(set(names)):
            raise ResearchError(
                f"finding {self.id} repeats an attribute name. Two values under one name makes "
                "what the finding says depend on which one is read."
            )
        object.__setattr__(self, "attributes", tuple(sorted(self.attributes, key=lambda a: a[0])))

    @property
    def ref(self) -> EvidenceRef:
        """Its own address — **this is what citability is.**

        A DERIVED finding can be addressed, therefore cited, therefore checked.
        `ResearchSynthesis` has no counterpart to this property, and that
        absence is how Rule 12 is enforced: an INFERRED object is not refused a
        citation, it has no address to be cited by.
        """
        return EvidenceRef(kind=FINDING_KIND, id=self.id)


def research_finding_id(
    *,
    workspace_id: UUID,
    subject: EvidenceRef,
    derivation: str,
    derivation_version: int,
    cited: tuple[EvidenceRef, ...],
) -> UUID:
    """Derived from the computation and its inputs, never allocated.

    Re-running the same derivation over the same rows must produce the same
    finding and insert nothing — the property that lets research be replayed,
    regression-tested, and rebuilt after a pipeline rebuild without duplicating
    everything it ever found.

    **The attributes are deliberately not part of the key.** They are what the
    derivation *computes* from inputs already in the key, so including them
    would add nothing when the derivation is deterministic — and would hide the
    defect when it is not, by minting a fresh id instead of colliding with the
    old one. Excluding them makes a non-deterministic derivation show up as two
    different contents under one identity, which a round-trip test catches and
    a uniqueness constraint refuses.
    """
    evidence = _SEPARATOR.join(sorted(ref.token for ref in cited))
    return uuid5(
        RESEARCH_FINDING_NAMESPACE,
        _SEPARATOR.join(
            (
                str(workspace_id),
                subject.token,
                f"{derivation}@{derivation_version}",
                evidence,
            )
        ),
    )


@dataclass(frozen=True, slots=True)
class ResearchSynthesis:
    """What the model made of the findings. **INFERRED, and never citable.**

    It has no `ref`. Nothing addresses it, so nothing can cite it, so no
    consumer can make one model's output another model's evidence — the failure
    Rule 12 exists to prevent, enforced by the absence of an address rather
    than by a check somebody could forget to call.

    **It references its findings rather than absorbing them** (Rule 7). A
    composite takes the origin of its most powerful author, so this object is
    INFERRED as a whole — but the findings beneath it stay individually
    addressable and individually checkable. Flattening them into it would make
    a conclusion and its evidence equally untrustworthy, which is backwards.

    Provenance is complete and denormalized because **for inferred knowledge,
    auditability is a property of the act, never the content** (Rule 22). What
    can be established later is exactly this: which findings, which prompt,
    which model, which inference, when.

    **Denormalized deliberately, against this repository's own preference for
    referencing immutable history.** `ai_inference` already holds every one of
    these fields and is never edited, so copying them would ordinarily be
    duplicate truth. It is copied because **the AI Platform publishes an
    `InferenceRecorder` and no reader** — nothing outside it can read that row.
    Adding one would be an M8 change, and M10 consumes the platform rather than
    reshaping it. M9's Decision Package carries the same fields for the same
    reason; two sibling modules disagreeing about their own provenance would be
    worse than one copied row.
    """

    origin: ClassVar[EpistemicOrigin] = EpistemicOrigin.INFERRED

    id: UUID
    workspace_id: UUID
    task_id: UUID
    #: Grounded against the findings, so a statement that cites nothing, cites
    #: something fabricated, or states a figure absent from its own evidence
    #: fails the call rather than reaching a customer.
    statements: tuple[GroundedStatement, ...]
    #: The findings it was composed from, by identity. Referenced rather than
    #: copied: a finding is immutable, so a reference cannot drift, and copying
    #: would duplicate a fact that cannot change.
    finding_ids: tuple[UUID, ...]

    prompt_name: str
    prompt_version: int
    prompt_fingerprint: str
    model: str
    #: Which vendor served it. **Provenance only** — nothing in this module may
    #: branch on it, and business behaviour must be identical whichever vendor
    #: answered.
    vendor: AIVendor
    evidence_digest: str
    inference_id: UUID

    created_at: datetime
    payload_version: int = PAYLOAD_VERSION

    def __post_init__(self) -> None:
        if not self.statements:
            raise ResearchError(
                f"synthesis {self.id} says nothing. An empty synthesis is a failed inference "
                "recorded as a successful one, and the operational history would then disagree "
                "with itself."
            )
        if not self.finding_ids:
            raise ResearchError(
                f"synthesis {self.id} rests on no findings. A narration over nothing is a model "
                "writing unprompted, which is the one thing this module must never publish."
            )
        if len(self.finding_ids) != len(set(self.finding_ids)):
            raise ResearchError(
                f"synthesis {self.id} names a finding twice. One finding counted twice is the "
                "corroboration defect in miniature — the same source appearing to agree with "
                "itself."
            )
