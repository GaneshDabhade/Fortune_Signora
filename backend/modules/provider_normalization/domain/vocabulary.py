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

VOCABULARY_VERSION: Final = 2
#: ⚡ **Incremented to 2 by [ADR-0409](../../../../docs/architecture/adr/
#: 0409-commercial-account-facts.md) §5, which asks for it by name**: *"It
#: exists to be incremented; a vocabulary change that leaves it at 1 is a
#: stored fact disagreeing with the code that wrote it."*
#: ⛔ **The `COMMERCIAL` domain and its three attributes are what changed.**


class ClaimDomain(StrEnum):
    """Groups attributes by the kind of question they answer."""

    FIRMOGRAPHIC = "firmographic"
    TECHNOGRAPHIC = "technographic"
    CAPITAL = "capital"
    WORKFORCE = "workforce"
    BEHAVIOURAL = "behavioural"
    COMMERCIAL = "commercial"
    """**What this account is worth to us, and where it stands** —
    📁 [ADR-0409](../../../../docs/architecture/adr/0409-commercial-account-facts.md) §2,
    ratified by the product owner as [C-209](../../../../docs/LANE_COORDINATION.md)
    option A.

    ⛔ **Deliberately NOT folded into `CAPITAL`.** ⚡ **Capital is what happened
    to the *company*; commercial is the state of *our relationship with it*.**
    Different subject, different provenance — **and a consumer filtering on
    domain would get the wrong set.**
    """


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

    # --- commercial
    OPEN_ACV = "open_acv"
    """**What this account is worth, as the customer's own system states it.**

    ⚠️ **Whether it is *open* is a question about the STAGE, not about this
    figure** — see `CommercialStage.is_open`. ⛔ **The two are separate
    attributes because a provider supplies them separately**, and fusing them
    would make a deal that closed since the last sync carry a figure this
    layer had already decided was open.
    """

    RENEWAL_DATE = "renewal_date"
    """**When the current term ends.** ⛔ **A `date`, never a countdown** — the
    design draws *"Renewal 69d"* and *"Renewal in 38 days"*, and **a stored
    number of days is wrong the next morning.**"""

    COMMERCIAL_STAGE = "commercial_stage"
    """**Where the relationship stands, canonically, with the tenant's own
    word beside it.**

    📁 [ADR-0409](../../../../docs/architecture/adr/0409-commercial-account-facts.md)
    §3: *"Reasoning reads the canonical position. A screen may show the
    customer's word."* ⚡ **[ADR-0034](../../../../docs/architecture/adr/
    0034-ubiquitous-language.md) inside a single attribute.**
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
    ClaimAttribute.OPEN_ACV: ClaimDomain.COMMERCIAL,
    ClaimAttribute.RENEWAL_DATE: ClaimDomain.COMMERCIAL,
    ClaimAttribute.COMMERCIAL_STAGE: ClaimDomain.COMMERCIAL,
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


class CommercialStage(StrEnum):
    """Where a relationship stands, in the smallest set the consumers need.

    🔴 **[ADR-0409](../../../../docs/architecture/adr/0409-commercial-account-facts.md)
    §3 delegates these members to this lane and says why**: *"Naming them from
    this office, without a mapper in front of me, would be the invention this
    ADR exists to avoid."* ⚡ **They are proposed in the Slice Handoff and
    become part of the ratified contract.**

    ## 📁 Where each member comes from, because *the smallest set* needs a test

