"""The commercial reasoning graph.

**Deterministic, end to end. Nothing here calls a model, and nothing here
may.** [ADR-0200](../../../../docs/architecture/adr/0200-sales-engagement.md)
splits the module in two: *reasoning* decides which Buying Committee Role to
approach at a Target Account, why, what is unknown and what could be wrong;
*synthesis* explains those conclusions in prose. **AI participates only in the
second**, and the fence is structural — synthesis reads this module's output
and nothing else, so it cannot introduce a role, a risk or an unknown that was
not derived here.

If the system already knows something deterministically, never ask a model to
invent it again (`CLAUDE.md` §2). A declared title matching an observed
appointment is a string comparison. A provider disagreement is a set
difference. **Both are known.**

### Nothing here is stored

Every value below is derived at read time from facts other modules own — the
same rule `evidence_state` follows in the Opportunity Engine. A stored ranking
would be a second representation of a conclusion whose inputs move daily, and
the two would disagree within a week.

### The vocabulary

**Signora Customer** — the organization that bought Signora. **Target
Account** — the company they want to sell to; every value here is about one.
**Buying Committee Role** — a job title the Signora Customer declared must
agree, and the unit this module reasons about. **Stakeholder** and **Contact**
are deliberately absent: no person exists in the platform
([C-210](../../../../docs/LANE_COORDINATION.md)), and a ranked role is a *slot*
a person could later fill without changing anything derived here.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import Final
from uuid import UUID


class ReasoningError(Exception):
    """A reasoning input is not usable as given."""


class Strength(StrEnum):
    """How firmly the evidence supports a conclusion.

    **Words, never a percentage, and the refusal is the same one this platform
    has made three times already**: revenue is a band because *"inventing a
    point estimate from a range is exactly the kind of quiet fabrication"* this
    architecture rejects, and `MatchStrength` refuses numeric conversion for
    the same reason.

    A figure would imply an arithmetic nobody performed. **These are ordered
    for reading, not for adding**, which is why there is no numeric value to
    reach for and no `__lt__` to sort by weight.
    """

    STRONG = "strong"
    """Named directly by more than one provider's evidence, recently."""

    REASONABLE = "reasonable"
    """Named directly, but by one provider or less recently."""

    THIN = "thin"
    """Supported indirectly, or by a single ageing observation."""


class RiskKind(StrEnum):
    """What could be wrong with a conclusion.

    **Not a confidence in different clothes.** `Strength` answers *how much to
    lean on this*; a risk answers *what specifically could be wrong and why*.
    Two questions, two answers, and collapsing them would lose the half a
    seller can act on.
    """

    CONTRADICTION = "contradiction"
    """Two providers reported the same attribute differently."""

    SINGLE_SOURCE = "single_source"
    """One provider, uncorroborated."""

    STALE = "stale"
    """The evidence behind this has aged past the point of being current."""

    INFERRED = "inferred"
    """The link from evidence to conclusion is indirect. Stated, not hidden."""


@dataclass(frozen=True, slots=True)
class CommitteeRoleRef:
    """One Buying Committee Role, as this module needs it.

    **The Signora Customer's own words for `title`**, and `part` passed
    through as the string Commercial Profile declared. **No enum is redefined
    here.** That module owns the vocabulary and may extend it; a copy in this
    one would be a second definition that drifts the first time it does
    (`CLAUDE.md` §4).

    Reasoning therefore keys on `part` through a rule table this module owns
    (`_BEARS_ON`), and a part with no rule simply ranks on title evidence
    alone — which is the correct behaviour for a vocabulary that grew.
    """

    title: str
    part: str

    def __post_init__(self) -> None:
        if not self.title.strip():
            raise ReasoningError("a committee role has no title.")


@dataclass(frozen=True, slots=True)
class Evidence:
    """One recorded fact this module reasoned from.

    **A citation, never a copy.** `event_id` is the Business Event Engine's,
    and a reader follows it to the observations and providers behind it. This
    module stores nothing and reproduces nothing.
    """

    event_id: UUID
    type_key: str
    summary: str
    occurred_at: datetime
    #: How many providers' series independently supported it. **A count of
    #: agreement, never a weight** — the Business Event Engine's own words.
    corroborating_providers: int
    #: The job title the evidence named, where it named one. `role_change`
    #: claims carry it; most event types do not.
    names_title: str | None = None


