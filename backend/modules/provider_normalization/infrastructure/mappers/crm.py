"""Mappers for a customer's own CRM.

**The first source that is not one of Signora's suppliers.** Everything else
in this package translates a vendor Signora pays; this translates a system
the *customer* owns and holds the credential for. Above this file that
difference is invisible and must stay so — a claim from HubSpot is a claim,
carrying its provider and its `observed_at` like every other, and nothing
downstream branches on where evidence came from.

**Nothing here decides how the payload arrived.** A mapper receives a stored
record and translates it; who fetched it, with whose credential, through
which port, is a question this layer has never been able to ask and still
cannot. That is why this file is buildable while
[ADR-0300](../../../../docs/architecture/adr/0300-inbound-customer-systems.md)
is still proposed: **the gap Epic E1 found is in acquiring records, not in
interpreting them.**

**These translate the current DEVELOPMENT FIXTURE shapes**, in the same
sense and with the same honesty as the four mappers beside them. The shape
below is HubSpot's documented CRM v3 company object; no live call has
confirmed it, and `payload_provenance` marks every claim derived from a
fixture so the distinction survives all the way to a customer's screen.
"""

from __future__ import annotations

from collections.abc import Iterator, Mapping
from datetime import datetime
from typing import Any, Final

from modules.provider_normalization.domain.claim import SubjectHint
from modules.provider_normalization.domain.mapper import MappedClaim, ProviderMapper
from modules.provider_normalization.domain.outcome import Rejection, RejectionReason
from modules.provider_normalization.domain.vocabulary import ClaimAttribute, RevenueBand

#: Where a figure falls, as declared boundaries rather than judgement.
#:
#: **This is the reverse of the conversion the vocabulary forbids.**
#: `RevenueBand` refuses *"inventing a point estimate from a range"* — and a
#: CRM reports the opposite: a figure the customer typed or their finance
#: system supplied. Placing a known figure inside a declared band **loses
#: precision and invents nothing**, which is the only direction of this
#: conversion that is not interpretation.
#:
#: Read as *lower bound inclusive*: exactly 1,000,000 is `1m_10m`, never
#: `under_1m`. Stated because a boundary convention left implicit is a
#: boundary convention two readers will disagree about.
_REVENUE_BOUNDARIES: Final[tuple[tuple[int, RevenueBand], ...]] = (
    (1_000_000, RevenueBand.UNDER_1M),
    (10_000_000, RevenueBand.FROM_1M_TO_10M),
    (50_000_000, RevenueBand.FROM_10M_TO_50M),
    (250_000_000, RevenueBand.FROM_50M_TO_250M),
    (1_000_000_000, RevenueBand.FROM_250M_TO_1B),
)

#: Properties every HubSpot company carries and none of which says anything
#: about the company. **Distinct from unknown**, exactly as `ignored_fields`
#: is at the top level: *"we chose not to map this"* and *"we could not map
#: this"* must never look the same in a diagnosis.
_IGNORED_PROPERTIES: Final[frozenset[str]] = frozenset(
    {"hs_object_id", "createdate", "hs_lastmodifieddate", "lastmodifieddate"}
)


def _band_for(amount: int) -> RevenueBand:
    for ceiling, band in _REVENUE_BOUNDARIES:
        if amount < ceiling:
            return band
    return RevenueBand.OVER_1B


