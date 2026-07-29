"""The signal profile — a workspace's commercial interpretation.

**The first genuinely customer-authored configuration in the platform.**
Everything else Signora stores is either evidence it received or knowledge
it derived; a profile is a statement a customer makes about their own
business, and it cannot be regenerated from anything.

That has two consequences the design turns on:

**It lives in the database, not in a repository artifact** — unlike the
business event taxonomy and the signal catalog, which are *ours*. A
customer cannot be asked to wait for a Signora release to say that hiring
surges matter to them. The deciding criterion is **ownership, not
technology**.

**It is immutable and versioned**, superseded rather than edited. Every
signal records the profile version that produced it, and if a profile
could be edited in place, every historical signal would become
unexplainable — *"why was I told this?"* would have no answer, because the
reason changed underneath it.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Final
from uuid import UUID

from modules.signal_engine.domain.catalog import Relevance, SignalCatalog, SignalType

DEFAULT_PROFILE_VERSION: Final = 0
"""The version recorded when a workspace has configured nothing.

An absent profile falls back to the catalog's declared defaults rather than
producing nothing, so the out-of-box behaviour is reviewable in the catalog
instead of emerging from an empty table — and no seeding write is needed,
which keeps the Signal Engine free of any dependency on workspace creation.
"""


@dataclass(frozen=True, slots=True)
class ProfileEntry:
    """One workspace's reading of one signal type."""

    signal_type: SignalType
    relevance: Relevance
    #: Tuning within catalog-declared semantics. Absent means "use the
    #: catalog's". A workspace adjusts *how much evidence* and *over what
    #: period* — never what the hypothesis means.
    window_days: int | None = None
    minimum_contributors: int | None = None

    @property
    def is_active(self) -> bool:
        return self.relevance is not Relevance.IGNORED


@dataclass(frozen=True, slots=True)
class SignalProfile:
    id: UUID
    workspace_id: UUID
    version: int
    entries: tuple[ProfileEntry, ...]
    created_at: datetime
    #: Auditability. A profile change is a commercial decision, and a
    #: customer should be able to see who made it and when.
    created_by: UUID
    supersedes: UUID | None = None

    def entry(self, signal_type: SignalType) -> ProfileEntry | None:
        return next((e for e in self.entries if e.signal_type is signal_type), None)


def default_profile(catalog: SignalCatalog) -> tuple[ProfileEntry, ...]:
    """What a workspace gets before it has said anything.

    Read from the catalog rather than hardcoded, so the out-of-box reading
    of every signal type is visible in the same artifact that defines it.
    """
    return tuple(
        ProfileEntry(signal_type=definition.key, relevance=definition.default_relevance)
        for definition in catalog.types
    )


def resolve_entry(
    catalog: SignalCatalog, profile: SignalProfile | None, signal_type: SignalType
) -> ProfileEntry:
    """This workspace's reading of one type, falling back to the catalog.

    Falling back rather than failing: a workspace that has configured some
    types and not others should still receive the rest at their default
    relevance, not silently lose them.
    """
    if profile is not None and (entry := profile.entry(signal_type)) is not None:
        return entry
    return ProfileEntry(
        signal_type=signal_type,
        relevance=catalog.definition(signal_type).default_relevance,
    )
