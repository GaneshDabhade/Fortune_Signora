"""Where somebody was working, and where they may still go.

**[TASK-1422](../../../../../docs/BACKLOG.md) · Workflow 29 · rule 12
`LAST_USED`.**

## 🔴 The hazard this row exists for, and the shape that removes it

📁 **[D-196](../../../../../docs/DECISION_REGISTER.md)**: *"last-used workspace
is a stored preference that **OUTLIVES MEMBERSHIP** — if it is not cleared on
removal, a departed member's next login routes at a workspace they can no
longer see, which is an authorization failure wearing a convenience feature's
clothes."*

⛔ **The obvious implementation is a `last_used_workspace_id` pointer, and it is
the one that carries the hazard**: the pointer is a second representation of a
fact the preference rows already hold, so **the two disagree the first time a
membership ends without something remembering to rewrite it.**

✅ **So there is no pointer.** ⚡ **Each workspace's row records when this person
last entered it, and the answer is DERIVED over their live memberships** —
📁 [§2](../../../../../CLAUDE.md), *truth has exactly one authoritative
representation; everything else derives from it.*

🔴 **That is what makes the clearing provable rather than diligent.** **A
workspace somebody has left is not in the set the derivation reads**, so the
stale row is *unreachable* rather than merely *stale* — **there is nothing to
forget to clear**, which is [§2](../../../../../CLAUDE.md)'s *prefer a
violation that is unrepresentable over one that is merely discouraged.*

## ⚠️ The row's own distinction, kept

📁 *"A stale preference cannot route anybody — TASK-1400 already asserts that
over 2,880 session/intent pairs — ⛔ but it CAN cost a person their real
destination and land them at the chooser, which is a correctness defect rather
than a security one."*

⚡ **Both halves are true here and the tests say so separately.** The engine is
the security control; this is the correctness one, **and neither is asked to be
the other.**
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from modules.workspace_tenancy.application.ports import (
    PersonPreferencesRepository,
    RoleChangeLog,
)
from modules.workspace_tenancy.domain.entities import RoleChange


@dataclass(frozen=True, slots=True)
class Entry:
    """What Home needs to know about one arrival.

    🔴 **Three of Authenticated Entry's rules terminate on Home and all three are
    entry-time facts**, which is why one call answers them together:
    **rule 12** confirms which workspace for four seconds, **Home state 13**
    suppresses that on a return visit, and **rule 21** *"adds a notice naming what
    changed and by whom"*.

    ⛔ **All of them are read BEFORE the entry is recorded.** ⚡ Recording it moves
    `last_entered_at` to now, so *"since last session"* and *"first today"* both
    become meaningless to anything that asks afterwards.
    """

    first_today: bool
    #: 📁 Rule 21 — `None` when nothing changed since this person was last here.
    role_change: RoleChange | None


@dataclass(frozen=True, slots=True)
class RecordWorkspaceEntry:
    """Somebody is in this workspace, now.

    ⛔ **Not *"they chose this workspace"*.** Entering is something a person
    does; choosing is a setting they can see. **There is no such control in the
    design**, and naming it as one would invite somebody to build the screen.
    """

    preferences: PersonPreferencesRepository
    #: 📁 **Rule 21's source** — the append-only log, read rather than written.
    history: RoleChangeLog

    async def execute(self, workspace_id: UUID, person_id: UUID, *, now: datetime) -> Entry:
        """Record the entry, and answer **whether it was the first one today.**

        🔴 **The answer is read BEFORE the write, and that order is the whole
        reason this returns anything.** ⚡ Recording an entry sets
        `last_entered_at` to `now`, so *"is this the first entry today?"* is
        `False` for every caller that asks afterwards — 📁 including Home, whose
        state 13 is *"second or later entry on the same calendar day"* and whose
        confirmation strip is *"gone on the second visit that day"* (Entry rule 12).

        ⛔ **Not a separate read endpoint.** Two calls would let the second one
        land after the write, which is the same bug one round trip later; and a
        `GET` that decided this would have to write to be meaningful, which §7
        keeps out of a read.
        """
        current = await self.preferences.get(workspace_id, person_id)
        first_today = current.first_entry_today(now)
        # 📁 **Rule 21 — *"role changed since last session"*.** ⛔ Read before the
        # write, for the same reason `first_today` is: `last_entered_at` IS *last
        # session*, and recording this arrival overwrites it.
        role_change = await self.history.latest_since(
            workspace_id=workspace_id, person_id=person_id, since=current.last_entered_at
        )
        entered = current.entered(now)
        # ⚡ **Nothing is written when nothing changed.** The aggregate refuses
        # a moment older than the one it holds, so a retried request or a clock
        # that stepped back costs an idempotent read rather than a write that
        # moves somebody's destination backwards.
        if entered is not current:
            await self.preferences.save(entered)
        return Entry(first_today=first_today, role_change=role_change)


@dataclass(frozen=True, slots=True)
class ForgetWorkspaceEntry:
    """A membership ended — forget that this person was ever here.

    🔴 **Hygiene, and NOT the control.** ⚡ **The control is the derivation
    below, which reads only live memberships**, so this row is already
    unreachable by the time this runs.

    ⛔ **It is still done**, because a record of where somebody used to work
    should not outlive their access to it — 📁 the same reasoning
    [§2](../../../../../CLAUDE.md) applies to immutability: *the rows most worth
    keeping quiet about are always the inconvenient ones.*

    ⚠️ **And it is stated as hygiene rather than sold as the fix**, because a
    guard that is not load-bearing but is described as one is exactly the
    Decorative Logic [§2](../../../../../CLAUDE.md) names.
    """

    preferences: PersonPreferencesRepository

    async def execute(self, workspace_id: UUID, person_id: UUID) -> None:
        current = await self.preferences.get(workspace_id, person_id)
        forgotten = current.left()
        if forgotten is not current:
            await self.preferences.save(forgotten)


@dataclass(frozen=True, slots=True)
class ResolveLastUsedWorkspace:
    """Which of the workspaces this person may enter did they use most recently.

    ⛔ **`live_workspace_ids` is a required argument and cannot be empty of
    meaning.** ⚡ **A signature that let a caller ask *across all workspaces*
    would be a signature somebody eventually calls that way** — and that call is
    the D-196 defect, restored by convenience
    ([§2](../../../../../CLAUDE.md), *types should make incorrect architecture
    impossible*).

    ⚠️ **`None` when nothing qualifies**, and the caller is meant to route to
    the chooser. 📁 **Rule 13 `AMBIGUOUS` is the designed destination for
    exactly that**, so answering *nothing* is an answer rather than a failure.
    """

    preferences: PersonPreferencesRepository

    async def execute(
        self, person_id: UUID, live_workspace_ids: frozenset[UUID]
    ) -> UUID | None:
        best: tuple[datetime, UUID] | None = None

        for workspace_id in live_workspace_ids:
            entered = (await self.preferences.get(workspace_id, person_id)).last_entered_at
            # ⛔ **`None` is *never entered*, not *entered at the beginning of
            # time*.** Treating it as a very old timestamp would let a workspace
            # nobody has opened win a comparison against another that is also
            # unentered, and rule 12 would fire on a person who has been nowhere.
            if entered is None:
                continue
            if best is None or entered > best[0]:
                best = (entered, workspace_id)

        return None if best is None else best[1]


__all__ = [
    "Entry",
    "ForgetWorkspaceEntry",
    "RecordWorkspaceEntry",
    "ResolveLastUsedWorkspace",
]
