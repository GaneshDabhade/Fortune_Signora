"""Reading and changing preferences — [TASK-470](../../../../docs/BACKLOG.md).

⚡ **The case that matters is the partial write.** The design's profile is
several panels edited independently, so a request that mentions the theme must
leave the pronouns alone — and `None` cannot express *not mentioned*, because
clearing a field is a legitimate thing to ask for.
"""

from __future__ import annotations

from uuid import uuid4

import pytest

from modules.workspace_tenancy.application.use_cases.preferences import (
    ChangePreferencesInput,
    ChangePreferencesUseCase,
    GetPreferencesUseCase,
)
from modules.workspace_tenancy.domain.preferences import Density, Theme, TimeFormat
from modules.workspace_tenancy.tests.fakes import FakePersonPreferencesRepository

pytestmark = pytest.mark.asyncio


class TestSomebodyWhoHasNeverOpenedTheScreen:
    async def test_reads_the_defaults_rather_than_nothing(self) -> None:
        """⛔ **The absence of a row is not the absence of an answer.** A port
        that could answer `None` would push that reasoning into every caller,
        and the first to forget it renders a blank profile to a new account."""
        prefs = await GetPreferencesUseCase(preferences=FakePersonPreferencesRepository()).execute(
            uuid4(), uuid4()
        )

        assert prefs.theme is Theme.SYSTEM
        assert prefs.timezone is None


class TestAPartialChange:
    async def test_changing_the_theme_leaves_everything_else_alone(self) -> None:
        repo = FakePersonPreferencesRepository()
        change = ChangePreferencesUseCase(preferences=repo)
        ws, person = uuid4(), uuid4()
        await change.execute(
            ChangePreferencesInput(
                workspace_id=ws, person_id=person, pronouns="she/her", timezone="Europe/Copenhagen"
            )
        )

        after = await change.execute(
            ChangePreferencesInput(workspace_id=ws, person_id=person, theme=Theme.DARK)
        )

        assert after.theme is Theme.DARK
        assert after.pronouns == "she/her"
        assert after.timezone == "Europe/Copenhagen"

    async def test_clearing_a_field_is_possible_and_is_not_the_same_as_omitting_it(
        self,
    ) -> None:
        """**The whole reason `UNSET` exists.** With `None` meaning both, a
        panel that omitted a field it does not own would silently erase what
        another panel had set."""
        repo = FakePersonPreferencesRepository()
        change = ChangePreferencesUseCase(preferences=repo)
        ws, person = uuid4(), uuid4()
        await change.execute(
            ChangePreferencesInput(workspace_id=ws, person_id=person, pronouns="she/her")
        )

        cleared = await change.execute(
            ChangePreferencesInput(workspace_id=ws, person_id=person, pronouns=None)
        )

        assert cleared.pronouns is None

    async def test_a_change_persists_and_reads_back(self) -> None:
        repo = FakePersonPreferencesRepository()
        ws, person = uuid4(), uuid4()
        await ChangePreferencesUseCase(preferences=repo).execute(
            ChangePreferencesInput(
                workspace_id=ws,
                person_id=person,
                density=Density.COMPACT,
                time_format=TimeFormat.TWELVE_HOUR,
            )
        )

        reread = await GetPreferencesUseCase(preferences=repo).execute(ws, person)

        assert reread.density is Density.COMPACT
        assert reread.time_format is TimeFormat.TWELVE_HOUR

    async def test_one_persons_change_is_not_anothers(self) -> None:
        """🔴 **The Security Invariant this row names, at the layer above the
        policy.** A preference row must never become a route to another
        account's data — and the query predicate is the first of the two
        guards, the RLS policy being the one that holds regardless."""
        repo = FakePersonPreferencesRepository()
        ws, me, colleague = uuid4(), uuid4(), uuid4()
        await ChangePreferencesUseCase(preferences=repo).execute(
            ChangePreferencesInput(workspace_id=ws, person_id=me, theme=Theme.DARK)
        )

        theirs = await GetPreferencesUseCase(preferences=repo).execute(ws, colleague)

        assert theirs.theme is Theme.SYSTEM
