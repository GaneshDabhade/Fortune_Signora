"""Storing a completed research run — and the codec that keeps a value typed.

**Findings insert with `ON CONFLICT DO NOTHING`, and that is the whole of
resumability.** A finding's identity is derived from its content, so a
collision means *this exact finding already exists*: a re-run inserts what is
new and silently agrees about what is not. There is no progress checkpoint,
because there is nothing a checkpoint would know that the primary key does not.

**Nothing is updated, anywhere.** `signora_app` holds no `UPDATE` grant on any
of the three tables, so the absence of an update method here is a second lock
rather than the only one.

---

**The attribute codec exists because JSON has fewer types than the domain.**
`EvidenceValue` spans `bool`, `int`, `Decimal`, `datetime`, `date` and `str`;
JSON has numbers, strings and booleans. Writing a `date` as `"2026-06-01"` and
reading it back as a string would silently turn a comparison over dates into a
comparison over text — and a finding recomputed after a round trip would differ
from the one stored, which content-derived identity would then report as a
different finding.

So each value is stored **tagged with its type** and reconstructed by that tag.
This is the same reasoning `EvidenceFact.canonical_form` gives for tagging, and
deliberately not the same function: that one produces a hashing form documented
as *"not for prompts"*, this one must round-trip.
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from modules.ai_platform.public import EvidenceRef, EvidenceValue
from modules.ai_research_engine.domain.research import (
    ResearchError,
    ResearchFinding,
    ResearchSynthesis,
    ResearchTask,
)
from modules.ai_research_engine.infrastructure.models import (
    ResearchFindingModel,
    ResearchSynthesisModel,
    ResearchTaskModel,
)

#: The identity every row is attributed to when the platform acts without a
#: user — the same constant M9's repository uses, for the same reason.
SYSTEM_USER_ID = UUID("00000000-0000-0000-0000-000000000001")


def encode(value: EvidenceValue) -> dict[str, Any]:
    """One value, tagged with its type so it can come back as itself.

    `bool` is tested before `int` and `datetime` before `date`, because each is
    a subclass of the other — reversing the order would tag a boolean as an
    integer and a timestamp as a date, and a stored form that mislabels a type
    is one nobody can reconstruct from.
    """
    if isinstance(value, bool):
        return {"type": "bool", "value": value}
    if isinstance(value, int):
        return {"type": "int", "value": value}
    if isinstance(value, Decimal):
        return {"type": "decimal", "value": str(value)}
    if isinstance(value, datetime):
        return {"type": "datetime", "value": value.isoformat()}
    if isinstance(value, date):
        return {"type": "date", "value": value.isoformat()}
    return {"type": "str", "value": value}


def decode(stored: dict[str, Any]) -> EvidenceValue:
    tag = stored["type"]
    raw = stored["value"]
    if tag == "bool":
        return bool(raw)
    if tag == "int":
        return int(raw)
    if tag == "decimal":
        return Decimal(str(raw))
    if tag == "datetime":
        return datetime.fromisoformat(str(raw))
    if tag == "date":
        return date.fromisoformat(str(raw))
    if tag == "str":
        return str(raw)
    raise ResearchError(
        f"stored attribute has unknown type tag '{tag}'. A value nobody can reconstruct is a "
        "finding nobody can recompute, which is the one property a derivation must keep."
    )


class SqlResearchRepository:
    """Persists one completed research run."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(
        self,
        task: ResearchTask,
        findings: tuple[ResearchFinding, ...],
        synthesis: ResearchSynthesis,
    ) -> None:
        """Everything, or nothing. **One transaction, and it is the caller's.**

        The three rows describe one run: a task whose findings are absent is a
        run that appears to have found nothing, and a synthesis whose findings
        are absent cites rows that do not exist. Committing is the caller's
        decision, so the use case can publish its event in the same transaction
        as the write — which is what the outbox requires.
        """
        self._session.add(_task_row(task))
        for finding in findings:
            await self._session.execute(
                insert(ResearchFindingModel)
                .values(**_finding_values(finding))
                # A re-run recomputing an identical finding must insert nothing
                # rather than fail. The key *is* the content, so a conflict
                # means agreement, not a collision.
                .on_conflict_do_nothing(index_elements=["id"])
            )
        self._session.add(_synthesis_row(synthesis))
        await self._session.flush()


def _task_row(task: ResearchTask) -> ResearchTaskModel:
    return ResearchTaskModel(
        id=task.id,
        workspace_id=task.workspace_id,
        correlation_id=task.correlation_id,
        subject_kind=task.subject.kind,
        subject_id=task.subject.id,
        opportunity_id=task.opportunity_id,
        requested_at=task.requested_at,
        created_by=SYSTEM_USER_ID,
        updated_by=SYSTEM_USER_ID,
    )


def _finding_values(finding: ResearchFinding) -> dict[str, Any]:
    return {
        "id": finding.id,
        "workspace_id": finding.workspace_id,
        "task_id": finding.task_id,
        "subject_kind": finding.subject.kind,
        "subject_id": finding.subject.id,
        "derivation": finding.derivation,
        "derivation_version": finding.derivation_version,
        "attributes": [
            {"name": name, **encode(value)} for name, value in finding.attributes
        ],
        "cited": [ref.token for ref in finding.cited],
        "payload_version": finding.payload_version,
        "created_by": SYSTEM_USER_ID,
        "updated_by": SYSTEM_USER_ID,
    }


def _synthesis_row(synthesis: ResearchSynthesis) -> ResearchSynthesisModel:
    return ResearchSynthesisModel(
        id=synthesis.id,
        workspace_id=synthesis.workspace_id,
        task_id=synthesis.task_id,
        statements=[
            {"text": s.text, "evidence": list(s.evidence)} for s in synthesis.statements
        ],
        finding_ids=list(synthesis.finding_ids),
        prompt_name=synthesis.prompt_name,
        prompt_version=synthesis.prompt_version,
        prompt_fingerprint=synthesis.prompt_fingerprint,
        model=synthesis.model,
        vendor=synthesis.vendor.value,
        evidence_digest=synthesis.evidence_digest,
        inference_id=synthesis.inference_id,
        payload_version=synthesis.payload_version,
        created_by=SYSTEM_USER_ID,
        updated_by=SYSTEM_USER_ID,
    )


def attributes_of(stored: list[dict[str, Any]]) -> tuple[tuple[str, EvidenceValue], ...]:
    """Read attributes back, typed. Used by tests and by any future reader —
    a stored finding that cannot be reconstructed is one nobody can check."""
    return tuple((entry["name"], decode(entry)) for entry in stored)


def cited_of(stored: list[str]) -> tuple[EvidenceRef, ...]:
    return tuple(EvidenceRef.parse(token) for token in stored)
