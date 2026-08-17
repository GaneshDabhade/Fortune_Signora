"""Accepting an offer of membership — and every way it must refuse.

**The only operation in Signora performed from outside the workspace**, so most
of this file is about what a stranger cannot do with an invitation link. The
happy path is three tests; the refusals are the rest, and they are the point.

**The threat model in one sentence.** The link carries a workspace id and an
invitation id, both of which anybody could hold — forwarded mail, a screenshot,
a shared browser. **Neither is authority.** Authority is the verified email
claim, and these tests exist to keep that true when somebody later finds the
membership check inconvenient.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import pytest

from modules.workspace_tenancy.application.use_cases.accept_invitation import (
    AcceptInvitationInput,
    AcceptInvitationUseCase,
    InvitationNotFoundError,
    UnverifiedEmailError,
)
from modules.workspace_tenancy.domain.entities import Membership, WorkspaceRole
from modules.workspace_tenancy.domain.invitation import (
    Invitation,
    InvitationNotPendingError,
    normalize_email,
)
from modules.workspace_tenancy.tests.fakes import (
    FakeEventPublisher,
    FakeMembershipRepository,
    FakeWorkspaceRepository,
)

NOW = datetime(2026, 8, 5, 12, 0, tzinfo=UTC)
INVITED = "ada@example.com"


class FakeInvitationRepository:
    """**Workspace-scoped on every read, exactly as the real one is.**

    `get` filters on `workspace_id` because the SQL repository's rows are
    filtered on it by row-level security. A fake that ignored the workspace
    would let the cross-tenant test below pass while the deployed system
    behaved differently — which is the only kind of double worth having.
    """

    def __init__(self) -> None:
        self.invitations: list[Invitation] = []
        self.settled: list[Invitation] = []

    async def add(self, invitation: Invitation) -> None:
        self.invitations.append(invitation)

    async def get(self, workspace_id: UUID, invitation_id: UUID) -> Invitation | None:
        return next(
            (
                i
                for i in self.invitations
                if i.id == invitation_id and i.workspace_id == workspace_id
            ),
            None,
        )

    async def find_live(self, workspace_id: UUID, email: str) -> Invitation | None:
        """**Implemented rather than stubbed**, even though acceptance never
        calls it. A double that satisfies only the methods one test happens to
        use is not standing in for the port — it is standing in for this
        file's idea of the port, and `mypy --strict` refuses the difference.

        **B-189. This filtered on ``state(at=datetime.now(UTC))`` and was wrong
        twice over.**

        It read the wall clock while the file declares ``NOW`` — the hidden
        input `CLAUDE.md` §2 names, and the exact thing ``state``'s own
        docstring refuses by giving ``at`` no default. Seven days after the
        fixture was written, its offers expired against the real clock and five
        tests went red on a backend tree that had not changed.

        **And it filtered on something the real repository does not filter on.**
        ``SqlInvitationRepository.find_live`` matches the partial unique index —
        ``accepted_at IS NULL AND revoked_at IS NULL`` — and says nothing about
        expiry. Expiry is decided one layer up, by ``require_pending(now)``, on
        the clock the use case is handed.

        **That difference is not cosmetic: it changes what a customer is
        told.** An expired offer must reach the use case so it can answer
        *"this invitation has expired"* — the one refusal that tells a person
        what to do next. Filtering it out here produced *"there is no
        invitation to this organization for your address"*, which is the
        sentence reserved for a revoked or never-issued offer.
        """
        return next(
            (
                i
                for i in self.invitations
                if i.workspace_id == workspace_id
                and normalize_email(i.invited_email) == normalize_email(email)
                and i.accepted_at is None
                and i.revoked_at is None
            ),
            None,
        )

    async def list_for_workspace(self, workspace_id: UUID) -> list[Invitation]:
        return [i for i in self.invitations if i.workspace_id == workspace_id]

    async def settle(self, invitation: Invitation) -> None:
        self.settled.append(invitation)


@pytest.fixture
def workspaces() -> FakeWorkspaceRepository:
    return FakeWorkspaceRepository()


@pytest.fixture
def memberships() -> FakeMembershipRepository:
    return FakeMembershipRepository()


@pytest.fixture
def invitations() -> FakeInvitationRepository:
    return FakeInvitationRepository()


@pytest.fixture
def publisher() -> FakeEventPublisher:
    return FakeEventPublisher()


@pytest.fixture
def use_case(
    invitations: FakeInvitationRepository,
    memberships: FakeMembershipRepository,
    publisher: FakeEventPublisher,
) -> AcceptInvitationUseCase:
    return AcceptInvitationUseCase(
        invitations=invitations,
        memberships=memberships,
        event_publisher=publisher,
    )


async def _workspace(workspaces: FakeWorkspaceRepository) -> UUID:
    from modules.workspace_tenancy.domain.entities import Workspace

    workspace, _ = Workspace.create(name="Acme", slug="a-workspace", created_by=uuid4())
    await workspaces.add(workspace)
    return workspace.id


def _invitation(workspace_id: UUID, *, email: str = INVITED, **overrides: object) -> Invitation:
    defaults: dict[str, object] = {
        "id": uuid4(),
        "workspace_id": workspace_id,
        "invited_email": email,
        "role": WorkspaceRole.MEMBER,
        "expires_at": NOW + timedelta(days=7),
        "invited_by": uuid4(),
        "created_at": NOW,
    }
    return Invitation(**{**defaults, **overrides})  # type: ignore[arg-type]


def _input(workspace_id: UUID, **overrides: object) -> AcceptInvitationInput:
    defaults: dict[str, object] = {
        "workspace_id": workspace_id,
        "user_id": uuid4(),
        "email": INVITED,
        "email_verified": True,
    }
    return AcceptInvitationInput(**{**defaults, **overrides})  # type: ignore[arg-type]


class TestTheOfferBecomesAMembership:
    async def test_the_invited_person_joins(
        self,
        use_case: AcceptInvitationUseCase,
        workspaces: FakeWorkspaceRepository,
        invitations: FakeInvitationRepository,
    ) -> None:
        workspace_id = await _workspace(workspaces)
        invitation = _invitation(workspace_id)
        await invitations.add(invitation)

        membership = await use_case.execute(_input(workspace_id), now=NOW, correlation_id=uuid4())

        assert membership.workspace_id == workspace_id
        assert membership.is_live

    async def test_they_join_with_the_role_the_offer_named(
        self,
        use_case: AcceptInvitationUseCase,
        workspaces: FakeWorkspaceRepository,
        invitations: FakeInvitationRepository,
    ) -> None:
        """**The email said what it said.** An invitation that granted a role
        other than the one offered would be the product telling somebody one
        thing and doing another — which is why the aggregate refuses edits."""
        workspace_id = await _workspace(workspaces)
        invitation = _invitation(workspace_id, role=WorkspaceRole.OWNER)
        await invitations.add(invitation)

        membership = await use_case.execute(_input(workspace_id), now=NOW, correlation_id=uuid4())

        assert membership.role is WorkspaceRole.OWNER

    async def test_the_invitation_is_settled_and_the_arrival_announced(
        self,
        use_case: AcceptInvitationUseCase,
        workspaces: FakeWorkspaceRepository,
        invitations: FakeInvitationRepository,
        publisher: FakeEventPublisher,
    ) -> None:
        workspace_id = await _workspace(workspaces)
        invitation = _invitation(workspace_id)
        await invitations.add(invitation)

        await use_case.execute(_input(workspace_id), now=NOW, correlation_id=uuid4())

        assert [i.accepted_at for i in invitations.settled] == [NOW]
        assert len(publisher.published) == 1


class TestNamingTheLinkIsNotAuthorityToUseIt:
    """**The threat model.** A workspace id and an invitation id travel in a
    URL — forwarded, screenshotted, left in a shared browser. Neither is a
    secret and neither is authority."""

    async def test_somebody_else_cannot_accept_it(
        self,
        use_case: AcceptInvitationUseCase,
        workspaces: FakeWorkspaceRepository,
        invitations: FakeInvitationRepository,
        memberships: FakeMembershipRepository,
    ) -> None:
        """**The test this file exists for.** Holding the link is not being the
        person it was sent to.

        **And it is now unreachable rather than refused.** The offer is looked
        up by the caller's own verified address, so there is no query here that
        could return somebody else's invitation — which is why this asserts
        *not found* rather than *not yours*."""
        workspace_id = await _workspace(workspaces)
        invitation = _invitation(workspace_id)
        await invitations.add(invitation)

        with pytest.raises(InvitationNotFoundError):
            await use_case.execute(
                _input(workspace_id, email="mallory@elsewhere.com"),
                now=NOW,
                correlation_id=uuid4(),
            )

        assert memberships.memberships == []

    async def test_an_unverified_address_cannot_claim_one(
        self,
        use_case: AcceptInvitationUseCase,
        workspaces: FakeWorkspaceRepository,
        invitations: FakeInvitationRepository,
        memberships: FakeMembershipRepository,
    ) -> None:
        """**Otherwise anybody types their way in.** An unverified address is
        an assertion by the person making it, not a proof by the identity
        provider — and the whole authority of this endpoint rests on the
        difference."""
        workspace_id = await _workspace(workspaces)
        invitation = _invitation(workspace_id)
        await invitations.add(invitation)

        with pytest.raises(UnverifiedEmailError):
            await use_case.execute(
                _input(workspace_id, email_verified=False),
                now=NOW,
                correlation_id=uuid4(),
            )

        assert memberships.memberships == []

    async def test_an_invitation_from_another_workspace_is_not_reachable(
        self,
        use_case: AcceptInvitationUseCase,
        workspaces: FakeWorkspaceRepository,
        invitations: FakeInvitationRepository,
    ) -> None:
        """**Acceptance never reads across tenants** (C-208). Naming workspace
        A while holding an invitation issued by workspace B must find nothing,
        which is what the workspace-scoped read guarantees."""
        theirs = await _workspace(workspaces)
        mine = await _workspace(workspaces)
        invitation = _invitation(theirs)
        await invitations.add(invitation)

        with pytest.raises(InvitationNotFoundError):
            await use_case.execute(_input(mine), now=NOW, correlation_id=uuid4())

    async def test_never_invited_and_invited_someone_else_are_one_answer(
        self,
        use_case: AcceptInvitationUseCase,
        workspaces: FakeWorkspaceRepository,
        invitations: FakeInvitationRepository,
    ) -> None:
        """**One sentence for every reason there is no offer.** Distinguishing
        them would answer *"has this workspace invited this person?"* to
        anybody who can sign in."""
        empty = await _workspace(workspaces)
        with_offer = await _workspace(workspaces)
        await invitations.add(_invitation(with_offer))

        with pytest.raises(InvitationNotFoundError) as never:
            await use_case.execute(_input(empty), now=NOW, correlation_id=uuid4())
        with pytest.raises(InvitationNotFoundError) as theirs:
            await use_case.execute(
                _input(with_offer, email="mallory@elsewhere.com"),
                now=NOW,
                correlation_id=uuid4(),
            )

        assert str(never.value) == str(theirs.value)

    async def test_an_unknown_workspace_is_refused_as_a_missing_invitation(
        self, use_case: AcceptInvitationUseCase
    ) -> None:
        """**There is no separate "no such workspace" answer, deliberately.**

        The first draft checked the workspace existed. `workspace`'s row-level
        security is membership-based, so the accepter could never pass it and
        every acceptance answered `workspace_not_found` — caught by an
        integration test, not by this file, because a fake repository has no
        RLS to fail. It also leaked a distinct code for a workspace the caller
        cannot see. **The invitation read is the existence proof.**
        """
        with pytest.raises(InvitationNotFoundError):
            await use_case.execute(_input(uuid4()), now=NOW, correlation_id=uuid4())


class TestTheAddressIsComparedAsOneAddress:
    async def test_capitalisation_does_not_make_two_people(
        self,
        use_case: AcceptInvitationUseCase,
        workspaces: FakeWorkspaceRepository,
        invitations: FakeInvitationRepository,
    ) -> None:
        """`Ada@Example.COM` signing in and `ada@example.com` being invited are
        one person. Comparing raw strings would refuse the person the offer was
        addressed to, which is the failure a customer would report as *"the
        link doesn't work"*."""
        workspace_id = await _workspace(workspaces)
        invitation = _invitation(workspace_id, email="ada@example.com")
        await invitations.add(invitation)

        membership = await use_case.execute(
            _input(workspace_id, email="  Ada@Example.COM "),
            now=NOW,
            correlation_id=uuid4(),
        )

        assert membership.is_live


