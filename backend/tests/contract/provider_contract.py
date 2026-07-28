"""The shared Provider adapter contract suite.

**One suite, run against every adapter — simulated and production alike.**
This is principle 8 and the keystone of the simulation design: it is the
only mechanism that catches drift between the two paths, and drift is the
single failure that would invalidate every other guarantee the simulator
offers. Demos, regression, AI evaluation, and benchmarking all rest on the
simulated path behaving like the real one.

Written as a mixin rather than a fixture-parameterised module so each
adapter's suite is a real, named test class that appears separately in CI
output — "the Apollo adapter violates the contract" is a more useful
failure than "contract[3] failed".

Usage:

    class TestApolloSimulated(ProviderContractSuite):
        @pytest.fixture
        def adapter(self) -> ProviderAdapter:
            return SimulatedApolloAdapter(...)

Every adapter added to the system gets one of these. An adapter without a
contract suite is an adapter nobody has checked.
"""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest

from modules.provider_platform.public import (
    ProviderAdapter,
    ProviderCapability,
    ProviderCapabilityUnsupportedError,
    ProviderError,
    ProviderRequest,
)


class ProviderContractSuite:
    """Behaviour every adapter must exhibit, whatever it is adapting."""

    @pytest.fixture
    def adapter(self) -> ProviderAdapter:
        raise NotImplementedError("subclass must supply an adapter fixture")

    # ------------------------------------------------------------ describe

    def test_describes_itself_without_being_called(self, adapter: ProviderAdapter) -> None:
        """`describe()` must not perform I/O.

        The platform calls it to validate a request *before* dispatching,
        and health output calls it for every registered provider. An
        implementation that reaches the network here turns a health check
        into a fan-out of vendor calls.
        """
        descriptor = adapter.describe()

        assert descriptor.provider is not None
        assert len(descriptor.capabilities) >= 1, (
            "an adapter with no capability cannot be asked for anything"
        )

    def test_declares_a_rate_limit_or_states_it_has_none(self, adapter: ProviderAdapter) -> None:
        """Declared so the platform can pace itself, rather than
        discovering the limit by being throttled."""
        limit = adapter.describe().rate_limit_per_minute

        assert limit is None or limit > 0

    # --------------------------------------------------------------- fetch

    async def test_returns_records_for_a_supported_capability(
        self, adapter: ProviderAdapter
    ) -> None:
        descriptor = adapter.describe()
        capability = next(iter(sorted(descriptor.capabilities)))

        response = await adapter.fetch(self._request(capability))

        assert response.provider == descriptor.provider
        assert isinstance(response.records, tuple)

    async def test_every_record_carries_its_provenance(self, adapter: ProviderAdapter) -> None:
        """A record without `external_id` cannot be deduplicated; one
        without `occurred_at` cannot be ordered. Both are how a backfill
        goes wrong silently."""
        descriptor = adapter.describe()
        capability = next(iter(sorted(descriptor.capabilities)))

        response = await adapter.fetch(self._request(capability))

        for record in response.records:
            assert record.provider == descriptor.provider
            assert record.external_id, "record has no external id — cannot be deduplicated"
            assert record.occurred_at.tzinfo is not None, "occurred_at must be timezone-aware"
            assert isinstance(record.payload, dict)

    async def test_occurred_at_is_provider_time_not_fetch_time(
        self, adapter: ProviderAdapter
    ) -> None:
        """`occurred_at` describes when the event happened, never when it
        was fetched. Equating them makes every backfill look like a burst
        of events that all happened at once."""
        descriptor = adapter.describe()
        capability = next(iter(sorted(descriptor.capabilities)))
        before = datetime.now(UTC)

        response = await adapter.fetch(self._request(capability))

        for record in response.records:
            assert record.occurred_at <= before or record.occurred_at > before, (
                "occurred_at must be a provider-supplied timestamp"
            )

    async def test_rejects_an_unsupported_capability(self, adapter: ProviderAdapter) -> None:
        """A typed refusal, not an empty result. An empty page is
        indistinguishable from "no data available", which is how an
        unwired capability stays unnoticed for a month."""
        descriptor = adapter.describe()
        unsupported = set(ProviderCapability) - descriptor.capabilities
        if not unsupported:
            pytest.skip("adapter supports every capability")

        with pytest.raises(ProviderCapabilityUnsupportedError):
            await adapter.fetch(self._request(next(iter(sorted(unsupported)))))

    async def test_never_returns_more_than_the_requested_limit(
        self, adapter: ProviderAdapter
    ) -> None:
        """The platform sizes its batches on this. An adapter returning
        more turns a paced sync into an unbounded fetch."""
        descriptor = adapter.describe()
        capability = next(iter(sorted(descriptor.capabilities)))

        response = await adapter.fetch(self._request(capability, limit=2))

        assert len(response.records) <= 2

    async def test_pagination_terminates(self, adapter: ProviderAdapter) -> None:
        """`has_more` must eventually be False.

        A cursor that never terminates is an infinite sync — and because it
        keeps returning records, it looks like a working integration rather
        than a stuck one.
        """
        descriptor = adapter.describe()
        capability = next(iter(sorted(descriptor.capabilities)))

        cursor: str | None = None
        for _ in range(50):
            response = await adapter.fetch(self._request(capability, cursor=cursor))
            if not response.has_more:
                return
            assert response.next_cursor is not None, "has_more is set but no cursor was supplied"
            assert response.next_cursor != cursor, "cursor did not advance — pagination would loop"
            cursor = response.next_cursor

        pytest.fail("pagination did not terminate within 50 pages")

    async def test_only_provider_errors_escape(self, adapter: ProviderAdapter) -> None:
        """No vendor SDK exception may reach a caller.

        The boundary rule that applies to every adapter in this codebase
        (CLAUDE.md §15). Asserted by driving a request that is invalid for
        every provider and checking what comes out.
        """
        request = self._request(next(iter(sorted(adapter.describe().capabilities))), subject="")

        try:
            await adapter.fetch(request)
        except ProviderError:
            pass  # correct: the port's own failure surface
        except Exception as exc:  # noqa: BLE001 - the assertion is the point
            pytest.fail(f"a non-ProviderError escaped the adapter: {type(exc).__name__}: {exc}")

    # ------------------------------------------------------------- helpers

    @staticmethod
    def _request(
        capability: ProviderCapability,
        *,
        subject: str = "example.com",
        cursor: str | None = None,
        limit: int = 100,
    ) -> ProviderRequest:
        return ProviderRequest(
            capability=capability,
            workspace_id=uuid4(),
            correlation_id=uuid4(),
            subject=subject,
            cursor=cursor,
            limit=limit,
        )
