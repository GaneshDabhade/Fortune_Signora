"""Golden datasets — engineering assets, treated as source code.

A golden dataset is a **recorded** set of evidence, not a generated one. It
is produced once from the M2.0 simulation scenarios by running the real
pipeline (``tests/ai_platform/seed_golden_dataset.py``), then checked in,
reviewed, versioned, and thereafter changed only deliberately.

That separation is the point. **Seeding needs the pipeline; evaluating does
not.** The harness reads JSON and nothing else, so a quality measurement can
never be affected by a change to the pipeline that produced its inputs — and
a movement in the numbers is therefore always attributable to the prompt or
the model, which is the only reason to run it.

**Historical expectations are never modified silently.** The dataset carries
a `version` and a `fingerprint` over its own content: an edit that leaves the
version alone fails to load, so revising a case is a version bump and a
review rather than an edit nobody sees. Every result records the version it
was measured against (``Evaluation.dataset_version``), so a score can always
name the expectations behind it.
"""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from modules.ai_platform.domain.errors import AIPlatformError
from modules.ai_platform.domain.evidence import EvidenceSet, EvidenceSetBuilder

DATASET_DIR = Path(__file__).resolve().parent / "datasets"


class DatasetError(AIPlatformError):
    """A golden dataset could not be loaded, or does not describe itself."""


class _FactRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    kind: str
    id: UUID
    summary: str
    #: Quantities are written as strings by the seeder and read back exactly
    #: as written. Evidence canonicalises by type, and a number arriving as a
    #: JSON float would digest differently from the same fact assembled in
    #: Python — so the transcript keeps the text rather than a parsed value.
    attributes: dict[str, str] = Field(default_factory=dict)


class _CaseRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    workspace_id: UUID
    facts: tuple[_FactRecord, ...]
    #: The refs a narrative must actually mention to be useful. Declared per
    #: case rather than inferred, because *which* facts carry the argument is
    #: a judgement about that scenario — and one an engineer should have to
    #: write down.
    load_bearing: tuple[str, ...]
    note: str = Field(default="", alias="_comment")


class _DatasetRecord(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    name: str
    version: int
    #: SHA-256 over the cases. Declared rather than computed, for the same
    #: reason the prompt manifest declares one: a hash taken from whatever is
    #: on disk agrees with every possible edit.
    fingerprint: str
    seeded_from: str
    cases: tuple[_CaseRecord, ...]
    note: str = Field(default="", alias="_comment")


class GoldenCase:
    """One scenario: a closed evidence set, and what a narrative must cover."""

    def __init__(self, *, name: str, evidence: EvidenceSet, load_bearing: tuple[str, ...]) -> None:
        resolvable = {fact.ref.token for fact in evidence}
        unknown = sorted(set(load_bearing) - resolvable)
        if unknown:
            raise DatasetError(
                f"case '{name}' requires coverage of {unknown}, which its own evidence does "
                "not contain. A case demanding a fact the model is never shown cannot be "
                "passed by any output, so it would measure nothing but itself."
            )
        if not load_bearing:
            raise DatasetError(
                f"case '{name}' declares no load-bearing facts, so coverage over it is "
                "vacuously perfect and the case can only ever confirm what it assumes."
            )
        self.name = name
        self.evidence = evidence
        self.load_bearing = load_bearing


class GoldenDataset:
    """A named, versioned set of cases."""

    def __init__(
        self,
        *,
        name: str,
        version: int,
        fingerprint: str,
        seeded_from: str,
        cases: list[GoldenCase],
    ) -> None:
        if not cases:
            raise DatasetError(f"dataset '{name}@{version}' holds no cases.")
        self.name = name
        self.version = version
        self.fingerprint = fingerprint
        self.seeded_from = seeded_from
        self.cases = cases

    @property
    def reference(self) -> str:
        return f"{self.name}@{self.version}"

    def __len__(self) -> int:
        return len(self.cases)


def fingerprint_of(cases: object) -> str:
    """SHA-256 over the cases, canonically serialised.

    Keys sorted and separators pinned, so a reformatting of the file — which
    changes nothing about the expectations — does not read as a change to
    them. Everything *outside* `cases` is excluded: the note, the name and
    the version itself are how the dataset describes itself, not what it
    asserts.
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
            "code change.\n"
            f"  recorded: {record.fingerprint}\n  on disk:  {actual}"
        )

    return GoldenDataset(
        name=record.name,
        version=record.version,
        fingerprint=record.fingerprint,
        seeded_from=record.seeded_from,
        cases=[_case(c) for c in record.cases],
    )


def _case(record: _CaseRecord) -> GoldenCase:
    builder = EvidenceSetBuilder(record.workspace_id)
    for fact in record.facts:
        builder.add(
            kind=fact.kind, id=fact.id, summary=fact.summary, attributes=dict(fact.attributes)
        )
    return GoldenCase(
        name=record.name,
        # A recorded dataset has no assembly moment of its own — it is a
        # transcript. The epoch is used rather than "now" so that loading the
        # same file twice produces the same set; `assembled_at` is excluded
        # from the digest for exactly this reason, and relying on that here
        # would be relying on it silently.
        evidence=builder.build(assembled_at=datetime.fromtimestamp(0, tz=UTC)),
        load_bearing=record.load_bearing,
    )
