"""Recording what a person decided about a signal.

**The Signal Engine's first write that a customer causes.** Everything else
this module stores is derived: the pipeline reads business events and produces
hypotheses, and the only human input was the profile that interpreted them.
This is a person saying *"I dealt with it"*, *"not now"*, or *"you were
wrong"*, and none of those can be reconstructed from anything.

**It writes exactly one row and announces it.** No signal is updated, no
evidence is re-read and no score is recomputed — *"resolution never mutates the
signal or its evidence"* is the acceptance criterion, and the repository this
use case holds has no method that could.

⚡ **The announcement arrived with TASK-432, and this paragraph used to end
*"and no event is published."*** That was true and was the gap: **a human
decision was the one thing in this pipeline that produced no event**, so
`timeline` could not project it and nothing measuring whether Signora's
judgement was any good had a transition to read. **The row recorded the state
and nothing recorded the change**, which is evidence that cannot be recovered
later. **Publishing does not weaken the acceptance criterion** — an event is
not a mutation, and the signal is still never touched.

**The event goes in the same transaction as the row**, through the outbox, so a
consumer can never hear about a decision that was rolled back (§9).

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

from sqlalchemy.ext.asyncio import AsyncSession

from modules.signal_engine.application.ports import ResolutionRepository, SignalRepository
from modules.signal_engine.domain.events import SignalResolved
from modules.signal_engine.domain.resolution import Outcome, Resolution, discriminator
from signora_platform.event_bus import EventPublisher

#: Matches `GenerateSignals`. One module, one producer name, however many use
#: cases publish from it.
PRODUCER_MODULE = "signal_engine"


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
        publisher: EventPublisher,
        session: AsyncSession,
        clock: Callable[[], datetime] = lambda: datetime.now(UTC),
    ) -> None:
        self._signals = signals
        self._resolutions = resolutions
        self._publisher = publisher
        # **The caller's own session, not one this use case opens.** The outbox
        # row must commit with the resolution or neither should exist, and two
        # sessions cannot promise that.
        self._session = session
        self._clock = clock

    async def execute(
        self,
        workspace_id: UUID,
        signal_id: UUID,
        *,
        outcome: Outcome,
        actor_id: UUID,
        correlation_id: UUID,
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

        # See the note in `generate.py`: the platform's `PublishableEvent`
        # Protocol declares settable members, which frozen domain events cannot
        # satisfy. Raised as a finding there, and not fixed here either.
        resolved = SignalResolved(
            event_id=uuid4(),
            workspace_id=workspace_id,
            occurred_at=resolution.recorded_at,
            resolution_id=resolution.id,
            signal_id=signal_id,
            # **From the signal that was read to prove it exists**, not from
            # the request. A consumer projecting per account cannot reach this
            # module to look it up.
            entity_id=signal.entity_id,
            outcome=discriminator(outcome),
            actor_id=actor_id,
            supersedes=resolution.supersedes,
            payload_version=resolution.payload_version,
        )
        await self._publisher.publish(
            [resolved],  # type: ignore[list-item]
            session=self._session,
            producer_module=PRODUCER_MODULE,
            correlation_id=correlation_id,
        )
        return resolution


__all__ = ["ResolveSignal", "SignalNotFoundError"]
