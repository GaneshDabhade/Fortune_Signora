"""What has happened to this organization, and who did it.

**Every fact was already stored.** Invitations carry their four states and
their inviter; `membership_role_change` carries every promotion and step back;
an ended membership carries when, by whom and why. **This is the reading, and
it is the half that could always be added later** — which is exactly why the
writing was not deferred.

### Two people per entry, and that is what makes it a different surface

The account timeline answers *what happened to this account* and names nobody.
This answers ***who did what to whom***, and the actor/subject pair is
structural rather than a detail field.

### Identity follows the repository convention (46-team-management.md §24)

**Each entry carries an id and a snapshot.** The snapshot is what was true then
— the address a membership was created with, or the address an invitation was
sent to — and the id is what a screen resolves if a reader needs to *act*
rather than merely read. **Nothing here stores a rendering.**
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from uuid import UUID


class HistoryKind(StrEnum):
    JOINED = "joined"
    INVITED = "invited"
    INVITATION_WITHDRAWN = "invitation_withdrawn"
    INVITATION_ACCEPTED = "invitation_accepted"
    ROLE_CHANGED = "role_changed"
    REMOVED = "removed"


@dataclass(frozen=True, slots=True)
class HistoryEntry:
    """One thing that happened, in the terms it was recorded in.

    **No rendered sentence.** The words a customer reads are a reviewed catalog
    at the frontend edge (ADR-0034), so improving one is a deploy rather than a
    migration — and the same entry can be phrased differently in an export.
    """

    occurred_at: datetime
    kind: HistoryKind
    #: The row this entry was derived from — a membership, an invitation or a
    #: role change. **Added by TASK-443 so the history can be paged**: entries
    #: are derived rather than stored, so a keyset needs a stable tiebreak
    #: that survives two things happening in the same microsecond, and the
    #: source row's identifier is the only one that exists.
    #:
    #: **Not unique across the list** — one membership yields both a `joined`
    #: and a `removed` entry — so it pairs with `kind` and `occurred_at`
    #: rather than standing alone.
    #: Who acted. `None` where nothing recorded one — the founding membership
    #: has no actor but itself, and inventing one would be a guess.
    source_id: UUID
    actor_id: UUID | None
    actor_email: str | None
    #: Who it happened to. An address for an invitation; a membership's
    #: recorded address for everything else.
    subject_email: str | None
    subject_membership_id: UUID | None
    previous_role: str | None = None
    new_role: str | None = None
    #: Verbatim, when somebody gave one.
    reason: str | None = None


__all__ = ["HistoryEntry", "HistoryKind"]
