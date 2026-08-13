"""What each canonical attribute *is*, for the purpose of detecting change.

The vocabulary already contains two kinds of claim, and the whole module's
shape follows from naming the distinction:

* **State** — *this is currently true*. Change is a **transition** between
  consecutive assertions by one provider.
* **Occurrence** — *this happened*. Change is the **first sighting**; every
  later re-assertion of the same occurrence is a duplicate, not news.

`HEADCOUNT_CHANGE` shows why the distinction is load-bearing rather than
tidy: CoreSignal reports a *delta* directly, so it asserts an occurrence.
Deriving a transition from it would double-count against `EMPLOYEE_COUNT`.

**Classification is declared, never inferred.** An attribute missing from
`ATTRIBUTE_KINDS` raises rather than defaulting — the same discipline as
`TENANT_OWNED_TABLES`, and for the same reason: a silent default is how a
new attribute acquires a behaviour nobody chose.
"""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any, Final

from modules.provider_normalization.public import ClaimAttribute, RevenueBand


class AttributeKind(StrEnum):
    STATE = "state"
    OCCURRENCE = "occurrence"


class UnclassifiedAttributeError(Exception):
    """A canonical attribute has no declared observation semantics.

    Adding a canonical attribute already requires an RFC; classifying it is
    part of that RFC. Failing loudly here is the alternative to silently
    treating an unknown attribute as state and emitting transitions nobody
    designed.
    """

    def __init__(self, attribute: ClaimAttribute) -> None:
        super().__init__(
            f"'{attribute}' has no declared observation semantics. Classify it in "
            "ATTRIBUTE_KINDS as STATE or OCCURRENCE — the choice determines whether "
            "it produces transitions or first sightings, and there is no safe default."
        )


ATTRIBUTE_KINDS: Final[dict[ClaimAttribute, AttributeKind]] = {
    # --- state: the provider asserts what is currently true
    ClaimAttribute.EMPLOYEE_COUNT: AttributeKind.STATE,
    ClaimAttribute.REVENUE_BAND: AttributeKind.STATE,
    ClaimAttribute.INDUSTRY: AttributeKind.STATE,
    ClaimAttribute.FOUNDED_YEAR: AttributeKind.STATE,
    ClaimAttribute.COUNTRY: AttributeKind.STATE,
    ClaimAttribute.LEGAL_NAME: AttributeKind.STATE,
    ClaimAttribute.OPEN_ROLES: AttributeKind.STATE,
    # --- occurrence: the provider asserts that something happened
    ClaimAttribute.TECHNOLOGY_DETECTED: AttributeKind.OCCURRENCE,
    ClaimAttribute.TECHNOLOGY_REMOVED: AttributeKind.OCCURRENCE,
    ClaimAttribute.FUNDING_ROUND: AttributeKind.OCCURRENCE,
    ClaimAttribute.ACQUISITION: AttributeKind.OCCURRENCE,
    ClaimAttribute.ROLE_CHANGE: AttributeKind.OCCURRENCE,
    # **A roster, not a field.** The provider restates every member on every
    # sync, so the temptation is to call it STATE — but state is per
    # (entity, attribute) and produces *transitions*, which would collapse ten
    # people at one company into a single value that flips on each sync and
    # reads as nine departures that never happened. Keyed per member instead,
    # exactly as TECHNOLOGY_DETECTED is: a re-report of the same person is the
    # same sighting, and a new person is a new one.
    ClaimAttribute.PERSON_IDENTITY: AttributeKind.OCCURRENCE,
    # Already a delta. A transition derived from it would double-count
    # against EMPLOYEE_COUNT.
    ClaimAttribute.HEADCOUNT_CHANGE: AttributeKind.OCCURRENCE,
    # One claim per observed week. Each week is a distinct measurement, so
    # a re-report of week 3 in week 5 deduplicates and the weekly series
    # survives intact as a series of observations.
    ClaimAttribute.INTENT_TOPIC_SURGE: AttributeKind.OCCURRENCE,
}

