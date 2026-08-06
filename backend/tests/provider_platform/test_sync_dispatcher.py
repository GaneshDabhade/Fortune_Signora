"""The port that had no implementation, and the seam that runs what it asks for.

**TASK-901 slice 1.** `SyncDeclaredTargets` has decided which companies are new
since M12; nothing carried one to a provider, because `SyncDispatcher` was a
Protocol with no adapter anywhere in the repository.

These assert the three things that would silently break the chain without
breaking a single application-layer test: **what the dispatcher publishes**,
**that it refuses rather than going quiet when no provider can serve the
capability**, and **that the consumer runs what the event named rather than
re-resolving it.**
"""

from __future__ import annotations

from collections.abc import AsyncIterator, Sequence
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from typing import Any
from unittest.mock import patch
from uuid import UUID, uuid4

import pytest

from modules.provider_platform.domain.events import PROVIDER_SYNC_REQUESTED
from modules.provider_platform.domain.provider import (
    ProviderCapability,
    ProviderDescriptor,
    ProviderName,
    ProviderRegistry,
)
from modules.provider_platform.infrastructure.sync_dispatcher import (
    FIRST_READ,
    NoProviderSupportsCapabilityError,
    OutboxSyncDispatcher,
)
from modules.provider_platform.interface.handlers import SYSTEM_USER_ID, run_requested_sync
from signora_platform.event_bus import EventEnvelope

WORKSPACE = UUID("11111111-1111-4111-8111-111111111111")
CORRELATION = UUID("22222222-2222-4222-8222-222222222222")
SESSION = object()


class _Adapter:
    """A provider that declares capabilities and is never called."""

    def __init__(self, name: ProviderName, *capabilities: ProviderCapability) -> None:
        self._name = name
        self._capabilities = tuple(capabilities)

    def describe(self) -> ProviderDescriptor:
        return ProviderDescriptor(
            provider=self._name,
            capabilities=frozenset(self._capabilities),
            simulated=False,
        )


class _Publisher:
    def __init__(self) -> None:
        self.published: list[tuple[Sequence[Any], str, UUID, Any]] = []

    async def publish(
        self,
        events: Sequence[Any],
        *,
        session: Any,
        producer_module: str,
        correlation_id: UUID,
    ) -> None:
        self.published.append((events, producer_module, correlation_id, session))


def _registry(*adapters: _Adapter) -> ProviderRegistry:
    registry = ProviderRegistry()
    for adapter in adapters:
        registry.register(adapter)  # type: ignore[arg-type]
    return registry


class TestWhatTheDispatcherPublishes:
    async def test_asks_for_one_company_by_name(self) -> None:
        publisher = _Publisher()
        registry = _registry(_Adapter(ProviderName.APOLLO, FIRST_READ))

        await OutboxSyncDispatcher(
            session=SESSION,  # type: ignore[arg-type]
            publisher=publisher,
            registry=registry,
        ).sync(workspace_id=WORKSPACE, subject="Northwind Health", correlation_id=CORRELATION)

        (events, producer, correlation, session) = publisher.published[0]
        assert events[0].event_type == PROVIDER_SYNC_REQUESTED
        assert events[0].subject == "Northwind Health"
        assert events[0].capability is FIRST_READ
        assert producer == "provider_platform"
        assert correlation == CORRELATION

    async def test_publishes_on_the_callers_session(self) -> None:
        """**The request and the watermark it justifies commit together.**

        A dispatcher opening its own session would let a company be asked for
        and the record of having asked roll back — which is the outbox's whole
        reason for existing, applied one level up.
        """
        publisher = _Publisher()
        await OutboxSyncDispatcher(
            session=SESSION,  # type: ignore[arg-type]
            publisher=publisher,
            registry=_registry(_Adapter(ProviderName.APOLLO, FIRST_READ)),
        ).sync(workspace_id=WORKSPACE, subject="Acme", correlation_id=CORRELATION)

        assert publisher.published[0][3] is SESSION

    async def test_chooses_by_name_order_rather_than_registration_order(self) -> None:
        """**Deterministic, because insertion order is a hidden input** (§2),
        and this repository has eliminated that one before."""
        publisher = _Publisher()
        registry = _registry(
            _Adapter(ProviderName.CRUNCHBASE, FIRST_READ),
            _Adapter(ProviderName.APOLLO, FIRST_READ),
        )

        await OutboxSyncDispatcher(
            session=SESSION,  # type: ignore[arg-type]
            publisher=publisher,
            registry=registry,
        ).sync(workspace_id=WORKSPACE, subject="Acme", correlation_id=CORRELATION)

        chosen = publisher.published[0][0][0].provider
        assert chosen == sorted([ProviderName.APOLLO, ProviderName.CRUNCHBASE])[0]

    async def test_refuses_when_nothing_can_serve_the_capability(self) -> None:
        """**Loudly, not quietly.** A workspace whose declared companies are
        never read would otherwise look identical to one with nothing to read,
        and the platform's dead-letter path exists for exactly this."""
        publisher = _Publisher()
        registry = _registry(_Adapter(ProviderName.APOLLO, ProviderCapability.WORKFORCE))

        with pytest.raises(NoProviderSupportsCapabilityError):
            await OutboxSyncDispatcher(
                session=SESSION,  # type: ignore[arg-type]
                publisher=publisher,
                registry=registry,
            ).sync(workspace_id=WORKSPACE, subject="Acme", correlation_id=CORRELATION)

        assert publisher.published == []

    def test_the_refusal_names_no_provider(self) -> None:
        """§10 — *"an error must never name a component that was not
        involved."* **No provider was reached; none exists to reach.** A
        `ProviderError` here would put a false lead in the first place an
        engineer looks."""
        error = NoProviderSupportsCapabilityError(FIRST_READ)

        assert not hasattr(error, "provider")
        assert FIRST_READ.value in str(error)