**`NEGOTIATING` · `CLOSED_WON`** — ⚡ **drawn by name.** *"Weakest link:
    **Negotiation → Closed won**, down 9 points"* (Executive Dashboard) ·
    *"Stage · **Negotiation**"* (App Shell) · *"**Negotiation** since 12 Jun"*
    (Design System v2).

    **`CLOSED_LOST`** — 🔴 **required by the funnel the design draws.** That
    conversion is a ratio, **and its denominator is every deal that left
    Negotiation without winning.** ⛔ Without this member the figure cannot be
    computed honestly.

    **`QUALIFYING` · `EVALUATING`** — ⚡ **the two positions every CRM's default
    pipeline collapses into before Negotiation**: HubSpot's `qualifiedtobuy` /
    `presentationscheduled` / `decisionmakerboughtin`, Salesforce's
    `Qualification` / `Needs Analysis` / `Value Proposition`. ⛔ **Fewer would
    make the funnel a single step and the *weakest link* unanswerable.**

    ## ⛔ What is deliberately NOT here

    **`Commit` and `Best case`.** 📁 The Executive Dashboard draws them —
    *"commit, best case and AI projection against a $68.0M plan"* — ⚠️ **and
    they are FORECAST CATEGORIES, not pipeline positions.** ⛔ **A rep sets a
    forecast category as a judgement; a stage records where the work is.**
    Folding them in would put an opinion inside a fact, **and
    [C-297](../../../../docs/LANE_COORDINATION.md)'s refusal of probability is
    the same refusal one concept over.**

    **The tenant's own stages.** *"Legal review"*, *"Procurement"* — 📁 the CRM
    Integrations design's own example. ⚡ **They travel as
    `CommercialStageValue.label` and are never members here**, which is the
    whole reason the canonical set is closed.
    """

    QUALIFYING = "qualifying"
    EVALUATING = "evaluating"
    NEGOTIATING = "negotiating"
    CLOSED_WON = "closed_won"
    CLOSED_LOST = "closed_lost"

    @property
    def is_open(self) -> bool:
        """Whether work on this relationship is still live.

        🔴 **This is what makes `OPEN_ACV` computable, and it lives here rather
        than in every consumer.** 📁 [§2](../../../../CLAUDE.md), *least
        powerful author*: **which positions are open is static knowledge this
        enum owns**, and a consumer re-deriving it would be the second
        representation that eventually disagrees.

        ⛔ **Stated as *not closed* rather than as a list of the open ones.** ⚡
        **A sixth position added later is open until somebody says otherwise**,
        which is the safe direction — the alternative silently drops a stage
        out of every open-pipeline figure the day it is added.
        """
        return self not in {CommercialStage.CLOSED_WON, CommercialStage.CLOSED_LOST}


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
class MoneyValue:
    """A figure and the currency it is in, **and never one without the other.**

    📁 [ADR-0409](../../../../docs/architecture/adr/0409-commercial-account-facts.md)
    §3: *"A figure without its currency is not a fact."*

    ⚠️ **Both REQUIRED, which is where this departs from its own precedent and
    the departure is deliberate.** 📁 `FundingValue` and `AcquisitionValue`
    carry `amount: int | None` beside `currency: str | None`, **because a
    funding round is announced without a figure and the round is still the
    fact.** ⛔ **An Open ACV with no amount is not a thinner fact — it is no
    fact at all**, and [§2](../../../../CLAUDE.md) prefers a violation that
    cannot be constructed over one a reader has to remember to check.

    ⛔ **No conversion, ever.** 📁 §5: *"Currency is carried, never
    converted."* ⚡ **A rate is applied at a moment** — [§10](../../../../CLAUDE.md),
    *operational facts and commercial policy stay separate* — **so a converted
    figure stored on a claim is correct briefly and wrong permanently.**

    ⚠️ **Minor units are the provider's, uninterpreted.** This layer carries
    what the customer's system said; **deciding whether `1200` is twelve
    dollars or twelve hundred is a mapper's job**, and stating it here would
    be this file deciding a vendor's format.
    """

    amount: int
    currency: str


@dataclass(frozen=True, slots=True)
class CommercialStageValue:
    """A canonical position, **and the tenant's own word for it.**

    ## 🔴 `position` is optional, and the design is why

    📁 **The CRM Integrations screen states the case in full:**

    > ⚡ *"Salesforce added 'Legal review' and 'Procurement' to StageName last
    > week. **214 opportunities now sit in stages Signora treats as unmapped**,
    > and their velocity metrics are **excluded until mapped**."*

    ⛔ **So *unmapped* is a state the product SHOWS, counts, and acts on** — it
    is not an error and not a gap to be filled. ⚡ **`position=None` with a
    `label` is exactly that state**, and it is representable rather than
    inferred from a missing claim.

    ⚠️ **[ADR-0409](../../../../docs/architecture/adr/0409-commercial-account-facts.md)
    §3 describes the value as *"a closed canonical position, carrying the
    tenant's own label beside it"*, which reads as though a position is always
    present.** 🔴 **The design requires otherwise, and this is raised rather
    than resolved quietly** — 📁 [C-1514](../../../../docs/LANE_COORDINATION.md).
    **Implemented as optional because the alternative cannot express a screen
    the design draws**, and because ⛔ **coercing an unknown tenant stage into
    the nearest canonical one is precisely the invention the ADR exists to
    prevent.**

    ## ⛔ Why the label is never reasoned over

    📁 §5: *"The tenant's stage label is provenance and is never reasoned
    over."* ⚡ **A consumer branching on `label` would be parsing a vendor's
    string** — [§10](../../../../CLAUDE.md), vendor neutrality — **and the
    customer renames it the following week.**
    """

    #: ⛔ **`None` means the tenant's stage maps to nothing canonical.** Not
    #: *unknown*, not *missing* — **mapped to nothing, deliberately.**
    position: CommercialStage | None
    #: ⚡ **What the customer's own system calls it**, carried so a screen can
    #: show their word and so *"map both →"* has something to name.
    label: str

    def __post_init__(self) -> None:
        if not self.label.strip():
            # ⛔ **A stage with no label is a claim about nothing.** The
            # provider supplied a stage or it did not; an empty string is the
            # zero-filled absence §5 forbids wearing a value's clothes.
            raise ValueError("a commercial stage carries the tenant's own label")

    @property
    def is_mapped(self) -> bool:
        """Whether this stage means anything to reasoning yet.

        ⚡ **The predicate the design's *"excluded until mapped"* needs**, in
        one place rather than in every consumer that has to honour it.
        """
        return self.position is not None


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
    ClaimAttribute.OPEN_ACV: (MoneyValue,),
    ClaimAttribute.RENEWAL_DATE: (date,),
    ClaimAttribute.COMMERCIAL_STAGE: (CommercialStageValue,),
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
    | date
    | MoneyValue
    | CommercialStageValue
)


def observed_at_is_sane(observed_at: datetime) -> bool:
    """A timezone-naive timestamp is a bug, not a value.

    Rejected rather than coerced: assuming UTC for a provider that meant
    local time silently shifts a trajectory by hours, and nobody would find
    it.
    """
    return observed_at.tzinfo is not None
