"""Assembling one Target Account's approach reasoning.

**Composition, and nothing else.** The judgement is entirely in
`domain/reasoning.py`, which is pure; this reads the two ports and hands their
output to it. Anything that looked like a decision creeping in here would be
commercial reasoning outside the layer that is tested for it.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, replace
from datetime import UTC, datetime
from uuid import UUID

from modules.sales_engagement.application.ports import (
    CommitteeReader,
    EvidenceReader,
    PortfolioReader,
)
from modules.sales_engagement.domain.fit import ProductFit, ProductRef, fit, likely
from modules.sales_engagement.domain.reasoning import (
    ApproachReasoning,
    CommitteeRoleRef,
    Unknown,
    reason,
)


@dataclass(frozen=True, slots=True)
class ApproachInput:
    workspace_id: UUID
    account_id: UUID
    #: Which of the Signora Customer's products this approach is about.
    #:
    #: **The seller's override, and `None` means infer it** (SE-04). An
    #: override is an answer rather than a hint: when it is present the
    #: portfolio is not consulted at all, because re-checking a person's
    #: decision against a guess is how a product starts arguing with its own
    #: customer.
    product_id: UUID | None = None


@dataclass(frozen=True, slots=True)
class Approach:
    """The whole answer for one Target Account.

    **`fits` is empty when the seller said which product**, because nothing was
    inferred and showing a ranking beside their own answer would invite them to
    re-litigate a decision they already made.
    """

    reasoning: ApproachReasoning
    fits: tuple[ProductFit, ...]
    #: `None` when the seller overrode (their answer is on the request), when
    #: two products tie, or when nothing fits.
    product: ProductRef | None


class AssembleApproach:
    def __init__(
        self,
        *,
        committees: CommitteeReader,
        evidence: EvidenceReader,
        portfolio: PortfolioReader,
        clock: Callable[[], datetime] = lambda: datetime.now(UTC),
    ) -> None:
        self._committees = committees
        self._evidence = evidence
        self._portfolio = portfolio
        # Injected because staleness is time-dependent and a test that could
        # not fix *now* would assert against the day it ran.
        self._clock = clock

    async def execute(self, request: ApproachInput) -> Approach:
        now = self._clock()
        evidence = await self._evidence.evidence(
            request.workspace_id, account_id=request.account_id
        )

        if request.product_id is not None:
            committee = await self._committees.committee(
                request.workspace_id, product_id=request.product_id
            )
            return Approach(
                reasoning=reason(
                    account_id=request.account_id,
                    committee=committee,
                    evidence=evidence,
                    now=now,
                ),
                fits=(),
                product=None,
            )

        # **Inference, and the tie is left standing.** `likely` returns None
        # when two products fit equally well; the reasoning then runs against
        # the strongest committee anyway, so a seller still sees roles and
        # evidence rather than an empty screen while they answer the question.
        portfolio = await self._portfolio.portfolio(request.workspace_id)
        committees = {
            product: await self._committees.committee(request.workspace_id, product_id=product.id)
            for product in portfolio
        }
        fits = fit(committees, evidence, now=now)
        chosen = likely(fits)
        applies: tuple[CommitteeRoleRef, ...] = (
            committees.get(chosen, ()) if chosen is not None else _widest(committees, fits)
        )

        reasoning = reason(
            account_id=request.account_id,
            committee=applies,
            evidence=evidence,
            now=now,
        )
        if chosen is None and len(fits) > 1:
            reasoning = replace(
                reasoning,
                unknowns=reasoning.unknowns
                + (
                    Unknown(
                        subject="which product this is about",
                        question=(
                            f"Is this {fits[0].product.name} or {fits[1].product.name}? "
                            "The evidence fits both equally."
                        ),
                    ),
                ),
            )
        return Approach(reasoning=reasoning, fits=fits, product=chosen)


def _widest(
    committees: dict[ProductRef, tuple[CommitteeRoleRef, ...]],
    fits: tuple[ProductFit, ...],
) -> tuple[CommitteeRoleRef, ...]:
    """The committee to reason against when no product could be chosen.

    **The best-fitting one, rather than nothing.** A seller looking at a tie
    should still see which roles the evidence names — the open question is
    *which product*, not *whether anything is happening*.
    """
    return committees.get(fits[0].product, ()) if fits else ()
