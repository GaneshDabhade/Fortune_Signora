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
    PERSON_IDENTITY = "person_identity"
    """**Who holds a role, as opposed to that a role changed hands.**

    ⚠️ **The one attribute added by an approved task rather than an RFC**, and
    it is named here so nobody has to reconstruct why. `TASK-429` carries the
    provider contract Lane C prepared and the product owner ruled at `D-233`;
    the module docstring's *"RFC required to extend"* asks for a decision taken
    outside a coding session, and this is one.

    ⛔ **It is not `ROLE_CHANGE` with a name bolted on.** A role change is an
    **event** — somebody moved, on a date, in a direction — and this is a
    **snapshot**: the provider's current roster, restated in full on every
    sync. Folding them together would make a re-sync look like thirty-six
    people arriving.

    **Why the platform needed it.** `people` mints a new subject on every
    arrival and says so in its own docstring, because it holds no identifier
    to match one against — so *"where else has this person worked"* returns one
    affiliation in almost every case. **That is the defect this attribute
    supplies the input for**, and it is `person_ref` that closes it, not the
    name.
    """

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
    ClaimAttribute.PERSON_IDENTITY: ClaimDomain.WORKFORCE,
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


class OrgEdgeSource(StrEnum):
    """How sure the provider is that one person reports to another.

    **The vendor's own hedge about its own data, carried and never
    re-derived.** A contact provider confirms a reporting line where it has
    seen one stated and infers it elsewhere from title and seniority — and
    ⛔ **the distinction must survive to the screen**, because a seller
    planning who to approach through whom is entitled to know which edges the
    product is guessing at.
    """

    CONFIRMED = "confirmed"
    INFERRED = "inferred"


@dataclass(frozen=True, slots=True)
class OrgEdge:
    """Who somebody reports to, **and never one without the other.**

    ⚡ **One field rather than two**, so *"a reporting line with no stated
    confidence"* and *"a confidence attached to no line"* are both
    **unrepresentable** rather than merely discouraged — [§2](../../../../CLAUDE.md),
    *prefer a violation that cannot be constructed.* Two optional fields
    beside each other would make an unsourced edge a runtime check somebody
    eventually removes.
    """

    #: The manager's `person_ref`, in the same provider's namespace.
    manager_ref: str
    source: OrgEdgeSource


@dataclass(frozen=True, slots=True)
class PersonIdentityValue:
    """One person a contact provider says holds a role at this company.

    ### `person_ref` is the field that matters, and it is not the name

    **Provider-stable and opaque.** It is what lets `people` recognise a second
    arrival as the same subject instead of minting a stranger — the duplicate
    -person defect `RecordRoleChange.arrived` documents rather than fixes.
    ⛔ **Nothing may parse it.** It is a provider's key, not a description, and
    a consumer that read a company out of it would be depending on a format the
    vendor is free to change.

    ⚠️ **A name is carried because the provider supplies one, not because this
    layer decided a name was needed.** Normalization's whole rule is to carry a
    vendor's assertion into canonical vocabulary without interpreting it —
    ⛔ **and carrying it here does not oblige any consumer to store it.**
    `people` is anonymous by specification (`C-221`), and what it needs from
    this value is `person_ref`.

    ⛔ **No stance, no influence, no seat, no rank.** Those are the fields the
    neighbouring committee model warns are *one plausible field away* from
    turning an identity into a scoring input — and a provider claiming one
    would be a vendor deciding a customer's buying committee.

    `last_seen` is **when the provider last observed them in this role**, and
    an old one is not a departure. A departure is a `ROLE_CHANGE` with a
    direction, from a provider that watched it happen; inferring one from a
    stale timestamp would manufacture an event out of a vendor's refresh
    schedule.
    """

    person_ref: str
    full_name: str
    title: str
    seniority: str
    first_seen: date | None = None
    last_seen: date | None = None
    #: ⛔ **The one relationship fact a contact provider can legitimately
    #: author**, and the reason is what it is *about*: an org chart is a fact
    #: about the company, which a vendor observes, rather than a fact about
    #: the customer's deal, which it cannot see. **`stance`,
    #: `engagement_last_90d`, `relationship_strength` and `committee_role` are
    #: the four that are NOT here** — [C-1509](../../../../docs/LANE_COORDINATION.md).
    #:
    #: ⚠️ **A reorg is not observable through this.** The occurrence key is
    #: `person_ref` alone, so a changed reporting line deduplicates against the
    #: original sighting exactly as a changed title does. **Stated rather than
    #: left to be found**: making a reorg visible needs its own attribute, from
    #: a provider that reports the *change* rather than the current state.
    reports_to: OrgEdge | None = None


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
    ClaimAttribute.PERSON_IDENTITY: (PersonIdentityValue,),
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
    | PersonIdentityValue
    | IntentSurgeValue
)


def observed_at_is_sane(observed_at: datetime) -> bool:
    """A timezone-naive timestamp is a bug, not a value.

    Rejected rather than coerced: assuming UTC for a provider that meant
    local time silently shifts a trajectory by hours, and nobody would find
    it.
    """
    return observed_at.tzinfo is not None
