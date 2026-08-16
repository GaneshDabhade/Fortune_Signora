"""**In-app: the one channel Signora owns end to end.**

📁 **[TASK-495](../../../../docs/BACKLOG.md)**, on
[ADR-0017](../../../../docs/architecture/adr/0017-notifications.md).

## 🔴 Why this adapter has no credential, and why that is not an exemption

⚡ **Every other channel leaves the process.** 📁 `ai_platform`'s rule —
*"An adapter is registered only when its credentials exist"* — **exists because
a call that travels to a vendor without one fails somewhere less legible.**
⛔ **This one writes a row in Signora's own database and reads it back on
Signora's own screen**, so *"is it configured"* has no meaningful answer: the
database is the same dependency the request that triggered it already used.

✅ **So it is registered unconditionally, and that is the ONLY channel of which
that is true.** ⚠️ **It does not make in-app a default** — 📁 the row's own
correction: *"in-app is a distinct CHANNEL, never a substitute for a channel
that failed to configure."*

## ⛔ It does not commit

📁 **The repository never commits and neither does this** — the transaction
belongs to whoever opened the session. ⚡ **Which is what makes a notification
atomic with the thing it announces**: a research run that failed to record its
own outcome does not leave a customer told it succeeded.
"""

from __future__ import annotations

from modules.workspace_tenancy.domain.notification import Channel, Notification
from modules.workspace_tenancy.infrastructure.repositories import (
    SqlAlchemyNotificationRepository,
)


class InAppNotificationChannel:
    """Delivers by persisting — **the row the bell reads.**"""

    def __init__(self, repository: SqlAlchemyNotificationRepository) -> None:
        self._repository = repository

    @property
    def channel(self) -> Channel:
        return Channel.IN_APP

    async def deliver(self, notification: Notification) -> None:
        """Write it.

        ⛔ **No try/except.** ⚡ **A failed write must reach the caller** — 📁
        [§10](../../../../CLAUDE.md): a channel that swallowed its own failure
        would make a customer who was never told indistinguishable from one who
        was.
        """
        await self._repository.record(notification)


__all__ = ["InAppNotificationChannel"]
