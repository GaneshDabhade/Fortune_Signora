"""The canonical vocabulary — Signora's controlled language.

Every downstream intelligence module reasons in these terms. **Adding or
changing an attribute is an architectural decision requiring an RFC**;
adding or updating a *mapper* is routine engineering. That asymmetry is
what lets provider integrations evolve while the platform's language stays
stable.

The vocabulary is closed and explicitly typed per attribute. A generic
`value: Any` would push type-checking into every consumer, and by the
Signal Engine nobody would remember what an `employee_count` actually is.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from enum import StrEnum
from typing import Final

VOCABULARY_VERSION: Final = 1


class ClaimDomain(StrEnum):
    """Groups attributes by the kind of question they answer."""

    FIRMOGRAPHIC = "firmographic"
    TECHNOGRAPHIC = "technographic"
    CAPITAL = "capital"
    WORKFORCE = "workforce"
    BEHAVIOURAL = "behavioural"


class ClaimAttribute(StrEnum):
    """What a claim asserts. **RFC required to extend.**"""

    # --- firmographic
    EMPLOYEE_COUNT = "employee_count"
    REVENUE_BAND = "revenue_band"
    INDUSTRY = "industry"
    FOUNDED_YEAR = "founded_year"
    COUNTRY = "country"
    LEGAL_NAME = "legal_name"

    # --- technographic
    TECHNOLOGY_DETECTED = "technology_detected"
    TECHNOLOGY_REMOVED = "technology_removed"

    # --- capital
    FUNDING_ROUND = "funding_round"
    ACQUISITION = "acquisition"

    # --- workforce
    HEADCOUNT_CHANGE = "headcount_change"
    OPEN_ROLES = "open_roles"
    ROLE_CHANGE = "role_change"

    # --- behavioural
    INTENT_TOPIC_SURGE = "intent_topic_surge"
    """**One claim per observed week**, never a flattened current value.
    The trajectory is product value, not implementation detail: a consumer
    given only today's score cannot tell a company at 71 on the way up from
    one at 71 on the way down."""

    @property
    def domain(self) -> ClaimDomain:
        return _ATTRIBUTE_DOMAINS[self]


_ATTRIBUTE_DOMAINS: Final[dict[ClaimAttribute, ClaimDomain]] = {
    ClaimAttribute.EMPLOYEE_COUNT: ClaimDomain.FIRMOGRAPHIC,
    ClaimAttribute.REVENUE_BAND: ClaimDomain.FIRMOGRAPHIC,
    ClaimAttribute.INDUSTRY: ClaimDomain.FIRMOGRAPHIC,
    ClaimAttribute.FOUNDED_YEAR: ClaimDomain.FIRMOGRAPHIC,
    ClaimAttribute.COUNTRY: ClaimDomain.FIRMOGRAPHIC,
    ClaimAttribute.LEGAL_NAME: ClaimDomain.FIRMOGRAPHIC,
    ClaimAttribute.TECHNOLOGY_DETECTED: ClaimDomain.TECHNOGRAPHIC,
    ClaimAttribute.TECHNOLOGY_REMOVED: ClaimDomain.TECHNOGRAPHIC,
    ClaimAttribute.FUNDING_ROUND: ClaimDomain.CAPITAL,
    ClaimAttribute.ACQUISITION: ClaimDomain.CAPITAL,
    ClaimAttribute.HEADCOUNT_CHANGE: ClaimDomain.WORKFORCE,
    ClaimAttribute.OPEN_ROLES: ClaimDomain.WORKFORCE,
    ClaimAttribute.ROLE_CHANGE: ClaimDomain.WORKFORCE,
    ClaimAttribute.INTENT_TOPIC_SURGE: ClaimDomain.BEHAVIOURAL,
}


class RevenueBand(StrEnum):
    """Bands, not figures. Enrichment vendors report ranges, and inventing
    a point estimate from a range is exactly the kind of quiet
    interpretation this layer must not do."""

    UNDER_1M = "under_1m"
    FROM_1M_TO_10M = "1m_10m"
    FROM_10M_TO_50M = "10m_50m"
    FROM_50M_TO_250M = "50m_250m"
    FROM_250M_TO_1B = "250m_1b"
    OVER_1B = "over_1b"


class TrendDirection(StrEnum):
    EMERGING = "emerging"
    SUSTAINED = "sustained"
    DECAYING = "decaying"
    REACTIVATED = "reactivated"
    NOISE = "noise"


class RoleDirection(StrEnum):
    JOINED = "joined"
    LEFT = "left"
    PROMOTED = "promoted"


# --------------------------------------------------------------- values


@dataclass(frozen=True, slots=True)
class TechnologyValue:
    name: str
    category: str
    first_seen: date | None = None
    last_seen: date | None = None


@dataclass(frozen=True, slots=True)
class FundingValue:
    round_type: str
    amount: int | None
    currency: str | None
    announced_on: date | None
    investors: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class AcquisitionValue:
    counterparty: str
    announced_on: date | None
    amount: int | None = None
    currency: str | None = None


@dataclass(frozen=True, slots=True)
class RoleChangeValue:
    title: str
    seniority: str
    direction: RoleDirection


@dataclass(frozen=True, slots=True)
class IntentSurgeValue:
    """One week of one topic. Never a rollup.

    `observed_week` is carried separately from the claim's `observed_at`
    because intent is *reported* late: a provider may deliver week 3's
    score in week 5, and conflating the two would make the trajectory
    unreadable.
    """

    topic: str
    score: int
    observed_week: date
    trend: TrendDirection


#: Every attribute's permitted value type. Enforced at construction, so a
#: mapper cannot emit an `employee_count` holding a string and have it
#: surface three modules downstream.
ATTRIBUTE_VALUE_TYPES: Final[dict[ClaimAttribute, tuple[type, ...]]] = {
    ClaimAttribute.EMPLOYEE_COUNT: (int,),
    ClaimAttribute.REVENUE_BAND: (RevenueBand,),
    ClaimAttribute.INDUSTRY: (str,),
    ClaimAttribute.FOUNDED_YEAR: (int,),
    ClaimAttribute.COUNTRY: (str,),
    ClaimAttribute.LEGAL_NAME: (str,),
    ClaimAttribute.TECHNOLOGY_DETECTED: (TechnologyValue,),
    ClaimAttribute.TECHNOLOGY_REMOVED: (TechnologyValue,),
    ClaimAttribute.FUNDING_ROUND: (FundingValue,),
    ClaimAttribute.ACQUISITION: (AcquisitionValue,),
    ClaimAttribute.HEADCOUNT_CHANGE: (int,),
    ClaimAttribute.OPEN_ROLES: (int,),
    ClaimAttribute.ROLE_CHANGE: (RoleChangeValue,),
    ClaimAttribute.INTENT_TOPIC_SURGE: (IntentSurgeValue,),
}

ClaimValue = (
    int
    | str
    | RevenueBand
    | TechnologyValue
    | FundingValue
    | AcquisitionValue
    | RoleChangeValue
    | IntentSurgeValue
)


def observed_at_is_sane(observed_at: datetime) -> bool:
    """A timezone-naive timestamp is a bug, not a value.

    Rejected rather than coerced: assuming UTC for a provider that meant
    local time silently shifts a trajectory by hours, and nobody would find
    it.
    """
    return observed_at.tzinfo is not None
