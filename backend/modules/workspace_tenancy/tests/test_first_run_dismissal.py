"""**The first-run overlay is dismissible forever** — [TASK-1424].

📁 `Authenticated Entry.dc.html` rule 20: *"Home, with the first-run overlay:
one sentence on what this is, one on what to do, **dismissible forever**."*

⚡ **Forever is the whole assertion.** ⛔ A dismissal that returned at the next
sign-in would be a promise the product breaks, and it is the reason this lives
on `person_preferences` rather than in a browser — 📁 the sibling activation
cards carry the same sentence: *"nothing about activation lives in
localStorage."*
"""

from datetime import datetime, timezone
from uuid import uuid4

from modules.workspace_tenancy.domain.preferences import PersonPreferences
from modules.workspace_tenancy.interface.schemas import PreferencesResponse


def _prefs() -> PersonPreferences:
    return PersonPreferences(workspace_id=uuid4(), person_id=uuid4())


def test_a_new_person_has_not_dismissed_it() -> None:
    """⛔ **`None` is *not dismissed*, and every existing row honestly is.**"""
    assert _prefs().first_run_dismissed_at is None
    assert PreferencesResponse.from_domain(_prefs()).first_run_dismissed is False


def test_dismissing_records_the_moment() -> None:
    at = datetime(2026, 8, 12, 9, 30, tzinfo=timezone.utc)
    assert _prefs().dismissed_first_run(at).first_run_dismissed_at == at


def test_the_first_moment_wins_and_a_second_dismissal_changes_nothing() -> None:
    """🔴 **Idempotent, and the EARLIEST close is the answer.**

    ⚡ **Overwriting would lose the only fact the column exists to carry** —
    *when did this person stop being new* — and a retried request must not move
    it. ⛔ The same reasoning `entered` records one method up, where a later
    moment must not move somebody's last-used workspace backwards.
    """
    first = datetime(2026, 8, 12, 9, 30, tzinfo=timezone.utc)
    later = datetime(2027, 1, 1, tzinfo=timezone.utc)

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
    dismissed = _prefs().dismissed_first_run(datetime(2026, 8, 12, tzinfo=timezone.utc))
    response = PreferencesResponse.from_domain(dismissed)

    assert response.first_run_dismissed is True
    assert "first_run_dismissed_at" not in response.model_dump()