@dataclass(frozen=True, slots=True)
class RankedRole:
    """A Buying Committee Role, and why it ranked where it did.

    **`why_not` is not an empty field on a ranked role — it is the whole value
    of an unranked one.** *"No evidence names your CFO"* is more useful to a
    seller than the CFO's silent absence from a list, and it is the sentence a
    ranked list structurally cannot carry.
    """

    role: CommitteeRoleRef
    strength: Strength | None
    #: Oldest first, as the Business Event Engine ordered them.
    support: tuple[Evidence, ...]
    #: Present exactly when `strength` is None.
    why_not: str | None = None

    def __post_init__(self) -> None:
        if (self.strength is None) != (self.why_not is not None):
            raise ReasoningError(
                "a role is either ranked with supporting evidence or unranked with a stated "
                "reason. **A role that is neither is a gap the reader has to explain to "
                "themselves**, which is the failure this whole module exists to remove."
            )
        if self.strength is not None and not self.support:
            raise ReasoningError(
                "a ranked role cites no evidence. A conclusion that cannot be opened is an "
                "assertion, and this module publishes none."
            )


@dataclass(frozen=True, slots=True)
class Unknown:
    """Something Signora does not know, computed rather than guessed.

    **An absence is a set difference**, which is why this is the cheapest
    section in the module and possibly the most valuable: the platform holds a
    closed evidence set, a declared committee and a canonical attribute
    vocabulary, and **nothing has ever computed the gaps.**

    `question` is what a seller would ask to close it — the reason an unknown
    is worth surfacing at all rather than merely admitted.
    """

    subject: str
    question: str


@dataclass(frozen=True, slots=True)
class Risk:
    """What could be wrong, and why."""

    kind: RiskKind
    detail: str


class NextAction(StrEnum):
    """What a seller should do with the next fifteen minutes.

    **The question the Signora Customer is actually paying for**, and it is a
    larger one than *"who do I contact?"*: the honest answer is often *not
    yet*, and a platform that can only ever say *approach* is a platform whose
    recommendation carries no information.

    **Restraint is the trust mechanism.** A seller who is told to wait once,
    correctly, believes the next *approach* — and one who is told to approach
    every account learns to ignore all of them, which is the same failure the
    attention list avoids by badging only the minority that matters.
    """

    APPROACH = "approach"
    """The evidence names a role, recently, and more than one provider saw it."""

    VERIFY = "verify"
    """**One missing fact stands between here and an approach.** Named, so it
    can be closed in a single call rather than guessed at."""

    WAIT = "wait"
    """Nothing here supports reaching out yet. **Said plainly, with why.**"""


@dataclass(frozen=True, slots=True)
class Recommendation:
    """What to do, why, and — where it applies — with whom.

    **`reason` is the *why now*, or the why-not-now**, and it cites the
    evidence that decides it. A recommendation a seller cannot repeat to their
    manager is not one this module will make.
    """

    action: NextAction
    reason: str
    #: The role to approach or verify. `None` on a `WAIT`, because there is
    #: nobody to name yet.
    role: CommitteeRoleRef | None = None

    def __post_init__(self) -> None:
        if self.action is NextAction.WAIT and self.role is not None:
            raise ReasoningError(
                "a recommendation to wait names a role. **Naming somebody while advising "
                "against contact is an invitation dressed as caution**, and a seller will "
                "read the name and ignore the advice."
            )
        if self.action is not NextAction.WAIT and self.role is None:
            raise ReasoningError("a recommendation to act names nobody to act with.")


@dataclass(frozen=True, slots=True)
class ApproachReasoning:
    """Everything the deterministic layer concluded about one Target Account.

    **This is the closed set the synthesis layer reads.** It may explain any
    of it and may introduce none of it — a synthesis naming a role absent from
    `roles`, or a risk absent from `risks`, is refused, by the same mechanism
    that already refuses a citation to evidence outside an assembled set.
    """

    account_id: UUID
    #: **The answer to *"what should I do with the next fifteen minutes?"***,
    #: and the first thing a seller reads. Everything below it is why.
    recommendation: Recommendation
    roles: tuple[RankedRole, ...]
    unknowns: tuple[Unknown, ...]
    risks: tuple[Risk, ...]


