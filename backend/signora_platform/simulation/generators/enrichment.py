"""DEVELOPMENT FIXTURE generators for the four snapshot-style providers.

**None of these is an authentic vendor payload.** Each emits a
representative structure covering the *kind* of information the provider is
expected to expose, so the pipeline can be built and validated. Shapes must
be replaced when legitimate artifacts arrive; see the replacement procedure
in docs/architecture/provider-qualification.md.

The four live in one module because they are the same *kind* of generator —
a snapshot of facts about a company at a point in time. Bombora is separate
because it is categorically different: a trajectory, not a snapshot.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from signora_platform.simulation.generators.base import PayloadGenerator, _fixture_notice
from signora_platform.simulation.scenario import ScenarioEvent


class ApolloFixtureGenerator(PayloadGenerator):
    """Company profile, contacts, headcount, industry, revenue band."""

    provider = "apollo"

    def render(self, event: ScenarioEvent) -> Mapping[str, Any]:
        facts = event.facts
        return {
            "_fixture": _fixture_notice("Apollo"),
            "organization": {
                "id": event.subject,
                "name": facts.get("name", event.subject),
                "website_url": f"https://{facts.get('domain', 'example.com')}",
                "industry": facts.get("industry", "software"),
                "estimated_num_employees": facts.get("employees", 0),
                # A band rather than a figure: enrichment vendors report
                # ranges, and a pipeline built against an exact number would
                # need reworking when the real payload arrives.
                "annual_revenue_printed": facts.get("revenue_band", "$10M-$50M"),
                "founded_year": facts.get("founded"),
                "country": facts.get("country", "US"),
            },
            "contacts": [
                {
                    "id": f"{event.subject}-contact-{index}",
                    "title": title,
                    "seniority": "executive" if index == 0 else "manager",
                }
                for index, title in enumerate(facts.get("contact_titles", []))
            ],
        }


class BuiltWithFixtureGenerator(PayloadGenerator):
    """Technologies with first/last-detected dates.

    Detection *dates* rather than a flat list: a technology removal is only
    observable as a `last_detected` that has stopped advancing, and that is
    the signal a migration scenario depends on.
    """

    provider = "builtwith"

    def render(self, event: ScenarioEvent) -> Mapping[str, Any]:
        facts = event.facts
        return {
            "_fixture": _fixture_notice("BuiltWith"),
            "domain": facts.get("domain", "example.com"),
            "technologies": [
                {
                    "name": tech.get("name"),
                    "category": tech.get("category", "unknown"),
                    "first_detected": tech.get("first_detected"),
                    "last_detected": tech.get("last_detected"),
                    "is_live": tech.get("is_live", True),
                }
                for tech in facts.get("technologies", [])
            ],
        }


class CrunchbaseFixtureGenerator(PayloadGenerator):
    """Funding rounds, investors, stage, acquisitions."""

    provider = "crunchbase"

    def render(self, event: ScenarioEvent) -> Mapping[str, Any]:
        facts = event.facts
        return {
            "_fixture": _fixture_notice("Crunchbase"),
            "organization": {
                "uuid": event.subject,
                "name": facts.get("name", event.subject),
                # The registry's own homepage field. Added at M12.1.5, and not
                # cosmetically: without a domain, Crunchbase can only reach an
                # existing company by asserting the *same* legal name it already
                # carries — so two providers could agree about a name and could
                # never disagree, because disagreeing split them into two
                # companies. A registry that reports a homepage is also simply
                # what Crunchbase is.
                "website_url": f"https://{facts.get('domain', 'example.com')}",
                "funding_stage": facts.get("stage", "series_a"),
            },
            "funding_rounds": [
                {
                    "uuid": f"{event.subject}-round-{index}",
                    "investment_type": round_.get("type", "series_a"),
                    "money_raised_usd": round_.get("amount_usd"),
                    "announced_on": round_.get("announced_on"),
                    "investors": round_.get("investors", []),
                }
                for index, round_ in enumerate(facts.get("funding_rounds", []))
            ],
            "acquisitions": facts.get("acquisitions", []),
        }


class CoreSignalFixtureGenerator(PayloadGenerator):
    """Workforce metrics, hiring trends, employee changes.

    Carries a *delta* alongside the absolute count: headcount growth is the
    signal, and deriving it downstream would require the pipeline to
    remember the previous value — state the provider is better placed to
    report than the platform is to reconstruct.
    """

    provider = "coresignal"

    def render(self, event: ScenarioEvent) -> Mapping[str, Any]:
        facts = event.facts
        return {
            "_fixture": _fixture_notice("CoreSignal"),
            "company_id": event.subject,
            # A workforce provider identifies companies by their website; it
            # has to, or it could not tell two employers with the same name
            # apart. Added at M12.1.5 for the reason Crunchbase's was: without
            # it this provider matched on nothing any other provider emits, so
            # every hiring surge and every reduction resolved to a company of
            # its own — nameless, and invisible beside the account it described.
            "website": facts.get("domain", "example.com"),
            "workforce": {
                "employee_count": facts.get("employees", 0),
                "employee_count_change_90d": facts.get("employee_delta_90d", 0),
                "open_positions": facts.get("open_roles", 0),
            },
            "hiring_by_function": facts.get("hiring_by_function", {}),
            "employee_changes": [
                {
                    "type": change.get("type", "hire"),
                    "title": change.get("title"),
                    "seniority": change.get("seniority", "manager"),
                    "occurred_on": change.get("occurred_on"),
                }
                for change in facts.get("employee_changes", [])
            ],
        }
