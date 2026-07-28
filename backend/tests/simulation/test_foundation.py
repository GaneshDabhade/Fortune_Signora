"""Tests for the simulation framework's foundation: safety, clock, dataset.

These cover the pieces that exist before any provider generator does, and
that are provider-agnostic by design — Provider Independence (principle 9)
means qualification outcomes change which generators exist, never whether
the framework works.
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from signora_platform.simulation import (
    ClockMode,
    DatasetError,
    SimulationForbiddenError,
    VirtualClock,
    content_hash,
    enforce,
    evaluate,
    is_permitted,
    load,
)


class TestSafetyGuards:
    """The highest-risk control in M2.0. A simulator active in production
    fabricates customer intelligence — a trust failure, not a bug."""

    @pytest.mark.parametrize(
        "environment", ["local", "test", "ci", "development", "production-local"]
    )
    def test_permits_known_non_production_environments(self, environment: str) -> None:
        assert is_permitted(environment) is True

    @pytest.mark.parametrize(
        "environment",
        ["production", "prod", "", "  ", "staging", "productin", "PRODUCTION_EU"],
    )
    def test_fails_closed_on_anything_else(self, environment: str) -> None:
        """An unrecognised value is not an implicit "not production".

        A typo, an empty string, and a new environment nobody thought to
        add are all treated as production — that reasoning is what stops a
        new environment silently gaining permission it was never granted.
        """
        assert is_permitted(environment) is False

    def test_refuses_to_start_in_production(self) -> None:
        with pytest.raises(SimulationForbiddenError) as exc_info:
            enforce(enabled=True, environment="production")

        # The message must name the consequence, not just the rule — an
        # operator hitting this at 2am needs to know why it matters.
        assert "fabricates customer intelligence" in str(exc_info.value)

    def test_permits_production_only_under_an_explicit_override(self) -> None:
        status = enforce(enabled=True, environment="production", override=True)

        assert status.enabled is True
        assert status.override_in_use is True

    def test_an_override_in_force_still_alerts(self) -> None:
        """An override is a deliberate, temporary act. The dangerous
        version is one applied during an incident and never removed, so it
        keeps alerting for as long as it is in force."""
        status = evaluate(enabled=True, environment="production", override=True)

        assert status.should_alert is True

    def test_a_disabled_simulator_never_alerts_or_raises(self) -> None:
        status = enforce(enabled=False, environment="production")

        assert status.should_alert is False

    def test_a_permitted_environment_does_not_alert(self) -> None:
        assert evaluate(enabled=True, environment="local").should_alert is False


class TestVirtualClock:
    def test_instant_mode_produces_timestamps_independent_of_real_duration(self) -> None:
        """The determinism property that matters: a four-week scenario
        yields identical timestamps whether generation took a millisecond
        or a minute."""
        clock = VirtualClock(mode=ClockMode.INSTANT)
        start = clock.now

        assert clock.at(timedelta(weeks=4)) == start + timedelta(weeks=4)

    async def test_advance_moves_logical_time(self) -> None:
        clock = VirtualClock(mode=ClockMode.INSTANT)
        before = clock.now

        await clock.advance(timedelta(days=7))

        assert clock.now == before + timedelta(days=7)

    async def test_instant_mode_does_not_sleep(self) -> None:
        """A scenario spanning weeks must complete in milliseconds, or CI
        cannot run it."""
        import time

        clock = VirtualClock(mode=ClockMode.INSTANT)
        started = time.monotonic()

        await clock.advance(timedelta(weeks=4))

        assert time.monotonic() - started < 0.5

    async def test_logical_time_never_moves_backwards(self) -> None:
        """Late arrival is expressed by emitting an earlier `occurred_at`,
        not by rewinding the clock — rewinding would corrupt every
        subsequent timestamp in the run."""
        clock = VirtualClock()

        with pytest.raises(ValueError, match="does not move backwards"):
            await clock.advance(timedelta(days=-1))

    def test_a_naive_epoch_is_rejected(self) -> None:
        with pytest.raises(ValueError, match="timezone-aware"):
            VirtualClock(epoch=datetime(2026, 1, 1))  # noqa: DTZ001 - the point of the test

    def test_accelerated_mode_requires_a_multiplier(self) -> None:
        with pytest.raises(ValueError, match="multiplier"):
            VirtualClock(mode=ClockMode.ACCELERATED, multiplier=1.0)

    def test_describes_itself_for_the_replay_record(self) -> None:
        described = VirtualClock(mode=ClockMode.ACCELERATED, multiplier=60).describe()

        assert described["mode"] == "accelerated"
        assert described["multiplier"] == 60


class TestDatasetStore:
    def test_loads_a_published_dataset(self) -> None:
        dataset = load("baseline", 1)

        assert dataset.reference == "baseline@1"
        assert dataset.entity("acme-corp")["name"] == "Acme Corp"

    def test_a_missing_version_fails_at_load_not_at_run(self) -> None:
        """Refusing to start beats emitting an empty scenario, which is
        indistinguishable from a pipeline that consumed everything and
        produced nothing."""
        with pytest.raises(DatasetError, match="not found"):
            load("baseline", 99)

    def test_a_missing_entity_names_the_dataset(self) -> None:
        with pytest.raises(DatasetError, match="has no entity"):
            load("baseline", 1).entity("does-not-exist")

    def test_a_mutated_dataset_is_rejected(self, tmp_path: Path) -> None:
        """This is what makes "immutable once published" enforceable
        rather than aspirational. A silently-edited dataset invalidates
        every historical comparison built on it."""
        entities = {"a": {"name": "A"}}
        (tmp_path / "probe@1.json").write_text(
            json.dumps({"content_hash": "deadbeefdeadbeef", "entities": entities})
        )

        with pytest.raises(DatasetError, match="content hash mismatch"):
            load("probe", 1, root=tmp_path)

    def test_the_hash_depends_on_content_not_key_order(self, tmp_path: Path) -> None:
        """Otherwise a reformatting pass would invalidate every recorded
        run, and nobody would trust the hash."""
        assert content_hash({"a": 1, "b": 2}) == content_hash({"b": 2, "a": 1})

    def test_a_loaded_dataset_cannot_be_mutated(self) -> None:
        dataset = load("baseline", 1)

        with pytest.raises(TypeError):
            dataset.entities["acme-corp"]["name"] = "Changed"  # type: ignore[index]

    def test_malformed_json_names_the_dataset(self, tmp_path: Path) -> None:
        (tmp_path / "broken@1.json").write_text("{not json")

        with pytest.raises(DatasetError, match="not valid JSON"):
            load("broken", 1, root=tmp_path)


class TestPacedClockModes:
    """Realtime and accelerated modes actually sleep — the property that
    makes a scenario watchable, and the one a demo depends on."""

    async def test_realtime_mode_sleeps_for_the_logical_duration(self) -> None:
        import time

        clock = VirtualClock(mode=ClockMode.REALTIME)
        started = time.monotonic()

        await clock.advance(timedelta(milliseconds=60))

        assert time.monotonic() - started >= 0.05

    async def test_accelerated_mode_sleeps_less_than_the_logical_duration(self) -> None:
        """Four simulated weeks in ninety seconds is what makes a temporal
        provider demonstrable at all."""
        import time

        clock = VirtualClock(mode=ClockMode.ACCELERATED, multiplier=1000)
        started = time.monotonic()

        await clock.advance(timedelta(seconds=10))

        elapsed = time.monotonic() - started
        assert elapsed < 1.0
        assert clock.now == clock.epoch + timedelta(seconds=10), "logical time advanced fully"