#: Attributes whose values are counts, so an arithmetic delta is meaningful.
#: Magnitude is subtraction — never a score, and never normalized into one.
NUMERIC_ATTRIBUTES: Final[frozenset[ClaimAttribute]] = frozenset(
    {ClaimAttribute.EMPLOYEE_COUNT, ClaimAttribute.OPEN_ROLES, ClaimAttribute.FOUNDED_YEAR}
)

#: Attributes whose values are an ordered enumeration, so a direction is a
#: fact about the vocabulary rather than an interpretation. Revenue bands
#: run from `under_1m` to `over_1b` **by definition**; reading that order is
#: not a heuristic. The order is asserted by test, so reordering the enum
#: fails the build rather than silently inverting every direction.
ORDERED_ATTRIBUTES: Final[dict[ClaimAttribute, tuple[str, ...]]] = {
    ClaimAttribute.REVENUE_BAND: tuple(band.value for band in RevenueBand),
}


def attribute_kind(attribute: ClaimAttribute) -> AttributeKind:
    try:
        return ATTRIBUTE_KINDS[attribute]
    except KeyError as exc:
        raise UnclassifiedAttributeError(attribute) from exc


def occurrence_key(attribute: ClaimAttribute, value: Any, observed_at: datetime) -> str:
    """What identifies *which* occurrence this is.

    Two providers reporting the same Series B, and one provider reporting it
    on twenty consecutive nightly syncs, must all reduce to one key — that
    is what makes deduplication possible at all.

    **One function, deliberately.** These keys are read off fixture-shaped
    values today; when authentic payloads arrive they will need revisiting,
    and that revision should be a single edit rather than a hunt — the same
    reasoning as `normalize_domain` in the Knowledge Graph.
    """
    stamp = observed_at.isoformat()

    if attribute in (ClaimAttribute.TECHNOLOGY_DETECTED, ClaimAttribute.TECHNOLOGY_REMOVED):
        # Keyed on the technology alone: a vendor re-reporting the same
        # technology with a later `last_detected` is the same detection, not
        # a new one.
        return _normalized(_field(value, "name"))

    if attribute is ClaimAttribute.FUNDING_ROUND:
        return f"{_normalized(_field(value, 'round_type'))}|{_field(value, 'announced_on')}"

    if attribute is ClaimAttribute.ACQUISITION:
        return f"{_normalized(_field(value, 'counterparty'))}|{_field(value, 'announced_on')}"

    if attribute is ClaimAttribute.ROLE_CHANGE:
        return f"{_normalized(_field(value, 'title'))}|{_field(value, 'direction')}|{stamp}"

    if attribute is ClaimAttribute.PERSON_IDENTITY:
        # **The provider's key alone, and deliberately not the title.** A
        # nightly roster re-reports the same people indefinitely, and keying on
        # anything that moves — a title, a `last_seen`, the sync stamp — would
        # turn every sync into a fresh sighting of everybody. ⛔ **And not the
        # name**: a person who corrects a spelling or marries has not arrived.
        return _normalized(_field(value, "person_ref"))

    if attribute is ClaimAttribute.INTENT_TOPIC_SURGE:
        # The observed week, never the reporting week. Intent is reported
        # late by design, and keying on arrival would make one week's
        # measurement look like several.
        return f"{_normalized(_field(value, 'topic'))}|{_field(value, 'observed_week')}"

    if attribute is ClaimAttribute.HEADCOUNT_CHANGE:
        return f"{stamp}|{value}"

    raise UnclassifiedAttributeError(attribute)


def _field(value: Any, name: str) -> str:
    if isinstance(value, dict):
        return str(value.get(name, ""))
    return ""


def _normalized(raw: str) -> str:
    return " ".join(raw.strip().lower().split())
