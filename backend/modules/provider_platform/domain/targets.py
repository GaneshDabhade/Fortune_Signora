"""What a customer has asked to be watched, and what has actually been read.

**The delta this module computes is not the delta it is handed.**
[ADR-0036](../../../../docs/architecture/adr/0036-target-account-contract.md) §4
is explicit: Commercial Profile could compute a difference between two
*declarations*, and it would answer the wrong question. What matters here is
the difference against **what has actually been synced** — a different set, and
one only this module holds.

The case that separates them: a customer declares Acme, the fetch fails, and
later they re-add Acme after removing it. A declaration-delta calls that *"no
change"*. It is not: nothing was ever read.
"""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True, slots=True)
class DeclaredAccount:
    """One company a customer asked Signora to watch.

    `subject` is **exactly what they typed** — unresolved, unnormalised, and
    not guaranteed to identify anything (ADR-0036 §5). Resolution happens
    downstream in the Knowledge Graph; asking a customer to perform it would
    hand Signora's own competence back across the table.

    `id` is the declaration entry's stable identifier, which is what makes a
    *rename* distinguishable from a *remove and add*. Those are different
    instructions about spending money.
    """

    id: UUID
    subject: str


@dataclass(frozen=True, slots=True)
class TargetSyncState:
    """The declaration this workspace's targets were last synchronised against.

    **Ordering, not idempotency.** Idempotency on `event_id` stops one event
    being handled twice; it does nothing about two events arriving in the wrong
    order. Two declarations in quick succession are two workspace-level events,
    and a handler for version 5 running after version 6's would act on a list
    one revision stale.
    """

    workspace_id: UUID
    #: `None` when this workspace has never been synchronised against any
    #: declaration — distinct from version 0, which nothing produces.
    declaration_version: int | None = None

    def is_stale(self, incoming: int) -> bool:
        """Whether an announced version has already been overtaken.

        **Equal counts as stale.** Re-handling the version already acted on
        would re-derive a delta that is by definition empty, and the only way
        it could be non-empty is if a sync failed — which is a retry's job,
        not a redelivered event's.
        """
        return self.declaration_version is not None and incoming <= self.declaration_version


def subjects_needing_sync(
    declared: tuple[DeclaredAccount, ...], already_read: frozenset[str]
) -> tuple[str, ...]:
    """Which declared companies have never been successfully read.

    **`already_read` is what has a position**, not what has a watermark row. A
    watermark that exists with no position records an attempt that stored
    nothing, and an account nobody has ever managed to fetch is exactly the
    case a declaration-delta would call *"no change"*.

    **Order follows the declaration.** The customer's own order is the only
    one with any meaning here — nothing in this module knows which of their
    companies matters more, and inventing a priority would be a commercial
    judgement nobody asked for.

    Duplicates collapse: two entries naming the same company are one thing to
    fetch, however many times it was typed.
    """
    seen: set[str] = set()
    needing: list[str] = []
    for account in declared:
        if account.subject in already_read or account.subject in seen:
            continue
        seen.add(account.subject)
        needing.append(account.subject)
    return tuple(needing)


__all__ = ["DeclaredAccount", "TargetSyncState", "subjects_needing_sync"]
