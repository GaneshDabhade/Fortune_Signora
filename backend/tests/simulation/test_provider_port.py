"""Tests for the Provider Port itself.

The Port is defined before any adapter implements it, so that it describes
what a real vendor integration needs rather than what happened to be
convenient to simulate. That ordering leaves its own behaviour — the
registry, the error hierarchy, the replay record — needing tests of its
own; a contract nobody exercises is a contract nobody has checked.
"""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest

from modules.provider_platform.public import (
    ProviderCapability,
    ProviderDescriptor,
    ProviderError,
    ProviderName,
    ProviderPayloadInvalidError,
    ProviderPermanentError,
    ProviderRateLimitedError,
    ProviderRecord,
    ProviderRegistry,
    ProviderResponse,
    ProviderTransientError,
    ReplayContext,
)


class _StubAdapter:
    """Minimal Port implementation, standing in for an adapter until a
    provider qualifies. Deliberately not a simulated *provider* — it emits
    no vendor-shaped payload, so it cannot be mistaken for one and does not
    require provenance."""

    def __init__(self, provider: ProviderName, capabilities: set[ProviderCapability]) -> None:
        self._descriptor = ProviderDescriptor(
            provider=provider, capabilities=frozenset(capabilities), simulated=True
        )

    def describe(self) -> ProviderDescriptor:
        return self._descriptor

    async def fetch(self, request: object) -> ProviderResponse:
        return ProviderResponse(provider=self._descriptor.provider, records=())


class TestErrorHierarchy:
    """Every failure a caller must handle, reachable from one base."""

    def test_every_failure_is_a_provider_error(self) -> None:
        """A caller catching ProviderError has caught everything the Port
        can raise. No vendor SDK exception escapes an adapter."""
        for error in (
            ProviderTransientError(ProviderName.APOLLO, "x"),
            ProviderRateLimitedError(ProviderName.APOLLO, "x"),
            ProviderPermanentError(ProviderName.APOLLO, "x"),
            ProviderPayloadInvalidError(ProviderName.APOLLO, "x"),
        ):
            assert isinstance(error, ProviderError)

    def test_rate_limiting_is_transient(self) -> None:
        """A caller handling transient failures generically must back off
        correctly on a rate limit without special-casing it."""
        assert isinstance(
            ProviderRateLimitedError(ProviderName.BOMBORA, "slow down"), ProviderTransientError
        )

    def test_a_transient_failure_is_not_permanent(self) -> None:
        """The distinction that matters: retrying a permanent failure burns
        quota to no purpose; giving up on a transient one loses data that
        was merely late."""
        transient = ProviderTransientError(ProviderName.APOLLO, "timeout")

        assert not isinstance(transient, ProviderPermanentError)

    def test_rate_limiting_carries_the_vendor_supplied_wait(self) -> None:
        """Guessing a backoff when the vendor stated one is how an
        integration gets throttled harder."""
        error = ProviderRateLimitedError(ProviderName.APOLLO, "slow down", retry_after_seconds=30)

        assert error.retry_after_seconds == 30

    def test_an_error_names_its_provider(self) -> None:
        """With five providers syncing concurrently, an error that does not
        say which one is close to useless."""
        assert "apollo" in str(ProviderTransientError(ProviderName.APOLLO, "boom"))


