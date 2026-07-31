"""Storing and reading back a Decision Package.

**Save, and read the latest. There is no update and no delete**, because a
package is a historical fact: it records the conclusion a customer was
actually shown. A better conclusion is a *new* package naming a later score,
and editing one would destroy the only record of what was in front of them —
which would silently invalidate every audit citing it.

Immutability is enforced at the database by the absent `UPDATE` grant
(migration 0017). The absent method here means no code path even asks.

It shares the **caller's session**, matching `SqlNarrationRepository` and
deliberately unlike `SqlInferenceRecorder`. The asymmetry is the point
(ADR-0029): a package and its event are the unit of work, so a rolled-back
transaction must leave neither behind — a package nobody committed was never
shown to anyone. Operational history is the opposite case, because the model
call happened whatever became of the transaction that asked for it.

**Two columns are written and never read.** `support_level` and `contested`
duplicate facts the `support` JSONB already carries, and duplicated truth
eventually becomes contradictory truth. They earn their place as an operator
query surface — *"which accounts are on limited support?"* — and the
duplication is neutralised by never letting them influence behaviour: reading
reconstructs `SupportBasis` from the JSONB alone and lets `level` derive, so a
drift between the two could never reach a customer. Asserted, not merely
intended.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from modules.ai_platform.public import AIVendor, GroundedStatement
from modules.ai_reasoning_engine.domain.package import AlternativeReading, DecisionPackage
from modules.ai_reasoning_engine.domain.support import SupportBasis
from modules.ai_reasoning_engine.domain.temporal import TemporalExplanation
from modules.ai_reasoning_engine.infrastructure.models import AIReasoningModel
from modules.buying_score_engine.public import ScoreTrigger, Trend
from modules.opportunity_engine.public import EvidenceState

#: The actor recorded on rows nobody clicked to create. Matches the AI
#: Platform's: a package is produced by the pipeline, and attributing it to a
#: person would be a false audit trail.
SYSTEM_USER_ID = UUID("00000000-0000-0000-0000-000000000001")


class SqlDecisionPackageRepository:
    """Satisfies `DecisionPackageRepository`. **No update, no delete.**"""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(self, package: DecisionPackage) -> None:
        self._session.add(
            AIReasoningModel(
                id=package.id,
                workspace_id=package.workspace_id,
                correlation_id=package.correlation_id,
                subject_kind=package.subject_kind,
                subject_id=package.subject_id,
                summary=_statement(package.summary),
                proposition=_statement(package.proposition),
                stated_reasoning=[_statement(s) for s in package.stated_reasoning],
                supporting_evidence=list(package.supporting_evidence),
                support=_support(package.support),
                # Written from the same object as the JSONB above, so the two
                # cannot disagree at the moment of writing. Nothing reads them.
                support_level=package.support.level.value,
                contested=package.support.contested,
                temporal=_temporal(package.temporal),
                alternative_readings=[
                    {"signal_type": r.signal_type, "reason": r.reason}
                    for r in package.alternative_readings
                ],
                limitations=list(package.limitations),
                suggested_validation=list(package.suggested_validation),
                catalog_version=package.catalog_version,
                prompt_name=package.prompt_name,
                prompt_version=package.prompt_version,
                prompt_fingerprint=package.prompt_fingerprint,
                model=package.model,
                vendor=package.vendor.value,
                evidence_digest=package.evidence_digest,
                inference_id=package.inference_id,
                originating_buying_score_id=package.originating_buying_score_id,
                payload_version=package.payload_version,
                created_at=package.created_at,
                updated_at=package.created_at,
                created_by=SYSTEM_USER_ID,
                updated_by=SYSTEM_USER_ID,
            )
        )
        await self._session.flush()

    async def latest_for(self, workspace_id: UUID, subject_id: UUID) -> DecisionPackage | None:
        """The most recent package for a subject.

        **Derived from the rows, never a stored "current" flag.** Packages
        accumulate; a column marking one as current would be a second
        representation of a fact the timestamps already carry, and it would
        need the `UPDATE` grant this table withholds to maintain.
        """
        row = (
            await self._session.execute(
                select(AIReasoningModel)
                .where(
                    AIReasoningModel.workspace_id == workspace_id,
                    AIReasoningModel.subject_id == subject_id,
                )
                .order_by(AIReasoningModel.created_at.desc())
                .limit(1)
            )
        ).scalar_one_or_none()
        return _to_package(row) if row is not None else None


def _statement(statement: GroundedStatement) -> dict[str, Any]:
    return {"text": statement.text, "evidence": list(statement.evidence)}


def _support(basis: SupportBasis) -> dict[str, Any]:
    """The basis, not the level. Sorted so two identical bases store
    identically — insertion order is a hidden input."""
    return {
        "corroborating_providers": sorted(basis.corroborating_providers),
        "contributing_events": basis.contributing_events,
        "evidence_state": basis.evidence_state.value,
        "contested": basis.contested,
        "dissenting_signals": basis.dissenting_signals,
    }


def _temporal(temporal: TemporalExplanation) -> dict[str, Any]:
    return {
        "trigger": temporal.trigger.value,
        "basis_at": temporal.basis_at.isoformat(),
        "computed_at": temporal.computed_at.isoformat(),
        "delta": temporal.delta,
        "trend": temporal.trend.value,
        "evidence_state": temporal.evidence_state.value,
        "valid_until": temporal.valid_until.isoformat() if temporal.valid_until else None,
        "supersedes": str(temporal.supersedes) if temporal.supersedes else None,
    }


def _to_package(row: AIReasoningModel) -> DecisionPackage:
    """Reconstruct the package. **`support_level` and `contested` are not
    read** — `SupportBasis` derives its level, and a stored copy that had
    drifted must not be able to reach a customer."""
    support = row.support
    temporal = row.temporal
    return DecisionPackage(
        id=row.id,
        workspace_id=row.workspace_id,
        correlation_id=row.correlation_id,
        subject_kind=row.subject_kind,
        subject_id=row.subject_id,
        summary=GroundedStatement(**row.summary),
        proposition=GroundedStatement(**row.proposition),
        stated_reasoning=tuple(GroundedStatement(**s) for s in row.stated_reasoning),
        supporting_evidence=tuple(row.supporting_evidence),
        support=SupportBasis(
            corroborating_providers=frozenset(support["corroborating_providers"]),
            contributing_events=support["contributing_events"],
            evidence_state=EvidenceState(support["evidence_state"]),
            contested=support["contested"],
            dissenting_signals=support["dissenting_signals"],
        ),
        temporal=TemporalExplanation(
            trigger=ScoreTrigger(temporal["trigger"]),
            basis_at=datetime.fromisoformat(temporal["basis_at"]),
            computed_at=datetime.fromisoformat(temporal["computed_at"]),
            delta=temporal["delta"],
            trend=Trend(temporal["trend"]),
            evidence_state=EvidenceState(temporal["evidence_state"]),
            valid_until=(
                datetime.fromisoformat(temporal["valid_until"]) if temporal["valid_until"] else None
            ),
            supersedes=UUID(temporal["supersedes"]) if temporal["supersedes"] else None,
        ),
        alternative_readings=tuple(
            AlternativeReading(signal_type=r["signal_type"], reason=r["reason"])
            for r in row.alternative_readings
        ),
        limitations=tuple(row.limitations),
        suggested_validation=tuple(row.suggested_validation),
        catalog_version=row.catalog_version,
        prompt_name=row.prompt_name,
        prompt_version=row.prompt_version,
        prompt_fingerprint=row.prompt_fingerprint,
        model=row.model,
        vendor=AIVendor(row.vendor),
        evidence_digest=row.evidence_digest,
        inference_id=row.inference_id,
        originating_buying_score_id=row.originating_buying_score_id,
        created_at=row.created_at,
        payload_version=row.payload_version,
    )
