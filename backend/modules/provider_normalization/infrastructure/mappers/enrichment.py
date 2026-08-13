"""Mappers for the four snapshot-style providers.

**These translate the current DEVELOPMENT FIXTURE shapes.** When authentic
payloads arrive, only these files change — the canonical vocabulary is the
platform contract and does not move with a vendor.

Each mapper reads only its own vendor's shape. No vendor field name appears
anywhere else in the codebase (AC-23).
"""

from __future__ import annotations

from collections.abc import Iterator, Mapping
from datetime import datetime
from typing import Any

from modules.provider_normalization.domain.claim import SubjectHint
from modules.provider_normalization.domain.mapper import (
    MappedClaim,
    ProviderMapper,
    parse_date,
    require,
)
from modules.provider_normalization.domain.outcome import Rejection, RejectionReason
from modules.provider_normalization.domain.vocabulary import (
    AcquisitionValue,
    ClaimAttribute,
    FundingValue,
    PersonIdentityValue,
    RevenueBand,
    RoleChangeValue,
    RoleDirection,
    TechnologyValue,
)

#: Fixture bands → canonical bands. An unrecognised band is rejected rather
#: than bucketed into the nearest one: silently widening a revenue estimate
#: is interpretation, and this layer does not interpret.
_REVENUE_BANDS: dict[str, RevenueBand] = {
    "$0-$1M": RevenueBand.UNDER_1M,
    "$1M-$10M": RevenueBand.FROM_1M_TO_10M,
    "$10M-$50M": RevenueBand.FROM_10M_TO_50M,
    "$50M-$250M": RevenueBand.FROM_50M_TO_250M,
    "$250M-$1B": RevenueBand.FROM_250M_TO_1B,
    "$1B+": RevenueBand.OVER_1B,
}

#: Every mapper ignores the fixture marker. It disappears when fixtures are
#: replaced, and its absence is how a completed replacement is confirmed.
_FIXTURE_MARKER = frozenset({"_fixture"})


class ApolloMapper(ProviderMapper):
    provider = "apollo"
    known_fields = frozenset({"organization", "contacts"})
    ignored_fields = _FIXTURE_MARKER

    def subject(self, payload: Mapping[str, Any]) -> SubjectHint:
        org = payload.get("organization", {})
        website = str(org.get("website_url", ""))
        return SubjectHint(
            provider_external_id=str(org.get("id", "")),
            domain=website.removeprefix("https://").removeprefix("http://") or None,
            legal_name=org.get("name"),
        )

    def translate(
        self, payload: Mapping[str, Any], observed_at: datetime
    ) -> Iterator[MappedClaim | Rejection]:
        org, missing = require(payload, "organization")
        if missing:
            yield missing
            return

        for path, attribute in (
            ("estimated_num_employees", ClaimAttribute.EMPLOYEE_COUNT),
            ("founded_year", ClaimAttribute.FOUNDED_YEAR),
        ):
            value = org.get(path)
            if isinstance(value, int):
                yield MappedClaim(attribute, value, observed_at)

        for path, attribute in (
            ("industry", ClaimAttribute.INDUSTRY),
            ("country", ClaimAttribute.COUNTRY),
            ("name", ClaimAttribute.LEGAL_NAME),
        ):
            value = org.get(path)
            if isinstance(value, str) and value:
                yield MappedClaim(attribute, value, observed_at)

        printed = org.get("annual_revenue_printed")
        if printed is not None:
            band = _REVENUE_BANDS.get(str(printed))
            if band is None:
                yield Rejection(
                    RejectionReason.UNPARSEABLE_VALUE,
                    f"revenue band {printed!r} is not in the canonical band set",
                )
            else:
                yield MappedClaim(ClaimAttribute.REVENUE_BAND, band, observed_at)

        # **`contacts` has been declared in `known_fields` since M2.2 and never
        # translated** — the same shape `acquisitions` was found in one mapper
        # down, and with the same consequence: the field arrived, the strict
        # unknown-field check accepted it, and nothing downstream could ever see
        # it. `people` recorded the cost as a duplicate-person defect it could
        # not fix, because the identifier that would have fixed it stopped here.
        yield from self._identities(
            payload.get("contacts", []),
            company_domain=self.subject(payload).domain,
            observed_at=observed_at,
        )

    def _identities(
        self, contacts: Any, *, company_domain: str | None, observed_at: datetime
    ) -> Iterator[MappedClaim | Rejection]:
        """Contacts become identities, **and a contact at another company does not.**

        ⛔ **`email` is deliberately not lifted into the vocabulary.** The
        provider supplies one and the fixture emits one, because a fixture that
        omitted a field the vendor returns would mislead whoever swaps it for a
        real payload. **The platform declines to carry it**: `people` holds no
        direct identifier by specification (`C-221`), nothing has asked for an
        address, and a canonical attribute is the wrong place to discover later
        that nobody wanted it. **`person_ref` is what joins a person across
        arrivals, and it does that without being one.** If `C-203` is ruled the
        other way, this becomes one field.
        """
        for index, contact in enumerate(contacts):
            # **The join key, checked rather than assumed.** A contact provider
            # keys people by employer, and a roster entry naming a different
            # company is a payload assembled wrongly — accepting it would attach
            # somebody to an account they have never worked at, which is the one
            # error on this screen a seller would act on and could not detect.
            stated = contact.get("company_domain")
            if stated is not None and company_domain is not None and stated != company_domain:
                yield Rejection(
                    RejectionReason.UNPARSEABLE_VALUE,
                    f"contacts[{index}].company_domain {stated!r} is not this payload's "
                    f"company {company_domain!r} — a roster entry for another employer",
                )
                continue

            # ⛔ **A contact with no provider identifier is rejected rather than
            # given a synthesised one.** Minting a key here would put a
            # *platform* invention behind a *provider*'s field name, and
            # `people` would then join two strangers on it and have no way to
            # tell that it had.
            person_ref = contact.get("person_id")
            if not person_ref:
                yield Rejection(
                    RejectionReason.MISSING_REQUIRED_FIELD,
                    f"contacts[{index}].person_id — an identity with no identifier "
                    "is the duplicate-person defect this attribute exists to end",
                )
                continue

            full_name = contact.get("full_name")
            if not full_name:
                yield Rejection(
                    RejectionReason.MISSING_REQUIRED_FIELD, f"contacts[{index}].full_name"
                )
                continue

            title = contact.get("title")
            if not title:
                yield Rejection(
                    RejectionReason.MISSING_REQUIRED_FIELD, f"contacts[{index}].title"
                )
                continue

            first_seen, bad_first = parse_date(
                contact.get("first_seen"), f"contacts[{index}].first_seen"
            )
            last_seen, bad_last = parse_date(
                contact.get("last_seen"), f"contacts[{index}].last_seen"
            )
            for problem in (bad_first, bad_last):
                if problem:
                    yield problem

            yield MappedClaim(
                ClaimAttribute.PERSON_IDENTITY,
                PersonIdentityValue(
                    person_ref=str(person_ref),
                    full_name=str(full_name),
                    title=str(title),
                    # Carried verbatim. The band decides whether a leadership
                    # rule fires, and re-deriving it from the title here would
                    # put a second seniority vocabulary in the layer whose whole
                    # job is to carry the provider's.
                    seniority=str(contact.get("seniority", "unknown")),
                    first_seen=first_seen,
                    last_seen=last_seen,
                ),
                observed_at,
            )


