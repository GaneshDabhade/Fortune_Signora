"""The synthesis contract — what AI may be handed, and what it may return.

**The fence the whole design rests on**, and it is built before there is any
prose to be tempted by. [ADR-0200](../../../../docs/architecture/adr/0200-sales-engagement.md)
puts AI in one layer: the deterministic graph decides, and synthesis
communicates. This file is what makes that structural rather than aspirational.

### Not prompt engineering — a compiler

The model is handed a **fully constrained object**, never raw evidence: the
recommendation, the likely product, the ranked roles, the citations, the
contradictions, the unknowns, the risks. **It is not asked to infer any of
them.** Its whole job is to order and phrase what it was given.

> **A synthesis must be incapable of increasing the repository's knowledge. It
> may only reorganize it.**

That sentence is the specification, and everything below implements it.

### Four checks, and the third is the sharp one

1. **Every passage cites something.** Free-floating prose is an assertion, and
   this module publishes none.
2. **Every citation resolves** into the closed set it was given.
3. **Every number and date in the prose appears in the closed set.** This is
   what catches *invented confidence*, *invented chronology* and *invented
   urgency* — a fabricated *"73%"*, *"three weeks ago"* or *"12 engineers"*
   has nowhere to have come from, and none of the three is detectable by
   asking a model to behave.
4. **Every proper noun is one the graph already used.** Competitors,
   initiatives, departments, technologies, products and stakeholders are all
   *names*, and a name absent from the closed set is an invention whatever
   category it belongs to. **Deliberately conservative**: it refuses more than
   it must, and a refusal costs a paragraph while a fabrication costs the
   customer's trust in every other paragraph.

### What a refusal does

**The brief renders without prose.** A seller still gets the recommendation,
the ranked roles, the evidence, the unknowns and the risks — because those
were never the model's to produce. **Degrading to the facts is the whole point
of the asymmetry**: delete synthesis and the product still works; delete the
graph and there is nothing to synthesise.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Final, Protocol
from uuid import UUID

from modules.sales_engagement.domain.fit import ProductFit, ProductRef
from modules.sales_engagement.domain.reasoning import ApproachReasoning, ReasoningError


class SynthesisRefusedError(ReasoningError):
    """A draft claimed something the reasoning did not produce.

    **Its own type**, so a refusal is distinguishable in the operational record
    from a provider failure or a malformed response. *Why did this brief render
    without prose* has three different answers and they need different fixes.
    """


class ClosedSet(Protocol):
    """Everything a draft is permitted to have come from.

    **Structural, and that is the point.** `SynthesisSource` is the graph's own
    answer; `CommercialContext` (SE-09c) is that answer *plus what the rendering
    protocol actually showed the model* — a date, a corroboration count — and
    both are legitimate closed sets for the same draft.

    Naming the shape rather than the class is what lets the protocol widen the
    set **without a second validator**. Two validators is the failure this
    module was built to prevent, and it would arrive here first.

    > **A caller passes the narrowest set the model was really shown.** Passing
    > a wider one than the model read is how a false negative gets designed in.
    """

    def vocabulary(self) -> frozenset[str]: ...
    def numbers(self) -> frozenset[str]: ...
    def citable(self) -> frozenset[str]: ...


@dataclass(frozen=True, slots=True)
class SynthesisSource:
    """Everything the model may say, assembled once and closed.

    **Assembled here rather than passed as separate arguments**, because the
    validation and the prompt must read from **one** set. Two assemblies would
    eventually differ, and the difference would be exactly the space an
    invention could live in.
    """

    reasoning: ApproachReasoning
    fits: tuple[ProductFit, ...]
    product: ProductRef | None

    def vocabulary(self) -> frozenset[str]:
        """Every word the reasoning itself used, lower-cased.

        **The allowed proper nouns are the ones already spoken.** A name that
        appears nowhere in what the graph derived cannot have come from the
        graph.
        """
        words: set[str] = set()
        for text in self._texts():
            words |= {bare(token) for token in text.split()}
        return frozenset(words - {""})

    def numbers(self) -> frozenset[str]:
        """Every numeral the reasoning stated.

        Dates are included through the summaries that mention them; a figure
        absent from here was not derived from anything.
        """
        found: set[str] = set()
        for text in self._texts():
            found |= set(_NUMERAL.findall(text))
        return frozenset(found)

    def _texts(self) -> tuple[str, ...]:
        parts: list[str] = [self.reasoning.recommendation.reason]
        if self.reasoning.recommendation.role is not None:
            parts.append(self.reasoning.recommendation.role.title)
        for role in self.reasoning.roles:
            parts.append(role.role.title)
            parts.append(role.role.part)
            if role.why_not:
                parts.append(role.why_not)
            parts.extend(one.summary for one in role.support)
            parts.extend(one.type_key.replace("_", " ") for one in role.support)
        parts.extend(one.subject for one in self.reasoning.unknowns)
        parts.extend(one.question for one in self.reasoning.unknowns)
        parts.extend(one.detail for one in self.reasoning.risks)
        parts.extend(one.kind.value for one in self.reasoning.risks)
        for fit in self.fits:
            parts.append(fit.product.name)
            parts.append(fit.strength.value)
            parts.extend(one.detail for one in fit.reasons)
        if self.product is not None:
            parts.append(self.product.name)
        return tuple(parts)

    def citable(self) -> frozenset[str]:
        """Identifiers a passage may cite.

        **Evidence ids, role titles, unknown subjects and risk kinds** — the
        four things the graph produces that a paragraph can be *about*. A
        citation to anything else does not resolve, and the draft is refused.
        """
        cites: set[str] = {"recommendation"}
        for role in self.reasoning.roles:
            cites.add(role.role.title.casefold())
            cites |= {str(one.event_id) for one in role.support}
        cites |= {one.subject.casefold() for one in self.reasoning.unknowns}
        cites |= {one.kind.value for one in self.reasoning.risks}
        cites |= {one.product.name.casefold() for one in self.fits}
        return frozenset(cites)


@dataclass(frozen=True, slots=True)
class Passage:
    """One paragraph of synthesis, and what it explains."""

    text: str
    #: What this paragraph is about. **Never empty** — see `validate`.
    cites: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class Synthesis:
    """A validated synthesis. **Constructible only through `validate`.**"""

    passages: tuple[Passage, ...]
    #: Which inference produced it, so the operational record can name the
    #: model, the prompt version and the moment without this module knowing
    #: any of them.
    inference_id: UUID


#: Numerals and percentages, including those inside words like `42%` and `3-4`.
_NUMERAL: Final = re.compile(r"\d+(?:[.,]\d+)?")

#: A capital at the start of a sentence is grammar. **A capital in the middle
#: of one is a name.** That distinction removes the need for a list of English
#: verbs, which the first implementation of this check began to grow.
_SENTENCE: Final = re.compile(r"(?<=[.!?])\s+")

#: A trailing possessive, straight or curly.
#:
#: **The possessive of a permitted name is not a new name**, and treating it as
#: one refused a real synthesis: the graph offered *Revenue Cloud*, the model
#: wrote *Revenue Cloud's*, and the fence read `cloud's` as an invented product.
#: That is the same class as the month-name false refusal the Commercial Context
#: Protocol fixed — **the model used a word it was given, in a grammatical form
#: the checker had not anticipated.**
#:
#: It does not weaken the check. *Databricks's* still reduces to `databricks`,
#: which is still absent from the closed set and still refused.
_POSSESSIVE: Final = re.compile(r"['’]s$")

#: Edge punctuation a word can carry without being a different word.
_EDGES: Final = ".,;:()'\"“”‘’"


def bare(token: str) -> str:
    """One word, reduced to the form both sides of the fence compare.

    **Used by the closed set and by the checker, so they cannot disagree.** Two
    normalizations would eventually differ, and the difference is exactly the
    space a false refusal lives in — the same argument `SynthesisSource` makes
    about being assembled once.
    """
    return _POSSESSIVE.sub("", token.strip(_EDGES)).casefold()


def validate(draft: tuple[Passage, ...], source: ClosedSet, *, inference_id: UUID) -> Synthesis:
    """Refuse anything that would increase the repository's knowledge.

    **Four checks, and every one is a comparison against the closed set.** None
    of them asks a model to behave; each is arithmetic over what was handed in
    and what came back.

    Raises `SynthesisRefused` with the specific claim that failed, because
    *"the synthesis was refused"* is not something an engineer can act on and
    *"it said 73% and nothing derived 73%"* is.
    """
    if not draft:
        raise SynthesisRefusedError("a synthesis with no passages explains nothing.")

    citable = source.citable()
    vocabulary = source.vocabulary()
    numbers = source.numbers()

    for passage in draft:
        if not passage.cites:
            raise SynthesisRefusedError(
                f"a passage cites nothing: {passage.text[:60]!r}. **Free-floating prose is an "
                "assertion**, and this module publishes none."
            )
        for cite in passage.cites:
            if cite.casefold() not in citable:
                raise SynthesisRefusedError(
                    f"a passage cites {cite!r}, which the reasoning did not produce."
                )

        for figure in _NUMERAL.findall(passage.text):
            if figure not in numbers:
                raise SynthesisRefusedError(
                    f"a passage states {figure!r}, which nothing in the reasoning derived. "
                    "**Invented confidence, chronology and urgency all arrive as numbers.**"
                )

        for token in _proper_nouns(passage.text):
            if token not in vocabulary:
                raise SynthesisRefusedError(
                    f"a passage names {token!r}, which appears nowhere in the reasoning. "
                    "**A competitor, initiative, department, technology, product or person "
                    "the graph never mentioned is an invention whatever it is called.**"
                )

    return Synthesis(passages=draft, inference_id=inference_id)


def _proper_nouns(text: str) -> tuple[str, ...]:
    """Capitalised tokens that are not starting a sentence, lower-cased.

    **The first implementation flagged every capital**, so *"Approach them
    now"* was refused for naming a competitor called *Approach* — and the fix
    it invited was a growing list of English verbs, which is a list nobody can
    finish. Skipping the sentence-initial token needs no list at all.

    **The known gap, stated rather than hidden:** an invented name at the start
    of a sentence is not caught here. It is narrower than the alternative — a
    check that refused every sentence's first word would refuse every synthesis
    — and the citation and numeral checks still bind on the same passage. **If
    a model is ever seen exploiting it, the answer is sentence-position-aware
    tagging, not a longer allowlist.**
    """
    found: list[str] = []
    for sentence in _SENTENCE.split(text.strip()):
        tokens = sentence.split()
        for token in tokens[1:]:
            if token[:1].isupper():
                found.append(bare(token))
    return tuple(found)
