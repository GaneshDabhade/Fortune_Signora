"""What a commercial synthesis is measured on, and what is deliberately not
measured yet.

**A rubric is published criteria, versioned**, so a change to what *good* means
is legible as a change to the rubric rather than as a movement in quality.

### The dimensions, and why only some are implemented

The product owner's list is long and right: factual correctness, citation
correctness, unsupported claims, hallucination rate, stability, consistency,
commercial usefulness, actionability, readability, executive quality, seller
usefulness, latency, cost. **Four families, and they do not all become
measurable at the same time.**

**Deterministic — ✅ implemented.** The fence is arithmetic over a closed set,
so refusals, malformed drafts, citation resolution and numeric invention are all
*counted* rather than judged.

**Commercial — ⚠️ coverage only.** Clarity, actionability and executive quality
need a human or a judge model. **Coverage is the honest proxy**: a summary that
never mentions the recommendation is unhelpful whatever its prose.

**Operational — ⚠️ stability only, and it is not yet durable.** Latency and cost
belong on an inference record, and a synthesis does not write one yet (C-214).
**Stability needs nothing but a second run** — but `Evaluation` has no field for
it, so it is computed, rendered on the report, and then lost. A regression in
stability between two releases is currently invisible in the manifest, which is
the sharpest argument in C-214 for reconciling the record type.

**Enterprise — ✅ structural.** Reproducibility, auditability and traceability
are properties of the artifacts — prompt fingerprint, dataset fingerprint,
context protocol version — and every one is already recorded on a report.

**Nothing is stubbed.** A dimension with a field and no measurement behind it
would be Decorative Logic (`CLAUDE.md` §2) — the defect this module found and
fixed twice already, once in `reasoning.py` and once in `FitDimension`.

### Why stability is the cheap one, and why it matters most

> **The input is a closed set, so two runs differ only by the model.**

A pass whose output swings between identical inputs is a pass that is not ready,
and that is measurable without a human reading either output. It is the one
quality dimension this architecture gets almost for free, and it catches the
failure a single-run evaluation structurally cannot: a prompt that passes once
and fabricates on the third attempt.
"""

from __future__ import annotations

from typing import Final

from modules.sales_engagement.domain.synthesis import Synthesis

#: Which published criteria were applied. Recorded on every evaluation so a
#: rubric change is legible as a rubric change **rather than as a movement in
#: quality** — which is exactly what the bump to 2 exists to prevent.
#:
#: ### Version 2 — current, 2026-08-03
#:
#: **The fence stopped refusing the possessive of a name it had permitted.** The
#: graph offered *Revenue Cloud*, `conversation_strategy@1` wrote *Revenue
#: Cloud's*, and `_proper_nouns` read `cloud's` as an invented product. A
#: possessive of a permitted noun is English morphology, not a new name.
#:
#: **What passes therefore changed, so the criteria changed**, and a run
#: measured under version 1 is not comparable with one measured under version 2.
#: Recording that here is what stops the improvement reading as the model
#: getting better.
#:
#: **It does not weaken anything.** *Databricks's* still reduces to `databricks`,
#: is still absent from the closed set, and is still refused — pinned by a test.
#:
#: ### Version 1 — superseded, and its measurements stand
#:
#: The two runs recorded against it are still true accounts of what happened.
#: They would both score better today, and neither is re-run to make them look
#: so: **a record of what was true then is not rewritten to match now**
#: (`CLAUDE.md` §2).
RUBRIC_VERSION: Final = 2


def coverage(synthesis: Synthesis, load_bearing: tuple[str, ...]) -> float:
    """The share of a case's load-bearing conclusions the synthesis spoke to.

    **Measured over citations, not over prose.** A passage declares what it is
    about, and matching on the declaration rather than on the words is what
    keeps this from rewarding a summary that happens to contain the right
    string in an unrelated sentence.

    Grounding bounds what a synthesis *may* claim and says nothing about
    whether it claimed anything worth reading — which is the gap this closes.
    """
    if not load_bearing:
        return 0.0
    cited = {one.casefold() for passage in synthesis.passages for one in passage.cites}
    hit = sum(1 for one in load_bearing if one.casefold() in cited)
    return hit / len(load_bearing)


def stability(first: Synthesis, second: Synthesis) -> float:
    """How far two runs over the same closed set agreed about what to talk about.

    **Jaccard over the cited conclusions, not over the words.** Two good
    summaries of one graph will phrase things differently and that is not
    instability; two summaries that disagree about *which findings matter* are
    a pass that has not settled.

    Returns 1.0 when both cited nothing, which cannot occur — a passage with no
    citation is refused at the shape boundary — and is defined here so the
    function is total rather than conditionally correct.
    """
    left = {one.casefold() for passage in first.passages for one in passage.cites}
    right = {one.casefold() for passage in second.passages for one in passage.cites}
    if not left and not right:
        return 1.0
    return len(left & right) / len(left | right)


def criteria() -> tuple[str, ...]:
    """The release criteria, rendered for a human reading a report.

    Stated positively and in one place, so the report and the derivation cannot
    describe different rules.
    """
    from modules.sales_engagement.domain.release import MINIMUM_COVERAGE

    return (
        "refusals            0   the fence is deterministic; any refusal is a defect",
        "malformed drafts    0   a model that cannot hold the schema is unusable here",
        f"coverage           >= {MINIMUM_COVERAGE:.2f}  load-bearing conclusions spoken to",
        "context protocol    current   a measurement describes the text a model was shown",
    )
