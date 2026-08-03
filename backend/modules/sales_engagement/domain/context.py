"""The Commercial Context Protocol — the form the reasoning graph takes when a
model reads it.

**This is the layer the product owner asked whether to build now, and the
repository has already paid for the answer once.**

[`ai_platform/domain/rendering.py`](../../ai_platform/domain/rendering.py)
exists because, until M9.5, *what a model was shown* was an experimental input
that nothing recorded. A prompt fingerprint covers the template — which contains
`{context}`, not context. An evidence digest covers a canonical form its own
module documents as *"for hashing only. Not for prompts."* So two inferences
carrying identical fingerprints could have been shown different text, and a
change to the rendering was undetectable. **Hidden inputs are architecture
defects** (`CLAUDE.md` §2).

**That defect is available here right now.** A prompt that interpolated
`reasoning.roles[0].role.title` directly would couple a frozen, fingerprinted
artifact to a moving domain object: rename a field or reorder a tuple in
`reasoning.py` and every released evaluation silently stops describing what the
model reads, with nothing in the fingerprint moving. So the layer is not
speculative generalization for a second pass — **it is the declared contract
between an immutable artifact and a domain that evolves**, and this slice would
introduce the hidden input without it.

```
  reasoning graph ──▶ CommercialContext ──▶ prompt ──▶ model ──▶ draft
                            │                                     │
                            └──────── one closed set ─────────────┘
```

### The property that makes it more than a formatter

**The closed set is computed from the rendered text, not in parallel with it.**

SE-09a's `SynthesisSource` states the rule: *the validation and the prompt must
read from one set, because two assemblies would eventually differ and the
difference is exactly the space an invention could live in.* A renderer that
showed the model a date the validator had never heard of would cause a **false
refusal** — the model faithfully copies what it was given and is punished for
it. Deriving `numbers()` and `vocabulary()` from the same fragments that produce
`render()` makes that unrepresentable rather than merely tested for.

### Citations are excluded from what may be quoted, deliberately

A UUID contains digits. Folding citation tokens into `numbers()` would admit
every digit in every identifier — so *"3 providers"* would pass because some
event id happened to contain a `3`, and the numeral check that catches invented
confidence, chronology and urgency would be **decorative** (`CLAUDE.md` §2).

Fragments therefore carry whether they are *quotable*. A citation is shown so it
can be copied, and never counted as something the graph said.

### Protocol version 2 — current, and it is version 2 for a measured reason

**Sections in a fixed order, each a heading and indented `label: value` lines,
followed by an explicit list of every token that may be cited.**

- Sections with nothing to say are **absent**, matching `ApproachBrief.sections()`
  — a heading with nothing under it looks the same for every Target Account.
- **Headings are lower case and delimited**, so no heading can be mistaken for a
  citation. See the superseded protocol below for why this is not cosmetic.
- **The context ends with `citable`, listing every legal token, one per line,
  exactly as `citable()` accepts it.** A model that has to *infer* the set of
  legal citations will infer it wrongly; one that can read it does not have to.
- A citation also appears beside the thing it names, on its own `cite:` line, so
  a model reading top-to-bottom never has to hold the trailing list in mind.
- Dates are ISO **and carry their month name**, because a model asked for prose
  writes *July* and a protocol that showed only `2026-07-20` would have refused
  it for a word it had itself withheld.
- Counts are bare integers. All of the above are quotable; citation tokens are
  not.

Bumping this invalidates every evaluation earned under the previous value, by
derivation rather than by anyone remembering to withdraw them.

### Protocol version 1 — superseded 2026-08-03, before any release, recorded

Version 1 headed each section in capitals (`BUYING COMMITTEE ROLES`), listed a
`cite:` line beside each entity, and rendered dates as bare ISO.

**The first real evaluation refused eight of ten cases, and the protocol caused
both failure modes.**

**Six cases cited a section heading** — `BUYING COMMITTEE ROLES`,
`WHAT SIGNORA DOES NOT KNOW`, `LIKELY PRODUCT`. A capitalised heading looks
exactly like a token. The model was never shown the *set* of legal citations and
had to infer one, so it took the most visually salient strings on the page. It
cited correctly on the richest case, which is what a guess looks like when it
happens to land.

**Two cases wrote *"July 20th"*** from `occurred: 2026-07-20`. A false refusal:
the date was shown and only the English word for its month was withheld. The
model rephrased a fact it had been given and was punished for the phrasing —
precisely the failure this class exists to remove, fixed for numerals and missed
for month names.

> **This is the same defect class ADR-0031 found in the evidence rendering
> protocol**, and it is resolved the same way: *every observed grounding failure
> was an error about how much to transform, and a form that requires no
> transformation has no mechanism for one.* The remedy is not a longer
> instruction in the prompt — a rule the format keeps cannot be forgotten.

**Kept here rather than deleted**, so the recorded run at protocol 1 in
[50-sales-engagement.md](../../../../docs/architecture/50-sales-engagement.md)
§27 stays explicable. That measurement is still true; it simply no longer
describes what a model would be shown.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Final

from modules.sales_engagement.domain.reasoning import RankedRole
from modules.sales_engagement.domain.synthesis import SynthesisSource, bare

#: The Commercial Context Protocol this process implements.
#:
#: Recorded on every evaluation and compared at the point of use: a measurement
#: taken under one protocol does not describe a system running another.
#:
#: **A change to what a model is shown requires a bump**, and the specimen test
#: in `tests/sales_engagement/test_context.py` is what enforces it — the same
#: mechanism `PROMPT_RENDERING_PROTOCOL_VERSION` uses, for the same reason.
COMMERCIAL_CONTEXT_PROTOCOL_VERSION: Final = 2

#: Numerals and percentages. Identical to the synthesis contract's, deliberately:
#: the set the model may quote from and the set it is checked against must be
#: recognised by one expression, or a figure could be quotable here and invented
#: there.
_NUMERAL: Final = re.compile(r"\d+(?:[.,]\d+)?")

_INDENT: Final = "  "


@dataclass(frozen=True, slots=True)
class _Fragment:
    """One rendered line, and whether the model may quote from it.

    **`quotable` is the whole reason this is a type rather than a string.** A
    citation must be visible and must never widen what counts as a fact the
    graph stated.
    """

    text: str
    quotable: bool = True


@dataclass(frozen=True, slots=True)
class CommercialContext:
    """The reasoning graph, normalized for a model to read.

    **It adds nothing.** Every value here was decided by the deterministic
    layer; this arranges them and decides nothing. A judgement creeping in would
    be commercial reasoning outside the layer that is tested for it — the same
    rule `brief.assemble` follows.
    """

    source: SynthesisSource

    def render(self) -> str:
        """The text a model is shown, under protocol 1."""
        return "\n".join(one.text for one in self._fragments())

    def vocabulary(self) -> frozenset[str]:
        """Every word the model was shown, lower-cased.

        **The union of what the graph said and what this protocol showed.** A
        name absent from here appears nowhere in the reasoning *and* nowhere in
        what the model read, so it can only have been invented.
        """
        words: set[str] = set()
        for fragment in self._fragments():
            if not fragment.quotable:
                continue
            # **`bare`, not a local normalization.** The set the model may quote
            # from and the set it is checked against must be reduced by one
            # function, or a word could be quotable here and invented there.
            words |= {bare(token) for token in fragment.text.split()}
        return frozenset(words - {""}) | self.source.vocabulary()

    def numbers(self) -> frozenset[str]:
        """Every numeral the model was shown, excluding citations.

        Dates and corroboration counts are here because the protocol shows
        them; identifiers are not, because a digit inside a UUID is not
        something the graph asserted.
        """
        found: set[str] = set()
        for fragment in self._fragments():
            if fragment.quotable:
                found |= set(_NUMERAL.findall(fragment.text))
        return frozenset(found) | self.source.numbers()

    def citable(self) -> frozenset[str]:
        """Delegated unchanged.

        **What may be cited is the graph's question, not the protocol's.** This
        layer decides how a citation is *displayed*; `SynthesisSource` decides
        what exists to be cited, and a second opinion here would be the two
        assemblies SE-09a exists to prevent.
        """
        return self.source.citable()

    def _fragments(self) -> tuple[_Fragment, ...]:
        """Every line of the rendered context, in protocol order.

        **One traversal produces the text and both closed sets**, which is what
        makes it impossible to show the model something the validator would
        refuse.
        """
        out: list[_Fragment] = []
        reasoning = self.source.reasoning

        out.append(_heading("recommendation"))
        out.append(_line("cite", "recommendation", quotable=False))
        out.append(_line("action", reasoning.recommendation.action.value))
        if reasoning.recommendation.role is not None:
            out.append(_line("role", reasoning.recommendation.role.title))
        out.append(_line("reason", reasoning.recommendation.reason))

        if self.source.product is not None:
            out.append(_Fragment(""))
            out.append(_heading("likely product"))
            out.append(_line("name", self.source.product.name))
            out.append(_line("cite", self.source.product.name, quotable=False))

        if self.source.fits:
            out.append(_Fragment(""))
            out.append(_heading("product fit"))
            for one in self.source.fits:
                out.append(_line("product", one.product.name))
                out.append(_line("cite", one.product.name, quotable=False))
                out.append(_line("strength", one.strength.value))
                for reason in one.reasons:
                    out.append(_line(reason.dimension.value, reason.detail))

        if reasoning.roles:
            out.append(_Fragment(""))
            out.append(_heading("buying committee roles"))
            for role in reasoning.roles:
                out.extend(_role(role))

        if reasoning.unknowns:
            out.append(_Fragment(""))
            out.append(_heading("what signora does not know"))
            for unknown in reasoning.unknowns:
                out.append(_line("subject", unknown.subject))
                out.append(_line("cite", unknown.subject, quotable=False))
                out.append(_line("question", unknown.question))

        if reasoning.risks:
            out.append(_Fragment(""))
            out.append(_heading("what could be wrong"))
            for risk in reasoning.risks:
                out.append(_line("kind", risk.kind.value))
                out.append(_line("cite", risk.kind.value, quotable=False))
                out.append(_line("detail", risk.detail))

        # **The authoritative list, last and complete.** A model that has to
        # infer which strings are citable will infer wrongly — protocol 1
        # refused six of ten cases on headings the model took for tokens. One
        # that can read the set does not have to guess at it.
        out.append(_Fragment(""))
        out.append(_heading("citable"))
        out.extend(
            _Fragment(f"{_INDENT}{token}", quotable=False) for token in self._citation_tokens()
        )
        return tuple(out)

    def _citation_tokens(self) -> tuple[str, ...]:
        """Every legal citation, in reading order rather than sorted.

        **Order follows the sections above**, so the trailing list reads as a
        recapitulation rather than as a second, differently-organised source.
        """
        reasoning = self.source.reasoning
        tokens: list[str] = ["recommendation"]
        if self.source.product is not None:
            tokens.append(self.source.product.name)
        tokens.extend(one.product.name for one in self.source.fits)
        for role in reasoning.roles:
            tokens.append(role.role.title)
            tokens.extend(str(one.event_id) for one in role.support)
        tokens.extend(one.subject for one in reasoning.unknowns)
        tokens.extend(one.kind.value for one in reasoning.risks)

        seen: set[str] = set()
        unique: list[str] = []
        for token in tokens:
            if token.casefold() not in seen:
                seen.add(token.casefold())
                unique.append(token)
        return tuple(unique)


def _role(role: RankedRole) -> tuple[_Fragment, ...]:
    """One ranked role and the evidence that ranked it.

    **An unranked role carries its reason**, because *"nothing names your CFO"*
    is the useful half of an empty result — and a protocol that dropped unranked
    roles would hide the sentence the whole module exists to produce.
    """
    out = [
        _line("title", role.role.title),
        _line("cite", role.role.title, quotable=False),
        _line("part", role.role.part),
        _line("strength", role.strength.value if role.strength else "not ranked"),
    ]
    if role.why_not is not None:
        out.append(_line("why not", role.why_not))
    for one in role.support:
        out.append(_line("evidence", one.summary))
        out.append(_line("cite", str(one.event_id), quotable=False))
        # **The month name is shown, not merely the ISO date.** A model asked
        # for prose writes *July*, and protocol 1 refused two cases for a word
        # it had itself withheld — the date was given and only its English name
        # was not.
        occurred = one.occurred_at.date()
        out.append(_line("occurred", f"{occurred.isoformat()} ({occurred:%B %Y})"))
        out.append(_line("corroborating providers", str(one.corroborating_providers)))
    return tuple(out)


def _heading(text: str) -> _Fragment:
    """A section heading no citation can be mistaken for.

    **Lower case and delimited.** Protocol 1 headed sections in capitals, and a
    model with no list of legal citations cited the headings — they were the
    most token-shaped strings on the page. A heading that cannot be confused
    with a token removes the confusion rather than instructing against it.
    """
    return _Fragment(f"── {text} ──")


def _line(label: str, value: str, *, quotable: bool = True) -> _Fragment:
    return _Fragment(f"{_INDENT}{label}: {value}", quotable=quotable)
