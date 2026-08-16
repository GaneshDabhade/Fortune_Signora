"""SQLAlchemy implementations of this module's repository ports.

Each repository is constructed with the request/job-scoped ``AsyncSession``
(bound by the composition root — see ``composition.py``) and maps explicitly
between domain entities and ORM models in both directions.
"""

from collections.abc import Sequence
from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import Select, func, literal, select, tuple_, update
from sqlalchemy.dialects.postgresql import insert as pg_insert

from modules.workspace_tenancy.domain.entities import Membership, Workspace, WorkspaceRole
from modules.workspace_tenancy.domain.invitation import Invitation
from modules.workspace_tenancy.domain.notification import (
    Actor,
    ActorKind,
    Category,
    Notification,
    NotificationError,
    Subject,
)
from modules.workspace_tenancy.domain.notification_state import (
    CAP,
    UnreadCount,
)
from modules.workspace_tenancy.domain.notification_state import unread as unread_count
from modules.workspace_tenancy.domain.onboarding import (
    Answer,
    CompanySizeBand,
    Goal,
    OnboardingRun,
    OnboardingStep,
    Provenance,
    Role,
)
from modules.workspace_tenancy.domain.preferences import (
    AnswerStyle,
    Density,
    PersonPreferences,
    ScreenReaderVerbosity,
    TextSize,
    Theme,
    TimeFormat,
)
from modules.workspace_tenancy.domain.saved_view import SavedView
from modules.workspace_tenancy.domain.security_event import SecurityEvent
from modules.workspace_tenancy.infrastructure.models import (
    InvitationModel,
    MembershipModel,
    MembershipRoleChangeModel,
    NotificationReadRow,
    NotificationRow,
    OnboardingRunModel,
    PersonPreferencesModel,
    SavedViewModel,
    SecurityEventModel,
    WorkspaceModel,
)
from signora_platform.db import SqlAlchemyRepository
from signora_platform.pagination import CursorPosition


def _workspace_to_domain(model: WorkspaceModel) -> Workspace:
    return Workspace(
        id=model.id,
        name=model.name,
        created_at=model.created_at,
        updated_at=model.updated_at,
        created_by=model.created_by,
        updated_by=model.updated_by,
    )


def _membership_to_domain(model: MembershipModel) -> Membership:
    return Membership(
        id=model.id,
        workspace_id=model.workspace_id,
        user_id=model.user_id,
        role=model.role,
        created_at=model.created_at,
        updated_at=model.updated_at,
        created_by=model.created_by,
        updated_by=model.updated_by,
        ended_at=model.ended_at,
        ended_by=model.ended_by,
        ended_reason=model.ended_reason,
        member_email=model.member_email,
    )


def _apply_keyset[M: MembershipModel | SavedViewModel | WorkspaceModel](
    statement: Select[tuple[M]],
    model: type[M],
    after: CursorPosition | None,
) -> Select[tuple[M]]:
    """Apply newest-first keyset ordering and a strict "after" bound.

    The bound is a SQL row-value comparison — ``(created_at, id) < (…)`` —
    rather than two chained column comparisons. That is what makes the page
    boundary exact when rows share a timestamp: comparing on ``created_at``
    alone would drop or repeat rows at the seam, and an ``OR``-based
    rewrite is both harder to read and worse for the planner.

    ``tuple_()`` is required here; a plain Python tuple comparison would
    compare the column objects themselves, not emit SQL.
    """
    statement = statement.order_by(model.created_at.desc(), model.id.desc())
    if after is not None:
        # literal() binds the cursor values as parameters rather than
        # inlining them, so the comparison is both typed and injection-safe.
        statement = statement.where(
            tuple_(model.created_at, model.id)
            < tuple_(literal(after.created_at), literal(after.id))
        )
    return statement


