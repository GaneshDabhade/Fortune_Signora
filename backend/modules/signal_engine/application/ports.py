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
from modules.signal_engine.domain.precision import RulePrecision
from modules.signal_engine.domain.profile import SignalProfile
from modules.signal_engine.domain.resolution import Resolution
from modules.signal_engine.domain.signal import Signal
from signora_platform.pagination import CursorPosition


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

    async def for_workspace(
        self,
        workspace_id: UUID,
        *,
        live_at: datetime,
        after: CursorPosition | None,
        limit: int,
    ) -> tuple[Signal, ...]:
        """Every live hypothesis in the workspace, newest first, one page.

        **Separate from `for_entity` rather than an optional `entity_id`.** An
        optional filter would make *"the whole workspace"* the accidental
        default of a method whose every existing caller means one account —
        and the two answer different questions, on different screens, with
        different cost. **`live_at` is required here** for the same reason: a
        queue read that could omit it would silently return work nobody should
        be shown.
        """
        ...

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


class ResolutionRepository(Protocol):
    """Persistence for how a signal left the queue.

    **No update method, like the two above and for a sharper reason.** A
    resolution records what somebody decided and when; an editable one is a
    record nobody could cite. Changing your mind is a new resolution naming the
    one it supersedes, which is also what keeps a regretted dismissal readable
    rather than gone.

    **Nothing here writes to a signal.** The acceptance criterion *"resolution
    never mutates the signal or its evidence"* is visible in the shape of this
    port: there is no method that could.
    """

    async def record(self, resolution: Resolution) -> None:
        """Append one decision."""
        ...

    async def current_for_signals(
        self, workspace_id: UUID, signal_ids: Sequence[UUID]
    ) -> dict[UUID, Resolution]:
        """The resolution in force for each of these signals, keyed by signal.

        **Superseded resolutions are excluded, and a signal nobody has decided
        about is absent rather than present with a null.** An absent key means
        *"still open"*, which is not the same fact as a decision to do nothing
        and must not be readable as one.
        """
        ...

    async def history_for_signal(
        self, workspace_id: UUID, signal_id: UUID
    ) -> tuple[Resolution, ...]:
        """Every decision ever recorded about this signal, oldest first —
        *"nothing is deleted: every resolution is auditable."*"""
        ...

    async def judgements_by_type(self, workspace_id: UUID) -> tuple[RulePrecision, ...]:
        """How often each signal type was acted on versus dismissed.

        **Only the two outcomes that are judgements** — `Assigned` is routing
        and `Snoozed` is deferral, and neither is anybody saying the rule was
        right or wrong (`domain/precision.py`).

        ⛔ **Only currently-in-force resolutions**, on `current_for_signals`'
        reasoning exactly: a superseded dismissal is a decision somebody
        already changed their mind about, and counting it would hold a rule to
        a judgement that has been withdrawn.

        **A type nobody has judged is absent from the result rather than
        present with zeroes** — the caller decides what *no judgements yet*
        renders as, which is the only way P-A survives the trip to a screen.
        """
        ...
