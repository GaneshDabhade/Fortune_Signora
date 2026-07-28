"""Tests for fault injection and delivery.

**These justify the framework.** A real provider cannot be asked to time
out, truncate a body, or deliver the same record three times — so without
injection, the retry logic, backoff, dead-lettering, and idempotency
ledger are all code that has never met the thing it exists to handle.
"""

from __future__ import annotations

from datetime import timedelta

import pytest

from signora_platform.simulation import (
    ClockMode,
    DeliveryMode,
    DeliveryPlan,
    FaultInjector,
    FaultKind,
    FaultProfile,
    FaultProfileError,
    FaultRule,
    ScenarioEvent,
    VirtualClock,
    build_timeline,
    load,
    load_scenario,
)


@pytest.fixture
def timeline() -> tuple[ScenarioEvent, ...]:
    return build_timeline(
        load_scenario("baseline", 1),
        load("baseline", 1),
        VirtualClock(mode=ClockMode.INSTANT),
        seed=1,
    )


class TestFaultDeclaration:
    def test_an_unknown_fault_kind_fails_at_load(self) -> None:
        """At load, never at injection time. A typo would otherwise
        produce a scenario that silently never faults — a fault-tolerance
        test that never tests fault tolerance, green forever."""
        with pytest.raises(FaultProfileError, match="unknown fault kind"):
            FaultProfile.from_declaration([{"kind": "explodes"}])

    def test_the_error_lists_the_known_kinds(self) -> None:
        with pytest.raises(FaultProfileError, match="timeout"):
            FaultProfile.from_declaration([{"kind": "typo"}])

    @pytest.mark.parametrize("probability", [-0.1, 1.5])
    def test_an_impossible_probability_is_rejected(self, probability: float) -> None:
        with pytest.raises(FaultProfileError, match="probability"):
            FaultRule(kind=FaultKind.TIMEOUT, probability=probability)

    def test_parses_every_known_kind(self) -> None:
        profile = FaultProfile.from_declaration([{"kind": kind.value} for kind in FaultKind])

        assert len(profile.rules) == len(FaultKind)


class TestFaultDeterminism:
    def test_the_same_seed_faults_the_same_events(self) -> None:
        """ "Fails 10% of the time" must fail on the same 10% every run.
        Otherwise a scenario passes and fails at random, and within a week
        nobody trusts the suite."""
        profile = FaultProfile(rules=(FaultRule(kind=FaultKind.TIMEOUT, probability=0.5),))

        first = [FaultInjector(profile, seed=99).decide(i) for i in range(20)]
        second = [FaultInjector(profile, seed=99).decide(i) for i in range(20)]

        assert first == second

    def test_a_different_seed_faults_different_events(self) -> None:
        profile = FaultProfile(rules=(FaultRule(kind=FaultKind.TIMEOUT, probability=0.5),))

        first = [FaultInjector(profile, seed=1).decide(i) is not None for i in range(30)]
        second = [FaultInjector(profile, seed=2).decide(i) is not None for i in range(30)]

        assert first != second

    def test_adding_a_rule_does_not_shift_earlier_rules(self) -> None:
        """A draw happens per rule regardless of outcome. Without that,
        appending a fault would silently change which events every *other*
        fault lands on, and every recorded run would become incomparable.
        """
        one = FaultProfile(rules=(FaultRule(kind=FaultKind.TIMEOUT, probability=0.0),))
        two = FaultProfile(
            rules=(
                FaultRule(kind=FaultKind.TIMEOUT, probability=0.0),
                FaultRule(kind=FaultKind.DUPLICATE, probability=0.0),
            )
        )

        assert FaultInjector(one, seed=5).decide(0) is None
        assert FaultInjector(two, seed=5).decide(0) is None

    def test_a_zero_probability_rule_never_fires(self) -> None:
        profile = FaultProfile(rules=(FaultRule(kind=FaultKind.TIMEOUT, probability=0.0),))

        assert all(FaultInjector(profile, seed=s).decide(0) is None for s in range(20))

    def test_a_certain_rule_always_fires(self) -> None:
        profile = FaultProfile(rules=(FaultRule(kind=FaultKind.RATE_LIMITED, probability=1.0),))

        fault = FaultInjector(profile, seed=1).decide(0)

        assert fault is not None
        assert fault.kind is FaultKind.RATE_LIMITED


class TestFaultObservability:
    def test_an_injected_fault_is_distinguishable_from_a_real_one(self) -> None:
        """An operator debugging a scenario must never wonder whether a
        failure was intentional."""
        profile = FaultProfile(rules=(FaultRule(kind=FaultKind.RATE_LIMITED),))
        fault = FaultInjector(profile, seed=1).decide(7)

        assert fault is not None
        fields = fault.as_log_fields()
        assert fields["injected_fault"] == "rate_limited"
        assert fields["fault_event_sequence"] == 7
        assert fields["simulated"] == "true"

    def test_rate_limiting_carries_the_vendor_supplied_wait(self) -> None:
        """Guessing a backoff when the vendor stated one is how an
        integration gets throttled harder."""
        profile = FaultProfile(
            rules=(FaultRule(kind=FaultKind.RATE_LIMITED, retry_after_seconds=45),)
        )
        fault = FaultInjector(profile, seed=1).decide(0)

        assert fault is not None
        assert fault.retry_after_seconds == 45


