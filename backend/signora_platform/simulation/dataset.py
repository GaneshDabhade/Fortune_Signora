"""The Dataset Store — versioned, immutable, content-hashed fixture data.

A dataset is the *cast*; a scenario is the *narrative*. Separating them
means the same companies can play different stories, and a story can be
re-run against corrected data without rewriting the story.

**A published version is immutable.** A correction ships as a new version.
Regenerating a dataset in place invalidates every historical AI comparison
built on it, which is the entire reason regression datasets exist — the
comparison is the product, and it is only as good as the fixity of what it
compares against.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Any, Final

DATASET_ROOT: Final = Path(__file__).parent / "datasets"


class DatasetError(RuntimeError):
    """A dataset could not be loaded, or is not what it claims to be."""


@dataclass(frozen=True, slots=True)
class Dataset:
    """Immutable fixture data, addressed by name and version.

    `entities` is a read-only mapping rather than a dict: a scenario that
    mutated the dataset would silently change what every subsequent run
    compares against, and the corruption would be invisible in a diff.
    """

    name: str
    version: int
    content_hash: str
    entities: Mapping[str, Mapping[str, Any]]

    @property
    def reference(self) -> str:
        """The form recorded in every replay context: `saas-growth@3`."""
        return f"{self.name}@{self.version}"

    def entity(self, key: str) -> Mapping[str, Any]:
        entity = self.entities.get(key)
        if entity is None:
            raise DatasetError(
                f"dataset {self.reference} has no entity '{key}'. A scenario referencing a "
                "missing entity fails here rather than emitting an empty timeline that looks "
                "like a working pipeline producing nothing."
            )
        return entity


def content_hash(payload: Mapping[str, Any]) -> str:
    """Stable hash of dataset content.

    `sort_keys` so the hash depends on content rather than on key ordering
    — otherwise a reformatting pass would invalidate every recorded run.
    """
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode()).hexdigest()[:16]


def load(name: str, version: int, *, root: Path | None = None) -> Dataset:
    """Load a published dataset version.

    A missing version is a **startup failure**, not a runtime one: the
    simulator refuses to start rather than emitting an empty scenario,
    which is indistinguishable from a pipeline that consumed everything and
    produced nothing.
    """
    directory = root if root is not None else DATASET_ROOT
    path = directory / f"{name}@{version}.json"

    if not path.exists():
        available = sorted(p.stem for p in directory.glob(f"{name}@*.json"))
        raise DatasetError(
            f"dataset '{name}@{version}' not found at {path}. "
            f"Available versions: {available or 'none'}."
        )

    try:
        raw: Any = json.loads(path.read_text())
    except json.JSONDecodeError as exc:
        raise DatasetError(f"dataset '{name}@{version}' is not valid JSON: {exc}") from exc

    if not isinstance(raw, dict):
        raise DatasetError(f"dataset '{name}@{version}' must be a JSON object")

    declared = raw.get("content_hash")
    entities = raw.get("entities")

    if not isinstance(entities, dict):
        raise DatasetError(f"dataset '{name}@{version}' has no 'entities' object")

    actual = content_hash(entities)
    if declared is not None and declared != actual:
        # A mutated dataset is a corrupted one. Failing here is what makes
        # "immutable once published" enforceable rather than aspirational.
        raise DatasetError(
            f"dataset '{name}@{version}' content hash mismatch: declared {declared}, "
            f"computed {actual}. A published dataset is immutable — ship a correction as "
            f"'{name}@{version + 1}' rather than editing this one, or every historical "
            "comparison built on it becomes meaningless."
        )

    return Dataset(
        name=name,
        version=version,
        content_hash=actual,
        entities=MappingProxyType(
            {key: MappingProxyType(dict(value)) for key, value in entities.items()}
        ),
    )
