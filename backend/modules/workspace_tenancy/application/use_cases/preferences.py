"""Reading and changing what a person chose — **[TASK-470](../../../../../docs/BACKLOG.md)**.

⚡ **Two use cases, and the write is a *partial* one.** The design's profile is
several panels a person edits independently: changing the theme on
`03 Appearance` must not clear the pronouns they set on `01`. **So the input
distinguishes *not supplied* from *set to nothing*** — a distinction a plain
`str | None` cannot make, and the reason `UNSET` exists below.

⛔ **Nothing here decides a default.** The aggregate carries them, so a person
who has never opened the screen gets the same answer from the domain that the
screen would draw.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime
from enum import Enum
from typing import Literal
from uuid import UUID

from modules.workspace_tenancy.application.ports import PersonPreferencesRepository
from modules.workspace_tenancy.domain.preferences import (
    AnswerStyle,
    Density,
    HomeCardLayout,
    PersonPreferences,
    ScreenReaderVerbosity,
    TextSize,
    Theme,
    TimeFormat,
)


class _Unset(Enum):
    """A sentinel, because `None` is a legitimate value here.

    ⛔ **Clearing a timezone and not mentioning it are different requests.**
    With `None` meaning both, a panel that omits a field it does not own would
    silently erase whatever another panel had set — which is the defect the
    onboarding company step also had to avoid, one workflow over.
    """

    TOKEN = 0


UNSET = _Unset.TOKEN
type Maybe[T] = T | Literal[_Unset.TOKEN]


@dataclass(frozen=True)
class ChangePreferencesInput:
    workspace_id: UUID
    person_id: UUID
    theme: Maybe[Theme] = UNSET
    density: Maybe[Density] = UNSET
    time_format: Maybe[TimeFormat] = UNSET
    timezone: Maybe[str | None] = UNSET
    language: Maybe[str | None] = UNSET
    pronouns: Maybe[str | None] = UNSET
    display_name: Maybe[str | None] = UNSET
    ai_insights: Maybe[bool] = UNSET
    ai_drafts: Maybe[bool] = UNSET
    always_show_citations: Maybe[bool] = UNSET
    answer_style: Maybe[AnswerStyle] = UNSET
    confidence_floor: Maybe[int] = UNSET
    #: 📁 **Home's rule 2.** ⚡ `Maybe`, so *absent* and *cleared to None* stay
    #: distinguishable — clearing the preference must return somebody to their
    #: role's composition rather than being ignored.
    home_composition: Maybe[str | None] = UNSET
    # ── The design's Profile, Language & region and Accessibility panels ──
    date_format: Maybe[str | None] = UNSET
    number_format: Maybe[str | None] = UNSET
    week_starts_on: Maybe[str | None] = UNSET
    reduce_motion: Maybe[bool] = UNSET
    increase_contrast: Maybe[bool] = UNSET
    always_show_focus_ring: Maybe[bool] = UNSET
    underline_links: Maybe[bool] = UNSET
    text_size: Maybe[TextSize] = UNSET
    screen_reader_verbosity: Maybe[ScreenReaderVerbosity] = UNSET


class GetPreferencesUseCase:
    def __init__(self, *, preferences: PersonPreferencesRepository) -> None:
        self._preferences = preferences

    async def execute(self, workspace_id: UUID, person_id: UUID) -> PersonPreferences:
        return await self._preferences.get(workspace_id, person_id)


class ChangePreferencesUseCase:
    """Apply only what the request actually mentioned."""

    def __init__(self, *, preferences: PersonPreferencesRepository) -> None:
        self._preferences = preferences

    async def execute(self, input_: ChangePreferencesInput) -> PersonPreferences:
        current = await self._preferences.get(input_.workspace_id, input_.person_id)

        def pick[T](supplied: Maybe[T], existing: T) -> T:
            return existing if supplied is UNSET else supplied

        # 🔴 **`replace` on the CURRENT value, never a rebuild** —
        # [B-264](../../../../../docs/BUGS.md).
        #
        # ⛔ **This constructed a fresh `PersonPreferences` from thirteen named
        # fields, and it did not name `last_entered_at`** — so **every profile
        # edit reset it to `None`, which reads as *never entered***, and entry
        # rule 12 sent a person who had changed their theme back to the
        # workspace chooser.
        #
        # ⚡ **The defect is the SHAPE rather than the missing line.** A
        # rebuild-everything use case silently drops any field added after it
        # was written, and this one has now been extended twice —
        # `last_entered_at` by [TASK-1422] and `first_run_dismissed_at` by
        # [TASK-1424], which would have inherited the same bug and broken
        # *"dismissible forever"* the first time somebody changed a setting.
        #
        # ✅ **`replace` carries every unmentioned field by construction**, so a
        # fourteenth field is safe without anybody remembering this file.
        updated = replace(
            current,
            theme=pick(input_.theme, current.theme),
            density=pick(input_.density, current.density),
            time_format=pick(input_.time_format, current.time_format),
            timezone=pick(input_.timezone, current.timezone),
            language=pick(input_.language, current.language),
            pronouns=pick(input_.pronouns, current.pronouns),
            display_name=pick(input_.display_name, current.display_name),
            ai_insights=pick(input_.ai_insights, current.ai_insights),
            ai_drafts=pick(input_.ai_drafts, current.ai_drafts),
            always_show_citations=pick(
                input_.always_show_citations, current.always_show_citations
            ),
            answer_style=pick(input_.answer_style, current.answer_style),
            confidence_floor=pick(input_.confidence_floor, current.confidence_floor),
            home_composition=pick(input_.home_composition, current.home_composition),
            date_format=pick(input_.date_format, current.date_format),
            number_format=pick(input_.number_format, current.number_format),
            week_starts_on=pick(input_.week_starts_on, current.week_starts_on),
            reduce_motion=pick(input_.reduce_motion, current.reduce_motion),
            increase_contrast=pick(input_.increase_contrast, current.increase_contrast),
            always_show_focus_ring=pick(
                input_.always_show_focus_ring, current.always_show_focus_ring
            ),
            underline_links=pick(input_.underline_links, current.underline_links),
            text_size=pick(input_.text_size, current.text_size),
            screen_reader_verbosity=pick(
                input_.screen_reader_verbosity, current.screen_reader_verbosity
            ),
        )
        await self._preferences.save(updated)
        return updated


class DismissFirstRunUseCase:
    """Record that this person closed the first-run overlay.

    ⚡ **A use case rather than a `ChangePreferences` field**, and the
    distinction is the design's. 📁 Rule 20's overlay is *"dismissible
    forever"* — ⛔ **there is no control anywhere that un-dismisses it**, so it
    is an event somebody caused rather than a setting they can see and change.
    **Routing it through the partial-update endpoint would put it in the
    profile panel's vocabulary**, where a reader would reasonably expect a
    toggle back.

    ⚠️ **`now` is a parameter, matching {@link RecordEntryUseCase} on the same
    table** — 📁 *"the clock is injected, everywhere"*, and a use case reading
    the wall clock itself is the untestable shape this module already refuses.
    """

    def __init__(self, *, preferences: PersonPreferencesRepository) -> None:
        self._preferences = preferences

    async def execute(
        self, workspace_id: UUID, person_id: UUID, *, now: datetime
    ) -> PersonPreferences:
        current = await self._preferences.get(workspace_id, person_id)
        dismissed = current.dismissed_first_run(now)
        # ⛔ **Only when something changed.** ⚡ A second dismissal must not
        # write a row, for the reason `left()` records: a write that stores no
        # new fact is a row created for nothing.
        if dismissed is not current:
            await self._preferences.save(dismissed)
        return dismissed


class ChooseHomeLayoutUseCase:
    """How this person arranged one composition's cards — Home §10's *Customise*.

    📁 `3.2.3`: *"card order within a composition is **stable across visits**."*
    📁 `U-05`'s interim: *"**reorder and remove only.**"*

    ⚡ **One composition per call**, matching the panel: it shows the composition
    the person is looking at, and 📁 the design scopes the control *"within a
    composition"*. ⛔ **Replacing the whole map would let that panel wipe an
    arrangement the person cannot see**, which they would meet the next time they
    switched with no way to know what happened.
    """

    def __init__(self, *, preferences: PersonPreferencesRepository) -> None:
        self._preferences = preferences

    async def execute(
        self,
        workspace_id: UUID,
        person_id: UUID,
        *,
        composition: str,
        layout: HomeCardLayout,
    ) -> PersonPreferences:
        current = await self._preferences.get(workspace_id, person_id)
        chosen = current.choose_home_layout(composition, layout)
        # ⛔ **Only when something changed**, the rule every neighbour here
        # follows: a write that stores no new fact is a row created for nothing.
        if chosen != current:
            await self._preferences.save(chosen)
        return chosen


class AcknowledgeSetupCompleteUseCase:
    """This person has been told that setup finished — Home state 04.

    📁 ***"A one-time strip states that setup is finished and what changed"***,
    and `AC-H03`'s *"shown **exactly once**"*.

    ⚡ **An event, not a setting** — the same shape as
    {@link DismissFirstRunUseCase} above, and for the same reason: **there is no
    control in the design that un-shows it.**

    ⚠️ **It does not decide WHETHER setup is complete.** 📁 Completion is
    *"derived from the source of truth, never stored on Home"*, and this records
    only that a reader was told. ⛔ **Calling this on a workspace that has not
    finished activating would be a client lying to itself** — nothing here can
    check that, which is why the strip's condition stays where the truth is.
    """

    def __init__(self, *, preferences: PersonPreferencesRepository) -> None:
        self._preferences = preferences

    async def execute(
        self, workspace_id: UUID, person_id: UUID, *, now: datetime
    ) -> PersonPreferences:
        current = await self._preferences.get(workspace_id, person_id)
        seen = current.saw_setup_complete(now)
        # ⛔ **Only when something changed** — a second acknowledgement writes
        # nothing, the same rule its two neighbours follow.
        if seen is not current:
            await self._preferences.save(seen)
        return seen


class SkipInviteUseCase:
    """Put the invite-the-team activation card away for thirty days.

    📁 ***"Non-blocking cards can be skipped, which hides them for 30 days per
    person and is reversible from the progress line."***

    ⚠️ **`skip=False` un-skips**, rather than a second use case. ⚡ **The design
    calls reversal part of the same control**, and two use cases would let one
    exist without the other — which is how a product ships a hide with no way
    back.
    """

    def __init__(self, *, preferences: PersonPreferencesRepository) -> None:
        self._preferences = preferences

    async def execute(
        self, workspace_id: UUID, person_id: UUID, *, skip: bool, now: datetime
    ) -> PersonPreferences:
        current = await self._preferences.get(workspace_id, person_id)
        updated = current.skipped_invite(now) if skip else current.unskipped_invite()
        if updated is not current:
            await self._preferences.save(updated)
        return updated
