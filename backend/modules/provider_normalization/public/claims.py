"""The claim read contract — how the rest of Signora sees evidence.

Downstream modules reason over claims constantly, and none of them may
reach into the `claim` table to do it. This port is the whole of the
permitted surface: frozen views, the canonical vocabulary, and two queries.

**Claims are returned, never a resolved value.** There is deliberately no
`current_value(subject, attribute)` method here. Offering one would put
truth resolution behind an innocuous-looking call, and every consumer would
use it instead of looking at the evidence — which is precisely the collapse
the architecture rejects (docs/architecture/22-knowledge-graph.md, Option A).
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date, datetime
from typing import Any, Protocol
from uuid import UUID

from modules.provider_normalization.domain.vocabulary import ClaimAttribute


def _as_date(raw: object) -> date | None:
    """Dates are stored as ISO strings so a claim stays readable in psql
    during an incident. A malformed one yields None rather than raising:
    the claim itself is still evidence, and losing all of it because one
    optional field is unparseable would be a worse failure."""
    if not isinstance(raw, str):
        return None
    try:
        return date.fromisoformat(raw)
    except ValueError:
        return None


@dataclass(frozen=True, slots=True)
class SubjectRef:
    """A provider identity, as the provider stated it. Never a resolved
    one — resolving these is the Knowledge Graph's job, not this module's."""

    provider: str
    provider_external_id: str


@dataclass(frozen=True, slots=True)
class TechnologyRef:
    """The part of a technographic claim a consumer can act on.

    The detection window travels with it. A vendor reporting a technology
    as *removed* usually reports when it was last seen too, and that
    interval is the whole of what makes a displacement observable —
    discarding it would leave a consumer knowing something ended without
    knowing when it ran.
    """

    name: str
    category: str
    first_seen: date | None = None
    last_seen: date | None = None


@dataclass(frozen=True, slots=True)
class ClaimView:
    """One piece of evidence, with its provenance intact.

    `value` is the stored JSON form. The typed accessors below exist so a
    consumer never has to know that encoding — reaching into the raw shape
    would couple every downstream module to this module's storage.
    """

    id: UUID
    provider: str
    attribute: ClaimAttribute
    value: Any
    observed_at: datetime
    subject_external_id: str
    subject_domain: str | None
    subject_legal_name: str | None
    payload_provenance: str

    @property
    def subject(self) -> SubjectRef:
        return SubjectRef(provider=self.provider, provider_external_id=self.subject_external_id)

    def as_text(self) -> str | None:
        """The value of a string-valued attribute (`COUNTRY`, `INDUSTRY`,
        `LEGAL_NAME`), or None when this claim is not one."""
        return self.value if isinstance(self.value, str) else None

    def as_technology(self) -> TechnologyRef | None:
        """The technology a technographic claim is about, or None."""
        if self.attribute not in (
            ClaimAttribute.TECHNOLOGY_DETECTED,
            ClaimAttribute.TECHNOLOGY_REMOVED,
        ):
            return None
        if not isinstance(self.value, dict):
            return None
        name, category = self.value.get("name"), self.value.get("category")
        if not isinstance(name, str) or not isinstance(category, str):
            return None
        return TechnologyRef(
            name=name,
            category=category,
            first_seen=_as_date(self.value.get("first_seen")),
            last_seen=_as_date(self.value.get("last_seen")),
        )


class ClaimReader(Protocol):
    """Read-only access to evidence, scoped by the caller's tenant session."""

    async def for_record(self, raw_record_id: UUID) -> tuple[ClaimView, ...]:
        """Every claim derived from one raw record."""
        ...

    async def for_subjects(
        self,
        subjects: Sequence[SubjectRef],
        *,
        attribute: ClaimAttribute | None = None,
    ) -> tuple[ClaimView, ...]:
        """Every claim about any of these provider identities.

        Queried by subject rather than by a stored list of claim ids so
        that evidence recorded *after* a resolution still appears: a
        snapshot taken at binding time would silently stop growing.
        """
        ...

    async def subjects_named_like(self, text: str, *, limit: int) -> tuple[SubjectRef, ...]:
        """Provider identities some source has called something matching `text`.

        Case-insensitive substring over `LEGAL_NAME` claims, ordered by the
        matched name then by identity, so the same query returns the same
        rows on every run and every machine.

        **Every name a source has ever given, not the one being displayed.**
        The displayed name is chosen by the Knowledge Graph's selection rule
        — newest per provider — and matching only that would require
        resolving every account in the workspace before knowing which to
        keep. Matching the claims means a
        company that has renamed is **found under its old name**, which is
        what somebody who has not heard about the rename is typing.

        **This is the searchable text, and it is the only one.**
        `identity_binding.legal_name` looks like a faster answer and is a
        resolution hint frozen at binding time — searching it would find an
        account under a name the product does not display.

        Returns identities, never accounts: resolving these to entities is
        the Knowledge Graph's job and this module has no idea they exist.
        """
        ...

    async def latest_observed_at(
        self, subjects: Sequence[SubjectRef]
    ) -> dict[SubjectRef, datetime]:
        """When the newest evidence about each of these identities was
        observed. Subjects with no claims are **absent**, not null-valued.

        **This is a time, never a value, and the distinction is what keeps
        it on the right side of the refusal above.** `current_value` was
        rejected because resolving truth behind a convenience call would
        stop every consumer looking at the evidence. A maximum over
        `observed_at` resolves nothing: it says *when the most recent thing
        we know was seen*, and answering it still requires reading the
        claims if you want to know **what** was seen.

        **Why it exists rather than being a `max()` over `for_subjects`.**
        That is what the first draft did, and it is an obvious N+1 in
        aggregate clothing — fetching every claim about fifty companies to
        keep fifty timestamps, on the list surface that renders fifty rows.
        The database can answer it with one grouped scan (§14: fix what you
        know is wrong).
        """
        ...
