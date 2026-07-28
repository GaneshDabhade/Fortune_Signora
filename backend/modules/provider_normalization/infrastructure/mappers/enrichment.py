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
    ClaimAttribute,
    FundingValue,
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
        return SubjectHint(
            provider_external_id=str(org.get("uuid", "")), legal_name=org.get("name")
        )

    def translate(
        self, payload: Mapping[str, Any], observed_at: datetime
    ) -> Iterator[MappedClaim | Rejection]:
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


class CoreSignalMapper(ProviderMapper):
    provider = "coresignal"
    known_fields = frozenset({"company_id", "workforce", "hiring_by_function", "employee_changes"})
    ignored_fields = _FIXTURE_MARKER

    def subject(self, payload: Mapping[str, Any]) -> SubjectHint:
        return SubjectHint(provider_external_id=str(payload.get("company_id", "")))

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