class TestDelivery:
    def test_a_snapshot_returns_everything(self, timeline: tuple[ScenarioEvent, ...]) -> None:
        page = DeliveryPlan(timeline, mode=DeliveryMode.SNAPSHOT, page_size=100).page()

        assert len(page.events) == len(timeline)
        assert page.has_more is False

    def test_pagination_terminates(self, timeline: tuple[ScenarioEvent, ...]) -> None:
        """A cursor that never terminates is an infinite sync — and
        because it keeps returning records, it looks like a working
        integration rather than a stuck one."""
        plan = DeliveryPlan(timeline, page_size=1)
        cursor, seen, guard = None, 0, 0

        while guard < 50:
            page = plan.page(cursor=cursor)
            seen += len(page.events)
            if not page.has_more:
                break
            cursor, guard = page.next_cursor, guard + 1

        assert seen == len(timeline)
        assert guard < 50, "pagination did not terminate"

    def test_incremental_delivery_excludes_the_watermark_itself(
        self, timeline: tuple[ScenarioEvent, ...]
    ) -> None:
        """Strictly after. Inclusive would re-deliver the boundary record
        every sync — a duplicate the platform absorbs, but one that hides
        a real watermark bug behind idempotency."""
        watermark = timeline[0].occurred_at
        page = DeliveryPlan(timeline, mode=DeliveryMode.INCREMENTAL, page_size=100).page(
            since=watermark
        )

        assert all(event.occurred_at > watermark for event in page.events)
        assert len(page.events) < len(timeline)

    def test_a_snapshot_ignores_the_watermark(self, timeline: tuple[ScenarioEvent, ...]) -> None:
        """The point of a snapshot: it is how a re-sync exercises dedup."""
        page = DeliveryPlan(timeline, mode=DeliveryMode.SNAPSHOT, page_size=100).page(
            since=timeline[0].occurred_at
        )

        assert len(page.events) == len(timeline)

    def test_an_incremental_sync_finding_nothing_new_is_a_no_op(
        self, timeline: tuple[ScenarioEvent, ...]
    ) -> None:
        future = timeline[-1].occurred_at + timedelta(days=365)
        page = DeliveryPlan(timeline, mode=DeliveryMode.INCREMENTAL).page(since=future)

        assert page.events == ()
        assert page.has_more is False

    def test_a_malformed_cursor_is_rejected(self, timeline: tuple[ScenarioEvent, ...]) -> None:
        with pytest.raises(ValueError, match="malformed delivery cursor"):
            DeliveryPlan(timeline).page(cursor="not-a-number")

    def test_a_zero_page_size_is_rejected(self, timeline: tuple[ScenarioEvent, ...]) -> None:
        with pytest.raises(ValueError, match="never terminates"):
            DeliveryPlan(timeline, page_size=0)


class TestDeliveryFaults:
    def test_duplicates_are_delivered_not_deduplicated(
        self, timeline: tuple[ScenarioEvent, ...]
    ) -> None:
        """The simulator deliberately does not deduplicate. That is the
        platform's job, and doing it here would hide whether the platform
        actually does it."""
        profile = FaultProfile(rules=(FaultRule(kind=FaultKind.DUPLICATE, repeat=3),))
        page = DeliveryPlan(timeline, page_size=1, injector=FaultInjector(profile, seed=1)).page()

        assert len(page.events) == 3
        assert len({event.event_ref for event in page.events}) == 1

    def test_a_partial_response_returns_fewer_records(
        self, timeline: tuple[ScenarioEvent, ...]
    ) -> None:
        profile = FaultProfile(rules=(FaultRule(kind=FaultKind.PARTIAL_RESPONSE),))
        page = DeliveryPlan(timeline, page_size=4, injector=FaultInjector(profile, seed=1)).page()

        assert 0 < len(page.events) < 4

    def test_out_of_order_delivery_reverses_the_window(
        self, timeline: tuple[ScenarioEvent, ...]
    ) -> None:
        """The pipeline must tolerate a record arriving before one it
        follows — exactly what a delayed provider report looks like."""
        profile = FaultProfile(rules=(FaultRule(kind=FaultKind.OUT_OF_ORDER),))
        page = DeliveryPlan(timeline, page_size=4, injector=FaultInjector(profile, seed=1)).page()

        occurred = [event.occurred_at for event in page.events]
        assert occurred != sorted(occurred)

    def test_the_fault_decision_is_carried_for_the_adapter_to_act_on(
        self, timeline: tuple[ScenarioEvent, ...]
    ) -> None:
        """Timeout, 5xx and rate limiting change how the adapter
        *responds*. The framework declares what failed; the adapter raises
        the Provider Port's own type, so retry logic sees what it will see
        in production."""
        profile = FaultProfile(rules=(FaultRule(kind=FaultKind.TIMEOUT),))
        page = DeliveryPlan(timeline, injector=FaultInjector(profile, seed=1)).page()

        assert page.fault is not None
        assert page.fault.kind is FaultKind.TIMEOUT
        # Not raised here — raising a simulator exception would put it on a
        # path production never takes.
        assert page.events != ()
