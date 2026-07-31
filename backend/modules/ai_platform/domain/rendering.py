"""The Prompt Rendering Protocol — the form evidence takes when a model reads it.

**What a model is shown is an experimental input, and until M9.5 it was the only
one nothing recorded.** A prompt evaluation measures a system with four inputs:
the prompt text, the rendered evidence, the model, and the dataset. Three were
bound to every measurement. This one was not — and, uniquely among the four, a
change to it was undetectable:

- ``PromptVersion.fingerprint`` covers name, version and **template text**. The
  template contains ``{facts}``; it does not contain facts.
- ``EvidenceSet.digest`` covers each fact's ``canonical_form()``, which that
  module documents as *"a stable text form, for hashing only. Not for prompts."*

So two inferences carrying an identical prompt fingerprint and an identical
evidence digest could have been shown different text, if the rendering changed
between them. That is a hidden input, and hidden inputs are architecture defects
(CLAUDE.md §2) — they defeat replay, regression testing, and every guarantee
proven by removal.

**This module gives that input a name, a specification and a version.**

---

### Why this is not part of ``evidence.py``

The citation *grammar* — ``EvidenceRef.token`` and ``EvidenceRef.parse`` — lives
in ``domain/evidence.py``, and those two have never drifted precisely because
they are neighbours. It is tempting to put the *display* form there too.

It does not belong there, and ``evidence.py`` says why in its own words:
*"Evidence is truth; prompts are language, and the moment a fact knows how it
will be phrased, changing the wording becomes a change to the evidence model."*
A fact must not learn how it will be presented.

So the protocol is its own concept, owned here, **depending on** the grammar
without living inside it. Language that is a contract is domain language — the
same reason ``prompt.py`` is domain rather than infrastructure.

---

### What the version identifies

A bare integer with no referent would be worse than nothing: nobody could tell
whether a given change required a bump, and the bump would become discipline —
which is what already failed. **The version identifies a specification, stated
below and pinned by a specimen in the test suite**, in the same way
``PINNED_FINGERPRINTS`` pins prompt text. Changing what a model sees without
bumping the version fails that test.

### Protocol version 2 — current, ratified as ADR-0031 Option A

**A citation is presented as a complete, copyable unit. Nothing surrounds it.**

- Facts appear in the evidence set's own canonical order, separated by a blank
  line.
- Each fact opens with its citation token, **exactly as ``EvidenceRef.token``
  produces it and exactly as ``EvidenceRef.parse`` accepts it**, followed by a
  space, an em dash, a space, and the fact's summary.
- Each attribute follows on its own line, indented two spaces, as
  ``name: value``, in the fact's canonical attribute order.

```
signal_contribution:3f40f486-98e5-5ff7-812d-feca5aa54af7 — A retired system suggests …
  contribution: 30
  relevance: primary
```

**The em dash is load-bearing, and an ASCII hyphen would not do.** A UUID
contains hyphens, so ``-`` sits inside the token's own alphabet and a model
deciding where a citation ends would have to reason about position rather than
about characters. An em dash appears nowhere in ``kind:uuid``, so the boundary
is unambiguous by construction — the token is bounded by the start of the line
and by a character it can never contain.

**What this buys is that copying becomes the winning strategy.** Under version 1
no form of the citation that the parser accepted was ever visible to the model
as a delimited unit: it had to *derive* one by removing characters. Every
observed grounding failure across three prompts and four models was an error in
how much to remove — too little (the bracket transcribed) or too much (the kind
prefix stripped). A form that requires no transformation has no mechanism for
either.

### Protocol version 1 — superseded 2026-07-31, recorded

The form shipped from M8 until M9.5 Step C. Kept here because evaluations in the
manifests still name it, and a version those records cite must remain
explicable:

```
[signal_contribution:3f40f486-98e5-5ff7-812d-feca5aa54af7] A retired system suggests …
  contribution: 30
  relevance: primary
```

The bracket was not part of the token. A model reproducing what it saw emitted a
citation the parser rejected; a model told to strip the bracket could strip more.
Measurements taken under it remain true and remain on record — they simply no
longer describe what a model would be shown.
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import Final

from modules.ai_platform.domain.evidence import EvidenceFact, EvidenceRef

#: The rendering protocol this process implements.
#:
#: Recorded on every evaluation and compared at the point of use: a measurement
#: taken under one protocol does not describe a system running another. Bumping
#: this invalidates every release earned under the previous value — automatically,
#: by derivation, rather than by anyone remembering to withdraw them.
#:
#: **A change to what a model is shown requires a bump.** The specimen test is
#: what enforces that, and the specification above is what makes the question
#: answerable.
PROMPT_RENDERING_PROTOCOL_VERSION: Final = 2

#: What separates a citation from the prose that follows it. Not part of the
#: citation, and — unlike a hyphen — not a character a citation can contain.
_DELIMITER: Final = " — "

#: How far an attribute is indented beneath the fact it belongs to.
_INDENT: Final = "  "


def cite(ref: EvidenceRef) -> str:
    """The citation exactly as a model should copy it, and exactly as
    ``EvidenceRef.parse`` accepts it.

    **This function existing at all is the fix.** Before it, the writer of the
    citation lived in ``application/render.py`` and the reader lived in
    ``domain/evidence.py``, and nothing reconciled them — two components sharing
    a protocol that neither owned (ADR-0031). There is now one authority, and it
    adds nothing to what ``token`` produces.

    It is deliberately a pass-through rather than an alias: a caller that wanted
    decoration would have to change *this*, in the module named for the protocol,
    where a version bump is the obvious next thought.
    """
    return ref.token


def render_fact(fact: EvidenceFact) -> str:
    """One fact, as protocol 2 presents it."""
    lines = [f"{cite(fact.ref)}{_DELIMITER}{fact.summary}"]
    lines.extend(f"{_INDENT}{name}: {value}" for name, value in fact.attributes)
    return "\n".join(lines)


def render_facts(facts: Iterable[EvidenceFact]) -> str:
    """Every fact, in the order the evidence set holds them.

    No ordering of its own: the set is already canonical, so the same evidence
    always produces the same text and a recorded ``evidence_digest`` identifies
    exactly what the model saw.
    """
    return "\n\n".join(render_fact(fact) for fact in facts)
