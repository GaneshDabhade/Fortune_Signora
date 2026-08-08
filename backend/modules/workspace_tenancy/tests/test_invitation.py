"""What an invitation is, and what it refuses to become.

**Domain tests against fakes, no database.** The rules asserted here are the
ones a customer would notice going wrong: an offer that could be edited under
them, an expiry that depended on which machine asked, or a revocation that
appeared to succeed after somebody had already accepted.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest

from modules.workspace_tenancy.domain.entities import WorkspaceRole
from modules.workspace_tenancy.domain.invitation import (
    INVITATION_VALID_FOR,
    InvalidInvitationEmailError,
    Invitation,
    InvitationAlreadyAcceptedError,
    InvitationExpiredError,
    InvitationNotPendingError,
    InvitationRevokedError,
    InvitationState,
    normalize_email,
)

NOW = datetime(2026, 8, 2, 9, 0, tzinfo=UTC)
WORKSPACE = uuid4()
ANA = uuid4()


def offer(email: str = "sam@acme.com", role: WorkspaceRole = WorkspaceRole.MEMBER) -> Invitation:
    return Invitation.offer(
        workspace_id=WORKSPACE,
        email=email,
        role=role,
        invited_by=ANA,
        now=NOW,
    )


class TestTheAddressIsPutIntoOneForm:
    def test_it_lowercases_and_trims(self) -> None:
        # Acceptance matches this against a verified JWT claim, so two
        # spellings of one address would be two live invitations the unique
        # index cannot see as one.
        assert normalize_email("  Sam@Acme.COM ") == "sam@acme.com"

    def test_an_offer_stores_the_normalized_form(self) -> None:
        assert offer(email="SAM@ACME.COM").invited_email == "sam@acme.com"

    @pytest.mark.parametrize(
        "value", ["", "   ", "sam", "sam@", "@acme.com", "sam@acme", "sam@.com"]
    )
    def test_it_refuses_what_could_never_receive_an_email(self, value: str) -> None:
        with pytest.raises(InvalidInvitationEmailError):
            normalize_email(value)

    def test_it_accepts_an_address_a_stricter_rule_would_reject(self) -> None:
        # Deliberately not RFC validation. The address is proved by Better Auth
        # when somebody signs in with it, and rejecting a legitimate address is
        # worse than accepting a typo — the typo is visible and revocable.
        assert normalize_email("sam+signora@acme.co.uk") == "sam+signora@acme.co.uk"


class TestFourStatesAndOnlyTwoAreStored:
    def test_a_new_offer_is_pending(self) -> None:
        assert offer().state(at=NOW) is InvitationState.PENDING

    def test_it_expires_by_the_clock_rather_than_by_a_job(self) -> None:
        # No job flips a flag. If one did, the row would be wrong from the
        # moment it expired until the job next ran.
        invitation = offer()
        just_after = NOW + INVITATION_VALID_FOR + timedelta(seconds=1)

        assert invitation.state(at=just_after) is InvitationState.EXPIRED
        assert invitation.accepted_at is None and invitation.revoked_at is None

    def test_expiry_is_inclusive_of_the_instant_it_lapses(self) -> None:
        assert offer().state(at=NOW + INVITATION_VALID_FOR) is InvitationState.EXPIRED

    def test_accepted_outranks_expired(self) -> None:
        # Somebody who accepted on Tuesday did not un-join on Wednesday.
        accepted = offer().accept(at=NOW)

        assert accepted.state(at=NOW + timedelta(days=30)) is InvitationState.ACCEPTED

    def test_revoked_outranks_expired(self) -> None:
        revoked = offer().revoke(at=NOW)

        assert revoked.state(at=NOW + timedelta(days=30)) is InvitationState.REVOKED


class TestItIsImmutable:
    def test_there_is_no_method_that_changes_the_offer(self) -> None:
        # **The absence is the assertion.** Editing a live invitation's role
        # would mean the email said *member* and acceptance granted *owner* —
        # so a change must be a revocation and a new offer.
        for forbidden in ("set_role", "change_role", "update", "edit", "extend"):
            assert not hasattr(Invitation, forbidden)

    def test_settling_returns_a_new_invitation_rather_than_mutating(self) -> None:
        original = offer()
        revoked = original.revoke(at=NOW)

        assert original.revoked_at is None
        assert revoked.revoked_at == NOW
        assert revoked.id == original.id

    def test_the_inviter_never_moves(self) -> None:
        # An invitation belongs to the workspace; the inviter is provenance.
        # Acceptance still succeeds after they leave, and the record still
        # says who acted.
        assert offer().accept(at=NOW).invited_by == ANA


class TestSettlingIsRefusedWhenItWouldClaimNothing:
    def test_revoking_twice_is_refused(self) -> None:
        revoked = offer().revoke(at=NOW)

        with pytest.raises(InvitationNotPendingError) as raised:
            revoked.revoke(at=NOW)
        assert raised.value.state is InvitationState.REVOKED

    def test_revoking_after_acceptance_is_refused(self) -> None:
        # The colleague is already in the organization. Removing them is a
        # different operation with a different blast radius.
        accepted = offer().accept(at=NOW)

        with pytest.raises(InvitationNotPendingError) as raised:
            accepted.revoke(at=NOW)
        assert raised.value.state is InvitationState.ACCEPTED

    def test_revoking_an_expired_invitation_is_refused(self) -> None:
        # Not pedantry: an administrator would believe they had closed a door
        # that had already shut, and the record would claim an act that changed
        # nothing.
        invitation = offer()

        with pytest.raises(InvitationNotPendingError) as raised:
            invitation.revoke(at=NOW + INVITATION_VALID_FOR)
        assert raised.value.state is InvitationState.EXPIRED

    def test_accepting_after_revocation_is_refused(self) -> None:
        # **Revocation wins over an email already opened.** State is checked at
        # acceptance and never at delivery, so there is no window.
        revoked = offer().revoke(at=NOW)

        with pytest.raises(InvitationNotPendingError):
            revoked.accept(at=NOW)

    def test_accepting_after_expiry_is_refused(self) -> None:
        with pytest.raises(InvitationNotPendingError) as raised:
            offer().accept(at=NOW + INVITATION_VALID_FOR)
        assert raised.value.state is InvitationState.EXPIRED

    def test_the_refusal_carries_the_state_it_found(self) -> None:
        # *"This was withdrawn"* and *"this expired"* are different sentences to
        # a customer, and only one of them offers a next step.
        states = {
            InvitationState.REVOKED: offer().revoke(at=NOW),
            InvitationState.ACCEPTED: offer().accept(at=NOW),
        }
        for expected, invitation in states.items():
            with pytest.raises(InvitationNotPendingError) as raised:
                invitation.accept(at=NOW)
            assert raised.value.state is expected


class TestTheOfferStands:
    def test_for_a_week(self) -> None:
        # Long enough to survive a holiday weekend, short enough that a
        # forgotten invitation surfaces rather than lingering.
        assert offer().expires_at == NOW + timedelta(days=7)

    def test_the_clock_is_an_argument_with_no_default(self) -> None:
        # An invitation that read the wall clock itself would give a different
        # answer to a test than to a request, and the state would stop being
        # reproducible (§2, hidden inputs).
        with pytest.raises(TypeError):
            offer().state()  # type: ignore[call-arg]


class TestASettledInvitationSaysWhichSettledStateItIs:
    """**[B-214](../../../../docs/BUGS.md)** — the regression test.

    ⛔ **The domain has always known, and nothing could read it.**
    `InvitationNotPendingError` carried the state from the day it was written
    and its own docstring said *"'this was withdrawn' and 'this expired' are
    different sentences to a customer"* — **and the API answered
    `invitation_not_pending` for all three**, so the design's screen
    `14 Invitation expired` could not be reached.
    """

    def _settled(self, state: InvitationState) -> Invitation:
        now = datetime(2026, 8, 8, 12, 0, tzinfo=UTC)
        invitation = Invitation.offer(
            workspace_id=uuid4(),
            email="m.reinhardt@northwind.com",
            role=WorkspaceRole.MEMBER,
            invited_by=uuid4(),
            now=now,
        )
        if state is InvitationState.EXPIRED:
            return invitation
        if state is InvitationState.REVOKED:
            return invitation.revoke(at=now)
        return invitation.accept(at=now)

    @pytest.mark.parametrize(
        ("state", "expected"),
        [
            (InvitationState.EXPIRED, InvitationExpiredError),
            (InvitationState.REVOKED, InvitationRevokedError),
            (InvitationState.ACCEPTED, InvitationAlreadyAcceptedError),
        ],
    )
    def test_each_settled_state_raises_its_own_type(
        self, state: InvitationState, expected: type[Exception]
    ) -> None:
        invitation = self._settled(state)
        # Far enough past the offer that an untouched invitation has expired.
        later = datetime(2027, 1, 1, tzinfo=UTC)

        with pytest.raises(expected):
            invitation.require_pending(later)

    def test_no_two_settled_states_share_an_error_type(self) -> None:
        """🔴 **The assertion the defect actually was**, and the one that can
        still fail.

        ⛔ **Two settled states sharing a type is exactly what made screen `14`
        unreachable** — an expired invitation and a withdrawn one arrived
        identical. **Counting distinct types catches a future state added to
        the enum and forgotten in the map**, which is how this would come back.

        ⚠️ **A first draft asserted `type(expired) is not type(revoked)` inside
        two `pytest.raises` blocks and `mypy --strict` refused it**: the raises
        narrow the types, so the comparison was statically decided and the test
        could not fail. **§2 — a guard that cannot fail is documentation
        pretending to be code** — so it was replaced rather than silenced.
        """
        settled = sorted(set(InvitationState) - {InvitationState.PENDING})
        produced = [type(InvitationNotPendingError.for_state(s)) for s in settled]

        assert len(set(produced)) == len(settled)
        assert InvitationNotPendingError not in produced

    def test_they_are_still_the_error_every_existing_caller_catches(self) -> None:
        """⚡ **Subclasses, not replacements.** Anything already written as
        `except InvitationNotPendingError` keeps working — the state moved into
        the type without moving out of the instance."""
        later = datetime(2027, 1, 1, tzinfo=UTC)

        with pytest.raises(InvitationNotPendingError) as caught:
            self._settled(InvitationState.EXPIRED).require_pending(later)

        assert caught.value.state is InvitationState.EXPIRED

    def test_the_api_gives_each_one_its_own_code(self) -> None:
        """🔴 **The half that was actually broken.** The domain distinguished
        them; the transport did not, and a screen only ever sees the code."""
        from modules.workspace_tenancy.interface.errors import ERROR_MAPPING

        codes = {
            ERROR_MAPPING[e][1]
            for e in (
                InvitationExpiredError,
                InvitationRevokedError,
                InvitationAlreadyAcceptedError,
            )
        }

        assert codes == {"invitation_expired", "invitation_revoked", "invitation_already_accepted"}
