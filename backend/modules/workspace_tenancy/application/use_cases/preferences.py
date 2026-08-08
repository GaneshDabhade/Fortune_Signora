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

from dataclasses import dataclass
from enum import Enum
from typing import Literal
from uuid import UUID

from modules.workspace_tenancy.application.ports import PersonPreferencesRepository
from modules.workspace_tenancy.domain.preferences import (
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

        updated = PersonPreferences(
            workspace_id=current.workspace_id,
            person_id=current.person_id,
            theme=pick(input_.theme, current.theme),
            density=pick(input_.density, current.density),
            time_format=pick(input_.time_format, current.time_format),
            timezone=pick(input_.timezone, current.timezone),
            language=pick(input_.language, current.language),
            pronouns=pick(input_.pronouns, current.pronouns),
            display_name=pick(input_.display_name, current.display_name),
        )
        await self._preferences.save(updated)
        return updated
