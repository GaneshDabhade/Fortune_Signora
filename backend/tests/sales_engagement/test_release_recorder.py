"""Appending a measurement to this module's prompt manifest.

**Written for [B-109](../../../docs/BUGS.md)**, which found `release.py` at 0% —
the file that writes the repository's evaluation history had never been executed
by a test, so **both of its refusals were untested**, and a refusal that has
never fired is indistinguishable from one that cannot.

The module's own docstring names them, and both exist to stop the same thing —
**a number nobody liked quietly ceasing to exist**:

- **A drifted prompt is refused**, so a measurement is never attached to text
  that did not produce it.
- **A duplicate is refused rather than overwritten**, so a re-run on the same
  day cannot replace the result it disagrees with.

Every test writes to a temporary manifest. The shipped one is never touched:
these exercise the recorder, and *"a record of what was true then is not
rewritten"*.
"""

from __future__ import annotations

import json
import shutil
from collections.abc import Iterator
from datetime import date
from pathlib import Path

import pytest

from modules.ai_platform.infrastructure.prompt_loader import load_prompt_registry
from modules.sales_engagement.application.synthesise import PassOutcome
from modules.sales_engagement.evaluation.release import ReleaseError, record
from modules.sales_engagement.evaluation.report import CaseResult, EvaluationReport
from modules.sales_engagement.infrastructure.prompts import MANIFEST

PROMPTS = MANIFEST.parent
NAME = "executive_summary"


@pytest.fixture
def manifest(tmp_path: Path) -> Iterator[Path]:
    """A private copy of the shipped prompt directory.

    The whole directory, not just the manifest: the loader verifies every
    prompt's fingerprint against its text, so a manifest without its prompts
    would fail for a reason these tests are not about.
    """
    for source in PROMPTS.iterdir():
        if source.is_file():
            shutil.copy(source, tmp_path / source.name)
    load_prompt_registry.cache_clear()
    yield tmp_path / "manifest.json"
    load_prompt_registry.cache_clear()


def _fingerprint(manifest: Path, name: str = NAME) -> str:
    document = json.loads(manifest.read_text())
    return str(next(p["fingerprint"] for p in document["prompts"] if p["name"] == name))


def _report(
    manifest: Path,
    *,
    name: str = NAME,
    version: int = 1,
    fingerprint: str | None = None,
    model: str = "claude-sonnet-4-5",
    on: date = date(2026, 8, 4),
    refused: bool = False,
) -> EvaluationReport:
    return EvaluationReport(
        prompt_name=name,
        prompt_version=version,
        prompt_fingerprint=fingerprint or _fingerprint(manifest, name),
        model=model,
        dataset_name="approach",
        dataset_version=1,
        dataset_fingerprint="a" * 64,
        rubric_version=1,
        evaluated_on=on,
        results=(
            CaseResult(
                case="northwind",
                outcome=PassOutcome.REFUSED if refused else PassOutcome.OK,
                coverage=0.0 if refused else 1.0,
            ),
        ),
    )


def _evaluations(manifest: Path, name: str = NAME) -> list[dict[str, object]]:
    document = json.loads(manifest.read_text())
    entry = next(p for p in document["prompts"] if p["name"] == name)
    return list(entry.get("evaluations", []))


