"""Load and validate the default scoring model artifact.

File I/O is infrastructure; the model is domain language. It is read once
and validated, so a malformed or incomplete model **fails at startup rather
than at the first scoring** — a signal type nobody weighted contributes
nothing, and an account with a strong hypothesis nobody weighted looks
exactly like an account where nothing happened.

The artifact lives in the repository because the *shape* of the model is
Signora's design. A customer's own weights live in the database because the
*values* are their commercial judgement. The deciding criterion is
ownership, not technology (docs/architecture/26-buying-score-engine.md).
"""

from __future__ import annotations

from functools import cache
from pathlib import Path

from pydantic import ValidationError

from modules.buying_score_engine.domain.scoring_model import (
    CURRENT_MODEL_VERSION,
    ScoringModel,
    ScoringModelError,
)

MODEL_DIR = Path(__file__).resolve().parent.parent / "scoring"


@cache
def load_scoring_model(version: int = CURRENT_MODEL_VERSION) -> ScoringModel:
    path = MODEL_DIR / f"scoring_model@{version}.json"
    if not path.exists():
        raise ScoringModelError(
            f"scoring model v{version} not found at {path}. A version recorded on historical "
            "scores must remain loadable, or those scores become unexplainable."
        )

    try:
        model = ScoringModel.model_validate_json(path.read_text())
    except ValidationError as exc:
        raise ScoringModelError(
            f"scoring model v{version} is malformed: {exc}. Failing at startup rather than at "
            "the first scoring — a type that silently weighs nothing is invisible."
        ) from exc

    if model.version != version:
        raise ScoringModelError(
            f"{path.name} declares version {model.version}. The filename and the declared "
            "version must agree, or a score's recorded version names the wrong weights."
        )
    return model
