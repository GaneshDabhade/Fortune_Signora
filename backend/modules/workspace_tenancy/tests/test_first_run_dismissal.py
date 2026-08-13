"""**The first-run overlay is dismissible forever** — [TASK-1424].

📁 `Authenticated Entry.dc.html` rule 20: *"Home, with the first-run overlay:
one sentence on what this is, one on what to do, **dismissible forever**."*

⚡ **Forever is the whole assertion.** ⛔ A dismissal that returned at the next
sign-in would be a promise the product breaks, and it is the reason this lives
on `person_preferences` rather than in a browser — 📁 the sibling activation
cards carry the same sentence: *"nothing about activation lives in
localStorage."*
"""

from dataclasses import replace
from datetime import UTC, datetime, timedelta
from uuid import uuid4

from modules.workspace_tenancy.domain.preferences import PersonPreferences, Theme
from modules.workspace_tenancy.interface.schemas import PreferencesResponse

_NOW = datetime(2026, 8, 13, tzinfo=UTC)


def _prefs() -> PersonPreferences:
    return PersonPreferences(workspace_id=uuid4(), person_id=uuid4())


def test_a_new_person_has_not_dismissed_it() -> None:
    """⛔ **`None` is *not dismissed*, and every existing row honestly is.**"""
    assert _prefs().first_run_dismissed_at is None
    assert PreferencesResponse.from_domain(_prefs(), now=_NOW).first_run_dismissed is False


def test_dismissing_records_the_moment() -> None:
    at = datetime(2026, 8, 12, 9, 30, tzinfo=UTC)
    assert _prefs().dismissed_first_run(at).first_run_dismissed_at == at


def test_the_first_moment_wins_and_a_second_dismissal_changes_nothing() -> None:
    """🔴 **Idempotent, and the EARLIEST close is the answer.**

    ⚡ **Overwriting would lose the only fact the column exists to carry** —
    *when did this person stop being new* — and a retried request must not move
    it. ⛔ The same reasoning `entered` records one method up, where a later
    moment must not move somebody's last-used workspace backwards.
    """
    first = datetime(2026, 8, 12, 9, 30, tzinfo=UTC)
    later = datetime(2027, 1, 1, tzinfo=UTC)

    once = _prefs().dismissed_first_run(first)
    twice = once.dismissed_first_run(later)

    assert twice.first_run_dismissed_at == first
    # ⚠️ **The same object, not a copy** — a `replace` that always produced one
    # would make the caller write a row for a person who changed nothing, which
    # is the cost `left()` records beside it.
    assert twice is once


def test_the_response_publishes_the_fact_and_not_the_moment() -> None:
    """⛔ **A client renders on the fact.** ⚡ A timestamp it does not need is a
    timestamp it could display wrongly."""
    dismissed = _prefs().dismissed_first_run(datetime(2026, 8, 12, tzinfo=UTC))
    response = PreferencesResponse.from_domain(dismissed, now=_NOW)

    assert response.first_run_dismissed is True
    assert "first_run_dismissed_at" not in response.model_dump()


class _InMemoryPreferences:
    """The repository's shape, and nothing more."""

    def __init__(self, current: PersonPreferences) -> None:
        self.current = current

    async def get(self, workspace_id: object, person_id: object) -> PersonPreferences:
        return self.current

    async def save(self, preferences: PersonPreferences) -> None:
        self.current = preferences


async def test_changing_one_preference_changes_nothing_else() -> None:
    """🔴 **[B-264] — the guard the suite did not have, and the defect it missed.**

    ⛔ **`ChangePreferencesUseCase` rebuilt `PersonPreferences` from thirteen
    named fields and did not name `last_entered_at`** — so **every profile edit
    reset it to `None`, which reads as *never entered***, and entry rule 12 sent
    a person who had changed their theme back to the workspace chooser.
    **289 tests passed throughout.**

    ⚡ **This asserts over the dataclass's OWN fields rather than a list somebody
    maintains**, which is the only version that catches the fourteenth field.
    📁 The same reasoning `tenancy_policy.py` uses: a table appearing in neither
    list is the thing you cannot enumerate your way to.
    """
    from dataclasses import fields

    from modules.workspace_tenancy.application.use_cases.preferences import (
        ChangePreferencesInput,
        ChangePreferencesUseCase,
    )

    before = _prefs().dismissed_first_run(datetime(2026, 8, 12, tzinfo=UTC))
    before = replace(before, last_entered_at=datetime(2026, 8, 11, tzinfo=UTC))

    repository = _InMemoryPreferences(before)
    after = await ChangePreferencesUseCase(preferences=repository).execute(
        ChangePreferencesInput(
            workspace_id=before.workspace_id,
            person_id=before.person_id,
            theme=Theme.DARK,
        )
    )

    assert after.theme == "dark"
    for field in fields(PersonPreferences):
        if field.name == "theme":
            continue
        assert getattr(after, field.name) == getattr(before, field.name), (
            f"{field.name} changed, and the request never mentioned it"
        )


def test_an_unskipped_invite_is_not_hidden() -> None:
    """⛔ **`None` is *not skipped*, and every existing row is.**"""
    assert _prefs().invite_is_hidden(_NOW) is False


def test_a_skip_hides_it_for_thirty_days_and_then_stops() -> None:
    """📁 ***"Hides them for 30 days per person."***

    ⚡ **The window is DERIVED from the moment and never stored** — 📁 [§2]: a
    stored expiry would be a second representation of a fact the timestamp
    already carries, **and the two disagree the first time a clock moves.**
    """
    skipped = _prefs().skipped_invite(_NOW)

    assert skipped.invite_is_hidden(_NOW) is True
    assert skipped.invite_is_hidden(_NOW + timedelta(days=29)) is True
    # ⛔ **Day thirty is the end of the window, not inside it.**
    assert skipped.invite_is_hidden(_NOW + timedelta(days=30)) is False
    assert skipped.invite_is_hidden(_NOW + timedelta(days=400)) is False


def test_skipping_again_restarts_the_window() -> None:
    """🔴 **The LATEST skip wins, and it is the opposite of a dismissal.**

    ⛔ A dismissal answers *when did this person stop being new*, which the
    first close settles forever. ⚡ **A skip restarts a window** — somebody
    skipping again a month later is asking for another thirty days, **not
    repeating an old request.**
    """
    first = _prefs().skipped_invite(_NOW)
    again = first.skipped_invite(_NOW + timedelta(days=60))

    assert again.invite_skipped_at == _NOW + timedelta(days=60)
    assert again.invite_is_hidden(_NOW + timedelta(days=61)) is True


def test_it_is_reversible() -> None:
    """📁 ***"Reversible from the progress line."*** ⛔ And un-skipping something
    that was never skipped changes nothing rather than writing a row."""
    skipped = _prefs().skipped_invite(_NOW)

    assert skipped.unskipped_invite().invite_is_hidden(_NOW) is False

    never = _prefs()
    assert never.unskipped_invite() is never


def test_the_response_publishes_the_answer_not_the_window() -> None:
    """⛔ **A client that computed the window from a timestamp would answer
    differently on a device whose clock is wrong.**"""
    skipped = _prefs().skipped_invite(_NOW)

    assert PreferencesResponse.from_domain(skipped, now=_NOW).invite_hidden is True
    assert (
        PreferencesResponse.from_domain(skipped, now=_NOW + timedelta(days=31)).invite_hidden
        is False
    )