#: Which business-event domains bear on which committee part.
#:
#: **A rule table this module owns, not a vocabulary it defines.** Commercial
#: Profile owns the parts and may add one; an unmapped part ranks on title
#: evidence alone, which is the right behaviour rather than a crash. The
#: mapping states ordinary sales reasoning: a champion is moved by their
#: organization growing and their leadership changing; a gatekeeper by what
#: the company has adopted.
_BEARS_ON: Final[dict[str, frozenset[str]]] = {
    "champion": frozenset({"workforce", "leadership"}),
    "economic_buyer": frozenset({"capital"}),
    "evaluator": frozenset({"technographic"}),
    "gatekeeper": frozenset({"technographic"}),
    "user": frozenset({"workforce"}),
}

#: Past this, evidence is reported as stale rather than silently trusted. A
#: declared constant rather than a literal in a branch: it is a judgement about
#: how quickly commercial evidence ages, and it belongs where somebody can see
#: and argue with it.
STALE_AFTER_DAYS: Final = 120


#: Filler a job title carries without meaning it. **Not a stopword list for
#: language** — it is the specific set that makes *"VP Engineering"* and *"VP
#: of Engineering"* the same job, which they are.
_FILLER: Final[frozenset[str]] = frozenset({"of", "the", "and", "for", "&"})


def _tokens(title: str) -> frozenset[str]:
    return frozenset(
        word for word in title.casefold().replace(",", " ").split() if word not in _FILLER
    )


def _names(evidence: Evidence, role: CommitteeRoleRef) -> bool:
    """Whether this evidence names this role's title.

    **Token subset, not substring**, and the first version of this was wrong in
    a way only a test caught: a Signora Customer declares *"VP Engineering"*
    and a provider reports *"VP of Engineering"*. Neither is wrong, neither
    contains the other, and substring matching ranked **nothing at all**.

    Comparing token sets after dropping filler makes those the same job, and
    keeps *"VP Engineering"* and *"VP Sales"* different ones — which is the
    property that matters, because a false match would put a seller in front of
    the wrong person with Signora's confidence behind it.

    This is the join the platform has never performed — a declared title
    against an observed appointment — and it is a set comparison, which is
    exactly why no model is asked to make it.
    """
    if evidence.names_title is None:
        return False
    declared, observed = _tokens(role.title), _tokens(evidence.names_title)
    if not declared or not observed:
        return False
    return declared <= observed or observed <= declared


def _strength(support: tuple[Evidence, ...], *, direct: bool, now: datetime) -> Strength:
    if not direct:
        return Strength.THIN
    aged = all((now - one.occurred_at).days > STALE_AFTER_DAYS for one in support)
    corroborated = any(one.corroborating_providers > 1 for one in support)
    if corroborated and not aged:
        return Strength.STRONG
    return Strength.REASONABLE if not aged else Strength.THIN


def rank_roles(
    committee: tuple[CommitteeRoleRef, ...],
    evidence: tuple[Evidence, ...],
    *,
    now: datetime,
) -> tuple[RankedRole, ...]:
    """Rank the declared committee by what the evidence actually names.

    **The declaration is a preference; the evidence is a fact.** The Signora
    Customer's ordering is deliberately not an input — Commercial Profile
    refuses to hold an influence model and a structural test enforces it, and
    reading its order as a ranking here would import the influence model it
    refused to keep.

    Two ways a role can rank, and the difference is stated to the reader
    through `Strength` rather than hidden:

    - **Directly** — some evidence names the role's title.
    - **Indirectly** — evidence in a domain that bears on the role's part.
      Always `THIN`, and always accompanied by an `INFERRED` risk.

    Ranked roles come first, strongest first; unranked roles follow **with
    their reason**, because *"nothing names your CFO"* is the useful half of an
    empty result.
    """
    # **Carried beside the role rather than read back off it.** `strength` is
    # `Strength | None` on the type, and a sort key that had to handle the
    # `None` case would contain a branch that can never fire here — which is
    # Decorative Logic (`CLAUDE.md` §2), not type safety.
    ranked: list[tuple[int, RankedRole]] = []
    unranked: list[RankedRole] = []

    for role in committee:
        direct = tuple(one for one in evidence if _names(one, role))
        bears = _BEARS_ON.get(role.part, frozenset())
        indirect = tuple(one for one in evidence if one.type_key.split("_")[0] in bears)
        support = direct or indirect

        if not support:
            unranked.append(
                RankedRole(
                    role=role,
                    strength=None,
                    support=(),
                    why_not="Nothing Signora has observed at this account names this role.",
                )
            )
            continue

        strength = _strength(support, direct=bool(direct), now=now)
        ranked.append((_ORDER[strength], RankedRole(role=role, strength=strength, support=support)))

    ranked.sort(key=lambda pair: pair[0])
    return tuple(one for _, one in ranked) + tuple(unranked)


