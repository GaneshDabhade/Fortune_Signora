"""Load and validate the taxonomy artifact.

File I/O is infrastructure; the taxonomy itself is domain language. The
artifact is read once and validated against the Pydantic model, so a
malformed taxonomy **fails at startup rather than at the first detection**
— a type that silently stops being detected is the failure mode nobody
notices, because "no events" looks exactly like "nothing happened".

The artifact lives in the repository rather than the database
deliberately: it is reviewed in a pull request, diffable, and the version
in force is a repository state, which is what makes a replay exact. The
cost — tuning a threshold requires a release — is accepted, with the
trigger for revisiting recorded in
docs/architecture/24-business-event-engine.md.
"""

from __future__ import annotations

from functools import cache
from pathlib import Path

from pydantic import ValidationError

from modules.business_event_engine.domain.taxonomy import (
    CURRENT_TAXONOMY_VERSION,
    Taxonomy,
    TaxonomyError,
)

TAXONOMY_DIR = Path(__file__).resolve().parent.parent / "taxonomy"


@cache
def load_taxonomy(version: int = CURRENT_TAXONOMY_VERSION) -> Taxonomy:
    path = TAXONOMY_DIR / f"business_events@{version}.json"
    if not path.exists():
        raise TaxonomyError(
            f"taxonomy v{version} not found at {path}. A version recorded on historical events "
            "must remain loadable, or those events become unexplainable."
        )

    try:
        taxonomy = Taxonomy.model_validate_json(path.read_text())
    except ValidationError as exc:
        raise TaxonomyError(
            f"taxonomy v{version} is malformed: {exc}. Failing at startup rather than at the "
            "first detection — a type that silently stops firing is invisible."
        ) from exc

    if taxonomy.version != version:
        raise TaxonomyError(
            f"{path.name} declares version {taxonomy.version}. The filename and the declared "
            "version must agree, or an event's recorded version names the wrong definitions."
        )
    return taxonomy
