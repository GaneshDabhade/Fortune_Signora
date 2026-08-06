"""Implements ``public.query_port.WorkspaceQueryPort`` — the one interface
other modules are allowed to call synchronously. Kept intentionally thin and
read-only; it must never grow write operations or module-internal logic.
"""

from uuid import UUID

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

from modules.workspace_tenancy.application.use_cases.organization_history import (
    HistoryEntry,
    HistoryKind,
)
from modules.workspace_tenancy.infrastructure.models import (
    InvitationModel,
    MembershipModel,
    MembershipRoleChangeModel,
    WorkspaceModel,
)
from modules.workspace_tenancy.public.query_port import MembershipView
from signora_platform.pagination import CursorPosition


class WorkspaceQueryService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def workspace_exists(self, workspace_id: UUID) -> bool:
        return await self._session.get(WorkspaceModel, workspace_id) is not None

    async def resolve_role(self, workspace_id: UUID, user_id: UUID) -> str | None:
        """The caller's role in a workspace, or ``None`` if not a member.

        Satisfies ``signora_platform.api.MembershipVerifier`` structurally,
        which is how the API dependency chain verifies membership without the
        platform layer importing this module (15-project-structure.md).

        This is the authoritative membership check performed on every
        authenticated request — the ``active_workspace_id`` JWT claim is only
        a hint (18-authentication.md).
        """
        membership = await self.get_membership(workspace_id, user_id)
        return membership.role if membership is not None else None

    async def get_membership(self, workspace_id: UUID, user_id: UUID) -> MembershipView | None:
        """The caller's **live** membership, and the filter is a security
        control rather than a tidiness.

        ⚠️ **`ended_at IS NULL` was missing until 2026-08-05 ([B-206](../../../../docs/BUGS.md)).**
        This is the authoritative membership check on every authenticated
        request, so without it **a person who was removed from an organization
        kept full access to it** — the exact outcome
        `SqlMembershipRepository.get` documents itself as existing to prevent:
        *"an ended membership that still resolved here would keep somebody
        signed in to an organization they had been removed from."* Two reads of
        one fact, and only one of them was filtered.

        **Both callers want live-only**, which is why the filter belongs here
        rather than at each of them: this powers `resolve_role` for every
        request, and `opportunity_engine` asks it before handing an account to
        a colleague — handing one to somebody who has left is the same defect
        wearing different clothes.
        """
        stmt = select(MembershipModel).where(
            MembershipModel.workspace_id == workspace_id,
            MembershipModel.user_id == user_id,
            MembershipModel.ended_at.is_(None),
        )
        model = (await self._session.execute(stmt)).scalar_one_or_none()
        if model is None:
            return None
        return MembershipView(
            workspace_id=model.workspace_id,
            user_id=model.user_id,
            role=model.role.value,
        )

    async def organization_history_page(
        self, workspace_id: UUID, *, after: CursorPosition | None, limit: int
    ) -> tuple[list[HistoryEntry], bool]:
        """One page of the organization's history, newest first — **TASK-443**.

        **The endpoint returned every entry there had ever been.** That is a
        contract a client cannot work with once a workspace has been running a
        year, and it is the collection §7 requires to be cursor-paginated.

        **Keyed on `(occurred_at, source_id)`.** Two things can happen in one
        microsecond, and a page boundary falling between them would drop one.
        `source_id` is the row an entry was derived from, which is the only
        stable identifier a derived entry has — entries are computed, not
        stored, so there is no id of their own to use.

        ⚠️ **The response is bounded and the *fetch* is not yet.** This pages
        over the full read below, so the query cost still grows with the
        workspace while the payload no longer does. **Said plainly rather than
        implied**: it fixes the contract and half the problem.

        **Bounding the fetch needs six queries, not one** — an entry is
        derived, so one membership yields a `joined` and possibly a `removed`
        at two different timestamps, and *"the newest N rows"* is a question no
        single table can answer. Each kind would be fetched bounded on its own
        timestamp and the six merged, taking `limit + 1` from each so the merge
        is provably complete. ⛔ **Still not a `UNION` of the three sources**,
        for the reason recorded below: the columns do not line up, and making
        them line up would turn adding a field to one source into a change to
        all three. **[C-231](../../../../docs/LANE_COORDINATION.md) carries it.**
        """
        found = await self.organization_history(workspace_id)
        if after is not None:
            found = [
                entry
                for entry in found
                if (entry.occurred_at, entry.source_id) < (after.created_at, after.id)
            ]
        return found[:limit], len(found) > limit

    async def organization_history(self, workspace_id: UUID) -> list[HistoryEntry]:
        """Everything that has happened to this organization, newest first.

        **A read model over three tables**, and deliberately not a projection
        into a fourth: the facts are already durable and already correct, and a
        copy would be a second representation to keep in step (`CLAUDE.md` §2).

        **Actor addresses are resolved at read time** from the actor's own
        membership — presentation resolving identity, per §24. An actor whose
        membership has since ended still resolves, because the row survives.
        """
        actors = aliased(MembershipModel)
        entries: list[HistoryEntry] = []

        memberships = (
            await self._session.execute(
                select(MembershipModel, actors.member_email)
                .outerjoin(
                    actors,
                    and_(
                        actors.workspace_id == MembershipModel.workspace_id,
                        actors.user_id == MembershipModel.ended_by,
                    ),
                )
                .where(MembershipModel.workspace_id == workspace_id)
            )
        ).all()
        for membership, remover_email in memberships:
            entries.append(
                HistoryEntry(
                    occurred_at=membership.created_at,
                    kind=HistoryKind.JOINED,
                    source_id=membership.id,
                    actor_id=None,
                    actor_email=None,
                    subject_email=membership.member_email,
                    subject_membership_id=membership.id,
                    new_role=membership.role.value,
                )
            )
            if membership.ended_at is not None:
                entries.append(
                    HistoryEntry(
                        occurred_at=membership.ended_at,
                        kind=HistoryKind.REMOVED,
                        source_id=membership.id,
                        actor_id=membership.ended_by,
                        actor_email=remover_email,
                        subject_email=membership.member_email,
                        subject_membership_id=membership.id,
                        reason=membership.ended_reason,
                    )
                )

        invitations = (
            await self._session.execute(
                select(InvitationModel, actors.member_email)
                .outerjoin(
                    actors,
                    and_(
                        actors.workspace_id == InvitationModel.workspace_id,
                        actors.user_id == InvitationModel.created_by,
                    ),
                )
                .where(InvitationModel.workspace_id == workspace_id)
            )
        ).all()
        for invitation, inviter_email in invitations:
            entries.append(
                HistoryEntry(
                    occurred_at=invitation.created_at,
                    kind=HistoryKind.INVITED,
                    source_id=invitation.id,
                    actor_id=invitation.created_by,
                    actor_email=inviter_email,
                    subject_email=invitation.invited_email,
                    subject_membership_id=None,
                    new_role=invitation.role.value,
                )
            )
            for moment, kind in (
                (invitation.revoked_at, HistoryKind.INVITATION_WITHDRAWN),
                (invitation.accepted_at, HistoryKind.INVITATION_ACCEPTED),
            ):
                if moment is not None:
                    entries.append(
                        HistoryEntry(
                            occurred_at=moment,
                            kind=kind,
                            source_id=invitation.id,
                            # **Withdrawal records no actor today**, and saying
                            # so is better than attributing it to the inviter,
                            # who may not be who withdrew it.
                            actor_id=None,
                            actor_email=None,
                            subject_email=invitation.invited_email,
                            subject_membership_id=None,
                        )
                    )

        changes = (
            await self._session.execute(
                select(MembershipRoleChangeModel, MembershipModel.member_email, actors.member_email)
                .outerjoin(
                    MembershipModel,
                    MembershipModel.id == MembershipRoleChangeModel.membership_id,
                )
                .outerjoin(
                    actors,
                    and_(
                        actors.workspace_id == MembershipRoleChangeModel.workspace_id,
                        actors.user_id == MembershipRoleChangeModel.created_by,
                    ),
                )
                .where(MembershipRoleChangeModel.workspace_id == workspace_id)
            )
        ).all()
        for change, subject_email, actor_email in changes:
            entries.append(
                HistoryEntry(
                    occurred_at=change.created_at,
                    kind=HistoryKind.ROLE_CHANGED,
                    source_id=change.id,
                    actor_id=change.created_by,
                    actor_email=actor_email,
                    subject_email=subject_email,
                    subject_membership_id=change.membership_id,
                    previous_role=change.previous_role.value,
                    new_role=change.new_role.value,
                )
            )

        # **Sorted here rather than by the database**, because the entries come
        # from three queries and a UNION would need every column to line up —
        # which would make adding a field to one of them a change to all three.
        entries.sort(key=lambda entry: entry.occurred_at, reverse=True)
        return entries