#: Reading order for ranked roles. **Not a weight**, and deliberately not a
#: field on `Strength`: a number on the enum is a number somebody will
#: eventually average.
_ORDER: Final[dict[Strength, int]] = {
    Strength.STRONG: 0,
    Strength.REASONABLE: 1,
    Strength.THIN: 2,
}


def unknowns(roles: tuple[RankedRole, ...]) -> tuple[Unknown, ...]:
    """What Signora does not know, from what it failed to rank.

    **Most GTM platforms tell a seller what they know.** Knowing the next
    question to ask is often worth more than another signal, and this is the
    only place in the platform that computes one.

    Each unranked role becomes an unknown with the question that would close
    it — phrased so a seller can ask it out loud, because a question a seller
    cannot say is an admission rather than a lead.
    """
    return tuple(
        Unknown(
            subject=one.role.title,
            question=f"Who is your {one.role.title}, and are they involved yet?",
        )
        for one in roles
        if one.strength is None
    )


def risks(roles: tuple[RankedRole, ...], *, now: datetime) -> tuple[Risk, ...]:
    """What could be wrong with the ranking.

    **Never suppressed, and never resolved.** Two providers disagreeing is
    reported as a disagreement; picking a winner would be this module deciding
    a question the evidence did not settle, which is exactly the confident
    wrong answer the platform refuses everywhere else.
    """
    found: list[Risk] = []
    for one in roles:
        if one.strength is None:
            continue
        if not any(_names(e, one.role) for e in one.support):
            found.append(
                Risk(
                    kind=RiskKind.INFERRED,
                    detail=(
                        f"{one.role.title} is inferred from what has happened at this account, "
                        "not from evidence that names the role."
                    ),
                )
            )
        if all(e.corroborating_providers == 1 for e in one.support):
            found.append(
                Risk(
                    kind=RiskKind.SINGLE_SOURCE,
                    detail=f"Only one provider supports {one.role.title}.",
                )
            )
        if all((now - e.occurred_at).days > STALE_AFTER_DAYS for e in one.support):
            found.append(
                Risk(
                    kind=RiskKind.STALE,
                    detail=(
                        f"The evidence behind {one.role.title} is more than "
                        f"{STALE_AFTER_DAYS} days old."
                    ),
                )
            )
    return tuple(found)


#: Event types that vacate a seat rather than fill one. **Split by direction
#: deliberately, and the Business Event Engine already splits them the same
#: way**: *"a leader joining and a leader leaving are not one event with a
#: flag"*. Reasoning that read only `leadership_*` would recommend approaching
#: somebody who has left.
_DEPARTURES: Final[frozenset[str]] = frozenset({"leadership_departed"})


def vacancy(role: RankedRole) -> Evidence | None:
    """The departure that emptied this seat, if the seat is empty.

    **The most recent naming event decides.** A VP who joined in March and left
    in July is a vacancy; one who left in March and was replaced in July is
    not. Reading the set rather than the sequence would get both wrong.

    This is the *"champion disappeared"* case, and it inverts the
    recommendation: the same evidence that would rank a role highest is the
    evidence that means nobody is there.
    """
    naming = sorted(
        (one for one in role.support if _names(one, role.role)),
        key=lambda one: one.occurred_at,
    )
    if not naming:
        return None
    latest = naming[-1]
    return latest if latest.type_key in _DEPARTURES else None