class SqlAlchemyWorkspaceRepository(SqlAlchemyRepository):
    async def add(self, workspace: Workspace) -> None:
        await self._add(
            WorkspaceModel(
                id=workspace.id,
                name=workspace.name,
                created_at=workspace.created_at,
                updated_at=workspace.updated_at,
                created_by=workspace.created_by,
                updated_by=workspace.updated_by,
            )
        )

    async def get(self, workspace_id: UUID) -> Workspace | None:
        model = await self._session.get(WorkspaceModel, workspace_id)
        return _workspace_to_domain(model) if model is not None else None

    async def list_visible(self, *, limit: int, after: CursorPosition | None) -> list[Workspace]:
        """No user filter appears here by design: the workspace table's RLS
        policy already restricts rows to workspaces the session's
        ``app.user_id`` is a member of (11-tenancy.md)."""
        statement = _apply_keyset(select(WorkspaceModel), WorkspaceModel, after).limit(limit)
        models = (await self._session.execute(statement)).scalars().all()
        return [_workspace_to_domain(model) for model in models]


class SqlAlchemyMembershipRepository(SqlAlchemyRepository):
    async def add(self, membership: Membership) -> None:
        await self._add(
            MembershipModel(
                id=membership.id,
                workspace_id=membership.workspace_id,
                user_id=membership.user_id,
                role=membership.role,
                created_at=membership.created_at,
                updated_at=membership.updated_at,
                created_by=membership.created_by,
                updated_by=membership.updated_by,
                member_email=membership.member_email,
            )
        )

    async def get(self, workspace_id: UUID, user_id: UUID) -> Membership | None:
        """The **live** membership, and the filter is security-relevant.

        This is what verifies membership on every request. An ended membership
        that still resolved here would keep somebody signed in to an
        organization they had been removed from.
        """
        stmt = select(MembershipModel).where(
            MembershipModel.workspace_id == workspace_id,
            MembershipModel.user_id == user_id,
            MembershipModel.ended_at.is_(None),
        )
        model = (await self._session.execute(stmt)).scalar_one_or_none()
        return _membership_to_domain(model) if model is not None else None

    async def list_page_for_workspace(
        self, workspace_id: UUID, *, limit: int, after: CursorPosition | None
    ) -> list[Membership]:
        statement = _apply_keyset(
            select(MembershipModel).where(
                MembershipModel.workspace_id == workspace_id,
                # Live only. *"Who is in my organization"* does not include
                # people who have left — their rows survive for the audit
                # trail, not for the roster.
                MembershipModel.ended_at.is_(None),
            ),
            MembershipModel,
            after,
        ).limit(limit)
        models = (await self._session.execute(statement)).scalars().all()
        return [_membership_to_domain(model) for model in models]

    async def get_by_id(self, workspace_id: UUID, membership_id: UUID) -> Membership | None:
        stmt = select(MembershipModel).where(
            MembershipModel.workspace_id == workspace_id,
            MembershipModel.id == membership_id,
        )
        model = (await self._session.execute(stmt)).scalar_one_or_none()
        return _membership_to_domain(model) if model is not None else None

    async def lock_membership_set(self, workspace_id: UUID) -> None:
        """Serialise changes to the shape of this workspace's membership set.

        **The last-owner invariant spans every membership, so counting is not
        enough.** Two owners demoted concurrently each read *two owners*, each
        compute *one remaining*, and both succeed — leaving an organization
        nobody can administer. Neither transaction did anything wrong; the
        check is simply not atomic across them.

        Locking the **workspace** row is the aggregate boundary made
        executable: §13 records that Workspace is the root for anything that
        changes the shape of the membership set, and this is what that means at
        runtime. It serialises only those operations, and only per workspace.
        """
        await self._session.execute(
            select(WorkspaceModel.id).where(WorkspaceModel.id == workspace_id).with_for_update()
        )

    async def count_live_owners(self, workspace_id: UUID) -> int:
        """How many people can still administer this organization.

        **The last-owner invariant spans the whole membership set**, so the
        aggregate cannot see it. A count rather than a collection: the rule
        needs a number, and loading every membership to change one is what the
        two-aggregate split deliberately avoids.
        """
        stmt = (
            select(func.count())
            .select_from(MembershipModel)
            .where(
                MembershipModel.workspace_id == workspace_id,
                MembershipModel.role == WorkspaceRole.OWNER,
                MembershipModel.ended_at.is_(None),
            )
        )
        return int((await self._session.execute(stmt)).scalar_one())

    async def save_role(self, membership: Membership) -> None:
        stmt = (
            update(MembershipModel)
            .where(
                MembershipModel.workspace_id == membership.workspace_id,
                MembershipModel.id == membership.id,
            )
            .values(
                role=membership.role,
                updated_at=membership.updated_at,
                updated_by=membership.updated_by,
            )
        )
        await self._session.execute(stmt)

    async def end(self, membership: Membership) -> None:
        stmt = (
            update(MembershipModel)
            .where(
                MembershipModel.workspace_id == membership.workspace_id,
                MembershipModel.id == membership.id,
            )
            .values(
                ended_at=membership.ended_at,
                ended_by=membership.ended_by,
                ended_reason=membership.ended_reason,
                updated_at=membership.updated_at,
                updated_by=membership.updated_by,
            )
        )
        await self._session.execute(stmt)


