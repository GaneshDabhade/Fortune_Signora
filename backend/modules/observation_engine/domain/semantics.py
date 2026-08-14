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


class UnkeyableOccurrenceError(Exception):
    """An occurrence carries nothing that says **which** occurrence it is.

    ⛔ **Distinct from `UnclassifiedAttributeError`, and the difference is the
    whole of it.** That one means *nobody declared what this attribute is*;
    this one means *the attribute is declared and the VALUE cannot be
    identified.* **Collapsing them would hide a data defect behind a
    configuration one.**

    ⚡ **Raised rather than returning an empty key**, because an empty key
    deduplicates: two unrelated occurrences with nothing to tell them apart
    would become one observation, and **the record of the second would not
    exist to be found later.**
    """

    def __init__(self, attribute: ClaimAttribute, field: str) -> None:
        super().__init__(
            f"a '{attribute}' occurrence carries no '{field}', so nothing distinguishes "
            "it from any other. An occurrence key identifies WHICH occurrence this is; "
            "an empty one silently merges unrelated records into a single observation, "
            "and the ones it swallowed leave no trace. Reject the claim at the mapper "
            "rather than admitting a value that cannot be identified."
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
        return _identifying(value, "name", attribute)

    if attribute is ClaimAttribute.FUNDING_ROUND:
        return f"{_identifying(value, 'round_type', attribute)}|{_field(value, 'announced_on')}"

    if attribute is ClaimAttribute.ACQUISITION:
        return f"{_identifying(value, 'counterparty', attribute)}|{_field(value, 'announced_on')}"

    if attribute is ClaimAttribute.ROLE_CHANGE:
        return f"{_identifying(value, 'title', attribute)}|{_field(value, 'direction')}|{stamp}"

    if attribute is ClaimAttribute.PERSON_IDENTITY:
        # **The provider's key alone, and deliberately not the title.** A
        # nightly roster re-reports the same people indefinitely, and keying on
        # anything that moves — a title, a `last_seen`, the sync stamp — would
        # turn every sync into a fresh sighting of everybody. ⛔ **And not the
        # name**: a person who corrects a spelling or marries has not arrived.
        return _identifying(value, "person_ref", attribute)

    if attribute is ClaimAttribute.INTENT_TOPIC_SURGE:
        # The observed week, never the reporting week. Intent is reported
        # late by design, and keying on arrival would make one week's
        # measurement look like several.
        return f"{_identifying(value, 'topic', attribute)}|{_field(value, 'observed_week')}"

    if attribute is ClaimAttribute.HEADCOUNT_CHANGE:
        return f"{stamp}|{value}"

    raise UnclassifiedAttributeError(attribute)


def _identifying(value: Any, name: str, attribute: ClaimAttribute) -> str:
    """The part of a value that says **which** occurrence this is — refused when absent.

    🔴 **An occurrence key that identifies nothing is not a key.** Every branch
    above used to fall through `_field`, which returns `""` for a missing
    field — so ten people with no `person_ref` all keyed to `""` and
    **deduplicated into one**, which is precisely the *"nine departures nobody
    made"* that `PERSON_IDENTITY`'s own comment says the design exists to
    prevent.

    ⚠️ **Found by QE attacking the claim, and it was true of seven of the
    eight occurrence attributes** — not one. `TECHNOLOGY_DETECTED`,
    `TECHNOLOGY_REMOVED` and `PERSON_IDENTITY` collapsed to `""`;
    `FUNDING_ROUND`, `ACQUISITION` and `INTENT_TOPIC_SURGE` to `"|"`; and
    `ROLE_CHANGE` to one key per instant, merging every role change reported
    at the same moment.

    ⛔ **The guard was at one producer, not at the function that collapses.**
    Every mapper does reject a value with no identifier — Apollo's says so in
    as many words — **but a seam that silently merges unrelated records when a
    future producer forgets is a seam that is trusting its callers.** 📁 The
    repository already prefers the opposite: *"failing loudly here is the
    alternative to silently treating an unknown attribute as state"*, one
    function up.

    ✅ **Unreachable through today's mappers, and stated rather than implied.**
    That is what makes it defence in depth rather than dead code — the same
    standing as the explicit `workspace_id` filter beside RLS (§8), and it is
    constructible directly, which is how it is fire-tested.
    """
    identity = _normalized(_field(value, name))
    if not identity:
        raise UnkeyableOccurrenceError(attribute, name)
    return identity


def _field(value: Any, name: str) -> str:
    if isinstance(value, dict):
        return str(value.get(name, ""))
    return ""


def _normalized(raw: str) -> str:
    return " ".join(raw.strip().lower().split())
