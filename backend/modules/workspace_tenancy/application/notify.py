"""**Tell somebody something happened** — the one trigger every module calls.

📁 **[TASK-495](../../../../docs/BACKLOG.md)**, on
[ADR-0017](../../../../docs/architecture/adr/0017-notifications.md):

> ***"a single, channel-agnostic notification trigger interface used by every
> module … that needs to notify a user"***

⚡ **This is that interface's one implementation.** ⛔ **It knows nothing about
how any channel works** — it resolves adapters from a registry and hands each
of them the same notification.

## 🔴 Every channel is resolved BEFORE any is delivered

⚠️ **This is the ordering decision in the file, and it is deliberate.**

⛔ **Resolving lazily would deliver in-app, then fail on Slack** — leaving the
caller with an exception and the customer with a notification. ⚡ **The retry
that follows then delivers the in-app one a second time**, and 📁 the Definition
of Done is *"a customer sees that something happened, **once**"*.

✅ **So an unreachable channel refuses the whole request and nothing is
delivered.** ⛔ **The alternative — deliver what works, report what did not — is
partial success dressed as a failure**, and no caller can act on it: it cannot
tell which half to retry.

## ⚡ The clock and the identifier are injected

📁 [§2](../../../../CLAUDE.md), *hidden inputs are architecture defects*, and
📁 `test_no_hidden_clock.py` is this module's standing guard on it. ⛔ **A
`datetime.now()` inside this class would make *when a notification happened*
untestable**, on the one surface that groups by day.
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime
from uuid import UUID, uuid4

from modules.workspace_tenancy.domain.notification import (
    Channel,
    Notification,
    NotificationChannel,
    NotificationChannelRegistry,
    NotificationRequest,
)


class Notify:
    """**The trigger.** ⚡ One method, and it is the only way a notification
    comes into being."""

    def __init__(
        self,
        *,
        channels: NotificationChannelRegistry,
        clock: Callable[[], datetime] = lambda: datetime.now(UTC),
        new_id: Callable[[], UUID] = uuid4,
    ) -> None:
        self._channels = channels
        self._clock = clock
        self._new_id = new_id

    async def notify(self, request: NotificationRequest) -> Notification:
        """Deliver `request` on every channel it names, or deliver none.

        ⚠️ **Named `notify` rather than this module's usual `execute`, and that
        is the point.** ⚡ **`Notifier` is a `Protocol`, so conformance is
        STRUCTURAL** — 📁 an `execute` here plus a one-line `notify` forwarding
        to it would be a second definition of one behaviour
        ([§2](../../../../CLAUDE.md)), added only to satisfy a naming habit.

        ⛔ **Raises {@link ChannelNotRegisteredError} before any delivery** if
        any named channel has no adapter — 📁 see the module docstring: partial
        delivery is the failure a retry turns into a duplicate.
        """
        adapters = self._resolve_all(request.channels)
        notification = Notification(
            id=self._new_id(),
            workspace_id=request.workspace_id,
            recipient_id=request.recipient_id,
            category=request.category,
            actor=request.actor,
            subject=request.subject,
            summary=request.summary,
            expectation=request.expectation,
            occurred_at=self._clock(),
        )
        for adapter in adapters:
            await adapter.deliver(notification)
        return notification

    def _resolve_all(self, channels: frozenset[Channel]) -> list[NotificationChannel]:
        """⚡ **Sorted, so two identical requests deliver in the same order.**

        ⛔ **A `frozenset` has no order**, and iteration order over one can vary
        between processes — which would make *"the in-app one arrived before
        the email"* a property of the hash seed rather than of the code.
        """
        return [
            self._channels.resolve(channel)
            for channel in sorted(channels, key=lambda c: c.value)
        ]


__all__ = ["Notify"]