class HubSpotCompanyMapper(ProviderMapper):
    """One company record from a customer's HubSpot.

    ### The properties bag is checked, and that is not over-engineering

    `unexpected_fields` inspects **top-level** keys, which is the right
    place for every provider in this package because their payloads are
    shaped objects. **HubSpot's top level is fixed** — `id`, `properties`,
    timestamps, `archived` — and everything that can change lives one level
    down, inside `properties`. Declaring only the top level would leave this
    mapper reporting *no unknown fields* on the day HubSpot adds one, which
    is precisely the signal `known_fields` exists to produce.

    So the properties are checked here, against the same two sets and
    yielding the same `UNKNOWN_FIELD` reason. **The guarantee is preserved at
    the level where it is load-bearing for this vendor**, rather than left
    formally satisfied and practically decorative.

    ### Every value is a string

    HubSpot returns property values as strings — `"350"`, not `350`. The
    mappers beside this one can type-check their way past a bad value; this
    one has to parse, and **an unparseable value is rejected rather than
    dropped.** A company whose employee count arrived as `"about 350"` must
    produce a diagnosis, not a silently thinner record.

    ### What it deliberately does not translate

    **Nothing commercial.** *Is this already a customer*, *contract value*,
    *renewal date*, *opportunity stage* — the facts that make a CRM worth
    connecting for Epic D — have **no canonical attribute**, and
    `ClaimAttribute` says an RFC extends it. Inventing one here would put a
    vocabulary decision inside a translation file, which is the quietest
    place in the codebase to make one.

    **What is translated is what the canonical language already accepts**,
    and it turns out to be six of the seven firmographic attributes. A
    customer's CRM is a firmographic source today, and the strongest thing
    about that is what it does to identity: the `domain` hint below resolves
    a CRM account against the same entity Apollo and Crunchbase describe, so
    *"your CRM says 350 employees and CoreSignal says 412"* becomes one
    account with two sources rather than two accounts.
    """

    provider = "hubspot"
    known_fields = frozenset({"id", "properties", "createdAt", "updatedAt", "archived"})
    ignored_fields = frozenset({"_fixture"})

    #: Properties this mapper translates, and the attribute each becomes.
    #: A dict rather than branches: adding a property is a row, and the
    #: unknown-property check below reads its keys rather than repeating them.
    _TEXT_PROPERTIES: Final[dict[str, ClaimAttribute]] = {
        "name": ClaimAttribute.LEGAL_NAME,
        "industry": ClaimAttribute.INDUSTRY,
        "country": ClaimAttribute.COUNTRY,
    }
    _INTEGER_PROPERTIES: Final[dict[str, ClaimAttribute]] = {
        "numberofemployees": ClaimAttribute.EMPLOYEE_COUNT,
        "founded_year": ClaimAttribute.FOUNDED_YEAR,
    }
    #: Read for its hints and never claimed: a domain is how identity
    #: resolves, not something a company asserts about itself.
    _SUBJECT_PROPERTIES: Final[frozenset[str]] = frozenset({"domain"})

    def subject(self, payload: Mapping[str, Any]) -> SubjectHint:
        """**The domain is what merges a CRM account into an existing company.**

        Identity resolves on provider id, exact domain, or legal name plus
        country. A CRM's own record id is shared with nobody, so a mapper
        emitting only that would give every connected customer a private set
        of companies sitting beside the ones Signora already knows — the
        exact failure CoreSignal's mapper was corrected for at M12.1.5, and
        it would be worse here, because the duplicate would be the account
        the customer actually sells to.
        """
        properties = payload.get("properties", {})
        domain = str(properties.get("domain", "") or "")
        name = properties.get("name")
        return SubjectHint(
            provider_external_id=str(payload.get("id", "")),
            domain=domain or None,
            legal_name=str(name) if name else None,
        )

    def translate(
        self, payload: Mapping[str, Any], observed_at: datetime
    ) -> Iterator[MappedClaim | Rejection]:
        properties = payload.get("properties")
        if not isinstance(properties, Mapping):
            yield Rejection(
                RejectionReason.MISSING_REQUIRED_FIELD,
                "'properties' absent — a HubSpot company with no properties bag is "
                "a shape this mapper has never seen",
            )
            return

        yield from self._unexpected_properties(properties)

        for key, attribute in self._TEXT_PROPERTIES.items():
            value = properties.get(key)
            if isinstance(value, str) and value.strip():
                yield MappedClaim(attribute, value, observed_at)

        for key, attribute in self._INTEGER_PROPERTIES.items():
            number, rejection = self._integer(properties.get(key), key)
            if rejection is not None:
                yield rejection
            elif number is not None:
                yield MappedClaim(attribute, number, observed_at)

        revenue, rejection = self._integer(properties.get("annualrevenue"), "annualrevenue")
        if rejection is not None:
            yield rejection
        elif revenue is not None:
            if revenue < 0:
                yield Rejection(
                    RejectionReason.UNPARSEABLE_VALUE,
                    f"'annualrevenue' is negative ({revenue}); no band describes it",
                )
            else:
                yield MappedClaim(ClaimAttribute.REVENUE_BAND, _band_for(revenue), observed_at)

    def _unexpected_properties(self, properties: Mapping[str, Any]) -> Iterator[Rejection]:
        """Every property this mapper neither translates nor ignores."""
        translated = (
            set(self._TEXT_PROPERTIES)
            | set(self._INTEGER_PROPERTIES)
            | self._SUBJECT_PROPERTIES
            | {"annualrevenue"}
        )
        for key in properties:
            if key not in translated and key not in _IGNORED_PROPERTIES:
                yield Rejection(
                    reason=RejectionReason.UNKNOWN_FIELD,
                    detail=(
                        f"{self.provider} company carried property '{key}', which mapper "
                        f"v{self.version} does not know. A customer added a custom "
                        "property, or HubSpot added a default one."
                    ),
                )

    @staticmethod
    def _integer(raw: Any, path: str) -> tuple[int | None, Rejection | None]:
        """A HubSpot number, which arrives as a string.

        `None` and `""` are *absence* and produce neither a claim nor a
        rejection — an unset property is the commonest state of any CRM field
        and is not a defect. Anything else that will not parse is reported,
        because a value that was present and unreadable is a shape change.
        """
        if raw is None or (isinstance(raw, str) and not raw.strip()):
            return None, None
        try:
            return int(str(raw).strip()), None
        except ValueError:
            return None, Rejection(
                RejectionReason.UNPARSEABLE_VALUE,
                f"'{path}' is not a whole number: {raw!r}",
            )


__all__ = ["HubSpotCompanyMapper"]
