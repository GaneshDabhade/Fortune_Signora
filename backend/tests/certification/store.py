"""Reading and appending the certification manifest.

**Append-only, and failed runs are written too.** `release.py` gives the reason
in its own words: *"a manifest that recorded only passes would show a prompt with
a clean history and no way to see it had been measured and found wanting."* A
certification manifest holding only successes would say a platform had never
failed to certify, which is a different claim from the true one and a more
flattering one.

**Not a second persistence mechanism.** This is the prompt manifest's shape —
a JSON document, a Pydantic record model with `extra="forbid"`, validated on
load, refusing rather than defaulting. The evidence lives in the repository for
the same reason prompts do: *the repository should always tell the truth*, and a
record only a terminal ever saw is one a reader cannot check.

The manifest sits at the **repository root**, not under `backend/`, because a
certification describes the whole repository — `make smoke` builds the frontend
and the infrastructure too, and evidence filed under one tier would understate
what it covers.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from tests.certification.record import (
    CertificationError,
    CertificationRun,
    Conditions,
    GateResult,
    PromptRelease,
    ScenarioResult,
    canonical_json,
)

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
MANIFEST = REPOSITORY_ROOT / "certification" / "manifest.json"

NOTE = (
    "Durable evidence that a specific commit satisfied the repository's guarantees under "
    "stated conditions (ADR-0032). Append-only: failed runs are recorded too, because a "
    "manifest holding only successes claims a platform that never failed to certify. "
    "Nothing here declares a verdict — `satisfied` is derived from the gates and scenarios "
    "below, and `is_certified` additionally requires that the recorded conditions still "
    "match the repository, so a rendering-protocol bump or a prompt re-release expires a "
    "certification without anyone editing this file. Written only by `make certify`."
)


class _GateRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    passed: bool
    detail: str


class _ScenarioRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    passed: bool
    detail: str


class _PromptReleaseRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    reference: str
    fingerprint: str
    model: str


class _ConditionsRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    rendering_protocol_version: int
    migration_head: str
    scenario_fingerprint: str
    prompt_releases: tuple[_PromptReleaseRecord, ...]


class _RunRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    commit: str
    tree_clean: bool
    certified_at: datetime
    record_version: int
    coverage: float
    conditions: _ConditionsRecord
    gates: tuple[_GateRecord, ...]
    scenarios: tuple[_ScenarioRecord, ...]
    tools: tuple[tuple[str, str], ...]


class _Manifest(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    runs: tuple[_RunRecord, ...] = ()
    note: str = Field(default="", alias="_comment")


def load(manifest: Path = MANIFEST) -> tuple[CertificationRun, ...]:
    """Every recorded run, oldest first. A missing manifest is **no runs**, not
    an error: a repository that has never certified is a legitimate state, and
    one that could not be read would be a different problem wearing the same
    message."""
    if not manifest.exists():
        return ()
    try:
        document = _Manifest.model_validate_json(manifest.read_text())
    except ValidationError as exc:
        raise CertificationError(f"the certification manifest is malformed: {exc}") from exc
    return tuple(sorted((_run(record) for record in document.runs), key=lambda r: r.certified_at))


def append(run: CertificationRun, *, manifest: Path = MANIFEST) -> None:
    """Add one run. **Never overwrites, never edits.**

    A repeated `(commit, certified_at)` is refused rather than replaced — two
    runs of the same tree at the same instant is one run written twice, and
    quietly replacing the earlier one is how a result nobody liked disappears.
    """
    existing = load(manifest)
    if any((r.commit, r.certified_at) == (run.commit, run.certified_at) for r in existing):
        raise CertificationError(
            f"a run for {run.commit[:12]} at {run.certified_at.isoformat()} is already "
            "recorded. Certification runs accumulate; overwriting one would remove the only "
            "evidence that it happened."
        )

    document: dict[str, Any] = {
        "_comment": NOTE,
        "runs": [_as_json(r) for r in (*existing, run)],
    }
    manifest.parent.mkdir(parents=True, exist_ok=True)
    manifest.write_text(canonical_json(document))


def _as_json(run: CertificationRun) -> dict[str, Any]:
    return {
        "commit": run.commit,
        "tree_clean": run.tree_clean,
        "certified_at": run.certified_at.isoformat(),
        "record_version": run.record_version,
        "coverage": run.coverage,
        "conditions": {
            "rendering_protocol_version": run.conditions.rendering_protocol_version,
            "migration_head": run.conditions.migration_head,
            "scenario_fingerprint": run.conditions.scenario_fingerprint,
            "prompt_releases": [
                {"reference": p.reference, "fingerprint": p.fingerprint, "model": p.model}
                for p in run.conditions.prompt_releases
            ],
        },
        "gates": [{"name": g.name, "passed": g.passed, "detail": g.detail} for g in run.gates],
        "scenarios": [
            {"name": s.name, "passed": s.passed, "detail": s.detail} for s in run.scenarios
        ],
        "tools": [list(pair) for pair in run.tools],
    }


def _run(record: _RunRecord) -> CertificationRun:
    return CertificationRun(
        commit=record.commit,
        tree_clean=record.tree_clean,
        certified_at=record.certified_at,
        record_version=record.record_version,
        coverage=record.coverage,
        conditions=Conditions(
            rendering_protocol_version=record.conditions.rendering_protocol_version,
            migration_head=record.conditions.migration_head,
            scenario_fingerprint=record.conditions.scenario_fingerprint,
            prompt_releases=tuple(
                PromptRelease(reference=p.reference, fingerprint=p.fingerprint, model=p.model)
                for p in record.conditions.prompt_releases
            ),
        ),
        gates=tuple(
            GateResult(name=g.name, passed=g.passed, detail=g.detail) for g in record.gates
        ),
        scenarios=tuple(
            ScenarioResult(name=s.name, passed=s.passed, detail=s.detail)
            for s in record.scenarios
        ),
        tools=tuple((name, version) for name, version in record.tools),
    )


def render(run: CertificationRun, conditions: Conditions) -> str:
    """The human-readable report, **rendered from the record rather than
    written beside it** — so the report cannot claim something the evidence
    does not."""
    verdict = (
        "CERTIFIED"
        if run.certifies(conditions)
        else ("AWAITING RE-CERTIFICATION" if run.satisfied else "NOT CERTIFIED")
    )
    lines = [
        f"# Certification — {run.commit[:12]}",
        "",
        f"**{verdict}**  ·  {run.certified_at.isoformat()}",
        "",
        "## Conditions",
        "",
        f"- rendering protocol v{run.conditions.rendering_protocol_version}",
        f"- migration head `{run.conditions.migration_head}`",
        f"- scenario set `{run.conditions.scenario_fingerprint[:12]}`",
        f"- working tree {'clean' if run.tree_clean else '**dirty**'}",
        "",
        "### Prompt releases in force",
        "",
    ]
    lines.extend(
        f"- `{p.reference}` on `{p.model}` — `{p.fingerprint[:12]}`"
        for p in run.conditions.prompt_releases
    )
    lines.extend(["", "## Gates", ""])
    lines.extend(
        f"- {'✅' if g.passed else '❌'} **{g.name}** — {g.detail}" for g in run.gates
    )
    lines.extend(["", "## Scenarios", ""])
    lines.extend(
        f"- {'✅' if s.passed else '❌'} **{s.name}** — {s.detail}" for s in run.scenarios
    )
    lines.extend(["", f"Coverage **{run.coverage:.2f}%**", ""])

    if not run.satisfied:
        lines.extend(["## Why this run does not certify", ""])
        lines.extend(f"- {reason}" for reason in run.failures)
        lines.append("")
    elif not run.is_current(conditions):
        lines.extend(
            [
                "## Why this run no longer applies",
                "",
                "The run satisfied every gate and every scenario. The repository has since "
                "changed one of the conditions above, so the measurement remains true and "
                "stops describing the system. Re-certify; do not edit this record.",
                "",
            ]
        )
    lines.append(
        "*Certification measures a system with zero production traffic. It is evidence of "
        "discipline, not of field reliability.*"
    )
    return "\n".join(lines)


def report_path(run: CertificationRun) -> Path:
    return MANIFEST.parent / "reports" / f"{run.commit[:12]}.md"
