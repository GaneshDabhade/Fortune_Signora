"""Ports the Signal Engine's use cases depend on.

Two repositories, deliberately separate: signals are **derived** and can be
rebuilt from business events, while profiles are **customer-authored** and
cannot be regenerated from anything. Conflating them would invite a rebuild
that quietly discards a customer's configuration.
"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime
from typing import Protocol
from uuid import UUID

from modules.signal_engine.domain.catalog import SignalType
from modules.signal_engine.domain.profile import SignalProfile
from modules.signal_engine.domain.signal import Signal


class SignalRepository(Protocol):
    """Persistence for signals. There is deliberately **no update
    method**: a hypothesis that gains evidence becomes a new signal naming
    the one it replaces."""

    async def current_for_entity(
        self, workspace_id: UUID, entity_id: UUID, *, signal_type: SignalType
    ) -> tuple[Signal, ...]:
        """Signals of this type that no later signal replaces."""
        ...

    async def record(self, signals: tuple[Signal, ...]) -> int:
        """Insert, ignoring any whose id is already present. Ids are derived
        from the evidence, so re-generating over the same business events
        inserts nothing."""
        ...

    async def for_entity(
        self,
        workspace_id: UUID,
        entity_id: UUID,
        *,
        signal_type: SignalType | None = None,
        live_at: datetime | None = None,
    ) -> tuple[Signal, ...]: ...

    async def by_id(self, workspace_id: UUID, signal_id: UUID) -> Signal | None: ...

    async def citing_events(
        self, workspace_id: UUID, business_event_ids: Sequence[UUID]
    ) -> tuple[Signal, ...]:
        """Signals resting on any of these business events — the query that
        makes citation worth its cost when evidence is later refined."""
        ...


class ProfileRepository(Protocol):
    """Persistence for customer-authored configuration.

    Immutable and versioned: a new profile is a new row naming the one it
    supersedes. An edited profile would make every historical signal
    unexplainable.
    """

    async def current(self, workspace_id: UUID) -> SignalProfile | None:
        """The version nothing supersedes, or None when the workspace has
        configured nothing and the catalog defaults apply."""
        ...

    async def by_version(self, workspace_id: UUID, version: int) -> SignalProfile | None:
        """A specific version — what **historical replay** needs to
        reproduce what a customer was originally told."""
        ...

    async def save(self, profile: SignalProfile) -> None: ...
