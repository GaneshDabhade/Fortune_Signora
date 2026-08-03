"""Assembling one Target Account's approach reasoning.

**Composition, and nothing else.** The judgement is entirely in
`domain/reasoning.py`, which is pure; this reads the two ports and hands their
output to it. Anything that looked like a decision creeping in here would be
commercial reasoning outside the layer that is tested for it.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID

from modules.sales_engagement.application.ports import CommitteeReader, EvidenceReader
from modules.sales_engagement.domain.reasoning import ApproachReasoning, reason


@dataclass(frozen=True, slots=True)
class ApproachInput:
    workspace_id: UUID
    account_id: UUID
    #: Which of the Signora Customer's products this approach is about.
    #:
    #: **Required, and deliberately not inferred here.** A Buying Committee is
    #: declared per product, so *"which committee applies"* is unanswerable
    #: without it. Inferring the likely product from the ICP, the signals and
    #: the intent is its own slice (SE-04) with its own evidence and its own
    #: override — folding a guess into this use case would bury a commercial
    #: decision inside an assembly step.
    product_id: UUID


class AssembleApproach:
    def __init__(
        self,
        *,
        committees: CommitteeReader,
        evidence: EvidenceReader,
        clock: Callable[[], datetime] = lambda: datetime.now(UTC),
    ) -> None:
        self._committees = committees
        self._evidence = evidence
        # Injected because staleness is time-dependent and a test that could
        # not fix *now* would assert against the day it ran.
        self._clock = clock

    async def execute(self, request: ApproachInput) -> ApproachReasoning:
        committee = await self._committees.committee(
            request.workspace_id, product_id=request.product_id
        )
        evidence = await self._evidence.evidence(
            request.workspace_id, account_id=request.account_id
        )
        return reason(
            account_id=request.account_id,
            committee=committee,
            evidence=evidence,
            now=self._clock(),
        )
