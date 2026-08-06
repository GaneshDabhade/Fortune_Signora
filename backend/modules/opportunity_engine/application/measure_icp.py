"""Assembling the measurement: outcomes, attributes, predicate, lift.

**A service of its own rather than a method on `OpportunityQueries`.** That
object answers *"what should Sales track?"* from this module's own tables and
takes three dependencies to do it; this one reaches two other modules'
published contracts and answers a different question. **Keeping them apart
means a change to one cannot silently reshape the other**, which is the same
reason `build_attributes_reader` is a separate builder in `knowledge_graph`.

### The dependency direction, and it is the one that was ruled

> **[C-328](../../../../docs/LANE_COORDINATION.md): *"`commercial_profile`
> declares. `opportunity_engine` measures."***

Both reads are through `public/` and nothing else: the criteria from
`commercial_profile`, the observed attributes from `knowledge_graph` on the
edge [D-111](../../../../docs/DECISION_REGISTER.md) opened. **The predicate is
called, never reimplemented** — which is what [C-330](../../../../docs/LANE_COORDINATION.md)
was about and why refusing to inline one here cost three coordination items and
was worth all three.
"""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from modules.commercial_profile.public import (
    CriterionKind,
    IcpReader,
    evaluate_criteria,
)
from modules.knowledge_graph.public import AccountAttributesReader
from modules.opportunity_engine.application.ports import OpportunityRepository
from modules.opportunity_engine.domain.criterion_lift import (
    CriterionLift,
    Outcome,
    lift_for,
)
from modules.opportunity_engine.domain.opportunity import TERMINAL_STAGES

#: How many decided accounts one measurement reads.
#:
#: **A bound, because a backtest over an unbounded history is an unbounded
#: fetch wearing a date** (§14). Five hundred is far past the sample size at
#: which a lift stops being directional, so the bound constrains cost without
#: constraining the answer — and a workspace that exceeds it is measured on its
#: most recent five hundred decisions, which is the half a seller would choose.
MEASUREMENT_LIMIT = 500


@dataclass(frozen=True, slots=True)
class IcpMeasurement:
    """What one product's ICP predicted.

    **`product_id` and not the product's name.** This module never learned what
    a product is called and does not start here; the surface that renders this
    already reads the catalog.
    """

    product_id: UUID
    criteria: tuple[CriterionLift, ...]
    #: Decided accounts the measurement drew on, before any criterion filtered
    #: them. **The honest denominator**, and the number that says whether any
    #: of the figures above are worth reading.
    decided: int


class MeasureIcp:
    """Score each declared criterion against decided accounts."""

    def __init__(
        self,
        *,
        repository: OpportunityRepository,
        icp: IcpReader,
        attributes: AccountAttributesReader,
    ) -> None:
        self._repository = repository
        self._icp = icp
        self._attributes = attributes

    async def for_workspace(self, workspace_id: UUID) -> tuple[IcpMeasurement, ...]:
        """One measurement per product the customer declared an ICP for.

        **Empty when no ICP has been declared** — not an error. A workspace
        that has not described who buys from it is in a state to wait in, and
        the surface says so rather than showing zeroes.
        """
        declared = await self._icp.current(workspace_id)
        if declared is None:
            return ()

        page = await self._repository.decided_page(
            workspace_id, after=None, limit=MEASUREMENT_LIMIT
        )
        decided = [
            (opportunity, state)
            for opportunity, state in page
            if state.stage in TERMINAL_STAGES
        ]
        # **One call for every account, not one per account** — the batch read
        # exists because this loop would otherwise be the N+1 §14 forbids.
        observed = await self._attributes.for_accounts(
            workspace_id, [opportunity.entity_id for opportunity, _ in decided]
        )

        measurements = []
        for criteria in declared.criteria:
            per_kind: dict[CriterionKind, list[Outcome]] = {
                kind: [] for kind in CriterionKind
            }
            for opportunity, state in decided:
                attributes = observed[opportunity.entity_id]
                for verdict in evaluate_criteria(
                    criteria,
                    industry=_text(attributes.industry.value),
                    country=_text(attributes.country.value),
                    employees=_count(attributes.employee_count.value),
                ):
                    per_kind[verdict.kind].append(
                        Outcome(stage=state.stage, verdict=verdict.verdict)
                    )

            measurements.append(
                IcpMeasurement(
                    product_id=criteria.product_id,
                    # **Sorted by the enum's own order**, so two requests
                    # render the same rows in the same order and a criterion
                    # added later cannot silently move.
                    criteria=tuple(
                        lift_for(kind, per_kind[kind]) for kind in CriterionKind
                    ),
                    decided=len(decided),
                )
            )
        return tuple(measurements)


def _text(value: object | None) -> str | None:
    """A resolved value as text, or `None` when it is not.

    **A guard rather than a cast.** The canonical vocabulary types values per
    attribute, but this reads across a published boundary — and a claim that
    arrived as the wrong shape should produce `UNMEASURED` here rather than a
    `TypeError` three frames down inside the predicate.
    """
    return value if isinstance(value, str) else None


def _count(value: object | None) -> int | None:
    # `bool` is an `int` in Python and would silently measure `True` as 1.
    return value if isinstance(value, int) and not isinstance(value, bool) else None


__all__ = ["MEASUREMENT_LIMIT", "IcpMeasurement", "MeasureIcp"]
