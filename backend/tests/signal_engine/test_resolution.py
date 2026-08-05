"""How a signal leaves the queue, and what the type refuses.

**The acceptance criterion says a dismissal cannot be recorded without a
reason, and that it is enforced in the type rather than by a check.** Most of
this file is therefore about what cannot be *built* rather than what is
rejected at runtime — a distinction that matters, because a validated optional
field fails for the caller who forgets it and a required one fails for the
person who wrote the code.
"""

from __future__ import annotations

from dataclasses import FrozenInstanceError
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest

from modules.signal_engine.domain.resolution import (
    MAX_REASON,
    Actioned,
    Assigned,
    DismissalReason,
    Dismissed,
    Resolution,
    ResolutionError,
    Snoozed,
)

NOW = datetime(2026, 8, 5, 12, 0, tzinfo=UTC)


def _resolution(**overrides: object) -> Resolution:
    defaults: dict[str, object] = {
        "id": uuid4(),
        "workspace_id": uuid4(),
        "signal_id": uuid4(),
        "outcome": Actioned(),
        "actor_id": uuid4(),
        "recorded_at": NOW,
    }
    return Resolution(**{**defaults, **overrides})  # type: ignore[arg-type]


class TestADismissalCannotExistWithoutAReason:
    """**The invariant the slice was asked for**, and it is a property of the
    type: `Dismissed` has one field and no default."""

    def test_a_reason_is_required_to_construct_one(self) -> None:
        with pytest.raises(TypeError):
            Dismissed()  # type: ignore[call-arg]

    def test_an_empty_reason_is_refused(self) -> None:
        with pytest.raises(ResolutionError, match="rule can learn from"):
            DismissalReason("")

    def test_whitespace_is_not_a_reason(self) -> None:
        """The failure a validated `str` field would let through: present,
        non-null, and says nothing."""
        with pytest.raises(ResolutionError):
            DismissalReason("   \n\t ")

    def test_a_reason_longer_than_the_limit_is_refused(self) -> None:
        """Bounded because dismissal reasons are read back to measure rule
        precision, and a pasted transcript is not a reason."""
        with pytest.raises(ResolutionError, match="at most"):
            DismissalReason("x" * (MAX_REASON + 1))

    def test_a_real_reason_is_carried_verbatim(self) -> None:
        reason = DismissalReason("They hired for the role internally.")

        dismissal = Dismissed(reason=reason)

        assert dismissal.reason.text == "They hired for the role internally."


class TestWhichOutcomesEndTheQueue:
    def test_acting_on_a_signal_closes_it(self) -> None:
        assert _resolution(outcome=Actioned()).closes_the_signal

    def test_dismissing_a_signal_closes_it(self) -> None:
        dismissal = Dismissed(reason=DismissalReason("Wrong account."))

        assert _resolution(outcome=dismissal).closes_the_signal

    def test_assigning_does_not_close_it(self) -> None:
        """**Assigning is routing, not resolving.** A queue that treated it as
        an ending would lose every signal handed to a colleague."""
        assert not _resolution(outcome=Assigned(to=uuid4())).closes_the_signal

    def test_snoozing_does_not_close_it(self) -> None:
        """*"Not now"* is not *"no"*."""
        snooze = Snoozed(until=NOW + timedelta(days=7))

        assert not _resolution(outcome=snooze).closes_the_signal


class TestASnoozedSignalComesBack:
    def test_it_is_not_due_before_the_stated_time(self) -> None:
        resolution = _resolution(outcome=Snoozed(until=NOW + timedelta(days=7)))

        assert not resolution.is_due(NOW + timedelta(days=6))

    def test_it_is_due_at_the_stated_time(self) -> None:
        """Inclusive deliberately: a signal snoozed until Monday 09:00 is due
        at Monday 09:00, which is what the person who set it meant."""
        due = NOW + timedelta(days=7)
        resolution = _resolution(outcome=Snoozed(until=due))

        assert resolution.is_due(due)

    def test_nothing_else_ever_comes_back(self) -> None:
        """**A guard that matters.** If this answered `True` for an actioned
        signal, finished work would reappear in front of a person — and the
        queue would stop being trustworthy in the one direction nobody checks.
        """
        for outcome in (
            Actioned(),
            Assigned(to=uuid4()),
            Dismissed(reason=DismissalReason("Not a competitor.")),
        ):
            assert not _resolution(outcome=outcome).is_due(NOW + timedelta(days=365))

    def test_a_snooze_that_has_already_elapsed_is_refused(self) -> None:
        """It would be a no-op wearing the clothes of a decision, and the queue
        would show it as handled while returning it immediately."""
        with pytest.raises(ResolutionError, match="not after it was recorded"):
            _resolution(outcome=Snoozed(until=NOW - timedelta(hours=1)))

    def test_snoozing_until_the_moment_it_is_recorded_is_refused(self) -> None:
        with pytest.raises(ResolutionError):
            _resolution(outcome=Snoozed(until=NOW))


class TestEveryResolutionIsAttributableAndOrderable:
    def test_an_actor_is_required(self) -> None:
        """**No outcome here may be authored by Signora.** Every one is a human
        judgement, and a machine-authored resolution would be the platform
        marking its own work."""
        with pytest.raises(TypeError):
            Resolution(  # type: ignore[call-arg]
                id=uuid4(),
                workspace_id=uuid4(),
                signal_id=uuid4(),
                outcome=Actioned(),
                recorded_at=NOW,
            )

    def test_a_naive_timestamp_is_refused(self) -> None:
        """A queue that returns snoozed work at a stated time cannot be built
        on a datetime whose meaning depends on where the reader is."""
        with pytest.raises(ResolutionError, match="without a timezone"):
            _resolution(recorded_at=datetime(2026, 8, 5, 12, 0))

    def test_a_naive_snooze_target_is_refused(self) -> None:
        with pytest.raises(ResolutionError, match="naive"):
            _resolution(outcome=Snoozed(until=datetime(2026, 8, 12, 9, 0)))

    def test_changing_your_mind_names_what_it_replaces(self) -> None:
        """**Immutability, made usable.** A correction is a new record naming
        the old one, so the queue can show what is true now while the history
        of how it got there stays readable — and a dismissal somebody regretted
        cannot quietly cease to exist."""
        first = _resolution(outcome=Dismissed(reason=DismissalReason("Not relevant.")))

        second = _resolution(outcome=Actioned(), supersedes=first.id)

        assert second.supersedes == first.id

    def test_the_first_resolution_supersedes_nothing(self) -> None:
        assert _resolution().supersedes is None


class TestTheRecordCannotBeEdited:
    """Frozen, because a resolution records what somebody decided and when.
    An editable one is a record nobody can cite."""

    def test_the_outcome_cannot_be_reassigned(self) -> None:
        resolution = _resolution()

        with pytest.raises(FrozenInstanceError):
            resolution.outcome = Actioned()  # type: ignore[misc]

    def test_a_reason_cannot_be_rewritten(self) -> None:
        reason = DismissalReason("Wrong account.")

        with pytest.raises(FrozenInstanceError):
            reason.text = "Actually it was right."  # type: ignore[misc]
