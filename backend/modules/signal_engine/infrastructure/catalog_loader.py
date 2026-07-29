"""Load and validate the signal catalog artifact.

File I/O is infrastructure; the catalog is domain language. It is read once
and validated against the Pydantic model, so a malformed catalog **fails at
startup rather than at the first generation** — a type that silently stops
being produced is invisible, because "no signals" looks exactly like
"nothing happened".

The catalog lives in the repository because it belongs to **Signora**. The
signal *profile* lives in the database because it belongs to the
**customer**. The deciding criterion is ownership, not technology
(docs/architecture/25-signal-engine.md).
"""

from __future__ import annotations

from functools import cache
from pathlib import Path

from pydantic import ValidationError

from modules.signal_engine.domain.catalog import (
    CURRENT_CATALOG_VERSION,
    CatalogError,
    SignalCatalog,
)

CATALOG_DIR = Path(__file__).resolve().parent.parent / "catalog"


@cache
def load_catalog(version: int = CURRENT_CATALOG_VERSION) -> SignalCatalog:
    path = CATALOG_DIR / f"signals@{version}.json"
    if not path.exists():
        raise CatalogError(
            f"signal catalog v{version} not found at {path}. A version recorded on historical "
            "signals must remain loadable, or those signals become unexplainable."
        )

    try:
        catalog = SignalCatalog.model_validate_json(path.read_text())
    except ValidationError as exc:
        raise CatalogError(
            f"signal catalog v{version} is malformed: {exc}. Failing at startup rather than at "
            "the first generation — a type that silently stops firing is invisible."
        ) from exc

    if catalog.version != version:
        raise CatalogError(
            f"{path.name} declares version {catalog.version}. The filename and the declared "
            "version must agree, or a signal's recorded version names the wrong definitions."
        )
    return catalog
