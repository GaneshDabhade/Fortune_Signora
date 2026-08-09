"""The activity stream, as other modules see it — **the contract only**.

**[TASK-492](../../../../docs/BACKLOG.md)**, migration `0046`, on
[493 §5](../../../../docs/architecture/493-security-platform-architecture.md).

### Why a port rather than a table other modules write to

📁 **[§8](../../../../CLAUDE.md): *"A module owns its own tables. No other
module's code may write to them directly."*** ⚡ **Every module has facts worth
recording** — a sign-in, a reset, a role change, a connection revoked — and the
alternative to this port is either thirteen private audit tables or twelve
modules reaching into one that is not theirs.

### ⛔ Write-only, and that is the whole contract today

📁 **[P-C](../../../../docs/DOMAIN_DISCOVERY_REGISTER.md): an event exists when
a consumer appears, and none has.** **The Security Center screens that READ
this stream are Workflow 23 and are not this row's**, so no reader is published
— ⛔ **a `SecurityEventReader` written now would be a contract nothing exercises
and everything would have to keep compatible.**

⚡ **The write side is published because it has FOUR producers waiting**, which
is the opposite situation and the reason the asymmetry is deliberate rather
than an oversight.

### 🔴 The two identities travel in the type, not in the call

**{@link SecurityEvent} carries `subject_id` and `acting_for`, both required.**
⛔ **This port deliberately does NOT offer `record(kind, subject, …)` as loose
arguments** — a signature a caller can satisfy with one identity is a signature
that will eventually be satisfied with one identity, and 496 §3's rule would
then hold only where somebody remembered it.
"""

from __future__ import annotations

from typing import Protocol

from modules.workspace_tenancy.domain.security_event import (
    ForbiddenDetailKey,
    MalformedEventKind,
    SecurityEvent,
)


class SecurityEventWriter(Protocol):
    """What a producing module depends on.

    ⛔ **One method, and no way to change anything already written.** The table
    has no `UPDATE` grant; a port offering an edit would promise what the
    database refuses.
    """

    async def record(self, event: SecurityEvent) -> None:
        """Append one event.

        ⚠️ **Raises {@link ForbiddenDetailKey} if `detail` carries a
        credential** and {@link MalformedEventKind} if the kind is not
        `noun.verb_past`. **Both are raised by the type on construction**, so a
        producer that builds its event before calling this has already been
        refused.
        """
        ...


__all__ = [
    "ForbiddenDetailKey",
    "MalformedEventKind",
    "SecurityEvent",
    "SecurityEventWriter",
]
