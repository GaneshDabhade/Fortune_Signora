"""`PersonPreferences`' one-time facts, as pure domain rules.

⚡ **Fast and databaseless on purpose.** The aggregate decides *whether* a moment
moves; the integration test decides *whether it persisted*. **Asserting the first
through HTTP would prove it slowly and locate the failure badly.**

📁 Home state 04 — *"a one-time strip"*, `AC-H03`'s *"shown exactly once"*.
"""

from datetime import UTC, datetime, timedelta
from uuid import uuid4

from modules.workspace_tenancy.domain.preferences import PersonPreferences

TOLD_AT = datetime(2026, 8, 18, 9, 0, tzinfo=UTC)


def _fresh() -> PersonPreferences:
    return PersonPreferences(workspace_id=uuid4(), person_id=uuid4())


class TestBeingToldSetupIsComplete:
    def test_a_new_person_has_not_been_told(self) -> None:
        """⛔ **`None` is the absence**, and it is what makes the strip render."""
        assert _fresh().setup_complete_seen_at is None

    def test_being_told_records_the_moment(self) -> None:
        told = _fresh().saw_setup_complete(TOLD_AT)

        assert told.setup_complete_seen_at == TOLD_AT

    def test_the_first_moment_wins(self) -> None:
        """🔴 **The rule *"exactly once"* rests on this.**

        ⚡ A second render, a retry or a second tab must not move the timestamp
        forward. ⛔ **Overwriting it would lose the only fact the column carries**
        — when this person was told — which is precisely what somebody asks for
        when a strip appears twice.
        """
        later = TOLD_AT + timedelta(days=3)

        told = _fresh().saw_setup_complete(TOLD_AT)
        again = told.saw_setup_complete(later)

        assert again.setup_complete_seen_at == TOLD_AT

    def test_a_second_call_returns_the_same_object(self) -> None:
        """⚡ **Identity, not equality**, because the use case branches on it:
        *"only when something changed"* is what stops a second acknowledgement
        writing a row for nothing."""
        told = _fresh().saw_setup_complete(TOLD_AT)

        assert told.saw_setup_complete(TOLD_AT) is told

    def test_it_does_not_disturb_its_neighbours(self) -> None:
        """⛔ **Three one-time facts share this table** and they are independent:
        being told setup finished is not dismissing the first-run overlay and is
        not skipping the invite card. ⚠️ A `replace` that touched a sibling would
        be invisible until somebody's overlay came back."""
        told = _fresh().saw_setup_complete(TOLD_AT)

        assert told.first_run_dismissed_at is None
        assert told.invite_skipped_at is None
