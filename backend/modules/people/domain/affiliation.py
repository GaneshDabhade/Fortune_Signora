"""Where somebody has worked, as an interval that closes rather than a field
that is overwritten.

**The load-bearing choice of
[ADR-0400](../../../../docs/architecture/adr/0400-person-as-an-entity.md)**, in
its own words:

> ***"Priya left Acme"* is not a mutation of Priya — it is an interval
> closing.** Storing a current employer as a field would destroy the history
> the entire product is built on, and would be **the one place in this
> repository where a state change overwrites its own evidence.**

### What an affiliation is made of, and where each part comes from

**Everything below already flows in production.** No provider work, no new
claim attribute, no vocabulary extension — which is what makes this a domain
foundation rather than an integration.

| | | |
|---|---|---|
| **person** | the subject | minted here; anonymous |
| **company** | `entity_id` | the Knowledge Graph's company, the same id every other module cites |
| **title · seniority** | what they do | `RoleChangeValue(title, seniority, direction)` |
| **interval** | when | `occurred_on` — a start, and later an end |

### Open-ended is a state, not a missing value

An affiliation with no `ended_on` means **the person still holds the role as
far as anybody has told us** — which is different from *"we do not know when
they left"*, and the two must not be collapsed. **This module can only ever
represent the first**: a departure Signora never saw leaves an interval open,
and the honest reading of an open interval is *"no departure has been
observed"* rather than *"they are still there"*.

**Stated here because a consumer will want the second reading**, and the
sentence a screen may write is the first one.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from uuid import UUID


class AffiliationError(ValueError):
    """An affiliation could not be described the way this module requires."""


@dataclass(frozen=True, slots=True)
class RoleInterval:
    """When somebody held a role. **Half-open, and open-ended is legal.**

    `started_on` is required and `ended_on` is not, because an arrival is
    always observed before a departure and most affiliations Signora records
    will never see one.
    """

    started_on: date
    ended_on: date | None = None

    def __post_init__(self) -> None:
        if self.ended_on is not None and self.ended_on < self.started_on:
            raise AffiliationError(
                f"an affiliation cannot end on {self.ended_on} having started on "
                f"{self.started_on}. A departure before an arrival is a provider "
                "reporting two people's events under one role, not a short tenure."
            )

    @property
    def is_open(self) -> bool:
        """**No departure has been observed.** Deliberately not *"they still
        work there"* — see the module docstring; the two are different claims
        and only the first is one this module can make."""
        return self.ended_on is None

    def closed_on(self, moment: date) -> RoleInterval:
        """The same interval, ended. **A new value, never a mutation.**

        Refuses to close twice: an affiliation that already ended and is being
        ended again means two departures were matched to one arrival, which is
        a matching defect and must surface rather than silently keep the later
        date.
        """
        if self.ended_on is not None:
            raise AffiliationError(
                f"this affiliation already ended on {self.ended_on} and cannot end again "
                f"on {moment}. Two departures matched to one arrival is a matching defect, "
                "and overwriting the first would hide it."
            )
        return RoleInterval(started_on=self.started_on, ended_on=moment)


@dataclass(frozen=True, slots=True)
class Affiliation:
    """**person × company × title × interval** — the entity the ADR calls the
    place *"where the intelligence lives"*.

    **An entity rather than a field on `Person`**, so that one person can hold
    two affiliations at once — a board seat and an executive role — and so
    that a departure has somewhere to be recorded instead of somewhere to be
    erased.
    """

    id: UUID
    workspace_id: UUID
    person_id: UUID
    #: The company, as the Knowledge Graph knows it. **The same `entity_id`
    #: every other module cites**, so an affiliation joins to an account
    #: without this module owning a second notion of what a company is.
    company_id: UUID
    #: Verbatim from the provider, through `RoleChangeValue.title`. **Not
    #: normalised and not mapped to a committee seat** — *"which seat does
    #: 'Head of Clinical Informatics' fill?"* is ❓3 of the ADR, is the same
    #: question as [C-018](../../../../docs/LANE_COORDINATION.md) with a
    #: different noun, and belongs to whoever owns that mapping.
    title: str
    #: The provider's own seniority band, carried for the same reason as the
    #: title: it is what the business-event rules already filter on
    #: (`qualifying_seniorities`), so re-deriving it here would be a second
    #: vocabulary.
    seniority: str
    interval: RoleInterval

    def __post_init__(self) -> None:
        if not self.title.strip():
            raise AffiliationError(
                "an affiliation with no title says only that somebody was somewhere, "
                "which no consumer can act on. A role change that carries no title is "
                "not an affiliation."
            )

    @property
    def is_current(self) -> bool:
        """**No departure observed.** The property is named for the reading a
        consumer wants; the docstring on `RoleInterval.is_open` is the one that
        says what it actually means."""
        return self.interval.is_open

    def ended(self, *, on: date) -> Affiliation:
        """Close this affiliation. **A new value; nothing is overwritten.**"""
        return Affiliation(
            id=self.id,
            workspace_id=self.workspace_id,
            person_id=self.person_id,
            company_id=self.company_id,
            title=self.title,
            seniority=self.seniority,
            interval=self.interval.closed_on(on),
        )


__all__ = ["Affiliation", "AffiliationError", "RoleInterval"]
