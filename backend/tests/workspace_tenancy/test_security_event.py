"""The activity stream's domain type — [TASK-492](../../../docs/BACKLOG.md).

⚡ **The table is verified by the Security Invariants; these are the properties
only the TYPE can hold.** 🔴 **The load-bearing one is that a caller with a
single identity cannot construct an event at all** — 496 §3's two-identity rule
made unrepresentable rather than reviewed.
"""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest

from modules.workspace_tenancy.domain.security_event import (
    FORBIDDEN_DETAIL_KEYS,
    MAX_KIND_LENGTH,
    ForbiddenDetailKey,
    MalformedEventKind,
    SecurityEvent,
)

NOW = datetime(2026, 8, 9, 12, 0, tzinfo=UTC)


def event(**overrides: object) -> SecurityEvent:
    person = uuid4()
    base: dict[str, object] = {
        "workspace_id": uuid4(),
        "kind": "session.signed_in",
        "subject_id": person,
        "acting_for": person,
        "occurred_at": NOW,
    }
    base.update(overrides)
    return SecurityEvent(**base)  # type: ignore[arg-type]


class TestTheTwoIdentities:
    """🔴 496 §3 — every event carries both, always."""

    def test_a_caller_holding_one_identity_cannot_construct_an_event(self) -> None:
        # ⛔ **This is the rule as a TYPE rather than as a review comment.**
        # Neither field has a default, so *on whose authority?* is answered at
        # the call site or the event does not exist.
        person = uuid4()
        with pytest.raises(TypeError):
            SecurityEvent(  # type: ignore[call-arg]
                workspace_id=uuid4(),
                kind="session.signed_in",
                subject_id=person,
                occurred_at=NOW,
            )

    def test_acting_for_equal_to_the_subject_is_stated_not_implied(self) -> None:
        # ⚡ A person acting directly is `self_directed`, and it is written
        # down. ⛔ A NULL would have meant *unattributed* and *self-directed*
        # at once, and an auditor cannot tell those apart.
        person = uuid4()
        e = event(subject_id=person, acting_for=person)
        assert e.self_directed
        assert not e.on_behalf

    def test_somebody_acting_for_somebody_else_is_the_case_an_auditor_wants(self) -> None:
        e = event(subject_id=uuid4(), acting_for=uuid4())
        assert e.on_behalf
        assert not e.self_directed


class TestDetailNeverCarriesACredential:
    """⛔ The stream is read by support and by compliance (§13, §16)."""

    @pytest.mark.parametrize("key", sorted(FORBIDDEN_DETAIL_KEYS))
    def test_every_forbidden_key_is_refused(self, key: str) -> None:
        with pytest.raises(ForbiddenDetailKey):
            event(detail={key: "whatever"})

    def test_the_check_is_case_insensitive_because_Token_is_one_too(self) -> None:
        with pytest.raises(ForbiddenDetailKey):
            event(detail={"Token": "abc"})
        with pytest.raises(ForbiddenDetailKey):
            event(detail={"PASSWORD": "abc"})

    def test_it_refuses_rather_than_silently_dropping_the_key(self) -> None:
        """🔴 **The difference that matters.**

        ⛔ **A scrubber leaves the producer believing the value was recorded**,
        and the first person to notice is an auditor reading a gap. **A raise
        is loud at the call site, where it can be fixed.**
        """
        with pytest.raises(ForbiddenDetailKey) as caught:
            event(detail={"api_key": "sk-live-1"})
        assert caught.value.key == "api_key"
        # ⚡ And the message says what to do instead, not merely what was wrong.
        assert "never the secret" in str(caught.value)

    def test_ordinary_context_is_kept(self) -> None:
        e = event(detail={"from": "member", "to": "owner"})
        assert e.detail == {"from": "member", "to": "owner"}


class TestTheKindIsAVocabularyRatherThanAString:
    def test_noun_verb_past_is_accepted(self) -> None:
        for kind in ("session.signed_in", "membership.role_changed", "password.reset_requested"):
            assert event(kind=kind).kind == kind

    @pytest.mark.parametrize(
        "kind",
        [
            "signed_in",  # no noun
            "session.SignedIn",  # not lower snake case
            "Session.signed_in",
            "session.signed-in",  # hyphen
            "session..signed_in",
            "",
        ],
    )
    def test_anything_else_is_refused(self, kind: str) -> None:
        # ⚡ A stream carrying `sign_in` beside `session.signed_in` is a stream
        # nobody can filter, and the second one is always added later.
        with pytest.raises(MalformedEventKind):
            event(kind=kind)

    def test_the_length_bound_matches_the_column(self) -> None:
        # ⛔ Refused by the domain rather than truncated by the driver: a
        # truncated kind is a kind that silently stops matching.
        assert event(kind="a." + "b" * (MAX_KIND_LENGTH - 2)).kind
        with pytest.raises(MalformedEventKind):
            event(kind="a." + "b" * MAX_KIND_LENGTH)


class TestTheMomentIsUnambiguous:
    def test_a_naive_timestamp_is_refused(self) -> None:
        # ⛔ An audit record with an ambiguous moment cannot be ordered or
        # cited. The column is `timestamptz`; the domain refuses rather than
        # letting the driver guess a zone.
        with pytest.raises(ValueError, match="timezone-aware"):
            event(occurred_at=datetime(2026, 8, 9, 12, 0))


class TestItRecordsSomethingThatWasTrue:
    def test_the_event_is_frozen(self) -> None:
        # §2 — immutability is the default for anything that records a fact,
        # and the table has no UPDATE grant. The two agree by construction.
        e = event()
        with pytest.raises(AttributeError):
            e.kind = "session.signed_out"  # type: ignore[misc]