class BuiltWithMapper(ProviderMapper):
    provider = "builtwith"
    known_fields = frozenset({"domain", "technologies"})
    ignored_fields = _FIXTURE_MARKER

    def subject(self, payload: Mapping[str, Any]) -> SubjectHint:
        domain = str(payload.get("domain", ""))
        return SubjectHint(provider_external_id=domain, domain=domain or None)

    def translate(
        self, payload: Mapping[str, Any], observed_at: datetime
    ) -> Iterator[MappedClaim | Rejection]:
        for index, tech in enumerate(payload.get("technologies", [])):
            name = tech.get("name")
            if not name:
                yield Rejection(
                    RejectionReason.MISSING_REQUIRED_FIELD, f"technologies[{index}].name"
                )
                continue

            first_seen, bad_first = parse_date(
                tech.get("first_detected"), f"technologies[{index}].first_detected"
            )
            last_seen, bad_last = parse_date(
                tech.get("last_detected"), f"technologies[{index}].last_detected"
            )
            for problem in (bad_first, bad_last):
                if problem:
                    yield problem

            value = TechnologyValue(
                name=str(name),
                category=str(tech.get("category", "unknown")),
                first_seen=first_seen,
                last_seen=last_seen,
            )
            # A removal is only observable as is_live going false. Emitting
            # both attributes from one field preserves that distinction
            # rather than making downstream infer it from a boolean.
            attribute = (
                ClaimAttribute.TECHNOLOGY_DETECTED
                if tech.get("is_live", True)
                else ClaimAttribute.TECHNOLOGY_REMOVED
            )
            yield MappedClaim(attribute, value, observed_at)


