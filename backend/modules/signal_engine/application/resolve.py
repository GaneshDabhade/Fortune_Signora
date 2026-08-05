"""Recording what a person decided about a signal.

**The Signal Engine's first write that a customer causes.** Everything else
this module stores is derived: the pipeline reads business events and produces
hypotheses, and the only human input was the profile that interpreted them.
This is a person saying *"I dealt with it"*, *"not now"*, or *"you were
wrong"*, and none of those can be reconstructed from anything.

**It writes exactly one row and touches nothing else.** No signal is updated,
no evidence is re-read, no score is recomputed and no event is published.
*"Resolution never mutates the signal or its evidence"* is the acceptance
criterion, and the shortest way to keep it is a use case with nothing else to
reach for — the repository it holds has no method that could.

**Superseding is worked out here rather than asked for.** A caller that had to
pass the resolution it replaces would eventually pass the wrong one, or `None`,
and the queue would show two current answers for one signal. The use case reads
what is current and names it, so the chain is a property of the write rather
than of the caller's diligence.
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime
from uuid import UUID, uuid4

from modules.signal_engine.application.ports import ResolutionRepository, SignalRepository
from modules.signal_engine.domain.resolution import Outcome, Resolution


class SignalNotFoundError(LookupError):
    """The signal is not visible in this workspace.

    **Deliberately does not distinguish "no such signal" from "not yours"** —
    the same rule the rest of the platform follows, because an error that told
    the two apart would answer *"does workspace X hold a signal with this
    id?"* to somebody who cannot see it.
    """


class ResolveSignal:
    """One decision, recorded."""

    def __init__(
        self,
        *,
        signals: SignalRepository,
        resolutions: ResolutionRepository,
        clock: Callable[[], datetime] = lambda: datetime.now(UTC),
    ) -> None:
        self._signals = signals
        self._resolutions = resolutions
        self._clock = clock

    async def execute(
        self, workspace_id: UUID, signal_id: UUID, *, outcome: Outcome, actor_id: UUID
    ) -> Resolution:
        """Record `outcome` against this signal, superseding any decision
        already in force.

        **The signal is read to prove it exists, not to change it.** Without
        this a resolution could name a signal from another workspace — the row
        would be refused by the foreign key eventually, or worse, accepted
        because the id happened to exist and RLS hid nothing.
        """
        signal = await self._signals.by_id(workspace_id, signal_id)
        if signal is None:
            raise SignalNotFoundError(
                "That signal is not in this workspace, so there is nothing here to decide about."
            )

        current = await self._resolutions.current_for_signals(workspace_id, [signal_id])
        previous = current.get(signal_id)

        resolution = Resolution(
            id=uuid4(),
            workspace_id=workspace_id,
            signal_id=signal_id,
            outcome=outcome,
            #: **The verified principal, never a value from a request body.**
            #: This is the only record of who made the call, and a resolution
            #: attributed to the wrong person is worse than an anonymous one.
            actor_id=actor_id,
            recorded_at=self._clock(),
            supersedes=previous.id if previous is not None else None,
        )
        await self._resolutions.record(resolution)
        return resolution


__all__ = ["ResolveSignal", "SignalNotFoundError"]