class TestASettledOfferCannotBeUsedAgain:
    async def test_an_expired_invitation_is_refused(
        self,
        use_case: AcceptInvitationUseCase,
        workspaces: FakeWorkspaceRepository,
        invitations: FakeInvitationRepository,
    ) -> None:
        """**A standing grant to enter a customer's data, so it ends.** One
        that never expired would be a credential nobody remembers issuing."""
        workspace_id = await _workspace(workspaces)
        invitation = _invitation(workspace_id)
        await invitations.add(invitation)

        with pytest.raises(InvitationNotPendingError):
            await use_case.execute(
                _input(workspace_id),
                now=NOW + timedelta(days=8),
                correlation_id=uuid4(),
            )

    async def test_the_wall_clock_decides_nothing(
        self,
        use_case: AcceptInvitationUseCase,
        workspaces: FakeWorkspaceRepository,
        invitations: FakeInvitationRepository,
    ) -> None:
        """**B-189's proof, and it has to fail when the clock moves.**

        Rewriting the fixture window would buy another seven days of silence
        and be green either way. This one cannot be: the offer expires in the
        year 2000 — permanently in the past for any real clock — and is
        accepted at a ``now`` before that.

        **If anything in this file reads the wall clock, the invitation is
        expired, ``find_live`` returns ``None``, and this goes red.** It stays a
        proof on every future date, which is the property the seven-day window
        never had.
        """
        long_ago = datetime(2000, 1, 1, 12, 0, tzinfo=UTC)
        workspace_id = await _workspace(workspaces)
        await invitations.add(
            _invitation(
                workspace_id,
                created_at=long_ago - timedelta(days=1),
                expires_at=long_ago + timedelta(days=7),
            )
        )

        await use_case.execute(_input(workspace_id), now=long_ago, correlation_id=uuid4())

        assert len(invitations.settled) == 1

    async def test_an_expired_offer_still_reaches_the_use_case(
        self,
        use_case: AcceptInvitationUseCase,
        workspaces: FakeWorkspaceRepository,
        invitations: FakeInvitationRepository,
    ) -> None:
        """**The other half of B-189, and it is about what a person is told.**

        ``find_live`` must hand an expired offer to the use case so acceptance
        can answer *"this invitation has expired"*. A repository that filtered
        expiry out would produce *"there is no invitation to this organization
        for your address"* — the sentence reserved for revoked or never-issued
        offers — and the person would have no idea to ask for a new one.

        **Clock-independent, deliberately**: both moments are in the year 2000,
        so this asserts the boundary rather than today's date.
        """
        long_ago = datetime(2000, 1, 1, 12, 0, tzinfo=UTC)
        workspace_id = await _workspace(workspaces)
        await invitations.add(
            _invitation(
                workspace_id,
                created_at=long_ago - timedelta(days=1),
                expires_at=long_ago,
            )
        )

        assert (
            await invitations.find_live(workspace_id, INVITED)
        ) is not None, "an expired offer must still be found; expiry is not this port's decision"

        with pytest.raises(InvitationNotPendingError):
            await use_case.execute(
                _input(workspace_id),
                now=long_ago + timedelta(days=1),
                correlation_id=uuid4(),
            )

    async def test_a_revoked_invitation_reads_as_no_invitation(
        self,
        use_case: AcceptInvitationUseCase,
        workspaces: FakeWorkspaceRepository,
        invitations: FakeInvitationRepository,
    ) -> None:
        """**Withdrawn is not distinguished from never invited, deliberately.**

        `find_live` excludes revoked offers, so this arrives as *no
        invitation* — and that is the answer worth giving. An administrator
        who withdraws an offer has decided the person should not join; a
        message saying *"that was withdrawn"* would confirm to whoever is
        holding the link that the workspace had once invited that address.

        **Expiry is the exception**, asserted above: nobody decided it, and it
        is the one refusal that tells a person what to do next.
        """
        workspace_id = await _workspace(workspaces)
        invitation = _invitation(workspace_id, revoked_at=NOW)
        await invitations.add(invitation)

        with pytest.raises(InvitationNotFoundError):
            await use_case.execute(_input(workspace_id), now=NOW, correlation_id=uuid4())


