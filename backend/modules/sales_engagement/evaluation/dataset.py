"""Golden reasoning graphs — engineering assets, treated as source code.

**A case here is a *conclusion*, not evidence.** The AI Platform's golden set is
a transcript of what providers reported; this one is a transcript of what the
deterministic layer *decided* from such reports. That difference is the whole
architecture: layer 2 is never shown raw evidence, so a dataset that held raw
evidence would be measuring a system Signora does not run.

**Recorded, never generated.** A case is written down and reviewed, so the
expectations cannot drift with the reasoning code. That separation is what makes
a movement in the numbers attributable to the prompt or the model — the only
reason to run the harness at all. A case that was computed by `reason()` at load
time would silently re-score every historical result the next time `reason()`
changed.

**Historical expectations are never modified silently.** The dataset carries a
`version` and a `fingerprint` over its own cases: an edit that leaves the version
alone fails to load, so revising a case is a version bump and a review rather
than an edit nobody sees.

### What the scenarios are for

The set is deliberately weighted toward the cases where a model is most tempted
to help. **A rich graph is the easy half.** The valuable cases are the ones
where the honest answer is small — a `wait` with one thin observation, a
contradiction with no resolution, a tie the platform refuses to break — because
those are exactly where a fluent model supplies the confidence the evidence did
not.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Final
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from modules.sales_engagement.domain.fit import FitDimension, FitReason, ProductFit, ProductRef
from modules.sales_engagement.domain.reasoning import (
    ApproachReasoning,
    CommitteeRoleRef,
    Evidence,
    NextAction,
    RankedRole,
    ReasoningError,
    Recommendation,
    Risk,
    RiskKind,
    Strength,
    Unknown,
)
from modules.sales_engagement.domain.synthesis import SynthesisSource

DATASET_DIR: Final = Path(__file__).resolve().parent / "datasets"


class DatasetError(ReasoningError):
    """A golden dataset could not be loaded, or does not describe itself."""


class _RoleRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str
    part: str


class _EvidenceRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    event_id: UUID
    type_key: str
    summary: str
    occurred_at: datetime
    corroborating_providers: int
    names_title: str | None = None


class _RankedRoleRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    role: _RoleRecord
    strength: Strength | None = None
    support: tuple[_EvidenceRecord, ...] = ()
    why_not: str | None = None


class _RecommendationRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    action: NextAction
    reason: str
    role: _RoleRecord | None = None


class _UnknownRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    subject: str
    question: str


class _RiskRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    kind: RiskKind
    detail: str


class _FitReasonRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    dimension: FitDimension
    detail: str


class _ProductRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID
    name: str


class _FitRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    product: _ProductRecord
    strength: Strength
    reasons: tuple[_FitReasonRecord, ...]


class _CaseRecord(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    name: str
    account_id: UUID
    recommendation: _RecommendationRecord
    roles: tuple[_RankedRoleRecord, ...] = ()
    unknowns: tuple[_UnknownRecord, ...] = ()
    risks: tuple[_RiskRecord, ...] = ()
    fits: tuple[_FitRecord, ...] = ()
    product: _ProductRecord | None = None
    #: The citable tokens a synthesis must actually speak to before it counts as
    #: useful. **Declared per case rather than inferred**, because *which*
    #: conclusions carry the argument for that scenario is a judgement — and one
    #: an engineer should have to write down.
    load_bearing: tuple[str, ...]
    note: str = Field(default="", alias="_comment")


class _DatasetRecord(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    name: str
    version: int
    #: SHA-256 over the cases. Declared rather than computed, for the same
    #: reason the prompt manifest declares one: a hash taken from whatever is on
    #: disk agrees with every possible edit.
    fingerprint: str
    cases: tuple[_CaseRecord, ...]
    note: str = Field(default="", alias="_comment")


class GoldenCase:
    """One recorded reasoning graph, and what a synthesis must speak to."""

    def __init__(
        self, *, name: str, source: SynthesisSource, load_bearing: tuple[str, ...]
    ) -> None:
        citable = source.citable()
        unknown = sorted({one.casefold() for one in load_bearing} - citable)
        if unknown:
            raise DatasetError(
                f"case '{name}' requires coverage of {unknown}, which its own reasoning does "
                "not produce. A case demanding a conclusion the model is never shown cannot "
                "be passed by any output, so it would measure nothing but itself."
            )
        if not load_bearing:
            raise DatasetError(
                f"case '{name}' declares no load-bearing conclusions, so coverage over it is "
                "vacuously perfect and the case can only ever confirm what it assumes."
            )
        self.name = name
        self.source = source
        self.load_bearing = load_bearing


class GoldenDataset:
    """A named, versioned set of cases."""

    def __init__(
        self, *, name: str, version: int, fingerprint: str, cases: list[GoldenCase]
    ) -> None:
        if not cases:
            raise DatasetError(f"dataset '{name}@{version}' holds no cases.")
        self.name = name
        self.version = version
        self.fingerprint = fingerprint
        self.cases = cases

    @property
    def reference(self) -> str:
        return f"{self.name}@{self.version}"

    def __len__(self) -> int:
        return len(self.cases)


def fingerprint_of(cases: object) -> str:
    """SHA-256 over the cases, canonically serialised.

    Keys sorted and separators pinned, so reformatting the file — which changes
    nothing about the expectations — does not read as a change to them.
    Everything *outside* `cases` is excluded: the note, the name and the version
    are how the dataset describes itself, not what it asserts.
    """
    canonical = json.dumps(cases, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(canonical.encode()).hexdigest()


def load_dataset(name: str, version: int, *, directory: Path = DATASET_DIR) -> GoldenDataset:
    path = directory / f"{name}@{version}.json"
    if not path.exists():
        raise DatasetError(
            f"no golden dataset at {path}. A result recording dataset '{name}@{version}' must "
            "remain re-measurable, or the release it supports becomes unexplainable."
        )

    raw = path.read_text()
    try:
        record = _DatasetRecord.model_validate_json(raw)
    except ValidationError as exc:
        raise DatasetError(f"golden dataset {path.name} is malformed: {exc}") from exc

    if (record.name, record.version) != (name, version):
        raise DatasetError(
            f"{path.name} declares itself {record.name}@{record.version}. A dataset whose "
            "filename and contents disagree cannot be cited by a result."
        )

    actual = fingerprint_of(json.loads(raw)["cases"])
    if actual != record.fingerprint:
        raise DatasetError(
            f"{path.name} does not match its recorded fingerprint. Its expectations were "
            "edited without a version bump, which silently re-scores every historical result "
            f"claiming {name}@{version}. Revising a case is a new version, reviewed like a "
            f"code change.\n  recorded: {record.fingerprint}\n  on disk:  {actual}"
        )

    return GoldenDataset(
        name=record.name,
        version=record.version,
        fingerprint=record.fingerprint,
        cases=[_case(one) for one in record.cases],
    )


def _case(record: _CaseRecord) -> GoldenCase:
    reasoning = ApproachReasoning(
        account_id=record.account_id,
        recommendation=Recommendation(
            action=record.recommendation.action,
            reason=record.recommendation.reason,
            role=_role(record.recommendation.role),
        ),
        roles=tuple(
            RankedRole(
                role=CommitteeRoleRef(title=one.role.title, part=one.role.part),
                strength=one.strength,
                support=tuple(
                    Evidence(
                        event_id=e.event_id,
                        type_key=e.type_key,
                        summary=e.summary,
                        occurred_at=e.occurred_at,
                        corroborating_providers=e.corroborating_providers,
                        names_title=e.names_title,
                    )
                    for e in one.support
                ),
                why_not=one.why_not,
            )
            for one in record.roles
        ),
        unknowns=tuple(
            Unknown(subject=one.subject, question=one.question) for one in record.unknowns
        ),
        risks=tuple(Risk(kind=one.kind, detail=one.detail) for one in record.risks),
    )
    return GoldenCase(
        name=record.name,
        source=SynthesisSource(
            reasoning=reasoning,
            fits=tuple(
                ProductFit(
                    product=ProductRef(id=one.product.id, name=one.product.name),
                    strength=one.strength,
                    reasons=tuple(
                        FitReason(dimension=r.dimension, detail=r.detail) for r in one.reasons
                    ),
                )
                for one in record.fits
            ),
            product=(
                ProductRef(id=record.product.id, name=record.product.name)
                if record.product
                else None
            ),
        ),
        load_bearing=record.load_bearing,
    )


def _role(record: _RoleRecord | None) -> CommitteeRoleRef | None:
    return CommitteeRoleRef(title=record.title, part=record.part) if record else None
