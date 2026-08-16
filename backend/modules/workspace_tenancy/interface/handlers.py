"""Event handler: deliver the notification somebody asked for.

📁 **[TASK-495](../../../../docs/BACKLOG.md)**, subscribing to
`notification.requested`.

## 🔴 Why the delivery happens HERE and not in the producer

📁 **[05 §Synchronous vs. Asynchronous](../../../../docs/architecture/05-module-dependencies.md)
approves exactly one kind of synchronous edge into this module and it is
read-only**: *"Any module → Workspace & Tenancy: resolve/validate workspace
context (read-only)."*

⛔ **A producer calling a notify port directly would be a synchronous WRITE into
another module's data** — ⚡ not on that list, and 🔴 **extending it is an
architecture change no lane may make** ([§20e](../../../../CLAUDE.md): *"a
dependency on a decision nobody has made is architectural however small the code
would be"*).

✅ **So the producer publishes and this consumes.** ⚡ **The edge that creates is
the one 05 already ratifies** — *"Workspace & Tenancy → all | Conformist | Every
module conforms; none influences it"* — **and 📁 the row asked for it in terms:
*"Publication rides the existing outbox/relay, not a new mechanism."***

## ⚡ The recipient is the envelope's, and the session is theirs

🔴 **`tenant_scoped_session` is opened with `user_id=SYSTEM_USER_ID`, not with
the recipient's.** ⛔ **The INSERT policy on `notification` is workspace-scoped
precisely so a notification can be written FOR somebody else** — 📁 migration
`0059`. ⚠️ **Setting `app.user_id` to the recipient here would work and would be
wrong**: it would say the recipient acted, on a row recording that somebody else
did.

## ⛔ Idempotency is the dispatcher's, and this handler adds none of its own

📁 **The platform claims `event_id` before invoking a handler**
([06-events.md](../../../../docs/architecture/06-events.md)) — ⚡ **so a
redelivery does not reach here.** ⚠️ **`ai_research_engine`'s handler records
that the claim and the work commit separately, and the same caveat applies:** a
claim lost after this committed would redeliver and write a second row. **The
row has no natural key to deduplicate on** — two genuinely distinct notifications
about one subject are legitimate — ⛔ **so absorbing it silently would be worse
than the duplicate.** ✅ **The at-least-once contract is the platform's and
consumers are required to tolerate it.**
"""

from __future__ import annotations

from collections.abc import Callable
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from modules.workspace_tenancy.application.notify import Notify
from modules.workspace_tenancy.domain.notification import request_from_payload
from signora_platform.db import tenant_scoped_session
from signora_platform.event_bus import EventEnvelope
from signora_platform.observability import get_logger

logger = get_logger(__name__)

CONSUMER_NAME = "workspace_tenancy.notification_requested"
"""A permanent contract. **Renaming it resets the idempotency ledger**, and
every historical request would be re-delivered on replay — which here means
every customer seeing every notification they have ever had, again."""

#: The identity rows are attributed to when the platform acts without a user.
#: The same constant `ai_research_engine`'s handler uses, for the same reason.
SYSTEM_USER_ID = UUID("00000000-0000-0000-0000-000000000001")

NotifyFactory = Callable[[AsyncSession], Notify]


async def deliver_requested_notification(
    envelope: EventEnvelope,
    *,
    session_factory: async_sessionmaker[AsyncSession],
    notify: NotifyFactory,
) -> None:
    """Resolve the channels and deliver, or fail loudly.

    ⛔ **No try/except.** ⚡ **An unregistered channel raises and the event
    dead-letters**, which is the visible failure — 📁 [§10](../../../../CLAUDE.md):
    a channel silently rerouted would report a delivery that did not happen.
    """
    request = request_from_payload(
        workspace_id=envelope.workspace_id, payload=envelope.payload
    )
    async with tenant_scoped_session(
        session_factory, workspace_id=envelope.workspace_id, user_id=SYSTEM_USER_ID
    ) as session:
        notification = await notify(session).notify(request)

    logger.info(
        "notification delivered",
        extra={
            "workspace_id": str(envelope.workspace_id),
            "correlation_id": str(envelope.correlation_id),
            "notification_id": str(notification.id),
            # ⛔ **Not the summary and not the expectation.** ⚡ **Both are
            # customer prose about a customer's account** — 📁
            # [§16](../../../../CLAUDE.md), never log PII without a policy.
            "category": notification.category.value,
            "channels": sorted(channel.value for channel in request.channels),
        },
    )


__all__ = ["CONSUMER_NAME", "deliver_requested_notification"]