class SqlAlchemyInvitationRepository(SqlAlchemyRepository):
    """Persistence for offers of membership.

    **No `update` method that takes arbitrary fields.** `settle` writes exactly
    the two timestamps the domain can produce, so an invitation cannot be edited
    through this seam even by accident — the domain's immutability is only real
    if the repository cannot undo it.
    """

    async def add(self, invitation: Invitation) -> None:
        await self._add(
            InvitationModel(
                id=invitation.id,
                workspace_id=invitation.workspace_id,
                invited_email=invitation.invited_email,
                role=invitation.role,
                expires_at=invitation.expires_at,
                accepted_at=invitation.accepted_at,
                revoked_at=invitation.revoked_at,
                created_at=invitation.created_at,
                updated_at=invitation.created_at,
                created_by=invitation.invited_by,
                updated_by=invitation.invited_by,
            )
        )

    async def get(self, workspace_id: UUID, invitation_id: UUID) -> Invitation | None:
        stmt = select(InvitationModel).where(
            InvitationModel.workspace_id == workspace_id,
            InvitationModel.id == invitation_id,
        )
        model = (await self._session.execute(stmt)).scalar_one_or_none()
        return _invitation_to_domain(model) if model is not None else None

    async def find_live(self, workspace_id: UUID, email: str) -> Invitation | None:
        """The one invitation that would collide with a new offer.

        **Matches the partial unique index exactly.** If these two ever disagree
        the index wins and the customer sees a database error instead of the
        sentence this lookup exists to produce.
        """
        stmt = select(InvitationModel).where(
            InvitationModel.workspace_id == workspace_id,
            InvitationModel.invited_email == email,
            InvitationModel.accepted_at.is_(None),
            InvitationModel.revoked_at.is_(None),
        )
        model = (await self._session.execute(stmt)).scalar_one_or_none()
        return _invitation_to_domain(model) if model is not None else None

    async def list_for_workspace(self, workspace_id: UUID) -> list[Invitation]:
        """Every invitation, in every state, newest first.

        **Not paginated, and it matches `list_connections`' reasoning**: an
        organization sends a handful of invitations, not thousands, and a cursor
        over a list that fits on one screen is ceremony. If that stops being
        true it becomes a collection like any other (19-api-conventions.md).
        """
        stmt = (
            select(InvitationModel)
            .where(InvitationModel.workspace_id == workspace_id)
            .order_by(InvitationModel.created_at.desc())
        )
        models = (await self._session.execute(stmt)).scalars().all()
        return [_invitation_to_domain(model) for model in models]

    async def settle(self, invitation: Invitation) -> None:
        stmt = (
            update(InvitationModel)
            .where(
                InvitationModel.workspace_id == invitation.workspace_id,
                InvitationModel.id == invitation.id,
            )
            .values(
                accepted_at=invitation.accepted_at,
                revoked_at=invitation.revoked_at,
                updated_by=invitation.invited_by,
            )
        )
        await self._session.execute(stmt)


def _invitation_to_domain(model: InvitationModel) -> Invitation:
    return Invitation(
        id=model.id,
        workspace_id=model.workspace_id,
        invited_email=model.invited_email,
        role=model.role,
        expires_at=model.expires_at,
        invited_by=model.created_by,
        created_at=model.created_at,
        accepted_at=model.accepted_at,
        revoked_at=model.revoked_at,
    )


