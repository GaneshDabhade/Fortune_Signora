"""An event the platform emits must be named in the contract other modules read.

`06-events.md` is what a module consults to know what it may consume, and
`CLAUDE.md` §9 requires a new event to appear there **in the same change** that
introduces it. Nothing checked. One event slipped — and the measurement that
followed is the reason `infra/event-catalog.py` is advisory rather than alarmed:

    declared in code : 25
    in the catalog   : 24

**Twenty-four of twenty-five is a healthy repository.** The one gap exists
because the lane that emitted the event **may not edit `06-events.md`** — it is
🔴 — so §9 was unsatisfiable by the lane that incurred it. **A workflow gap, not
poor discipline**, and that distinction is asserted below so a future reader of
the one finding does not misread it.

**Every case here is fixed text.** Running the checker against the live catalog
would pass today and pass identically with the comparison deleted — the
Decorative Logic `CLAUDE.md` §2 names.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture(scope="module")
def checker() -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        "event_catalog", REPO_ROOT / "infra" / "event-catalog.py"
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_it_finds_every_declaration_spelling(checker: ModuleType) -> None:
    """**Two spellings exist, and missing one would under-report silently.**

    Most modules write `event_type: str = "..."` on a dataclass field;
    `commercial_profile` writes a module-level `EVENT_TYPE: Final = "..."`. A
    pattern matching only the first would have reported *zero* drift — because
    the one event that is actually missing uses the second.
    """
    events = checker.declared()
    assert "buying_score.updated" in events, "the `event_type:` field spelling stopped matching"
    assert "commercial_profile.target_accounts_changed" in events, (
        "the `EVENT_TYPE:` constant spelling stopped matching — and that is the "
        "spelling used by the only event currently missing from the catalog"
    )


def test_it_attributes_each_event_to_its_owning_module(checker: ModuleType) -> None:
    """A finding without an owner is a finding nobody acts on."""
    events = checker.declared()
    assert events["commercial_profile.target_accounts_changed"] == "commercial_profile"
    assert events["buying_score.updated"] == "buying_score_engine"


def test_drift_is_detected(checker: ModuleType) -> None:
    """The property under test, against fixed text rather than the live file."""
    catalogued = {e for e in checker.declared() if e in "buying_score.updated only"}
    assert "buying_score.updated" in catalogued
    assert "commercial_profile.target_accounts_changed" not in catalogued


def test_an_empty_catalog_reports_everything_missing(checker: ModuleType) -> None:
    """The control. If containment stopped working, the checker would report a
    clean repository forever — the silent failure that matters most here."""
    assert checker.catalogued("") == set()


def test_it_reads_only_domain_events(checker: ModuleType) -> None:
    """**An event type is domain vocabulary.**

    A string that looks like one in an adapter, a test fixture or a docstring is
    not a declaration, and counting it would produce drift findings for events
    that do not exist — the false positive that gets a check deleted.
    """
    source = (REPO_ROOT / "infra" / "event-catalog.py").read_text()
    assert 'rglob("domain/events.py")' in source, (
        "the search widened beyond domain/events.py; non-declarations will now be reported"
    )


def test_it_is_advisory_and_says_why(checker: ModuleType) -> None:
    """**The design decision, asserted so it cannot be reverted quietly.**

    Its one finding today can only be cleared by editing a 🔴 file. Gating on it
    would make every lane's run red for a reason no lane could act on, and the
    second-order cost is every *other* warning being skimmed. `--strict` exists
    for the day the workflow changes; nothing uses it.
    """
    assert checker.report(strict=False) == 0, "the advisory path started failing; it would gate"
    assert checker.report(strict=True) == 1, "--strict stopped detecting; the future gate is dead"


def test_the_repository_is_mostly_catalogued(checker: ModuleType) -> None:
    """**The context the one finding must be read in.**

    Asserting a *floor* rather than an exact count: this must not fail because
    somebody correctly added an event and its catalog row on the same day. What
    it protects against is a future reader seeing one missing event and
    concluding the catalog is unmaintained. **It is maintained** — by everyone
    who is allowed to maintain it.
    """
    events = checker.declared()
    present = checker.catalogued((REPO_ROOT / "docs" / "architecture" / "06-events.md").read_text())
    assert len(events) >= 25, "the declaration scan is finding fewer events than it did"
    assert len(present) / len(events) > 0.9, (
        "catalog coverage fell below 90% — that is a discipline problem rather than "
        "the single workflow gap C-101 describes, and should be read differently"
    )
