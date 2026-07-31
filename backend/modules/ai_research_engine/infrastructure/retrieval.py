"""Retrieving what Signora already knows, through one ratified edge.

`OpportunityQueries` is the AI Research Engine's **only** pipeline dependency,
and it is enough: an `OpportunityExplanation` carries the opportunity, its
history, the originating score with its full contribution ledger, one
`SignalExplanation` per contributing signal, the business events beneath each,
and the dissent the score preserved.

**Nothing external is reachable from here, by construction.** There is no HTTP
client, no provider, no second module. The Internal Research ruling of
2026-07-31 is not enforced by discipline in this file — it is enforced by the
fact that this file has nothing else to call, and by the Security Invariant that
forbids a network client anywhere in the module.

**It translates; it never derives.** Each fact restates a value the pipeline
already computed, addressed by the id the pipeline already minted. The
comparisons that *use* these facts are derivations, and they produce a different
thing: a `ResearchFinding`, which cites the refs assembled here.

---

**Assembled in one function, typed on `OpportunityExplanation`.** Per-fact
helpers were written first and discarded: annotating them required naming
`BusinessEvent` and `SignalExplanation`, which arrive *inside* another module's
published contract and are not this module's dependencies to declare. Keeping
the types flowing from the one imported contract removes eight `type: ignore`s
and matches how M8's assembler is written, for the same reason.

**Attributes are typed, where M8's assembler writes strings.** That difference is
deliberate and narrow. M8 assembles evidence for a *prompt* and for recorded
golden datasets, where keeping the textual form is what makes a fact assembled
live and the same fact read back from a fixture identical. These facts are
assembled for *deterministic comparison*, and a comparison over strings is
precisely the type-loss `EvidenceFact`'s canonical form tags to prevent — `1`
and `"1"` must never compare equal by accident.
"""

from __future__ import annotations

from uuid import UUID

from modules.ai_platform.public import EvidenceFact, EvidenceRef, EvidenceValue
from modules.ai_research_engine.domain.retrieval import (
    BUSINESS_EVENT,
    CORROBORATED,
    DISSENTING_SIGNAL,
    EVENT_TYPE,
    OBSERVED_ON,
    OCCURRED_ON,
    PROVIDER_COUNT,
    PROVIDERS,
    RELEVANCE,
    SIGNAL_TYPE,
)
from modules.opportunity_engine.public import OpportunityExplanation, OpportunityQueries

#: Joins a provider set into one attribute. Sorted before joining, so the same
#: agreement read twice is the same value — the order providers come out of the
#: pipeline in is not a fact about the account.
PROVIDER_SEPARATOR = ","


class OpportunityFactSource:
    """The facts behind one tracked account, through `opportunity_engine.public`."""

    def __init__(self, queries: OpportunityQueries) -> None:
        self._queries = queries

    async def facts_for(self, workspace_id: UUID, entity_id: UUID) -> tuple[EvidenceFact, ...]:
        """Two reads rather than one, for the reason M8's source gives.

        Research asks about an *account*; the Opportunity Engine addresses an
        explanation by opportunity. Resolving that here keeps the port's
        vocabulary — a caller asks about a company, never about a workflow
        object it would have to know exists.
        """
        tracked = await self._queries.tracked(workspace_id, entity_id)
        if tracked is None:
            return ()
        explanation = await self._queries.explanation(workspace_id, tracked.opportunity.id)
        if explanation is None:
            return ()
        return assemble(explanation)


def assemble(explanation: OpportunityExplanation) -> tuple[EvidenceFact, ...]:
    """The translation, as a function — so a seeder, a test and the runtime
    source produce byte-identical facts from identical input.

    **Business events carry who independently agreed.**
    `corroborating_providers` is the only place in the reachable chain where
    provider agreement is visible, and nothing in the product surfaces it
    today. It is carried as both a count and the sorted names: a derivation
    compares counts, and a customer checking the finding needs the names.

    **Dissent is carried because the score preserved it.** The Buying Score
    Engine keeps outweighed readings through six stages precisely so they are
    not netted away. M8's assembler drops them — correctly, since they hold no
    counted arithmetic — which leaves them visible to nothing until here.
    """
    score = explanation.originating_score
    if score is None:
        return ()

    workspace_id = explanation.opportunity.workspace_id
    facts: dict[EvidenceRef, EvidenceFact] = {}

    # Two signals may cite one business event. Keyed by ref rather than
    # appended, so the same account read twice produces the same tuple and a
    # derivation over it cannot depend on traversal order.
    for signal in score.signals:
        for event in signal.business_events:
            providers = tuple(sorted(event.corroborating_providers))
            event_attributes: tuple[tuple[str, EvidenceValue], ...] = (
                (EVENT_TYPE, event.type_key.value),
                (OCCURRED_ON, event.occurred_at.date()),
                (PROVIDER_COUNT, len(providers)),
                (PROVIDERS, PROVIDER_SEPARATOR.join(providers)),
                (CORROBORATED, len(providers) > 1),
            )
            ref = EvidenceRef(kind=BUSINESS_EVENT, id=event.id)
            facts.setdefault(
                ref,
                EvidenceFact(
                    ref=ref,
                    workspace_id=workspace_id,
                    summary=event.summary,
                    attributes=event_attributes,
                ),
            )

    # A signal is never both dissenting and a counted contribution — dissent is
    # by definition what did not count — so this kind and M8's
    # `signal_contribution` can never address one row.
    for outweighed in score.dissent:
        dissenting = outweighed.signal
        signal_attributes: tuple[tuple[str, EvidenceValue], ...] = (
            (SIGNAL_TYPE, dissenting.signal_type.value),
            (RELEVANCE, dissenting.relevance.value),
            (OBSERVED_ON, dissenting.occurred_at.date()),
        )
        ref = EvidenceRef(kind=DISSENTING_SIGNAL, id=dissenting.id)
        facts.setdefault(
            ref,
            EvidenceFact(
                ref=ref,
                workspace_id=workspace_id,
                summary=dissenting.rationale,
                attributes=signal_attributes,
            ),
        )

    return tuple(sorted(facts.values(), key=lambda fact: fact.ref))