class SqlAlchemyRoleChangeLog(SqlAlchemyRepository):
    """Append-only. **There is no update method, and the grant has no UPDATE.**"""

    async def record(
        self,
        *,
        workspace_id: UUID,
        membership_id: UUID,
        previous_role: WorkspaceRole,
        new_role: WorkspaceRole,
        changed_by: UUID,
        at: datetime,
    ) -> None:
        await self._add(
            MembershipRoleChangeModel(
                id=uuid4(),
                workspace_id=workspace_id,
                membership_id=membership_id,
                previous_role=previous_role,
                new_role=new_role,
                created_at=at,
                updated_at=at,
                created_by=changed_by,
                updated_by=changed_by,
            )
        )


class SqlAlchemySecurityEventLog(SqlAlchemyRepository):
    """The activity stream's only write path — TASK-492.

    ⛔ **`record` and nothing else.** There is no update method, no correct
    method and no delete method, and the grant has no `UPDATE`: the two agree
    by construction rather than because a reviewer checked. **A repository
    that offered an edit would be offering something the database refuses**,
    and the caller would find out at runtime.

    ⚡ **It takes a {@link SecurityEvent}, never loose arguments.** The domain
    type is what enforces the two-identity rule and refuses a credential in
    `detail`; accepting `subject_id`/`acting_for` as parameters here would let
    a caller bypass both by calling the repository directly.
    """

    async def record(self, event: SecurityEvent) -> None:
        await self._add(
            SecurityEventModel(
                id=uuid4(),
                workspace_id=event.workspace_id,
                kind=event.kind,
                subject_id=event.subject_id,
                acting_for=event.acting_for,
                occurred_at=event.occurred_at,
                detail=event.detail,
            )
        )


__all__ = [
    "SqlAlchemyInvitationRepository",
    "SqlAlchemySecurityEventLog",
    "SqlAlchemyRoleChangeLog",
    "SqlAlchemyMembershipRepository",
    "SqlAlchemyWorkspaceRepository",
]


def _saved_view_to_domain(model: SavedViewModel) -> SavedView:
    return SavedView(
        id=model.id,
        workspace_id=model.workspace_id,
        name=model.name,
        declaration=model.declaration,
        created_by=model.created_by,
        created_at=model.created_at,
        supersedes=model.supersedes,
        retired_at=model.retired_at,
    )


class SqlAlchemySavedViewRepository(SqlAlchemyRepository):
    """Saved views, stored and read back. **No `update` path for a
    declaration** — the one write that touches an existing row stamps
    `retired_at`, and the table carries no `UPDATE` grant for anything else.
    """

    async def add(self, view: SavedView) -> None:
        self._session.add(
            SavedViewModel(
                id=view.id,
                workspace_id=view.workspace_id,
                name=view.name,
                declaration=view.declaration,
                supersedes=view.supersedes,
                retired_at=view.retired_at,
                created_by=view.created_by,
                updated_by=view.created_by,
            )
        )
        await self._session.flush()

    async def get(self, workspace_id: UUID, saved_view_id: UUID) -> SavedView | None:
        statement = select(SavedViewModel).where(
            SavedViewModel.id == saved_view_id,
            # Defence in depth beside RLS (11-tenancy.md): the policy is the
            # authoritative control and the predicate is stated anyway.
            SavedViewModel.workspace_id == workspace_id,
        )
        model = (await self._session.execute(statement)).scalar_one_or_none()
        return None if model is None else _saved_view_to_domain(model)

    async def list_live_page(
        self, workspace_id: UUID, *, limit: int, after: CursorPosition | None
    ) -> list[SavedView]:
        """In force: **not retired, and not replaced by a later version.**

        ⚡ **Both halves are derived from the rows themselves.** The supersession
        chain already records which version was replaced, so a `is_live` column
        beside it would be the same fact twice — and the partial index
        `ix_saved_view_live` exists precisely so deriving it stays cheap.
        """
        replaced = select(SavedViewModel.supersedes).where(
            SavedViewModel.workspace_id == workspace_id,
            SavedViewModel.supersedes.is_not(None),
        )
        statement = _apply_keyset(
            select(SavedViewModel).where(
                SavedViewModel.workspace_id == workspace_id,
                SavedViewModel.retired_at.is_(None),
                SavedViewModel.id.not_in(replaced),
            ),
            SavedViewModel,
            after,
        ).limit(limit)
        models = (await self._session.execute(statement)).scalars().all()
        return [_saved_view_to_domain(model) for model in models]

    async def mark_retired(self, view: SavedView) -> None:
        """Stamp a retirement onto the row it belongs to.

        ⛔ **Guarded by `retired_at IS NULL` in the `WHERE`**, so two concurrent
        retirements cannot overwrite the first timestamp. The aggregate refuses
        the second in memory; this refuses it in the database, and the fact
        that both do is the point — *a guard that cannot fail is documentation
        pretending to be code* (§2).
        """
        statement = (
            update(SavedViewModel)
            .where(
                SavedViewModel.id == view.id,
                SavedViewModel.workspace_id == view.workspace_id,
                SavedViewModel.retired_at.is_(None),
            )
            .values(retired_at=view.retired_at, updated_by=view.created_by)
        )
        await self._session.execute(statement)
        await self._session.flush()


