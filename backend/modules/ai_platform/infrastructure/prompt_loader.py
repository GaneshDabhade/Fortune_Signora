"""Load the prompt registry from the repository.

File I/O is infrastructure; a prompt is domain language. Read once and
validated, so a manifest that disagrees with the files on disk **fails at
startup rather than at the first inference** — a prompt whose text has
drifted from its recorded hash makes every result claiming that version
unreproducible, and there is no way to notice that after the fact.

Prompts live in the repository because they are Signora's language, decided
by the same ownership criterion that placed the business event taxonomy, the
scoring model and the opportunity policy here (26-buying-score-engine.md).
"""

from __future__ import annotations

from datetime import date
from functools import cache
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from modules.ai_platform.domain.prompt import (
    Evaluation,
    PromptError,
    PromptRegistry,
    PromptTamperedError,
    PromptVersion,
)

PROMPT_DIR = Path(__file__).resolve().parent.parent / "prompts"
MANIFEST = PROMPT_DIR / "manifest.json"


class _EvaluationRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    model: str
    dataset: str
    dataset_version: int
    rubric_version: int
    evaluated_on: date
    sample_size: int
    grounding_failures: int
    schema_failures: int
    coverage: float
    retries: int


class _PromptRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    version: int
    owner: str
    #: The SHA-256 the text is expected to hash to. Declared here rather
    #: than computed on load, so an edit to the file is a *mismatch* — the
    #: whole point. A hash computed from whatever happens to be on disk
    #: would agree with every possible edit.
    fingerprint: str
    evaluations: tuple[_EvaluationRecord, ...] = ()


class _Manifest(BaseModel):
    # `populate_by_name` plus the alias below is how every other artifact in
    # this repository carries its explanatory note (scoring_model.py:128) —
    # matched rather than reinvented.
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    prompts: tuple[_PromptRecord, ...]
    note: str = Field(default="", alias="_comment")


@cache
def load_prompt_registry(directory: Path = PROMPT_DIR) -> PromptRegistry:
    manifest_path = directory / "manifest.json"
    if not manifest_path.exists():
        raise PromptError(f"no prompt manifest at {manifest_path}.")

    try:
        manifest = _Manifest.model_validate_json(manifest_path.read_text())
    except ValidationError as exc:
        raise PromptError(f"the prompt manifest is malformed: {exc}") from exc

    return PromptRegistry(versions=tuple(_load(record, directory) for record in manifest.prompts))


def _load(record: _PromptRecord, directory: Path) -> PromptVersion:
    path = directory / f"{record.name}@{record.version}.md"
    if not path.exists():
        raise PromptError(
            f"the manifest declares {record.name}@{record.version} but {path.name} is missing. "
            "A version recorded on historical results must remain loadable, or those results "
            "become unexplainable."
        )

    prompt = PromptVersion(
        name=record.name,
        version=record.version,
        owner=record.owner,
        text=path.read_text(),
        evaluations=tuple(
            Evaluation(
                model=e.model,
                dataset=e.dataset,
                dataset_version=e.dataset_version,
                rubric_version=e.rubric_version,
                evaluated_on=e.evaluated_on,
                sample_size=e.sample_size,
                grounding_failures=e.grounding_failures,
                schema_failures=e.schema_failures,
                coverage=e.coverage,
                retries=e.retries,
            )
            for e in record.evaluations
        ),
    )

    if prompt.fingerprint != record.fingerprint:
        raise PromptTamperedError(
            f"{path.name} does not match the fingerprint recorded for "
            f"{prompt.reference}.\n  declared: {record.fingerprint}\n  actual:   "
            f"{prompt.fingerprint}\nA released prompt is never edited in place — every result "
            "recorded against this version was produced by different text than is now on disk. "
            "If the change is intended, it is a new version."
        )
    return prompt