def contradictions(roles: tuple[RankedRole, ...]) -> tuple[Risk, ...]:
    """Where the evidence about one role points both ways at once.

    **Reported, never resolved.** An appointment and a departure for the same
    title, neither superseding the other, is two providers describing
    different worlds — and picking one would be this module settling a question
    the evidence did not.
    """
    found: list[Risk] = []
    for one in roles:
        naming = [e for e in one.support if _names(e, one.role)]
        directions = {e.type_key in _DEPARTURES for e in naming}
        if len(directions) > 1:
            found.append(
                Risk(
                    kind=RiskKind.CONTRADICTION,
                    detail=(
                        f"Signora has seen this account both appoint and lose a "
                        f"{one.role.title}, and cannot tell which is current."
                    ),
                )
            )
    return tuple(found)


def recommend(
    roles: tuple[RankedRole, ...],
    *,
    now: datetime,
) -> Recommendation:
    """What to do with the next fifteen minutes at this Target Account.

    **The question the Signora Customer is paying for**, and the rules are
    stated here rather than inferred by a model because every one of them is a
    comparison over recorded facts.

    Read in order, and the order is the argument:

    1. **Nothing declared or nothing observed → wait.** A recommendation with
       no committee would be Signora inventing the Signora Customer's sales
       process; one with no evidence would be inventing a reason.
    2. **The seat is empty → verify.** The strongest evidence for a role can
       be the evidence that nobody holds it, and approaching a departed
       executive is the single most embarrassing thing this module could
       cause.
    3. **Everything is old → wait.** A six-month-old reason to call is a
       reason not to.
    4. **Strong, recent, corroborated → approach**, naming the role and the
       evidence that makes now the moment.
    5. **Otherwise → verify**, naming the one fact that would settle it.

    **`WAIT` is a first-class answer and the tests treat it as one.** A module
    that can only say *approach* is one whose recommendation carries no
    information.
    """
    ranked = tuple(one for one in roles if one.strength is not None)
    if not ranked:
        return Recommendation(
            action=NextAction.WAIT,
            reason=(
                "Nothing Signora has observed at this account names anybody you said has to "
                "agree. There is no argument to make yet."
            ),
        )

    lead = ranked[0]
    empty = vacancy(lead)
    if empty is not None:
        return Recommendation(
            action=NextAction.VERIFY,
            reason=(
                f"The most recent thing Signora saw about this role was a departure — "
                f"{empty.summary.lower()}. Find out who holds it now before reaching out."
            ),
            role=lead.role,
        )

    if all((now - e.occurred_at).days > STALE_AFTER_DAYS for e in lead.support):
        return Recommendation(
            action=NextAction.WAIT,
            reason=(
                f"Everything supporting this account is more than {STALE_AFTER_DAYS} days old. "
                "There is nothing recent enough to open a conversation with."
            ),
        )

    newest = max(lead.support, key=lambda one: one.occurred_at)
    days = (now - newest.occurred_at).days
    when = "today" if days == 0 else f"{days} days ago"

    if lead.strength is Strength.STRONG:
        return Recommendation(
            action=NextAction.APPROACH,
            reason=f"{newest.summary} — {when}, and more than one provider saw it.",
            role=lead.role,
        )

    return Recommendation(
        action=NextAction.VERIFY,
        reason=(
            f"{newest.summary} — {when}, but only one source supports it. Confirm it before "
            "building an approach on it."
        ),
        role=lead.role,
    )


def reason(
    *,
    account_id: UUID,
    committee: tuple[CommitteeRoleRef, ...],
    evidence: tuple[Evidence, ...],
    now: datetime,
) -> ApproachReasoning:
    """The whole deterministic graph, in one call.

    **Pure.** Same inputs, same output, forever — no clock is read, no
    database is touched, no model is called. That is what makes the conclusion
    replayable, testable against fakes, and defensible to a Signora Customer
    who asks why they were shown this.
    """
    ranked = rank_roles(committee, evidence, now=now)
    return ApproachReasoning(
        account_id=account_id,
        recommendation=recommend(ranked, now=now),
        roles=ranked,
        unknowns=unknowns(ranked) + _vacancies(ranked),
        risks=risks(ranked, now=now) + contradictions(ranked),
    )


def _vacancies(roles: tuple[RankedRole, ...]) -> tuple[Unknown, ...]:
    """An empty seat is something Signora does not know, and says so."""
    return tuple(
        Unknown(
            subject=one.role.title,
            question=f"Who is the {one.role.title} now, since the last one left?",
        )
        for one in roles
        if one.strength is not None and vacancy(one) is not None
    )
