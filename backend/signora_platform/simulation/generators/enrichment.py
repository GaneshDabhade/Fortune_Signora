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

import hashlib
import re
from collections.abc import Mapping
from typing import Any

from signora_platform.simulation.generators.base import PayloadGenerator, _fixture_notice
from signora_platform.simulation.scenario import ScenarioEvent

#: Non-name characters, for building an address out of a person's name.
_NOT_A_NAME_CHARACTER = re.compile(r"[^a-z]+")


def _person_id(company: str, ref: str) -> str:
    """A provider-stable, **opaque** identifier for one person.

    Derived rather than stored, for the two reasons that decide where a field
    lives. **Nothing downstream may parse it** — a readable id invites a
    consumer to recover the company or the role from it, and then the id has
    quietly become a second copy of facts the payload already carries. And a
    dataset holding thirty-six hand-written opaque ids is thirty-six chances
    to paste one twice, where a derivation cannot collide unless the inputs do.

    `hashlib` rather than `hash()`: Python's is seeded per process, and a
    provider identifier that changed between two runs of the same scenario
    would make replay impossible — the hidden-input defect the platform has
    already eliminated five times.
    """
    digest = hashlib.sha256(f"{company}/{ref}".encode()).hexdigest()
    return f"apollo_{digest[:20]}"


def _email(full_name: str, domain: str) -> str:
    """`first.last@domain`, on the company's **own** domain.

    Derived from the two fields that decide it, so an address can never point
    at a company the person does not work for — which is the one way a fixture
    address could become misleading rather than merely fictional.
    """
    parts = [_NOT_A_NAME_CHARACTER.sub("", part.casefold()) for part in full_name.split()]
    local = ".".join(part for part in parts if part)
    return f"{local}@{domain}"


def _reports_to(company: str, person: Mapping[str, Any]) -> dict[str, str] | None:
    """The person's reporting line, with the vendor's own confidence on it.

    **Absent for whoever the roster puts at the top**, which is the honest
    shape: a company's most senior person has no manager the vendor can see,
    and an edge pointing at nothing would be worse than none.
    """
    manager = person.get("reports_to")
    if not manager:
        return None
    return {
        "person_id": _person_id(company, str(manager)),
        # Defaulted nowhere else. A dataset entry that names a manager and no
        # confidence is a dataset defect, and the mapper rejects it rather
        # than showing a guess as a confirmed line.
        "source": str(person.get("reports_to_source", "")),
    }


class ApolloFixtureGenerator(PayloadGenerator):
    """Company profile, contacts, headcount, industry, revenue band.

    ### The contacts carry an identity from `playground@4` onward

    **Until [TASK-429](../../../../docs/BACKLOG.md) this generator emitted a
    title and a seniority band and nothing else**, and the comment one class
    down said what that cost: the people were *"nameless, and invisible beside
    the account"*. `people` felt it as a duplicate-person defect it had
    documented rather than fixed — **every arrival minted a new subject,
    because there was no identifier to match one against.**

    ⛔ **A company whose dataset entry has no `people` emits no contacts**, and
    that is deliberate rather than defensive. `playground@2`'s twelve entities
    are **real companies**, so a named individual must never be renderable from
    it — an invented person with an invented stance attached to a real employer
    is a fabricated claim about a real business. **`playground@2` supplies no
    `people` and therefore produces no named contact**, and a test pins it.
    """

    provider = "apollo"

    def render(self, event: ScenarioEvent) -> Mapping[str, Any]:
        facts = event.facts
        domain = str(facts.get("domain", "example.com"))
        return {
            "_fixture": _fixture_notice("Apollo"),
            "organization": {
                "id": event.subject,
                "name": facts.get("name", event.subject),
                "website_url": f"https://{domain}",
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
                    "person_id": _person_id(event.subject, str(person.get("ref", ""))),
                    "full_name": person.get("full_name"),
                    "title": person.get("title"),
                    # The provider's own band, per person. It used to be
                    # positional — `executive` for the first contact and
                    # `manager` for the rest — which made every leadership rule
                    # unreachable below index 0, because the taxonomy qualifies
                    # `executive`, `vp` and `director` and nothing else.
                    "seniority": person.get("seniority"),
                    # **The join key.** A contact provider that did not say
                    # which company it meant would resolve every person to an
                    # entity of its own, which is exactly what CoreSignal did
                    # to whole companies before M12.1.5.
                    "company_domain": domain,
                    "email": _email(str(person.get("full_name", "")), domain),
                    "first_seen": person.get("first_seen"),
                    "last_seen": person.get("last_seen"),
                    # **The org chart, and the only relationship fact a
                    # contact vendor can author** — an org chart is a fact
                    # about the company, which it observes; a stance is a fact
                    # about the customer's deal, which it has never seen
                    # (C-1509). The dataset names the manager by `ref`; the
                    # opaque id is derived here so the two sides of an edge
                    # cannot drift.
                    "reports_to": _reports_to(event.subject, person),
                }
                for person in facts.get("people", [])
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
