"""Appending a measurement to this module's prompt manifest — the release step.

**Release is not declared here; it is recorded.** This writes the facts a run
produced into the manifest and stops. Whether those facts make a prompt usable
is `domain/release.earns_release`, read at the point of use. Nothing in this
file, and nothing anywhere, sets a prompt to *released*.

Which means a **failing run is written too**, deliberately. A manifest recording
only passes would show a prompt with a clean history and no way to see it had
been measured and found wanting — and the second engineer to evaluate it would
repeat the work.

Two refusals, both structural:

**The prompt text must still match its fingerprint.** Appending to a manifest
whose prompt has drifted would attach a measurement to text that never produced
it.

**A duplicate is refused rather than overwritten.** Evaluations accumulate.
Re-running the same pairing on the same day and writing over the previous result
is how an inconvenient number disappears.

---

### The duplication here is deliberate, bounded, and has a stated trigger

`ai_platform/evaluation/release.py` does the same JSON append, and three modules
already call it — it is shared infrastructure by the repository's own test.
**This module cannot call it**, because its parameter is the AI Platform's
`EvaluationReport` and this module's report is a different measurement: it counts
refusals rather than grounding failures, carries stability, and renders criteria
whose thresholds differ (`domain/release.MINIMUM_COVERAGE` is 0.50, not 0.66).

Bending this module's report into that type to reuse forty lines would distort
what is measured in order to share how it is written — **the wrong trade, and the
one L-1 warns about when it says reuse must not force a wrong shape.**

> **The trigger for extraction is a manifest recorder with two callers that
> genuinely agree on the record's shape.** Reconciling that is
> [C-214](../../../../docs/LANE_COORDINATION.md), which already proposes
> parameterising the platform's evaluation on its protocol; a shared recorder
> falls out of that change rather than preceding it.
"""

from __future__ import annotations

import json
from pathlib import Path

from modules.ai_platform.infrastructure.prompt_loader import load_prompt_registry
from modules.ai_platform.public import AIPlatformError, Evaluation
from modules.sales_engagement.evaluation.report import EvaluationReport
from modules.sales_engagement.infrastructure.prompts import MANIFEST


class ReleaseError(AIPlatformError):
    """A measurement could not be recorded against its prompt."""


def record(report: EvaluationReport, *, manifest: Path = MANIFEST) -> Evaluation:
    """Append this run's measurement to the manifest, in place.

    Returns the evaluation written, so a caller can report whether it earned a
    release without re-deriving the criteria.
    """
    evaluation = report.as_evaluation()

    # Loading verifies every fingerprint on disk. Doing it first means a drifted
    # prompt is refused *before* the file is touched, rather than discovered by
    # the next process to start.
    registry = load_prompt_registry(manifest.parent)
    prompt = registry.get(report.prompt_name, report.prompt_version)
    if prompt.fingerprint != report.prompt_fingerprint:
        raise ReleaseError(
            f"{prompt.reference} now fingerprints as {prompt.fingerprint[:12]}, but the run "
            f"measured {report.prompt_fingerprint[:12]}. The prompt changed while it was being "
            "evaluated, so this measurement describes text that is no longer there."
        )

    document = json.loads(manifest.read_text())
    for entry in document["prompts"]:
        if (entry["name"], entry["version"]) == (report.prompt_name, report.prompt_version):
            entries = entry.setdefault("evaluations", [])
            written = _as_json(evaluation)
            if _key(written) in {_key(existing) for existing in entries}:
                raise ReleaseError(
                    f"{prompt.reference} already records an evaluation for {evaluation.model} "
                    f"on {evaluation.dataset}@{evaluation.dataset_version} dated "
                    f"{evaluation.evaluated_on}. Evaluations accumulate; overwriting one is "
                    "how a result nobody liked stops existing."
                )
            entries.append(written)
            break
    else:
        raise ReleaseError(
            f"the manifest holds no {report.prompt_name}@{report.prompt_version} to record "
            "against, though the registry loaded one — the manifest changed underneath this run."
        )

    manifest.write_text(json.dumps(document, indent=2, ensure_ascii=False) + "\n")
    # The registry caches, and the file it read is now stale. A later call in
    # this process must not serve a prompt whose evaluations it no longer has.
    load_prompt_registry.cache_clear()
    return evaluation


def _as_json(evaluation: Evaluation) -> dict[str, object]:
    return {
        "model": evaluation.model,
        "dataset": evaluation.dataset,
        "dataset_version": evaluation.dataset_version,
        "rubric_version": evaluation.rubric_version,
        "evaluated_on": evaluation.evaluated_on.isoformat(),
        "sample_size": evaluation.sample_size,
        "grounding_failures": evaluation.grounding_failures,
        "schema_failures": evaluation.schema_failures,
        "coverage": evaluation.coverage,
        "rendering_protocol_version": evaluation.rendering_protocol_version,
        "retries": evaluation.retries,
    }


def _key(entry: dict[str, object]) -> tuple[object, ...]:
    """What makes two evaluations the same measurement rather than two.

    Mirrors the uniqueness rule `PromptVersion` enforces on load, so a manifest
    this function writes is one the loader will accept — the alternative is a
    file that saves cleanly and refuses to start.
    """
    return (
        entry["model"],
        entry["dataset"],
        entry["dataset_version"],
        entry["rendering_protocol_version"],
        entry["evaluated_on"],
    )