class _Scope:
    def __init__(self) -> None:
        self.opened: list[dict[str, Any]] = []

    @asynccontextmanager
    async def __call__(
        self, factory: Any, *, workspace_id: UUID, user_id: UUID
    ) -> AsyncIterator[Any]:
        self.opened.append({"workspace_id": workspace_id, "user_id": user_id})
        yield SESSION


class _Sync:
    def __init__(self) -> None:
        self.calls: list[Any] = []

    async def execute(self, request: Any, *, correlation_id: UUID) -> Any:
        self.calls.append(request)

        class _Result:
            class sync:  # noqa: N801 — a stand-in for the recorded run
                id = uuid4()

                class status:  # noqa: N801
                    value = "completed"

            records_stored = 4

        return _Result()


def _requested(*, provider: str = "apollo", capability: str = FIRST_READ.value) -> EventEnvelope:
    return EventEnvelope(
        event_id=uuid4(),
        event_type=PROVIDER_SYNC_REQUESTED,
        event_version=1,
        workspace_id=WORKSPACE,
        occurred_at=datetime(2026, 8, 6, tzinfo=UTC),
        producer_module="provider_platform",
        correlation_id=CORRELATION,
        causation_id=None,
        payload={"subject": "Northwind Health", "provider": provider, "capability": capability},
    )


class TestTheConsumerRunsWhatWasAsked:
    async def test_runs_the_provider_the_event_named_rather_than_resolving_again(self) -> None:
        """**A replay must do what the original run did.** Re-resolving would
        let a registry that has changed since send the second run somewhere
        else — the same reasoning that keeps `declaration_version` on the
        event it answers."""
        apollo = _Adapter(ProviderName.APOLLO, FIRST_READ)
        registry = _registry(apollo, _Adapter(ProviderName.CRUNCHBASE, FIRST_READ))
        run, scope = _Sync(), _Scope()
        handed: list[Any] = []

        def build(session: Any, adapter: Any) -> Any:
            handed.append(adapter)
            return run

        with patch(
            "modules.provider_platform.interface.handlers.tenant_scoped_session", scope
        ):
            await run_requested_sync(
                _requested(provider="apollo"),
                session_factory=None,  # type: ignore[arg-type]
                registry=registry,
                build=build,
            )

        # The adapter handed to the use case is the one the event named, even
        # though another provider in the registry also declares the capability.
        assert handed == [apollo]
        assert run.calls[0].subject == "Northwind Health"
        assert run.calls[0].capability is FIRST_READ

    async def test_opens_a_workspace_scoped_session_as_the_system_identity(self) -> None:
        """A sync runs without an acting user, and the rows it causes are
        attributable to a machine rather than to whoever last saved a list."""
        registry = _registry(_Adapter(ProviderName.APOLLO, FIRST_READ))
        scope = _Scope()

        with patch(
            "modules.provider_platform.interface.handlers.tenant_scoped_session", scope
        ):
            await run_requested_sync(
                _requested(),
                session_factory=None,  # type: ignore[arg-type]
                registry=registry,
                build=lambda session, adapter: _Sync(),  # type: ignore[arg-type,return-value]
            )

        assert scope.opened[0]["workspace_id"] == WORKSPACE
        assert scope.opened[0]["user_id"] == SYSTEM_USER_ID