def _answer(value: object | None, provenance: str | None) -> Answer[Any] | None:
    """Rebuild a value and where it came from, or neither.

    ⛔ **Both columns or nothing.** A value whose provenance went missing
    cannot be rendered honestly — the screen would either drop the *Inferred*
    badge off something inferred, or attach it to something the person typed —
    so a half-written pair reads as unanswered rather than as a guess.
    """
    if value is None or provenance is None:
        return None
    return Answer(value=value, provenance=Provenance(provenance))


def _onboarding_to_domain(model: OnboardingRunModel) -> OnboardingRun:
    size = _answer(model.company_size, model.company_size_provenance)
    role = _answer(model.role, model.role_provenance)
    return OnboardingRun(
        workspace_id=model.workspace_id,
        person_id=model.person_id,
        started_at=model.started_at,
        current_step=OnboardingStep(model.current_step),
        completed_steps=frozenset(OnboardingStep(step) for step in model.completed_steps),
        industry=_answer(model.industry, model.industry_provenance),
        company_size=(
            None if size is None else Answer(CompanySizeBand(size.value), size.provenance)
        ),
        region=_answer(model.region, model.region_provenance),
        timezone=_answer(model.timezone, model.timezone_provenance),
        role=None if role is None else Answer(Role(role.value), role.provenance),
        team_size=_answer(model.team_size, model.team_size_provenance),
        goals=tuple(Goal(goal) for goal in model.goals),
        finished_at=model.finished_at,
        skipped_at=model.skipped_at,
        updated_at=model.updated_at,
    )


def _columns(run: OnboardingRun) -> dict[str, object]:
    """The aggregate flattened onto its row.

    ⛔ **`features` is deliberately absent** — it is derived from `goals` and
    storing it would be the second representation that eventually disagrees
    (§2).
    """
    return {
        "started_at": run.started_at,
        "current_step": run.current_step.value,
        "completed_steps": sorted(step.value for step in run.completed_steps),
        "industry": None if run.industry is None else run.industry.value,
        "industry_provenance": None if run.industry is None else run.industry.provenance.value,
        "company_size": None if run.company_size is None else run.company_size.value.value,
        "company_size_provenance": (
            None if run.company_size is None else run.company_size.provenance.value
        ),
        "region": None if run.region is None else run.region.value,
        "region_provenance": None if run.region is None else run.region.provenance.value,
        "timezone": None if run.timezone is None else run.timezone.value,
        "timezone_provenance": None if run.timezone is None else run.timezone.provenance.value,
        "role": None if run.role is None else run.role.value.value,
        "role_provenance": None if run.role is None else run.role.provenance.value,
        "team_size": None if run.team_size is None else run.team_size.value,
        "team_size_provenance": None if run.team_size is None else run.team_size.provenance.value,
        "goals": [goal.value for goal in run.goals],
        "finished_at": run.finished_at,
        "skipped_at": run.skipped_at,
    }


