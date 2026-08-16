"""What one person has read, of what this workspace told them.

**[TASK-480](../../../../docs/BACKLOG.md)**, on
[D-239](../../../../docs/DECISION_REGISTER.md) — **the product owner settled
the owner and the shape in one ruling, so this file invents neither.**

## 🔴 The ruling, and what it refused

> ✅ **`workspace_tenancy` owns per-person, per-workspace notification state.**
> ⛔ **No new module · no ADR · no abstraction · no architectural layer** —
> ⚡ ***"we are not building a notification platform."***

📁 **The precedent is `person_preferences` and it is followed exactly rather
than adapted** — 492 §0, quoted on the row:

> ***"A third tenancy class … which is a NARROWING of tenant-owned, never a
> parallel to it. `workspace_id` stays non-nullable and every existing
> guarantee still applies. One predicate is added."***

⚡ **So `workspace_id` is non-nullable, RLS is forced, and the person predicate
`user_id = current_setting('app.user_id')` is added on top — in the policy AND
in the query.** ⛔ **The second half is not belt-and-braces**: 📁 [§8](../../../../CLAUDE.md),
*"queries must still explicitly filter by `workspace_id` as defense-in-depth"*,
**and the person predicate earns the same treatment for the same reason.**

## ⛔ What this file deliberately does not model

**A notification.** ⚡ **This records that a person has READ one** — nothing
about what it said, when it was sent, or which channel carried it. 📁
[ADR-0017](../../../../docs/architecture/adr/0017-notifications.md) owns
delivery and [TASK-495](../../../../docs/BACKLOG.md) builds it.

⛔ **And no workspace-wide event carries per-person state**, which is the
ruling's own exclusion. ⚡ **Read state is the one fact here that is not the
workspace's to know collectively** — *"everyone has read it"* is a coincidence,
never a state.

## ⚠️ Why a read is recorded and an unread is an absence

🔴 **The alternative is a `read: bool` column per person per notification, and
it is worse for a reason that only shows up later**: ⛔ **it requires a row to
exist before a person has done anything**, so every delivery would write one
row per recipient whether or not they ever look. ⚡ **A workspace of 200 people
receiving 50 notifications would hold 10,000 rows describing inaction.**

✅ **A read is a FACT and an unread is the absence of one** — 📁
[§2](../../../../CLAUDE.md), *immutability is the default for anything that
records a fact*. **The count a customer sees is derived, never stored.**
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


class NotificationStateError(ValueError):
    """Every refusal this file makes, so a caller catches one thing."""


@dataclass(frozen=True, slots=True)
class NotificationRead:
    """**One person read one notification, at a time.**

    ⛔ **Immutable, and there is no method to undo it.** ⚡ **A read is a record
    of something that happened**; *mark as unread* is a different product
    feature, and 📁 the design does not ask for one — **inventing it would be
    the [§21](../../../../CLAUDE.md) failure this row's ruling names by
    exclusion.**

    🔴 **`workspace_id` and `user_id` are both required with no default.** ⚡
    **The pair is the primary key and the tenancy narrowing at once** — a read
    that names no workspace is a cross-tenant fact, and one that names no
    person is the collective state this ruling refuses.
    """

    workspace_id: UUID
    user_id: UUID
    notification_id: UUID
    read_at: datetime

    def __post_init__(self) -> None:
        # ⚡ **Construction is the only way in and it re-runs on every read**,
        # which is what makes this hold for a repository rather than only for
        # a caller — the same argument `action_batch` records at gate 4.
        if self.read_at.tzinfo is None:
            raise NotificationStateError(
                "a read time without a timezone is a claim about no particular "
                "moment. Every timestamp this module records is aware, so a "
                "naive one here would be the only one a report could not order."
            )


@dataclass(frozen=True, slots=True)
class UnreadCount:
    """**What the shell puts in the badge.**

    ⚠️ **Derived on every request rather than stored** — 📁
    [§2](../../../../CLAUDE.md), *truth has exactly one authoritative
    representation*. ⛔ **A stored counter is a second copy of a fact the reads
    already carry**, and the two disagree the first time a delivery fails
    half-way.

    ⚡ **`capped` is not a rendering concern.** 📁 The shell shows *"9+"* rather
    than a number, and **a count that stops at the cap costs one bounded query
    instead of one unbounded one** — ⛔ **on a person returning from leave, the
    unbounded version counts thousands of rows to render two characters.**
    """

    #: ⛔ **Never negative, and never larger than {@link CAP}.**
    value: int
    #: ⚡ **`True` when the real number is at least the cap** — the shell reads
    #: this rather than comparing, so *"9+"* has one definition.
    capped: bool

    def __post_init__(self) -> None:
        if self.value < 0:
            raise NotificationStateError(
                f"an unread count of {self.value} is not a count. A negative badge "
                "means the derivation subtracted reads from a total it did not "
                "have, which is a defect to surface rather than a number to clamp."
            )
        if self.value > CAP:
            raise NotificationStateError(
                f"an unread count of {self.value} exceeds the cap of {CAP}. The "
                "query is bounded, so a larger value means it was not the bounded "
                "one — and an unbounded count on this path is what the cap exists "
                "to prevent."
            )


#: 📁 **The shell's badge shows a number up to this and `9+` beyond it.**
#: ⚡ **The cap lives here rather than in the component** so the QUERY can be
#: bounded by it — ⛔ a cap applied only at render still reads every row.
CAP: int = 9


def unread(*, total: int) -> UnreadCount:
    """**Build a count from a bounded query's answer.**

    ⚡ **`total` is what the repository counted, already limited to `CAP + 1`.**
    ⛔ **The extra one is the whole trick**: it distinguishes *exactly nine*
    from *nine or more* without counting further.
    """
    if total < 0:
        raise NotificationStateError(f"a query returned {total} rows, which is not a count")
    return UnreadCount(value=min(total, CAP), capped=total > CAP)


__all__ = [
    "CAP",
    "NotificationRead",
    "NotificationStateError",
    "UnreadCount",
    "unread",
]
