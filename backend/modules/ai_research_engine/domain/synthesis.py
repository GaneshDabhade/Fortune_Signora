"""What the model is asked to produce at the end — and nothing else.

**Statements, and no fields at all beyond them.** A synthesis explains findings
that already exist; it does not add one, rank them, recommend anything, or say
how confident it is. Each of those is unrepresentable here rather than
discouraged, so a model that tries has nowhere to put it and the schema refuses
the output.

    Retrieval fetches · derivation computes · synthesis explains

**The evidence set a synthesis is grounded against holds findings, not facts.**
That is the whole design in one sentence. A narrator is shown the deterministic
results — each addressed by the id the derivation minted, summarised by the
catalog's reviewed question — and may cite nothing else. It cannot reach past a
finding to reinterpret the business event underneath, because the business event
is not in the set it was given.

**So a synthesis cannot investigate.** Not by rule, but because the only thing
it can address is a conclusion something else already computed.

---

**It is INFERRED, and never citable.** `ResearchSynthesis` stores what comes
back here and has no address, so no derivation and no later synthesis can rest
on it. One model's output never becomes another model's evidence.
"""

from __future__ import annotations

from pydantic import model_validator

from modules.ai_platform.public import GroundedOutput, GroundedStatement

#: A brief that says one thing has restated a single finding, which the
#: findings already do for themselves. Research is invoked selectively and
#: expensively; producing less than a relation between two results is not
#: worth a model call.
#:
#: Two rather than three, for the reason `MINIMUM_PREMISES` gives: demanding
#: more would reject an honest short brief on a thin account, and how thin the
#: account is is already visible in the findings themselves.
MINIMUM_STATEMENTS = 2


class SynthesisError(ValueError):
    """A synthesis was returned that could not be defended."""


class SynthesisedResearch(GroundedOutput):
    """The model's entire contribution to a research artifact.

    Deliberately smaller than M9's: reasoning authors three fields because it
    must state a conclusion, its premises and a summary. Research narrates
    results that are already stated, so there is one field and no shape for a
    verdict to hide in.
    """

    #: What the findings, taken together, say about this account. Each cites
    #: the findings it rests on; grounding refuses one that cites nothing.
    #:
    #: Named `brief` rather than `statements` because `GroundedOutput` declares
    #: `statements()` as the method every output implements — a field of that
    #: name would shadow it, and grounding would silently check nothing.
    brief: tuple[GroundedStatement, ...]

    def statements(self) -> tuple[GroundedStatement, ...]:
        return self.brief

    @model_validator(mode="after")
    def _relates_more_than_one_finding(self) -> SynthesisedResearch:
        """**A brief resting on one finding is that finding, reworded.**

        The findings are already addressed, already summarised by a reviewed
        question, and already readable. What a synthesis adds is the relation
        between them, so a narration citing a single finding across all of its
        statements has added nothing and cost a model call.
        """
        if len(self.brief) < MINIMUM_STATEMENTS:
            raise SynthesisError(
                f"a synthesis of {len(self.brief)} statement(s) is a restatement, not a "
                f"brief. At least {MINIMUM_STATEMENTS} are required, each citing what it rests "
                "on."
            )
        cited = {token for statement in self.brief for token in statement.evidence}
        if len(cited) < 2:
            raise SynthesisError(
                "every statement cites the same single finding. A brief that relates nothing "
                "is the finding reworded, and the finding is already readable on its own."
            )
        return self
