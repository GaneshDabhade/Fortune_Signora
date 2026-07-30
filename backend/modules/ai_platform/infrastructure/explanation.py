"""Turning the pipeline's explanation into a closed evidence set.

**The one file in the AI Platform that knows the pipeline exists**, and it
sits in `infrastructure/` for exactly that reason. It satisfies the
`ExplanationSource` Protocol declared in `application/ports.py`, reaching
`opportunity_engine.public` and nothing deeper — so the substrate above it
still knows nothing about opportunities, scores or signals.

**It translates; it never derives.** Every fact here restates something the
deterministic pipeline already computed, addressed by the id the pipeline
already minted for it. Nothing is totalled, ranked, inferred or summarised
into existence: if a proposition is not already in `OpportunityExplanation`,
it does not become one by passing through here. That is the boundary the M8
stop condition names — the moment this file needs to *decide* something, the
capability has moved into M9 and the correct response is to halt.

Quantities are written as **strings**, not numbers. Evidence canonicalises by
type, so a value's textual form is what the model is shown and what the
digest covers; keeping the text means a fact assembled here and the same fact
read back from a recorded golden dataset are the same fact.
"""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from modules.ai_platform.domain.evidence import EvidenceSet, EvidenceSetBuilder
from modules.opportunity_engine.public import OpportunityExplanation, OpportunityQueries

#: Evidence kinds. Each names *what the pipeline calls the thing*, so a
#: citation resolves back to a row a human can look at.
OPPORTUNITY = "opportunity"
BUYING_SCORE = "buying_score"
CONTRIBUTION = "signal_contribution"


class OpportunityExplanationSource:
    """Assembles the evidence behind one tracked opportunity."""

    def __init__(self, queries: OpportunityQueries) -> None:
        self._queries = queries

    async def evidence_for(self, workspace_id: UUID, entity_id: UUID) -> EvidenceSet | None:
        """The evidence behind this account's open opportunity, if it has one.

        Two reads rather than one: the port asks about an *account*, and the
        Opportunity Engine addresses an explanation by opportunity. Resolving
        that here keeps the port's vocabulary — a caller asks about a company,
        not about a workflow object it would have to know exists.
        """
        tracked = await self._queries.tracked(workspace_id, entity_id)
        if tracked is None:
            return None
        explanation = await self._queries.explanation(workspace_id, tracked.opportunity.id)
        if explanation is None:
            return None
        return assemble(explanation, assembled_at=datetime.now(UTC))


def assemble(explanation: OpportunityExplanation, *, assembled_at: datetime) -> EvidenceSet:
    """The translation, as a function — so the seeder and the runtime source
    produce byte-identical evidence from identical input."""
    opportunity = explanation.opportunity
    builder = EvidenceSetBuilder(opportunity.workspace_id)

    builder.add(
        kind=OPPORTUNITY,
        id=opportunity.id,
        summary=(
            f"An opportunity was opened for this account, qualified as "
            f"{opportunity.qualification.value}."
        ),
        attributes={
            "score_at_creation": str(opportunity.score_at_creation),
            "contested_at_creation": "true" if opportunity.contested_at_creation else "false",
            "opened_on": opportunity.created_at.date().isoformat(),
        },
    )

    score = explanation.originating_score
    if score is not None:
        builder.add(
            kind=BUYING_SCORE,
            id=score.score.id,
            summary=(
                f"The buying score that opened this opportunity was {score.score.value} out of "
                f"{score.score.ledger.ceiling}, {score.score.trend.value}."
            ),
            attributes={
                "value": str(score.score.value),
                "ceiling": str(score.score.ledger.ceiling),
                "delta": str(score.score.delta),
                "contested": "true" if score.score.contested else "false",
            },
        )

        for signal in score.signals:
            # The ledger is the authoritative arithmetic; a contribution is
            # attributed to exactly one signal there, and this reads that
            # attribution rather than recomputing it.
            entries = [
                c
                for c in score.score.ledger.entries
                if c.signal_id == signal.signal.id and c.counted
            ]
            if not entries:
                continue
            builder.add(
                kind=CONTRIBUTION,
                id=signal.signal.id,
                summary=signal.signal.rationale,
                attributes={
                    "signal_type": signal.signal.signal_type.value,
                    "relevance": signal.signal.relevance.value,
                    "contribution": str(sum(c.contribution for c in entries)),
                    "observed_on": signal.signal.occurred_at.date().isoformat(),
                },
            )

    return builder.build(assembled_at=assembled_at)
