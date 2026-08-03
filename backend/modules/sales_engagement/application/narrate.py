"""Narrating one Approach Brief — every pass that has an artifact, over one graph.

**Six views of one reasoning graph, and the graph is written once.** A pass is
not a different prompt over different data; it is a different *question about
the same closed set*. That is what makes a seventh pass cost an artifact rather
than a pipeline, and it is why this file contains no per-pass branch.

```
                         ┌──▶ executive summary
                         ├──▶ conversation strategy
  one reasoning graph ───┼──▶ evidence narration
                         ├──▶ risk narration
                         ├──▶ questions
                         └──▶ objections
```

### It attempts every pass and is not configured to

**A pass with no released artifact costs nothing**: `Synthesise.execute` resolves
the release before it renders anything, so an unreleased pass returns without
reaching a model. Attempting all of them therefore needs no feature flag, no
list to keep in step, and no deployment step — **a pass becomes reachable the
moment its prompt earns a release, and unreachable again the moment a protocol
change withdraws one.**

The alternative — a caller naming which passes to run — puts the release
decision in two places, and the copy nobody maintains is the one that will be
read (`CLAUDE.md` §2).

### What it refuses to decide

**Whether narration happens on a read or in a worker is not this file's
question, and it deliberately encodes no answer.** ADR-0200 leaves it open as
❓ Q-2 — materialized and auditable, or per-read and always current — and
`CLAUDE.md` §7 forbids an endpoint that triggers model work synchronously. So
this is an application service that *produces* narration when asked, and says
nothing about who asks or how often. A worker calling it and a request calling
it are both satisfied by this shape; **choosing between them is the product
owner's, and building either into this file would make the choice invisibly.**
"""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from modules.sales_engagement.application.approach import Approach
from modules.sales_engagement.application.synthesise import PassOutcome, PassResult, Synthesise
from modules.sales_engagement.domain.brief import ApproachBrief, Pass, assemble
from modules.sales_engagement.domain.synthesis import Synthesis


@dataclass(frozen=True, slots=True)
class NarratedBrief:
    """A brief, and an account of what happened to every pass that was tried.

    **The outcomes are carried beside the brief rather than folded into it.** A
    brief is what a seller reads; `attempts` is what an engineer reads when a
    section is missing — and *"executive summary refused: it said 73% and
    nothing derived 73%"* is a different fact from anything the brief itself
    could carry.

    Keeping them separate is what stops the brief growing a field about its own
    production, which is the shape that eventually puts a stack trace on a
    screen.
    """

    brief: ApproachBrief
    attempts: tuple[PassResult, ...]

    @property
    def refused(self) -> tuple[PassResult, ...]:
        """Passes that reached a model and were not trusted.

        **Narrower than *"did not produce prose"*, deliberately.** A pass with no
        released artifact never ran, and counting it as a refusal would make an
        unbuilt prompt look like a misbehaving one — a distinction the
        operational record needs, because one is a backlog item and the other is
        a defect.
        """
        return tuple(
            one
            for one in self.attempts
            if one.outcome in (PassOutcome.REFUSED, PassOutcome.MALFORMED)
        )


class NarrateBrief:
    """Runs every available pass over one Approach, and assembles the brief."""

    def __init__(self, *, synthesise: Synthesise) -> None:
        self._synthesise = synthesise

    async def execute(
        self, approach: Approach, *, workspace_id: UUID, correlation_id: UUID
    ) -> NarratedBrief:
        """Narrate what can be narrated, and assemble the brief either way.

        **Sequential, and that is a decision rather than an oversight.** Six
        independent model calls would gather concurrently, and today one pass
        has an artifact — so concurrency would be machinery for a load that does
        not exist (`CLAUDE.md` §6). **The trigger is a second released pass on a
        latency-sensitive path**, which needs Q-2 answered first: a worker
        materializing narration does not care how long six calls take, and a
        request path is forbidden from making them at all.
        """
        attempts: list[PassResult] = []
        narration: dict[Pass, Synthesis] = {}

        for pass_ in Pass:
            result = await self._synthesise.execute(
                approach,
                pass_,
                workspace_id=workspace_id,
                correlation_id=correlation_id,
            )
            attempts.append(result)
            if result.synthesis is not None:
                narration[pass_] = result.synthesis

        return NarratedBrief(
            brief=assemble(
                reasoning=approach.reasoning,
                fits=approach.fits,
                product=approach.product,
                # **Whatever survived, and nothing more.** A brief with no
                # narration is complete rather than degraded — every field above
                # it was produced without a model (ADR-0200).
                narration=narration,
            ),
            attempts=tuple(attempts),
        )
