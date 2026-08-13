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
from enum import Enum
from typing import Literal
from uuid import UUID

from modules.workspace_tenancy.application.ports import PersonPreferencesRepository
from modules.workspace_tenancy.domain.preferences import (
    AnswerStyle,
    Density,
    PersonPreferences,
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
        )
        await self._preferences.save(updated)
        return updated