class CrunchbaseMapper(ProviderMapper):
    provider = "crunchbase"
    known_fields = frozenset({"organization", "funding_rounds", "acquisitions"})
    ignored_fields = _FIXTURE_MARKER

    def subject(self, payload: Mapping[str, Any]) -> SubjectHint:
        org = payload.get("organization", {})
        website = str(org.get("website_url", ""))
        return SubjectHint(
            provider_external_id=str(org.get("uuid", "")),
            # **Added at M12.1.5, and it closes a real gap.** Identity resolves
            # on provider id, exact domain, or legal name *plus* country. With
            # no domain, a registry could reach an existing company only by
            # naming it identically — so `DISPUTED` was unreachable through this
            # provider by construction: a differing name produced a second
            # company rather than a disagreement about one.
            domain=website.removeprefix("https://").removeprefix("http://") or None,
            legal_name=org.get("name"),
        )

    def translate(
        self, payload: Mapping[str, Any], observed_at: datetime
    ) -> Iterator[MappedClaim | Rejection]:
        # A company registry's primary fact is what the company is *called*.
        # Claimed rather than only hinted, so the naming resolver has a second
        # source to agree or disagree with — until M12.1.5 exactly one mapper
        # emitted this attribute, which made `AGREED` and `DISPUTED` states the
        # product could render but the pipeline could never produce.
        name = payload.get("organization", {}).get("name")
        if isinstance(name, str) and name:
            yield MappedClaim(ClaimAttribute.LEGAL_NAME, name, observed_at)

        for index, round_ in enumerate(payload.get("funding_rounds", [])):
            announced, bad = parse_date(
                round_.get("announced_on"), f"funding_rounds[{index}].announced_on"
            )
            if bad:
                yield bad
            yield MappedClaim(
                ClaimAttribute.FUNDING_ROUND,
                FundingValue(
                    round_type=str(round_.get("investment_type", "unknown")),
                    amount=round_.get("money_raised_usd"),
                    # Currency preserved even though the fixture field says
                    # usd: an amount without its unit is a number that will
                    # eventually be wrong.
                    currency="USD" if round_.get("money_raised_usd") is not None else None,
                    announced_on=announced,
                    investors=tuple(str(i) for i in round_.get("investors", [])),
                ),
                observed_at,
            )

        # **Declared in `known_fields` since M2.2 and never translated.**
        # Everything downstream of this claim already existed — the
        # `acquisition_announced` rule, its taxonomy entry, the
        # `consolidation_underway` signal and its weight in the scoring model —
        # so an acquisition has been detectable in every layer except the one
        # that had to produce the evidence. The whole chain was unreachable.
        for index, acquisition in enumerate(payload.get("acquisitions", [])):
            counterparty = acquisition.get("acquiree_name")
            if not counterparty:
                yield Rejection(
                    RejectionReason.MISSING_REQUIRED_FIELD,
                    f"acquisitions[{index}].acquiree_name — an acquisition with no "
                    "counterparty names nothing a seller could act on",
                )
                continue

            announced, bad_date = parse_date(
                acquisition.get("announced_on"), f"acquisitions[{index}].announced_on"
            )
            if bad_date:
                yield bad_date

            yield MappedClaim(
                ClaimAttribute.ACQUISITION,
                AcquisitionValue(
                    counterparty=str(counterparty),
                    announced_on=announced,
                    amount=acquisition.get("price_usd"),
                    currency="USD" if acquisition.get("price_usd") is not None else None,
                ),
                observed_at,
            )


class CoreSignalMapper(ProviderMapper):
    provider = "coresignal"
    known_fields = frozenset(
        {"company_id", "website", "workforce", "hiring_by_function", "employee_changes"}
    )
    ignored_fields = _FIXTURE_MARKER

    def subject(self, payload: Mapping[str, Any]) -> SubjectHint:
        """**The domain is what makes workforce evidence reach a company.**

        Added at M12.1.5. Identity resolves on provider id, exact domain, or
        legal name plus country, and this mapper emitted only the first — its
        own key, which no other provider shares. So every hiring surge, every
        reduction and every executive appointment resolved to an entity of this
        provider's own, carrying no name, no domain and no firmographics.

        The account a seller could see and the account the workforce evidence
        described were **two different rows**, and the interesting one was the
        one with no name on it.
        """
        website = str(payload.get("website", ""))
        return SubjectHint(
            provider_external_id=str(payload.get("company_id", "")),
            domain=website.removeprefix("https://").removeprefix("http://") or None,
        )

    def translate(
        self, payload: Mapping[str, Any], observed_at: datetime
    ) -> Iterator[MappedClaim | Rejection]:
        workforce, missing = require(payload, "workforce")
        if missing:
            yield missing
        else:
            for path, attribute in (
                ("employee_count", ClaimAttribute.EMPLOYEE_COUNT),
                ("employee_count_change_90d", ClaimAttribute.HEADCOUNT_CHANGE),
                ("open_positions", ClaimAttribute.OPEN_ROLES),
            ):
                value = workforce.get(path)
                if isinstance(value, int):
                    yield MappedClaim(attribute, value, observed_at)

        for index, change in enumerate(payload.get("employee_changes", [])):
            title = change.get("title")
            if not title:
                yield Rejection(
                    RejectionReason.MISSING_REQUIRED_FIELD, f"employee_changes[{index}].title"
                )
                continue
            raw_direction = str(change.get("type", "hire"))
            direction = {
                "hire": RoleDirection.JOINED,
                "departure": RoleDirection.LEFT,
                "promotion": RoleDirection.PROMOTED,
            }.get(raw_direction)
            if direction is None:
                yield Rejection(
                    RejectionReason.UNPARSEABLE_VALUE,
                    f"employee_changes[{index}].type {raw_direction!r} is not a known direction",
                )
                continue
            yield MappedClaim(
                ClaimAttribute.ROLE_CHANGE,
                RoleChangeValue(
                    title=str(title),
                    seniority=str(change.get("seniority", "unknown")),
                    direction=direction,
                ),
                observed_at,
            )