class SqlAlchemyOnboardingRunRepository(SqlAlchemyRepository):
    """A person's onboarding run, stored and read back — **TASK-469**.

    ⚡ **`save` is an upsert on *(workspace, person)*, and the shape follows
    the design**: *"every step saves on advance and on blur"* means the client
    sends the same run repeatedly, and a create/update split at this layer
    would push the question *"is this the first save?"* into every caller.
    """

    async def get(self, workspace_id: UUID, person_id: UUID) -> OnboardingRun | None:
        statement = select(OnboardingRunModel).where(
            OnboardingRunModel.workspace_id == workspace_id,
            # Defence in depth beside RLS (11-tenancy.md): the policy is the
            # authoritative control and the predicate is stated anyway.
            OnboardingRunModel.person_id == person_id,
        )
        model = (await self._session.execute(statement)).scalar_one_or_none()
        return None if model is None else _onboarding_to_domain(model)

    async def save(self, run: OnboardingRun) -> None:
        statement = select(OnboardingRunModel).where(
            OnboardingRunModel.workspace_id == run.workspace_id,
            OnboardingRunModel.person_id == run.person_id,
        )
        model = (await self._session.execute(statement)).scalar_one_or_none()
        columns = _columns(run)
        if model is None:
            self._session.add(
                OnboardingRunModel(
                    workspace_id=run.workspace_id,
                    person_id=run.person_id,
                    created_by=run.person_id,
                    updated_by=run.person_id,
                    **columns,
                )
            )
        else:
            for column, value in columns.items():
                setattr(model, column, value)
            model.updated_by = run.person_id
        await self._session.flush()


def _preferences_to_domain(model: PersonPreferencesModel) -> PersonPreferences:
    return PersonPreferences(
        workspace_id=model.workspace_id,
        person_id=model.user_id,
        theme=Theme(model.theme),
        density=Density(model.density),
        timezone=model.timezone,
        language=model.language,
        time_format=TimeFormat(model.time_format),
        pronouns=model.pronouns,
        display_name=model.display_name,
        ai_insights=model.ai_insights,
        ai_drafts=model.ai_drafts,
        always_show_citations=model.always_show_citations,
        answer_style=AnswerStyle(model.answer_style),
        confidence_floor=model.confidence_floor,
        job_title=model.job_title,
        department=model.department,
        mobile=model.mobile,
        date_format=model.date_format,
        number_format=model.number_format,
        week_starts_on=model.week_starts_on,
        reduce_motion=model.reduce_motion,
        increase_contrast=model.increase_contrast,
        always_show_focus_ring=model.always_show_focus_ring,
        underline_links=model.underline_links,
        text_size=TextSize(model.text_size),
        screen_reader_verbosity=ScreenReaderVerbosity(model.screen_reader_verbosity),
        last_entered_at=model.last_entered_at,
        first_run_dismissed_at=model.first_run_dismissed_at,
        invite_skipped_at=model.invite_skipped_at,
    )


class SqlAlchemyPersonPreferencesRepository(SqlAlchemyRepository):
    """A person's preferences, stored and read back — **TASK-470**.

    ⚡ **`get` never returns `None`.** A person who has never opened the screen
    has preferences — the defaults — and **the absence of a row is not the
    absence of an answer.** Returning `None` would push that reasoning into
    every caller, and the first one to forget it renders a blank profile.
    """

    async def get(self, workspace_id: UUID, person_id: UUID) -> PersonPreferences:
        statement = select(PersonPreferencesModel).where(
            PersonPreferencesModel.workspace_id == workspace_id,
            # Defence in depth beside the RLS policy, which carries the same
            # two predicates (11-tenancy.md, 492 §0).
            PersonPreferencesModel.user_id == person_id,
        )
        model = (await self._session.execute(statement)).scalar_one_or_none()
        if model is None:
            return PersonPreferences(workspace_id=workspace_id, person_id=person_id)
        return _preferences_to_domain(model)

    async def save(self, preferences: PersonPreferences) -> None:
        statement = select(PersonPreferencesModel).where(
            PersonPreferencesModel.workspace_id == preferences.workspace_id,
            PersonPreferencesModel.user_id == preferences.person_id,
        )
        model = (await self._session.execute(statement)).scalar_one_or_none()
        columns = {
            "theme": preferences.theme.value,
            "density": preferences.density.value,
            "timezone": preferences.timezone,
            "language": preferences.language,
            "time_format": preferences.time_format.value,
            "pronouns": preferences.pronouns,
            "display_name": preferences.display_name,
            "ai_insights": preferences.ai_insights,
            "ai_drafts": preferences.ai_drafts,
            "always_show_citations": preferences.always_show_citations,
            "answer_style": preferences.answer_style.value,
            "confidence_floor": preferences.confidence_floor,
            # ⚡ **Every one round-trips.** ⛔ A column written on the way in and
            # dropped on the way out is a setting that silently forgets itself,
            # which is what TASK-1422 found one field over.
            "job_title": preferences.job_title,
            "department": preferences.department,
            "mobile": preferences.mobile,
            "date_format": preferences.date_format,
            "number_format": preferences.number_format,
            "week_starts_on": preferences.week_starts_on,
            "reduce_motion": preferences.reduce_motion,
            "increase_contrast": preferences.increase_contrast,
            "always_show_focus_ring": preferences.always_show_focus_ring,
            "underline_links": preferences.underline_links,
            "text_size": preferences.text_size.value,
            "screen_reader_verbosity": preferences.screen_reader_verbosity.value,
            # 🔴 **[TASK-1422] — round-trips like every other column.** ⛔ Omitting
            # it here would make `entered()` a no-op that every unit test still
            # passed, because the aggregate would be correct and the row never
            # written.
            "last_entered_at": preferences.last_entered_at,
            "first_run_dismissed_at": preferences.first_run_dismissed_at,
            "invite_skipped_at": preferences.invite_skipped_at,
        }
        if model is None:
            self._session.add(
                PersonPreferencesModel(
                    workspace_id=preferences.workspace_id,
                    user_id=preferences.person_id,
                    created_by=preferences.person_id,
                    updated_by=preferences.person_id,
                    **columns,
                )
            )
        else:
            for column, value in columns.items():
                setattr(model, column, value)
            model.updated_by = preferences.person_id
        await self._session.flush()


