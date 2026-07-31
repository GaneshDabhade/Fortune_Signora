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

### Protocol version 1

The form shipped since M8, specified here for the first time:

- Facts appear in the evidence set's own canonical order, separated by a blank
  line.
- Each fact opens with its citation token **wrapped in square brackets**,
  followed by a space and the fact's summary.
- Each attribute follows on its own line, indented two spaces, as
  ``name: value``, in the fact's canonical attribute order.

```
[signal_contribution:3f40f486-98e5-5ff7-812d-feca5aa54af7] A retired system suggests …
  contribution: 30
  relevance: primary
```

**This protocol is known to be defective** (ADR-0031): the bracket is not part
of the token, so a model that reproduces what it sees emits a citation the
parser rejects, and a model told to strip the bracket may strip more. Version 1
is specified here *as it is* rather than as it should be, because M9.5 Step B is
deliberately behaviour-neutral: naming the defect and correcting it are separate
changes, so that the release invalidation in Step C has exactly one cause.
"""

from __future__ import annotations

from typing import Final

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
PROMPT_RENDERING_PROTOCOL_VERSION: Final = 1
