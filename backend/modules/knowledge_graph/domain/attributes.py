"""Resolving an attribute's *value*, the way this module already resolves a name.

**The gap [C-332](../../../../docs/LANE_COORDINATION.md) found and
[462](../../../../docs/architecture/462-observed-attributes-proposal.md)
proposed**, approved exactly as written by
[D-111](../../../../docs/DECISION_REGISTER.md).

### Why the existing contract could not do this

`ClaimSet` is *"everything known about one attribute of one entity"* — three
providers, three answers, and **no rule for settling them.** A consumer that
projects it into one value has become **a second resolver**, and with sixteen
consumers of the matching capability that means up to sixteen rules for what an
account's industry is — **with the disagreements invisible, because each
answer looks correct in isolation.**

> **The existing contract is not insufficient in *shape*. It is insufficient in
> *authority*.** `ClaimSet` publishes evidence; a consumer needs a resolved
> fact, **and only the module that owns resolution may resolve it.**

The repository had already refused this twice in writing — `competitors.py`
(*"a second resolver here would be free to disagree with it"*) and
[443 §1](../../../../docs/architecture/443-account-matching-capability.md).

### The rule, stated here rather than buried in a query

> **The most recently observed claim wins, and the providers that agreed with
> it are named.**

**Identical to `select_name`, deliberately.** That function resolves the *name*
attribute by exactly this rule, and an account whose name resolves by recency
while its industry resolved by something else would be one account with two
notions of what *current* means. **[462 §3](../../../../docs/architecture/462-observed-attributes-proposal.md)
required the rule to be stated in the contract rather than decided by accident
inside the first implementation** — this docstring is where it is stated.

**And the refusal is inherited too.** `select_name`: *"provider precedence is a
customer policy… encoding one here would put an unreviewed judgement in the
substrate."* **No provider is ranked, scored or weighted here either.**

⬜ **What stays open**: whether *most-corroborated* should beat *most recent*,
and whether a customer may declare precedence. Both are policy, both need a
reviewed artifact, and neither is decided by shipping the simplest defensible
rule with its name on it.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

from modules.provider_normalization.public import ClaimView


class ValueAgreement(StrEnum):
    """Whether the sources agree about this attribute's value.

    **The same four states as `NameAgreement`, and the same reasoning**: a
    seller reading *"nobody has said"*, *"one source said"* and *"two sources
    disagree"* is in three different situations, and only the last is worth
    interrupting them for.
    """

    UNKNOWN = "unknown"
    """**No source has reported this attribute.** Absent, not disputed — and
    **not the same as a source reporting that it does not know.**"""

    SINGLE_SOURCE = "single_source"
    """One provider reports it. **Uncorroborated rather than agreed.**"""

    AGREED = "agreed"
    """Every provider that reports it says the same thing."""

    DISPUTED = "disputed"
    """They differ. **The value returned is the most recent**, and this is the
    field that says so — a consumer showing the value without this is showing a
    contested fact as a settled one."""


@dataclass(frozen=True, slots=True)
class ResolvedAttribute:
    """One attribute's value, resolved, with enough provenance to defend it.

    **`value is None` is a first-class outcome and never an error.** It means
    no provider has reported this attribute, which is exactly the *unmeasured*
    that [TASK-434](../../../../docs/BACKLOG.md)'s predicate already carries —
    **the same word arriving from the other end of the same call.**

    ⛔ **No `SubjectRef`, and that omission is load-bearing.** A provider
    identity crossing this boundary would let a consumer walk back to the
    claims and resolve them itself — **which is the entire defect this type
    closes.** `providers` carries provider *names*, which identify a source
    without identifying a subject.
    """

    #: `None` when nothing has been observed. Typed loosely because the
    #: canonical vocabulary types values per attribute — an `int` for
    #: `EMPLOYEE_COUNT`, a `str` for `INDUSTRY` — and narrowing here would
    #: mean a second copy of `ATTRIBUTE_VALUE_TYPES`.
    value: object | None
    agreement: ValueAgreement
    #: Every provider whose most recent claim matches `value`. **Sorted**, so
    #: the same evidence renders the same way on every machine.
    providers: tuple[str, ...]
    #: When the winning claim was observed — **not when Signora stored it.**
    #: The distinction is what lets a reader judge how current the answer is.
    observed_at: datetime | None

    @property
    def is_known(self) -> bool:
        return self.agreement is not ValueAgreement.UNKNOWN


UNKNOWN: ResolvedAttribute = ResolvedAttribute(
    value=None, agreement=ValueAgreement.UNKNOWN, providers=(), observed_at=None
)


def resolve_value(claims: tuple[ClaimView, ...]) -> ResolvedAttribute:
    """Resolve one attribute's claims into one value.

    **Pure.** No session, no clock, no repository — the caller supplies the
    claims, so the rule can be replayed and argued with without a database.

    **The most recent claim wins; ties break on provider name**, so two
    providers observing at the same instant resolve identically on every run
    and every machine. A value that depended on row order would make one
    account answer differently to two callers asking at once.
    """
    reported = tuple(claim for claim in claims if claim.value is not None)
    if not reported:
        return UNKNOWN

    latest_per_provider: dict[str, ClaimView] = {}
    for claim in sorted(reported, key=lambda c: (c.observed_at, c.provider)):
        latest_per_provider[claim.provider] = claim

    winner = max(latest_per_provider.values(), key=lambda c: (c.observed_at, c.provider))

    distinct = {_comparable(claim.value) for claim in latest_per_provider.values()}
    if len(latest_per_provider) == 1:
        agreement = ValueAgreement.SINGLE_SOURCE
    elif len(distinct) == 1:
        agreement = ValueAgreement.AGREED
    else:
        agreement = ValueAgreement.DISPUTED

    return ResolvedAttribute(
        value=winner.value,
        agreement=agreement,
        # **Only the providers that agree with the answer.** Listing every
        # provider that reported *something* would make a disputed attribute
        # look corroborated by the sources contradicting it.
        providers=tuple(
            sorted(
                provider
                for provider, claim in latest_per_provider.items()
                if _comparable(claim.value) == _comparable(winner.value)
            )
        ),
        observed_at=winner.observed_at,
    )


def _comparable(value: object) -> object:
    """A value in the form two claims are compared in.

    **Case and surrounding space folded for text, and nothing else.** `SaaS`
    and `saas` are one answer typed twice; `SaaS` and `Computer Software` are
    two answers, and deciding they mean one thing is a reviewed synonym catalog
    rather than code — the same limitation `commercial_profile.evaluation`
    carries, named in the same words, for the same reason.
    """
    if isinstance(value, str):
        return " ".join(value.split()).casefold()
    return value


__all__ = ["UNKNOWN", "ResolvedAttribute", "ValueAgreement", "resolve_value"]