class TestProviderRegistry:
    def test_registers_and_resolves_an_adapter(self) -> None:
        registry = ProviderRegistry()
        registry.register(
            _StubAdapter(ProviderName.APOLLO, {ProviderCapability.COMPANY_ENRICHMENT})
        )

        assert registry.get(ProviderName.APOLLO) is not None

    def test_an_unregistered_provider_is_a_typed_failure(self) -> None:
        """Not a None the caller must remember to check — an unwired
        provider should fail loudly at the point of use."""
        with pytest.raises(ProviderPermanentError, match="no adapter registered"):
            ProviderRegistry().get(ProviderName.BOMBORA)

    def test_finds_every_adapter_supporting_a_capability(self) -> None:
        registry = ProviderRegistry()
        registry.register(
            _StubAdapter(ProviderName.APOLLO, {ProviderCapability.COMPANY_ENRICHMENT})
        )
        registry.register(
            _StubAdapter(
                ProviderName.CORESIGNAL,
                {ProviderCapability.COMPANY_ENRICHMENT, ProviderCapability.WORKFORCE},
            )
        )
        registry.register(
            _StubAdapter(ProviderName.BOMBORA, {ProviderCapability.BEHAVIOURAL_INTENT})
        )

        assert registry.supporting(ProviderCapability.COMPANY_ENRICHMENT) == (
            ProviderName.APOLLO,
            ProviderName.CORESIGNAL,
        )

    def test_provider_independence_removing_one_leaves_the_rest_working(self) -> None:
        """AC-20. Each generator must be independently removable without
        affecting anything else — the property that lets Bombora stay
        Conditional without blocking the milestone."""
        registry = ProviderRegistry()
        registry.register(
            _StubAdapter(ProviderName.APOLLO, {ProviderCapability.COMPANY_ENRICHMENT})
        )
        registry.register(
            _StubAdapter(ProviderName.BOMBORA, {ProviderCapability.BEHAVIOURAL_INTENT})
        )

        del registry.adapters[ProviderName.BOMBORA]

        assert registry.get(ProviderName.APOLLO) is not None
        assert registry.supporting(ProviderCapability.COMPANY_ENRICHMENT) == (ProviderName.APOLLO,)
        with pytest.raises(ProviderPermanentError):
            registry.get(ProviderName.BOMBORA)

    def test_an_empty_registry_is_valid(self) -> None:
        """The current state: all five providers Conditional, no generator
        registered, and the platform nonetheless coherent."""
        registry = ProviderRegistry()

        assert registry.supporting(ProviderCapability.BEHAVIOURAL_INTENT) == ()


class TestReplayContext:
    def test_records_everything_needed_to_reproduce_a_run(self) -> None:
        """Without generator version in particular, a change in downstream
        output could come from a model change, a prompt change, a dataset
        change, or a quietly-updated payload shape — and separating them
        after the fact is impossible."""
        fields = ReplayContext(
            scenario="erp-replacement",
            seed=42,
            manifest_version="1",
            generator_version="0.1.0",
            clock_mode="accelerated",
            dataset_version="baseline@1",
        ).as_log_fields()

        assert fields == {
            "sim_scenario": "erp-replacement",
            "sim_seed": 42,
            "sim_manifest_version": "1",
            "sim_generator_version": "0.1.0",
            "sim_clock_mode": "accelerated",
            "sim_dataset_version": "baseline@1",
        }


class TestResponseShape:
    def test_simulated_marking_lives_on_the_response_not_the_payload(self) -> None:
        """Marking the payload would change its shape and defeat the
        identical-contract rule — the very thing the marking exists to
        make safe."""
        record = ProviderRecord(
            provider=ProviderName.APOLLO,
            capability=ProviderCapability.COMPANY_ENRICHMENT,
            external_id="acme",
            occurred_at=datetime.now(UTC),
            payload={"name": "Acme"},
        )
        response = ProviderResponse(provider=ProviderName.APOLLO, records=(record,), simulated=True)

        assert response.simulated is True
        assert "simulated" not in record.payload

    def test_cursor_and_has_more_are_independent(self) -> None:
        """A provider legitimately returns a cursor with no further
        records; conflating the two costs an extra empty request per sync
        on every provider that does."""
        response = ProviderResponse(
            provider=ProviderName.APOLLO, records=(), next_cursor="abc", has_more=False
        )

        assert response.next_cursor == "abc"
        assert response.has_more is False

    def test_a_request_carries_workspace_and_correlation_context(self) -> None:
        from modules.provider_platform.public import ProviderRequest

        request = ProviderRequest(
            capability=ProviderCapability.COMPANY_ENRICHMENT,
            workspace_id=uuid4(),
            correlation_id=uuid4(),
            subject="acme.example",
        )

        assert request.workspace_id is not None
        assert request.correlation_id is not None
        assert request.since is None, "no watermark requests a full snapshot"
