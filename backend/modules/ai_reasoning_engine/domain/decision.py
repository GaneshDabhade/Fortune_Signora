"""What the model is asked to produce — and nothing else.

The Decision Package has fifteen parts. **This file describes the three the
model authors.** The other twelve are derived from facts the pipeline already
owns, or composed from a reviewed catalog, and none of them appears here —
because a type is the strongest available statement about who may write what
(ADR-0030, *Deterministic Explainability*).

    Every field has the least powerful author capable of producing it
    correctly. The model keeps exactly the rung nothing else can reach.

**Three fields, and each is a `GroundedStatement`.** Text plus the citations
it rests on, checked by M8's `verify()` — so a conclusion that cites nothing,
cites something fabricated, or contains a figure absent from its own evidence
fails the call rather than reaching a customer.

**The shape is the stop condition.** M9 may conclude; it may not recommend an
action, compose a message, rank one account against another, or assert a fact
about the world its evidence does not contain. The first three are
unrepresentable here — there is no field for them, so a model that tries has
nowhere to put it and the schema refuses the output. The fourth is caught by
grounding. *The boundary is mechanical, not a matter of taste.*

If reasoning ever appears to need a field for an action, that is not a schema
change: it is M11 arriving early, and the correct response is to halt.
"""

from __future__ import annotations

from pydantic import model_validator

from modules.ai_platform.public import GroundedOutput, GroundedStatement

#: A conclusion resting on a single fact is an observation wearing a
#: conclusion's clothes. Reasoning means relating things that were not
#: previously related, which takes at least two of them.
#:
#: Two rather than three: a genuine inference from one strong corroborated
#: fact and one corroborating one is real reasoning, and demanding more would
#: reject sound conclusions on thin-but-honest evidence — which is what
#: `Support` exists to describe rather than to forbid.
MINIMUM_PREMISES = 2


class ReasoningError(ValueError):
    """A reasoning result was constructed that could not be defended."""


class ReasonedOutput(GroundedOutput):
    """The model's entire contribution to a Decision Package.

    Deliberately small. Everything a customer will lean on hardest — what
    contradicts this, how fresh the evidence is, why it appeared now, what it
    does not imply, how to check it — is derived or composed elsewhere,
    because those are the fields that must be *reproducible*.
    """

    #: The conclusion. One statement, because a package that concluded three
    #: things would need three sets of premises, three support ratings and
    #: three contradiction checks — and would be three Decision Packages
    #: wearing one header.
    proposition: GroundedStatement

    #: Understandable in seconds, and **grounded like everything else**. M8
    #: deleted exactly this field once, as an un-cited `summary`, because the
    #: sentence a reader looks at first must not be the one exempt from
    #: checking (28-ai-platform.md, Departure 4). It carries the most
    #: rhetorical weight and therefore the least entitlement to an exemption.
    summary: GroundedStatement

    #: **The explanation Signora stated, not the model's internal reasoning.**
    #:
    #: A language model has no introspective access to its own computation;
    #: what it emits when asked to explain itself is a plausible account
    #: generated alongside the answer. Since this field exists for audit and
    #: governance, a record misdescribing its own nature would be worse than
    #: none — so it is named for what it is (ADR-0030, Decision 2).
    #:
    #: Never presented as chain-of-thought. Each step is separately grounded,
    #: so the *evidence* of every step is real even though the ordering is
    #: narrative rather than causal.
    stated_reasoning: tuple[GroundedStatement, ...]

    def statements(self) -> tuple[GroundedStatement, ...]:
        """Every sentence the model wrote, so every one is checked.

        Omitting any part here would exempt it from grounding while leaving
        the output looking verified — the failure mode M8 removed by deleting
        the un-cited summary, reachable again through this method alone.
        """
        return (self.summary, self.proposition, *self.stated_reasoning)

    @model_validator(mode="after")
    def _rests_on_more_than_one_fact(self) -> ReasonedOutput:
        """A conclusion resting on a single fact is refused, not scored low.

        **Moved from the rubric into the type**, which is a simplification the
        ladder asked for: if a constraint can be made unrepresentable, it
        should not also be a thing an evaluation counts. The rubric no longer
        measures premise breadth — the type does, on every call, in production
        as well as at evaluation time.

        Reasoning means relating things that were not previously related. One
        premise cannot be related to anything, so such an output is an
        observation with a conclusion's grammar — and M8 already ships a
        capability for restating single facts.
        """
        if len(self.premises) < MINIMUM_PREMISES:
            raise ReasoningError(
                f"this conclusion rests on {len(self.premises)} distinct fact(s); reasoning "
                f"requires at least {MINIMUM_PREMISES}. A conclusion drawn from one fact is a "
                "restatement of that fact, which is narration rather than reasoning."
            )
        return self

    @property
    def premises(self) -> frozenset[str]:
        """Every distinct fact the conclusion and its reasoning rest on.

        Read from citations rather than prose: a statement mentioning a fact
        without citing it is making an uncited claim, which grounding already
        refuses. So the citation is the only evidence of a premise that means
        anything — the same read `coverage` takes for a different question.
        """
        return frozenset(token for statement in self.statements() for token in statement.evidence)
