"""What a person has read, as the shell sees it — **the contract only**.

**[TASK-480](../../../../docs/BACKLOG.md)**, on
[D-239](../../../../docs/DECISION_REGISTER.md), migration `0058`.

## ⛔ Minimal, because the ruling said minimal

📁 **D-239: *"expose only the minimal `workspace_tenancy/public/` contract the
shell actually needs."*** ⚡ **The shell needs two things** — **a badge number,
and a way to say *I have read these*.** ⛔ **Everything else a notification
system usually publishes is absent on purpose**: no per-notification read
timestamps, no *who else has read it*, no history.

⚠️ **That last one is not an omission to fill in later.** 📁 **The ruling's own
exclusion**: *no workspace-wide domain event carries per-person state.* ⚡ **A
port that answered *"who has read this"* would make one person's state the
workspace's to query**, which is the disclosure the person predicate exists to
prevent.

## 🔴 The caller supplies the candidates, and that is a boundary rather than a limitation

⛔ **This module does not know what a notification is.** 📁
[ADR-0017](../../../../docs/architecture/adr/0017-notifications.md) owns
delivery and [TASK-495](../../../../docs/BACKLOG.md) builds it. ✅ **So the
question this can honestly answer is *which of THESE has this person not
read*** — **and a signature that took no candidates would be promising a count
over a set it cannot see.**

## ⚡ Why a count type rather than an `int`

📁 **The shell renders `9+`.** ⛔ **An `int` would push *is this capped* to
every caller**, and the first one to compare against `9` itself has written the
cap down twice — 📁 [§2](../../../../CLAUDE.md), *behaviour exists exactly
once*. ✅ **{@link UnreadBadge} carries both, so the rule has one home.**
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol
from uuid import UUID

from modules.workspace_tenancy.domain.notification_state import CAP, UnreadCount

#: ⚡ **The shell's badge, and the name it is rendered under.** ⛔ **Re-exported
#: rather than redefined**: a second shape here would be a second definition of
#: the same fact ([§2](../../../../CLAUDE.md)).
UnreadBadge = UnreadCount

__all__ = [
    "CAP",
    "NotificationReadWriter",
    "NotificationStateReader",
    "UnreadBadge",
]


class NotificationStateReader(Protocol):
    """What the shell asks. **One question, and it names its own scope.**"""

    async def unread(
        self, workspace_id: UUID, person_id: UUID, candidates: Sequence[UUID]
    ) -> UnreadBadge:
        """How many of `candidates` this person has not read.

        ⚡ **Bounded by {@link CAP}** — the answer distinguishes *exactly nine*
        from *nine or more* and counts no further, because the badge cannot
        render the difference.

        🔴 **`person_id` is required and has no default.** ⛔ **A signature
        that defaulted it would answer for *the workspace*, and there is no
        such fact** — 📁 D-239's exclusion: read state is per person, and
        *"everyone has read it"* is a coincidence rather than a state.
        """
        ...


class NotificationReadWriter(Protocol):
    """What the shell records. **One verb, and no way to undo it.**"""

    async def mark_read(
        self, workspace_id: UUID, person_id: UUID, notification_ids: Sequence[UUID]
    ) -> None:
        """Record that this person has read these.

        ✅ **Idempotent.** ⚡ **Marking twice is something a customer does by
        double-clicking**, and the first read time survives — 📁
        [§2](../../../../CLAUDE.md), a record of what was true then is not
        rewritten.

        ⛔ **There is no `mark_unread`, and the absence is deliberate.** 📁 **The
        table has no `UPDATE` grant** and a read is a record of something that
        happened. ⚠️ **If the product ever asks for it, it is a DELETE** — the
        row stops existing, which is the same shape as *an unread is the
        absence of a row*. **A port offering an edit would promise what the
        database refuses.**
        """
        ...
