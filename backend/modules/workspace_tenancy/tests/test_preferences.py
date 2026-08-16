"""**Person preferences** — [TASK-470](../../../../docs/BACKLOG.md), Workflow 9.

⚡ **The tests are mostly about defaults and about what is *not* stored**,
because that is where this aggregate can lie: a person who has never opened
the screen still has preferences, and a value the product chose for them must
not be indistinguishable from one they picked.
"""

from __future__ import annotations

from dataclasses import replace
from uuid import uuid4

from modules.workspace_tenancy.domain.preferences import (
    Density,
    PersonPreferences,
    ScreenReaderVerbosity,
    TextSize,
    Theme,
    TimeFormat,
)


def _prefs() -> PersonPreferences:
    return PersonPreferences(workspace_id=uuid4(), person_id=uuid4())


class TestSomebodyWhoHasNeverOpenedTheScreen:
    def test_still_has_preferences(self) -> None:
        """⛔ **The absence of a row is not the absence of an answer.** A screen
        rendering blank for a new account would show a state the product does
        not have."""
        prefs = _prefs()

        assert prefs.theme is Theme.SYSTEM
        assert prefs.density is Density.COMFORTABLE
        assert prefs.time_format is TimeFormat.TWENTY_FOUR_HOUR

    def test_the_default_theme_follows_the_device_rather_than_picking_one(self) -> None:
        """⚡ **`SYSTEM`, not `LIGHT`.** The product has no opinion about a
        person's lighting until they express one, and *"follows your device"*
        is the choice that assumes least."""
        assert _prefs().theme is Theme.SYSTEM

    def test_an_unchosen_timezone_is_absent_rather_than_utc(self) -> None:
        """⛔ **`None` and `UTC` are different facts.** The design *offers* to
        change the zone and never asserts one, so a stored `UTC` would be an
        answer nobody gave — and the offer could never be shown again."""
        assert _prefs().timezone is None

    def test_pronouns_are_never_guessed(self) -> None:
        """⚠️ **Optional and person-authored.** Inferring somebody's pronouns
        from a name is worse than leaving the field empty."""
        assert _prefs().pronouns is None


class TestChoosing:
    def test_a_theme_is_recorded(self) -> None:
        assert _prefs().choose_theme(Theme.DARK).theme is Theme.DARK

    def test_system_stays_system_and_is_not_resolved_for_storage(self) -> None:
        """🔴 **The server must never resolve `SYSTEM` into a fixed value.**
        The person asked to follow the device; answering with one reading of
        it replaces their choice."""
        resolved = _prefs().choose_theme(Theme.SYSTEM)

        assert resolved.theme is Theme.SYSTEM
        assert resolved.theme.value == "system"

    def test_choosing_one_thing_changes_nothing_else(self) -> None:
        prefs = _prefs().choose_theme(Theme.DARK).choose_density(Density.COMPACT)

        after = prefs.choose_timezone("Europe/Copenhagen")

        assert after.theme is Theme.DARK
        assert after.density is Density.COMPACT
        assert after.timezone == "Europe/Copenhagen"

    def test_it_is_frozen(self) -> None:
        import pytest

        with pytest.raises(AttributeError):
            _prefs().theme = Theme.DARK  # type: ignore[misc]


class TestTheAggregateDoesNotKnowWhatAThemeLooksLike:
    """⛔ **Rendering is the frontend's.** A `Theme` carrying colours would put
    the design system in the database, where a token edit could not reach it.

    ⚠️ **The first version of this scanned the module source for `#` and `rgb(`
    and failed on the docstring's own markdown headings.** **A guard that fires
    on the wrong fact teaches people to widen it**, which is how a guard stops
    guarding — the same note this lane wrote into `auth-configuration.test.ts`
    after a bare `max:` matched a Postgres pool size. **Replaced with the
    property that actually matters and can only fail for the right reason.**
    """

    def test_a_theme_is_a_name_and_carries_nothing_else(self) -> None:
        # Three members, three plain strings. A rendering payload cannot be
        # attached without changing the type, which is a deliberate act.
        assert {t.value for t in Theme} == {"light", "dark", "system"}
        assert all(isinstance(t.value, str) for t in Theme)

    def test_the_choice_set_is_closed(self) -> None:
        """A fourth theme arriving from a request body maps to nothing, so the
        enum refuses it rather than storing a name the frontend cannot draw."""
        import pytest

        with pytest.raises(ValueError):
            Theme("solarized")


class TestTheProfileLocaleAndAccessibilityFieldsRoundTrip:
    """📁 **The finalized User Profile design's remaining three panels** —
    migration `0060`.

    ⚠️ **The preservation guarantee is asserted through the USE CASE**, in
    `test_preferences_use_cases.py` — 📁 [B-264](../../../../docs/BUGS.md)'s
    defect lived there, and a test that called `replace` directly would assert
    that `dataclasses.replace` preserves fields, **which is a guard that cannot
    fail** ([§2](../../../../CLAUDE.md)).
    """

    def test_a_person_who_has_never_opened_the_screen_has_every_default(self) -> None:
        """⚡ **The absence of a row is not the absence of an answer.**

        ⛔ **`underline_links` defaults ON and `reduce_motion` defaults OFF**, and
        neither is arbitrary: 📁 the design shows links underlined, and
        **defaulting reduced motion true would force it on everybody who never
        opened the screen** — the device's own `prefers-reduced-motion` already
        drives the shell, so this column is the override rather than the answer.
        """
        fresh = PersonPreferences(workspace_id=uuid4(), person_id=uuid4())

        assert fresh.underline_links is True
        assert fresh.reduce_motion is False
        assert fresh.increase_contrast is False
        assert fresh.always_show_focus_ring is False
        assert fresh.text_size is TextSize.HUNDRED
        assert fresh.screen_reader_verbosity is ScreenReaderVerbosity.DETAILED
        # ⛔ **`None` means not chosen** — never a default dressed as an answer.
        assert fresh.job_title is None
        assert fresh.date_format is None

    def test_the_enumerated_controls_carry_exactly_the_designs_options(self) -> None:
        """⛔ **Where the design enumerates, the type enumerates.**

        ⚠️ **And where it does not, there is deliberately no enum**: `date_format`,
        `number_format` and `week_starts_on` are text, because the design shows
        one value each and lists no options — **inventing a `DateFormat` would
        decide which formats Signora supports.**
        """
        assert [size.value for size in TextSize] == ["100", "112", "125"]
        assert [v.value for v in ScreenReaderVerbosity] == ["concise", "detailed"]