class SqlAlchemyNotificationReadRepository(SqlAlchemyRepository):
    """What one person has read — **[TASK-480](../../../../docs/BACKLOG.md)**.

    ⚡ **Every query carries BOTH predicates**, exactly as
    `SqlAlchemyPersonPreferencesRepository` does: **defence in depth beside the
    RLS policy, which carries the same two** (📁 `11-tenancy.md`, 492 §0).

    ⛔ **There is no `update`.** 📁 A read is a record of something that
    happened, the table has no `UPDATE` grant, and **a method offering one
    would promise what the database refuses.**
    """

    async def mark_read(
        self, workspace_id: UUID, person_id: UUID, notification_ids: Sequence[UUID]
    ) -> None:
        """Record that this person has read these.

        ⚡ **Idempotent by the primary key rather than by a check.** ⛔ **A
        `SELECT` then `INSERT` would race two tabs against each other**, and
        marking read twice is something a customer does by double-clicking —
        **it must not be an error and it must not need a transaction to be
        safe.**
        """
        if not notification_ids:
            return
        statement = (
            pg_insert(NotificationReadRow)
            .values(
                [
                    {
                        "workspace_id": workspace_id,
                        "user_id": person_id,
                        "notification_id": notification_id,
                    }
                    for notification_id in notification_ids
                ]
            )
            # ⚡ **The FIRST read time survives.** 📁 §2 — a record of what was
            # true then is not rewritten; the moment they read it is the fact,
            # and a later click does not change when it happened.
            .on_conflict_do_nothing(
                index_elements=["workspace_id", "user_id", "notification_id"]
            )
        )
        await self._session.execute(statement)

    async def unread(
        self, workspace_id: UUID, person_id: UUID, candidates: Sequence[UUID]
    ) -> UnreadCount:
        """How many of `candidates` this person has not read — **bounded**.

        🔴 **The query stops at `CAP + 1` and the extra one is the whole
        trick**: it distinguishes *exactly nine* from *nine or more* without
        counting further. ⛔ **An unbounded count on this path reads thousands
        of rows to render two characters**, on exactly the person most likely
        to have them — somebody returning from leave.

        ⚠️ **`candidates` is supplied by the caller rather than derived here.**
        📁 **Notifications are not this module's** — ADR-0017 owns delivery —
        **so this answers *which of these has this person not read*, which is
        the only question it can honestly answer.**
        """
        if not candidates:
            return unread_count(total=0)
        read = select(NotificationReadRow.notification_id).where(
            NotificationReadRow.workspace_id == workspace_id,
            # Defence in depth beside the RLS policy, which carries the same
            # two predicates (11-tenancy.md, 492 §0).
            NotificationReadRow.user_id == person_id,
            NotificationReadRow.notification_id.in_(candidates),
        )
        seen = set((await self._session.execute(read)).scalars().all())
        # ⚡ **Bounded in Python because the candidate set already is** — the
        # caller passed a page of ids, not a table. **Counting past the cap
        # would answer a question the badge cannot render.**
        total = 0
        for candidate in candidates:
            if candidate not in seen:
                total += 1
                if total > CAP:
                    break
        return unread_count(total=total)