class TestFollowingTheLinkTwiceIsNotAnError:
    async def test_an_existing_member_gets_their_membership_back(
        self,
        use_case: AcceptInvitationUseCase,
        workspaces: FakeWorkspaceRepository,
        invitations: FakeInvitationRepository,
        memberships: FakeMembershipRepository,
    ) -> None:
        """**The state they asked for is the state they are in.** Refusing here
        would show an error to somebody who has exactly what the invitation
        offered — and the second click is the ordinary one, not the strange
        one."""
        workspace_id = await _workspace(workspaces)
        invitation = _invitation(workspace_id)
        await invitations.add(invitation)
        joining = uuid4()
        already, _ = Membership.create(
            workspace_id=workspace_id,
            user_id=joining,
            role=WorkspaceRole.MEMBER,
            created_by=joining,
        )
        await memberships.add(already)

        membership = await use_case.execute(
            _input(workspace_id, user_id=joining),
            now=NOW,
            correlation_id=uuid4(),
        )

        assert membership.id == already.id
        assert len(memberships.memberships) == 1

    async def test_it_does_not_announce_an_arrival_that_did_not_happen(
        self,
        use_case: AcceptInvitationUseCase,
        workspaces: FakeWorkspaceRepository,
        invitations: FakeInvitationRepository,
        memberships: FakeMembershipRepository,
        publisher: FakeEventPublisher,
    ) -> None:
        """A second `member.added` for one person would make every consumer
        counting arrivals wrong."""
        workspace_id = await _workspace(workspaces)
        invitation = _invitation(workspace_id)
        await invitations.add(invitation)
        joining = uuid4()
        already, _ = Membership.create(
            workspace_id=workspace_id,
            user_id=joining,
            role=WorkspaceRole.MEMBER,
            created_by=joining,
        )
        await memberships.add(already)

        await use_case.execute(
            _input(workspace_id, user_id=joining),
            now=NOW,
            correlation_id=uuid4(),
        )

        assert publisher.published == []