class TestRecordingAMeasurement:
    def test_it_appends_rather_than_replacing(self, manifest: Path) -> None:
        before = len(_evaluations(manifest))

        record(_report(manifest), manifest=manifest)

        assert len(_evaluations(manifest)) == before + 1

    def test_the_written_row_carries_what_the_run_measured(self, manifest: Path) -> None:
        record(_report(manifest, model="llama3.1:8b"), manifest=manifest)

        written = _evaluations(manifest)[-1]
        assert written["model"] == "llama3.1:8b"
        assert written["dataset"] == "approach"
        assert written["evaluated_on"] == "2026-08-04"

    def test_it_returns_the_evaluation_so_a_caller_need_not_re_derive_it(
        self, manifest: Path
    ) -> None:
        evaluation = record(_report(manifest), manifest=manifest)

        assert evaluation.model == "claude-sonnet-4-5"

    def test_the_file_stays_loadable_by_the_registry_that_wrote_it(
        self, manifest: Path
    ) -> None:
        """A manifest that saves cleanly and refuses to start is the failure
        `_key` exists to prevent."""
        record(_report(manifest), manifest=manifest)

        load_prompt_registry.cache_clear()
        registry = load_prompt_registry(manifest.parent)

        assert registry.get(NAME, 1) is not None

    def test_a_failing_run_is_written_too(self, manifest: Path) -> None:
        """**Deliberate.** A manifest recording only passes shows a prompt with
        a clean history and no way to see it was measured and found wanting —
        and the second engineer to evaluate it repeats the work.
        """
        record(_report(manifest, refused=True), manifest=manifest)

        assert len(_evaluations(manifest)) >= 1

    def test_nothing_in_it_marks_a_prompt_released(self, manifest: Path) -> None:
        """Release is derived from evaluations, never declared (§2). A key here
        saying so would be a second representation of a rule."""
        record(_report(manifest), manifest=manifest)

        written = _evaluations(manifest)[-1]
        assert not any("release" in key.lower() for key in written)


class TestTheRefusals:
    def test_a_drifted_prompt_is_refused(self, manifest: Path) -> None:
        """Appending to a manifest whose prompt has changed would attach a
        measurement to text that never produced it."""
        with pytest.raises(ReleaseError, match="no longer there"):
            record(_report(manifest, fingerprint="f" * 64), manifest=manifest)

    def test_a_drifted_prompt_leaves_the_file_untouched(self, manifest: Path) -> None:
        """Refused *before* the file is opened, not discovered halfway."""
        before = manifest.read_text()

        with pytest.raises(ReleaseError):
            record(_report(manifest, fingerprint="f" * 64), manifest=manifest)

        assert manifest.read_text() == before

    def test_the_same_measurement_twice_is_refused(self, manifest: Path) -> None:
        """*"Evaluations accumulate; overwriting one is how a result nobody
        liked stops existing."*"""
        record(_report(manifest), manifest=manifest)

        with pytest.raises(ReleaseError, match="already records"):
            record(_report(manifest), manifest=manifest)

    def test_a_duplicate_does_not_grow_the_file(self, manifest: Path) -> None:
        record(_report(manifest), manifest=manifest)
        after_first = len(_evaluations(manifest))

        with pytest.raises(ReleaseError):
            record(_report(manifest), manifest=manifest)

        assert len(_evaluations(manifest)) == after_first

    def test_the_same_model_on_a_later_day_is_a_new_measurement(
        self, manifest: Path
    ) -> None:
        """The date is part of what makes two runs different, so re-measuring
        tomorrow is recording rather than overwriting."""
        record(_report(manifest, on=date(2026, 8, 4)), manifest=manifest)
        record(_report(manifest, on=date(2026, 8, 5)), manifest=manifest)

        dates = [row["evaluated_on"] for row in _evaluations(manifest)]
        assert "2026-08-04" in dates and "2026-08-05" in dates

    def test_a_different_model_is_a_new_measurement(self, manifest: Path) -> None:
        record(_report(manifest, model="a-model"), manifest=manifest)
        record(_report(manifest, model="b-model"), manifest=manifest)

        models = [row["model"] for row in _evaluations(manifest)]
        assert "a-model" in models and "b-model" in models

    def test_a_prompt_the_manifest_does_not_hold_is_refused(
        self, manifest: Path
    ) -> None:
        """The registry loaded one and the manifest has none — which means the
        file changed underneath the run."""
        document = json.loads(manifest.read_text())
        document["prompts"] = [p for p in document["prompts"] if p["name"] != NAME]
        stale = manifest.parent / "stale.json"
        stale.write_text(json.dumps(document))

        with pytest.raises(ReleaseError):
            record(_report(manifest), manifest=stale)