class SqlAlchemyNotificationRepository(SqlAlchemyRepository):
    """Notifications, written for one person and readable only by them —
    **[TASK-495](../../../../docs/BACKLOG.md)**.

    ⚡ **The asymmetry is the design and it comes from migration `0059`**:
    ⛔ **INSERT is workspace-scoped** — a notification is written FOR somebody
    else, so a recipient predicate on the write would permit notifying nobody
    but yourself — ✅ **and SELECT carries both predicates**, in the policy and
    again here.

    🔴 **`recipient_id` is filtered in every read even though the policy already
    does it.** 📁 [§8](../../../../CLAUDE.md), *defense-in-depth* — **the person
    predicate earns the same treatment the tenant one does**, and 📁 492 §0 says
    it in terms: *one predicate is added … in the policy AND in the query*.
    """

    async def record(self, notification: Notification) -> None:
        """Persist one notification.

        ⛔ **No upsert and no conflict clause.** ⚡ **The id is minted by the
        caller for this one delivery**, so a second row would mean a second
        delivery — 📁 which is the duplicate `Notify` resolves every channel
        up-front to prevent, and it should surface rather than be absorbed.
        """
        self._session.add(
            NotificationRow(
                id=notification.id,
                workspace_id=notification.workspace_id,
                recipient_id=notification.recipient_id,
                category=notification.category.value,
                actor_kind=notification.actor.kind.value,
                actor_person_id=notification.actor.person_id,
                actor_agent_name=notification.actor.agent_name,
                subject_kind=notification.subject.kind,
                subject_id=notification.subject.id,
                summary=notification.summary,
                expectation=notification.expectation,
                occurred_at=notification.occurred_at,
            )
        )
        await self._session.flush()

    async def feed(
        self, workspace_id: UUID, person_id: UUID, *, limit: int
    ) -> list[Notification]:
        """This person's notifications, newest first, bounded.

        ⚠️ **`limit` is required and has no default.** ⛔ **A caller that forgot
        it would read every notification a person has ever received** — on
        exactly the person most likely to have thousands, somebody returning
        from leave. 📁 The same argument `UnreadCount`'s cap makes, one layer
        down.

        ⚡ **Newest first, because the panel groups by DAY** — a page assembled
        from the oldest rows would group correctly and show the wrong days.
        """
        if limit <= 0:
            raise NotificationError(
                f"a feed limit of {limit} asks for no notifications and returns "
                "an empty panel, which a customer cannot tell from having none."
            )
        statement = (
            select(NotificationRow)
            .where(
                NotificationRow.workspace_id == workspace_id,
                # Defence in depth beside the RLS policy, which carries the
                # same two predicates (11-tenancy.md, 492 §0).
                NotificationRow.recipient_id == person_id,
            )
            .order_by(NotificationRow.occurred_at.desc(), NotificationRow.id.desc())
            .limit(limit)
        )
        rows = (await self._session.execute(statement)).scalars().all()
        return [_to_notification(row) for row in rows]


def _to_notification(row: NotificationRow) -> Notification:
    """**Mapped explicitly**, because the ORM row is not the domain model.

    ⚡ **The domain's guards re-run here**, which is what makes them hold for
    data that came back out of the database rather than only for data going in:
    a row written before a guard existed fails on READ rather than rendering.
    """
    return Notification(
        id=row.id,
        workspace_id=row.workspace_id,
        recipient_id=row.recipient_id,
        category=Category(row.category),
        actor=Actor(
            kind=ActorKind(row.actor_kind),
            person_id=row.actor_person_id,
            agent_name=row.actor_agent_name,
        ),
        subject=Subject(kind=row.subject_kind, id=row.subject_id),
        summary=row.summary,
        expectation=row.expectation,
        occurred_at=row.occurred_at,
    )
