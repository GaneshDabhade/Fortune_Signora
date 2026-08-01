"""HTTP response schemas for the Signal Engine's validation surface.

**The first thing Signora says that is about what a seller should *do*.**
Every surface before this one answers *which accounts* and *why*; this one
answers *what to check before you act on that*.

**It is not a recommendation, and the distinction is the whole design.** Nothing
here is about this account. `limitations` and `suggested_validation` are
properties of the *hypothesis type* — what `expansion_opportunity` fails to
prove is identical on Tuesday and Wednesday and for every workspace, which is
why the Signal Catalog owns them, versions them and reviews them like code. A
recommendation would be account-specific and inferred. This is neither, and it
required no model.

**Limitations are the load-bearing half.** A confident number invites
over-reading, and the catalog is the only place that says what the number
cannot support. Naming the uncertainty *is* the uncertainty reduction — the
product does not become more certain, the reader becomes better calibrated.
"""

from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from modules.signal_engine.domain.catalog import Relevance, SignalTypeDefinition
from modules.signal_engine.domain.signal import Signal


class HypothesisValidationResponse(BaseModel):
    """One live hypothesis, and what a seller should do about it."""

    model_config = ConfigDict(frozen=True)

    signal_id: UUID = Field(
        description=(
            "The hypothesis this guidance is for. The same identifier the score's ledger "
            "cites, so the two surfaces can be joined without a second lookup."
        )
    )
    title: str = Field(
        description=(
            "What this hypothesis is called. Owned by the Signal Catalog — one definition "
            "that the product, analytics, documentation and support all read, rather than "
            "four descriptions that drift."
        )
    )
    hypothesis: str = Field(
        description=(
            "What it *proposes*, phrased as a possibility. A signal does not assert; it "
            "suggests, and the wording is deliberate — if this reads as a fact, the type "
            "has drifted into territory the Business Event Engine owns."
        )
    )
    relevance: Relevance = Field(
        description=(
            "How central this hypothesis is to your ideal customer profile. Your "
            "declaration, not a measurement."
        )
    )

    limitations: tuple[str, ...] = Field(
        description=(
            "**What this hypothesis does not prove.** The half of the answer a confident "
            "number never gives: a score can tell you an account deserves attention and "
            "cannot tell you the things listed here. Never empty — a type that claimed no "
            "limitations would be asserting certainty the evidence cannot carry."
        )
    )
    suggested_validation: tuple[str, ...] = Field(
        description=(
            "**What to check before you act.** Written for a seller and phrased as things "
            "to do — read the announcement, ask on the first call. Not a recommendation "
            "about this account: it is what anyone holding this hypothesis, anywhere, "
            "should confirm."
        )
    )

    @classmethod
    def from_domain(
        cls, signal: Signal, definition: SignalTypeDefinition
    ) -> "HypothesisValidationResponse":
        return cls(
            signal_id=signal.id,
            title=definition.title,
            hypothesis=definition.hypothesis,
            relevance=signal.relevance,
            limitations=definition.limitations,
            suggested_validation=definition.suggested_validation,
        )


class AccountValidationResponse(BaseModel):
    """What to check on this account, and what its evidence cannot tell you."""

    model_config = ConfigDict(frozen=True)

    account_id: UUID = Field(description="The company this guidance is about.")
    hypotheses: tuple[HypothesisValidationResponse, ...] = Field(
        description=(
            "One entry per **live** hypothesis, most relevant first. Live rather than "
            "score-contributing: a hypothesis worth validating is one that is currently "
            "held, not one that happens to carry points today. Empty when nothing is "
            "current — which is itself the answer, and not an error."
        )
    )


__all__ = ["AccountValidationResponse", "HypothesisValidationResponse"]
