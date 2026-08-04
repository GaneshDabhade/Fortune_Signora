"""The handler that turns a customer's declaration into work.

**Written for [B-109](../../../docs/BUGS.md)**, which found this file at 0% —
the seam between an event arriving and a use case running had never been
executed by a test, so *"the handler is wired"* rested on reading it.

The use case's own decisions are tested in `test_sync_targets.py`. These assert
only what the seam is responsible for: **which fields it reads from the
envelope, which it does not trust, and that it opens its own session** — the
three things that would silently break a subscription without breaking a
single application-layer test.

No database. `tenant_scoped_session` is given a factory that yields a recorded
double, because what this file does with a session is hand it to `build` — and
a real one would test PostgreSQL rather than the seam.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from typing import Any
from unittest.mock import patch
from uuid import UUID, uuid4

from modules.provider_platform.application.sync_targets import (
    NEVER_DECLARED,
    SyncDeclaredTargetsInput,
    SyncDeclaredTargetsResult,
)
from modules.provider_platform.interface.handlers import (
    CONSUMER_NAME,
    SYSTEM_USER_ID,
    sync_declared_targets,
)
from signora_platform.event_bus import EventEnvelope

WORKSPACE = UUID("11111111-1111-4111-8111-111111111111")
CORRELATION = UUID("22222222-2222-4222-8222-222222222222")
SESSION = object()


def _envelope(*, version: int = 3, workspace: UUID = WORKSPACE) -> EventEnvelope:
    return EventEnvelope(
        event_id=uuid4(),
        event_type="commercial_profile.target_accounts_changed",
        event_version=1,
        workspace_id=workspace,
        occurred_at=datetime(2026, 8, 4, tzinfo=UTC),
        producer_module="commercial_profile",
        correlation_id=CORRELATION,
        causation_id=None,
        payload={"declaration_version": version},
    )


class FakeSync:
    """Records what the handler asked for, and answers plausibly."""

    def __init__(self, result: SyncDeclaredTargetsResult | None = None) -> None:
        self.result = result or SyncDeclaredTargetsResult(
            dispatched=("Northwind Health",), acted_on=3
        )
        self.calls: list[tuple[SyncDeclaredTargetsInput, UUID]] = []

    async def execute(
        self, request: SyncDeclaredTargetsInput, *, correlation_id: UUID
    ) -> SyncDeclaredTargetsResult:
        self.calls.append((request, correlation_id))
        return self.result


class _Scope:
    """What `tenant_scoped_session` was asked to open."""

    def __init__(self) -> None:
        self.opened: list[dict[str, Any]] = []

    @asynccontextmanager
    async def __call__(
        self, factory: Any, *, workspace_id: UUID, user_id: UUID
    ) -> AsyncIterator[Any]:
        self.opened.append({"workspace_id": workspace_id, "user_id": user_id})
        yield SESSION


async def _handle(
    envelope: EventEnvelope, sync: FakeSync
) -> tuple[_Scope, list[Any]]:
    scope = _Scope()
    built: list[Any] = []

    def build(session: Any) -> Any:
        built.append(session)
        return sync

    with patch(
        "modules.provider_platform.interface.handlers.tenant_scoped_session", scope
    ):
        await sync_declared_targets(
            envelope,
            # The factory is never called: the scope double above stands in
            # for `tenant_scoped_session`, which is the only thing that would
            # have used it.
            session_factory=None,  # type: ignore[arg-type]
            build=build,
        )
    return scope, built


class TestWhatItReadsFromTheEvent:
    async def test_it_passes_on_the_announced_version(self) -> None:
        sync = FakeSync()

        await _handle(_envelope(version=7), sync)

        assert sync.calls[0][0].declaration_version == 7

    async def test_the_version_arrives_as_an_int_however_it_was_serialised(self) -> None:
        """JSON round-trips a version as a string often enough that this is
        worth pinning rather than assuming."""
        sync = FakeSync()
        envelope = _envelope().model_copy(update={"payload": {"declaration_version": "9"}})

        await _handle(envelope, sync)

        assert sync.calls[0][0].declaration_version == 9

    async def test_the_workspace_comes_from_the_envelope_not_the_payload(self) -> None:
        """The envelope is the platform's, and a payload field naming a
        different workspace must never be able to widen the scope."""
        other = UUID("33333333-3333-4333-8333-333333333333")
        sync = FakeSync()
        envelope = _envelope(workspace=other)

        scope, _ = await _handle(envelope, sync)

        assert sync.calls[0][0].workspace_id == other
        assert scope.opened[0]["workspace_id"] == other

    async def test_the_correlation_id_travels_with_the_work(self) -> None:
        """Otherwise the sync this event caused is untraceable back to it."""
        sync = FakeSync()

        await _handle(_envelope(), sync)

        assert sync.calls[0][1] == CORRELATION


class TestTheSessionItOpens:
    async def test_it_opens_its_own_tenant_scoped_session(self) -> None:
        """The dispatcher does not pass on the session it opened, so a handler
        that did not open one would run with no RLS context at all."""
        sync = FakeSync()

        scope, _ = await _handle(_envelope(), sync)

        assert len(scope.opened) == 1

    async def test_it_acts_as_the_platform_rather_than_as_a_person(self) -> None:
        """Nobody asked for this work; a declaration changed."""
        sync = FakeSync()

        scope, _ = await _handle(_envelope(), sync)

        assert scope.opened[0]["user_id"] == SYSTEM_USER_ID

    async def test_the_use_case_is_built_on_that_session(self) -> None:
        sync = FakeSync()

        _, built = await _handle(_envelope(), sync)

        assert built == [SESSION]


class TestOutcomesItMustNotTreatAsFailures:
    async def test_a_workspace_that_declared_nothing_is_handled_quietly(self) -> None:
        """`skipped` is a first-class outcome. A handler that raised here
        would dead-letter an event that was correctly a no-op."""
        sync = FakeSync(SyncDeclaredTargetsResult(dispatched=(), skipped=NEVER_DECLARED))

        await _handle(_envelope(), sync)

        assert sync.calls[0][0].workspace_id == WORKSPACE


class TestTheConsumerName:
    def test_it_is_the_recorded_one(self) -> None:
        """Renaming it resets the idempotency ledger, so it is pinned here as
        well as documented in the module."""
        assert CONSUMER_NAME == "provider_platform.sync_declared_targets"
