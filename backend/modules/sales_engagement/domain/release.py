"""When a commercial synthesis prompt may be used, and why this module derives it.

**Release is earned, never declared** — the AI Platform's rule, adopted whole.
Nothing here can mark a prompt released; a prompt is usable exactly where a
recorded measurement satisfies the criteria below, so a change to what *fit for
use* means re-reads history correctly instead of leaving a stratum of rows
judged by a rule nobody remembers.

### Why this module derives eligibility instead of calling `PromptVersion.is_released`

**One field means something different here, and the difference is not cosmetic.**

`Evaluation.rendering_protocol_version` records *which protocol produced the text
the model actually read*. For every prompt written before this one that is the AI
Platform's evidence rendering protocol, and `earns_release` compares it against
`PROMPT_RENDERING_PROTOCOL_VERSION`. **A Sales Engagement prompt is never shown an
evidence set.** It is shown a reasoning graph, rendered by the Commercial Context
Protocol, and that is the condition its measurements are bound to.

Reusing `earns_release` would therefore compare this module's protocol version
against an unrelated module's constant — a comparison that is meaningless whatever
answer it returns. So the *records* are reused verbatim (`Evaluation` states facts,
not verdicts, and says so) and only the derivation is this module's.

> **The two protocols share an integer namespace and nothing coordinates them.**
> An earlier draft of this file claimed the divergence *failed closed* — that the
> platform's gate would always refuse a Sales Engagement measurement. **That held
> only while the constants happened to differ.** Bumping the Commercial Context
> Protocol to 2 made them equal, and `PromptVersion.is_released` silently began
> returning the right answer for the wrong reason.
>
> Neither state is a guarantee, because the comparison is meaningless whichever
> way it lands. What is pinned instead is **visibility**: a test asserts the two
> constants currently coincide, so the next move of either one fails a test and
> sends the reader to C-214 rather than leaving the coupling invisible.

**Reconciling the two is [C-214](../../../../docs/LANE_COORDINATION.md)**, raised
rather than fixed: `ai_platform` is not this lane's module, and parameterising a
frozen domain type to suit a second consumer is exactly the change §20e reserves
for its assignee. The trigger is stated there — a third input protocol.
"""

from __future__ import annotations

from typing import Final

from modules.ai_platform.public import Evaluation, PromptNotReleasableError, PromptVersion
from modules.sales_engagement.domain.context import COMMERCIAL_CONTEXT_PROTOCOL_VERSION

#: The share of a case's **load-bearing** graph elements a synthesis must speak
#: to before it counts as useful.
#:
#: The one number in these criteria that is a judgement rather than a
#: definition, so it is stated once, here, with its reasoning — rather than
#: appearing as a literal inside the harness.
#:
#: **Lower than the AI Platform's 0.66, deliberately, and for a stated reason.**
#: That figure governs a narration whose job is to restate facts, where omitting
#: a load-bearing one is a straightforward miss. An executive summary is
#: *supposed* to leave things out: §26 asks for the account in thirty seconds,
#: and a pass that must touch two thirds of a rich graph is a list wearing a
#: summary's name — which would make the criteria reward length, the failure
#: `MINIMUM_COVERAGE` was written to avoid in the first place.
#:
#: Not lower than a half, because below it the recommendation itself can go
#: unmentioned while the run still passes.
MINIMUM_COVERAGE: Final = 0.50


def earns_release(evaluation: Evaluation) -> bool:
    """Both halves: the run satisfied the criteria, **and** it was measured
    under the conditions now in force.

    Two of the three criteria are definitions rather than thresholds. A refused
    synthesis and a malformed draft are deterministic outcomes — the fence is
    arithmetic over a closed set — so any occurrence is a defect and no number
    of samples excuses one. The third is the judgement, and it lives on
    `MINIMUM_COVERAGE` where it can be read and argued with.

    `retries` is deliberately absent. It describes what the *provider* did, not
    what the prompt did, and penalising a prompt for its provider's bad
    afternoon would make the criteria measure the wrong thing.
    """
    return (
        evaluation.grounding_failures == 0
        and evaluation.schema_failures == 0
        and evaluation.coverage >= MINIMUM_COVERAGE
        and evaluation.rendering_protocol_version == COMMERCIAL_CONTEXT_PROTOCOL_VERSION
    )


def released_for(prompt: PromptVersion, model: str) -> bool:
    """Whether this prompt has earned this model, on any dataset.

    The **runtime** question. At the point of use there is no dataset — a
    dataset is what an evaluation was *conducted on*, and it lives in the record
    supporting the release rather than in the call relying on it.
    """
    return any(earns_release(one) and one.model == model for one in prompt.evaluations)


def require(prompt: PromptVersion, model: str) -> None:
    """Raise unless this prompt has earned this model.

    ADR-0028's release rule at the point of use: *a prompt may not be used with
    a model it was never evaluated on.* **Developing against a small local model
    demonstrates nothing about a frontier hosted one**, and the gap is made
    structural rather than remembered.
    """
    if released_for(prompt, model):
        return
    raise refusal(prompt, model)


def refusal(prompt: PromptVersion, model: str) -> PromptNotReleasableError:
    """The refusal for an unearned pairing, **as a value rather than a raise**.

    Returned so a caller that has already established the pairing is unreleased
    can raise it directly, instead of calling `require` and then writing an
    unreachable line to satisfy a type checker. **A guard that cannot fail is
    documentation pretending to be code** (`CLAUDE.md` §2), and that line was
    one.

    Both callers share this, so the two failures below are worded once.
    """
    stale = sorted(
        {
            one.rendering_protocol_version
            for one in prompt.evaluations
            if one.model == model
            and one.grounding_failures == 0
            and one.schema_failures == 0
            and one.coverage >= MINIMUM_COVERAGE
        }
        - {COMMERCIAL_CONTEXT_PROTOCOL_VERSION}
    )
    if stale:
        return PromptNotReleasableError(
            f"prompt {prompt.reference} passed for model '{model}' under Commercial Context "
            f"Protocol {stale}, but this process renders at protocol "
            f"{COMMERCIAL_CONTEXT_PROTOCOL_VERSION}. That measurement is still true and is "
            "still on record; it no longer describes what the model would be shown. "
            "Re-evaluate under the current protocol — do not re-author the prompt."
        )

    earned = sorted({one.model for one in prompt.evaluations if earns_release(one)})
    return PromptNotReleasableError(
        f"prompt {prompt.reference} has not passed evaluation for model '{model}'. "
        f"Passed for: {earned or 'nothing yet'}. A prompt tuned against one model has not "
        "been shown to behave on another."
    )
