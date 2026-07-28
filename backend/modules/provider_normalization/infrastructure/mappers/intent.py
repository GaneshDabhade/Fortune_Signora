"""Mapper for behavioural intent.

**One claim per observed week, never a rollup.** Bombora's payload carries
a history; flattening it to "current score" would destroy the trajectory
M2.0 was built to model, and the Observation Engine would have to
reconstruct it from nothing.

The reporting lag is preserved rather than folded into the timestamp:
intent is delivered late, and a consumer needs to know that week 3's score
arrived in week 5 — otherwise "no intent this week" and "this week's intent
has not arrived yet" look identical.
"""

from __future__ import annotations

from collections.abc import Iterator, Mapping
from datetime import datetime, timedelta
from typing import Any

from modules.provider_normalization.domain.claim import SubjectHint
from modules.provider_normalization.domain.mapper import (
    MappedClaim,
    ProviderMapper,
    parse_date,
)
from modules.provider_normalization.domain.outcome import Rejection, RejectionReason
from modules.provider_normalization.domain.vocabulary import (
    ClaimAttribute,
    IntentSurgeValue,
    TrendDirection,
)


class BomboraMapper(ProviderMapper):
    provider = "bombora"
    known_fields = frozenset(
        {"company_id", "domain", "report_week", "reporting_lag_days", "topics"}
    )
    ignored_fields = frozenset({"_fixture"})

    def subject(self, payload: Mapping[str, Any]) -> SubjectHint:
        domain = payload.get("domain")
        return SubjectHint(
            provider_external_id=str(payload.get("company_id", "")),
            domain=str(domain) if domain else None,
        )

    def translate(
        self, payload: Mapping[str, Any], observed_at: datetime
    ) -> Iterator[MappedClaim | Rejection]:
        report_week, bad_week = parse_date(payload.get("report_week"), "report_week")
        if bad_week:
            yield bad_week

        for index, topic in enumerate(payload.get("topics", [])):
            name = topic.get("topic")
            history = topic.get("weekly_history")

            if not name:
                yield Rejection(RejectionReason.MISSING_REQUIRED_FIELD, f"topics[{index}].topic")
                continue

            if not isinstance(history, list) or not history:
                # Rejected rather than falling back to `surge_score`. A
                # single value silently replacing a trajectory is exactly
                # the information loss this mapper exists to prevent, and
                # it would be invisible downstream.
                yield Rejection(
                    RejectionReason.MISSING_REQUIRED_FIELD,
                    f"topics[{index}].weekly_history absent — intent without its trajectory "
                    "cannot distinguish a rising account from a cooling one",
                )
                continue

            try:
                trend = TrendDirection(str(topic.get("trend", "emerging")))
            except ValueError:
                yield Rejection(
                    RejectionReason.UNPARSEABLE_VALUE,
                    f"topics[{index}].trend {topic.get('trend')!r} is not a known direction",
                )
                continue

            # The history runs backwards from the report week: the last
            # entry is that week, the one before it the week prior.
            weeks = len(history)
            for offset, score in enumerate(history):
                if not isinstance(score, int):
                    yield Rejection(
                        RejectionReason.UNPARSEABLE_VALUE,
                        f"topics[{index}].weekly_history[{offset}] is not an integer",
                    )
                    continue

                week = (
                    report_week - timedelta(weeks=weeks - 1 - offset)
                    if report_week
                    else observed_at.date() - timedelta(weeks=weeks - 1 - offset)
                )
                yield MappedClaim(
                    ClaimAttribute.INTENT_TOPIC_SURGE,
                    IntentSurgeValue(
                        topic=str(name),
                        score=score,
                        observed_week=week,
                        # The trend the provider reported, not one this
                        # mapper computed. Deriving it here would be
                        # interpretation, and downstream has the whole
                        # series to derive it from anyway.
                        trend=trend,
                    ),
                    observed_at,
                )
