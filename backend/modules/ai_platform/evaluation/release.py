"""Appending a measurement to the prompt manifest — the release step.

**Release is not declared here; it is recorded.** This writes the facts a run
produced into the manifest and stops. Whether those facts make a prompt
usable is `Evaluation.passed`, read at the point of use by
`PromptVersion.require_model`. Nothing in this file, and nothing anywhere,
sets a prompt to "released".

Which means a *failing* run is written too, and deliberately. A manifest that
recorded only passes would show a prompt with a clean history and no way to
see it had been measured and found wanting — and the second engineer to
evaluate it would repeat the work.

Two refusals, both structural:

**The prompt text must still match its fingerprint.** Appending to a manifest
whose prompt has drifted would attach a measurement to text that never
produced it.

**A duplicate is refused rather than overwritten.** Evaluations accumulate.
Re-running the same `(model, dataset_version)` on the same day and writing
over the previous result is how an inconvenient number disappears.
"""

from __future__ import annotations

import json
from pathlib import Path

from modules.ai_platform.domain.errors import AIPlatformError
from modules.ai_platform.domain.prompt import Evaluation
from modules.ai_platform.evaluation.report import EvaluationReport
from modules.ai_platform.infrastructure.prompt_loader import MANIFEST, load_prompt_registry


class ReleaseError(AIPlatformError):
    """A measurement could not be recorded against its prompt."""


def record(report: EvaluationReport, *, manifest: Path = MANIFEST) -> Evaluation:
    """Append this run's measurement to the manifest, in place.

    Returns the evaluation written, so a caller can report whether it earned
    a release without re-deriving the criteria.
    """
    # **Refused before anything else, including the fingerprint check.**
    #
    # A run served by a fake produces a report that looks exactly like a real
    # one — the schema parses, the citations resolve, the coverage computes —
    # and every one of those figures describes the fixture. **Recording it
    # would put a scripted answer into the artifact that decides whether a
    # prompt is released**, where nothing downstream could tell the difference
    # ([B-324](../../../../docs/BUGS.md)).
    #
    # **The condition names no vendor and no adapter**, which is what lets it
    # exist here at all: `TestTheEvaluationFrameworkNamesNoVendor` states that
    # evaluation code may not, and the first attempt at this fix was
    # `report.provider is AIVendor.MOCK` and was refused within the hour. The
    # capability is declared by whatever served the call and read back through
    # the report.
    if not report.output_is_evidence:
        raise ReleaseError(
            f"{report.prompt_name}@{report.prompt_version} was measured against "
            f"'{report.model}' by a provider whose output is not evidence about a model — "
            "a deterministic fake returns what it was configured to return, so this run "
            "describes the fixture. Nothing about it can be recorded as an evaluation. "
            "Configure a real provider for the model and run it again."
        )

    evaluation = report.as_evaluation()

    # Loading verifies every fingerprint on disk. Doing it first means a
    # drifted prompt is refused *before* the file is touched, rather than
    # discovered by the next process to start.
    registry = load_prompt_registry(manifest.parent)
    prompt = registry.get(report.prompt_name, report.prompt_version)
    if prompt.fingerprint != report.prompt_fingerprint:
        raise ReleaseError(
            f"{prompt.reference} now fingerprints as {prompt.fingerprint[:12]}, but the run "
            f"measured {report.prompt_fingerprint[:12]}. The prompt changed while it was being "
            "evaluated, so this measurement describes text that is no longer there."
        )

    document = json.loads(manifest.read_text())
    for record_ in document["prompts"]:
        if (record_["name"], record_["version"]) == (report.prompt_name, report.prompt_version):
            entries = record_.setdefault("evaluations", [])
            written = _as_json(evaluation)
            if _key(written) in {_key(existing) for existing in entries}:
                raise ReleaseError(
                    f"{prompt.reference} already records an evaluation for "
                    f"{evaluation.model} on {evaluation.dataset}@{evaluation.dataset_version} "
                    f"dated {evaluation.evaluated_on}. Evaluations accumulate; overwriting one "
                    "is how a result nobody liked stops existing."
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

    Mirrors the uniqueness rule `PromptVersion` enforces on load, so a
    manifest this function writes is one the loader will accept — the
    alternative is a file that saves cleanly and refuses to start.
    """
    return (
        entry["model"],
        entry["dataset"],
        entry["dataset_version"],
        entry["rendering_protocol_version"],
        entry["evaluated_on"],
    )
