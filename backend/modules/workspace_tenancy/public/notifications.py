"""**The one interface a module calls to tell somebody something happened.**

📁 **[TASK-495](../../../../docs/BACKLOG.md)**, on
[ADR-0017](../../../../docs/architecture/adr/0017-notifications.md):

> ***"Every module that needs to notify a user does so via one shared internal
> trigger interface, never per-channel bespoke code."***

## ⚡ What a caller sees, and what it deliberately cannot

✅ **{@link Notifier} — one verb.** ⛔ **No channel adapters, no vendor, no
template id, no delivery status, no retry policy.** 📁 **The ADR's own migration
strategy is the reason**: *"any module triggering a notification calls a single
internal interface, never Novu's SDK directly — a migration … would touch only
that adapter."* ⚡ **A caller that could see a vendor is a caller a migration
would have to change.**

## 🔴 The caller names the channels, and there is no default

⚠️ **This looks like an ergonomic wart and it is the guard.** 📁 The precedent
is `ai_platform/infrastructure/composition.py`: ✅ *"An adapter is registered
only when its credentials exist"* — 🔴 **and *"There is deliberately no fallback
between them."***

⛔ **So a request for an unconfigured channel FAILS**, and a default of
`{IN_APP}` would be exactly the fallback that rule refuses, arriving as a
convenience. ⚡ **In-app is a distinct channel, never a substitute for one that
failed to configure** — 📁 [§10](../../../../CLAUDE.md): *"a service running on
it is indistinguishable from one that works — which is strictly worse than the
outage it would hide."*

## ⛔ And it publishes no read side

⚡ **What a person has READ is already published**, next door in
`notification_state.py` — 📁 [TASK-480](../../../../docs/BACKLOG.md),
[D-239](../../../../docs/DECISION_REGISTER.md). ✅ **This half is write-only on
purpose**: **a module that triggers a notification has no business asking
whether it was read**, and a port that answered would make one person's state
the workspace's to query.
"""

from __future__ import annotations

from typing import Protocol

from modules.workspace_tenancy.domain.notification import (
    Actor,
    ActorKind,
    Category,
    Channel,
    ChannelNotRegisteredError,
    Notification,
    NotificationError,
    NotificationRequest,
    NotificationRequested,
    Subject,
)

#: ⚡ **Re-exported rather than redefined.** ⛔ **A second shape here would be a
#: second definition of the same fact** — 📁 [§2](../../../../CLAUDE.md), and the
#: same reason `UnreadBadge` aliases `UnreadCount` next door.
__all__ = [
    "Actor",
    "ActorKind",
    "Category",
    "Channel",
    "ChannelNotRegisteredError",
    "Notification",
    "NotificationError",
    "NotificationRequest",
    "NotificationRequested",
    "Notifier",
    "Subject",
]


class Notifier(Protocol):
    """**Tell one person that one thing happened.**

    ⚡ **Channel-agnostic**: the request names channels, and what serves each of
    them is the deployment's business rather than the caller's.
    """

    async def notify(self, request: NotificationRequest) -> Notification:
        """Deliver `request` on every channel it names.

        ⛔ **Raises {@link ChannelNotRegisteredError} if any named channel has
        no adapter, and delivers NONE of them when it does.** ⚡ **All-or-none
        is what makes a retry safe** — 📁 the Definition of Done is *"a customer
        sees that something happened, **once**"*, and a partial delivery
        followed by a retry is how *once* becomes twice.

        🔴 **Returning normally means delivered.** ⛔ **A channel that swallowed
        its own failure would make an outage indistinguishable from a working
        service.**
        """
        ...
