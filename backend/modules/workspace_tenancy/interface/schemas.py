"""HTTP request/response schemas for Workspace & Tenancy.

Deliberately separate from the domain entities in ``domain/entities.py``,
even where currently field-identical. Coupling the wire contract to the
domain model means a domain refactor becomes a client-breaking change
(19-api-conventions.md).
"""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from modules.workspace_tenancy.application.use_cases.organization_history import (
    HistoryEntry,
    HistoryKind,
)
from modules.workspace_tenancy.domain.entities import (
    MAX_WORKSPACE_NAME_LENGTH,
    Membership,
    Workspace,
    WorkspaceRole,
)
from modules.workspace_tenancy.domain.invitation import Invitation, InvitationState
from modules.workspace_tenancy.domain.onboarding import (
    MAX_GOALS,
    MAX_TEAM_SIZE,
    MIN_TEAM_SIZE,
    Answer,
    Goal,
    OnboardingRun,
    OnboardingStep,
    Provenance,
)
from modules.workspace_tenancy.domain.preferences import (
    MAX_CONFIDENCE_FLOOR,
    MIN_CONFIDENCE_FLOOR,
    AnswerStyle,
    Density,
    PersonPreferences,
    Theme,
    TimeFormat,
)
from modules.workspace_tenancy.domain.saved_view import SavedView


class CreateWorkspaceRequest(BaseModel):
    model_config = ConfigDict(frozen=True)

    name: str = Field(min_length=1, max_length=MAX_WORKSPACE_NAME_LENGTH)


class AddMemberRequest(BaseModel):
    model_config = ConfigDict(frozen=True)

    user_id: UUID
    role: WorkspaceRole


class WorkspaceResponse(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: UUID
    name: str
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_domain(cls, workspace: Workspace) -> WorkspaceResponse:
        return cls(
            id=workspace.id,
            name=workspace.name,
            created_at=workspace.created_at,
            updated_at=workspace.updated_at,
        )


class MembershipResponse(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: UUID
    workspace_id: UUID
    user_id: UUID
    role: WorkspaceRole
    created_at: datetime
    #: The address this membership was created with, when one is known.
    #: `None` for memberships added by identifier before invitations existed —
    #: the screen says *"Somebody here"*, which is the wording D23 established
    #: rather than an identifier dressed as information.
    member_email: str | None = None
    #: When this person stopped belonging, and `None` while they still do.
    #:
    #: **Added 2026-08-05 with the leave endpoint, because two endpoints were
    #: already claiming it.** `remove_member` says in its own docstring that
    #: *"the response returns the ended membership rather than `204`"* — and
    #: the response could not express endedness, so an ended membership was
    #: byte-for-byte indistinguishable from a live one. **A contract that
    #: cannot say what the endpoint says it says.**
    #:
    #: Additive and optional: every existing caller reads `None` and nothing
    #: about a live membership changes.
    ended_at: datetime | None = None

    @classmethod
    def from_domain(cls, membership: Membership) -> MembershipResponse:
        return cls(
            member_email=membership.member_email,
            id=membership.id,
            workspace_id=membership.workspace_id,
            user_id=membership.user_id,
            role=membership.role,
            created_at=membership.created_at,
            ended_at=membership.ended_at,
        )


class InviteMemberRequest(BaseModel):
    model_config = ConfigDict(frozen=True)

    #: As the customer typed it. Normalized by the domain — the one place an
    #: address is put into the form the unique index and acceptance compare.
    email: str
    role: WorkspaceRole


class InvitationResponse(BaseModel):
    """An offer, as an administrator reads it.

    **`state` is computed and sent, not stored.** The browser must not derive it
    from `expires_at`, because two clocks would disagree and the one that
    matters is the server's — the same reason `evidence_state` travels on the
    wire rather than being recomputed on the client.
    """

    model_config = ConfigDict(frozen=True)

    id: UUID
    workspace_id: UUID
    invited_email: str
    role: WorkspaceRole
    state: InvitationState
    expires_at: datetime
    created_at: datetime
    #: Who offered it. An identifier rather than a name, for the reason the
    #: members list has the same shape (C-203) — and it never changes, because
    #: the inviter is provenance rather than an owner.
    invited_by: UUID

    @classmethod
    def from_domain(cls, invitation: Invitation, *, at: datetime) -> InvitationResponse:
        return cls(
            id=invitation.id,
            workspace_id=invitation.workspace_id,
            invited_email=invitation.invited_email,
            role=invitation.role,
            state=invitation.state(at=at),
            expires_at=invitation.expires_at,
            created_at=invitation.created_at,
            invited_by=invitation.invited_by,
        )


class RemoveMemberRequest(BaseModel):
    model_config = ConfigDict(frozen=True)

    #: Why, in the customer's words, and optional — an administrator correcting
    #: a mistaken invitation should not be made to justify it.
    reason: str | None = Field(default=None, max_length=500)


class ChangeRoleRequest(BaseModel):
    model_config = ConfigDict(frozen=True)

    role: WorkspaceRole


class TransferOwnershipRequest(BaseModel):
    model_config = ConfigDict(frozen=True)

    #: Who is handing over. Explicit rather than inferred from the caller, so
    #: one owner can transfer on another's behalf after they have left.
    from_membership_id: UUID
    to_membership_id: UUID


class HistoryEntryResponse(BaseModel):
    """One thing that happened, in the terms it was recorded in.

    **No rendered sentence.** The words a customer reads are a reviewed catalog
    at the frontend edge (ADR-0034), so improving one is a deploy rather than a
    migration — and an export can phrase the same entry differently.

    **An id and a snapshot for each person** (46-team-management.md §24): the
    snapshot is what was true then, the id is what a screen resolves when a
    reader needs to act rather than merely read.
    """

    model_config = ConfigDict(frozen=True)

    occurred_at: datetime
    kind: HistoryKind
    source_id: UUID = Field(
        description=(
            "The record this entry was derived from — a membership, an invitation or a "
            "role change. Entries are computed rather than stored, so this is the only "
            "stable identifier one has, and it is what the page cursor is keyed on. Not "
            "unique on its own: one membership yields both a joined and a removed entry."
        )
    )
    actor_id: UUID | None
    actor_email: str | None
    subject_email: str | None
    subject_membership_id: UUID | None
    previous_role: str | None
    new_role: str | None
    reason: str | None

    @classmethod
    def from_domain(cls, entry: HistoryEntry) -> HistoryEntryResponse:
        return cls(
            occurred_at=entry.occurred_at,
            kind=entry.kind,
            source_id=entry.source_id,
            actor_id=entry.actor_id,
            actor_email=entry.actor_email,
            subject_email=entry.subject_email,
            subject_membership_id=entry.subject_membership_id,
            previous_role=entry.previous_role,
            new_role=entry.new_role,
            reason=entry.reason,
        )


class SaveViewRequest(BaseModel):
    """Declaring a view, or revising one.

    ⛔ **`declaration` is `dict[str, Any]` and stays that way.** A typed schema
    here would make this module know what a *filter* is, which is exactly what
    [D-091](../../../../docs/DECISION_REGISTER.md) puts outside it — and the
    schema would then have to change every time a screen added a control.
    """

    name: str = Field(description="What the person called it — the customer's own words.")
    declaration: dict[str, Any] = Field(
        description="The query as the owning screen wrote it. Never parsed here."
    )
    saved_view_id: UUID | None = Field(
        default=None,
        description=(
            "Optional client-supplied identity, so a retry is idempotent rather than "
            "creating a second view."
        ),
    )


class ReviseViewRequest(BaseModel):
    """A new version replacing an existing one.

    **Both fields optional, and omitting both is legitimate**: it records that
    somebody re-affirmed the view unchanged, under their own name and at a new
    time — which is a fact the supersession chain should carry.
    """

    name: str | None = None
    declaration: dict[str, Any] | None = None


class SavedViewResponse(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: UUID
    workspace_id: UUID
    name: str
    declaration: dict[str, Any]
    created_by: UUID
    created_at: datetime
    supersedes: UUID | None
    retired_at: datetime | None

    @classmethod
    def from_domain(cls, view: SavedView) -> SavedViewResponse:
        return cls(
            id=view.id,
            workspace_id=view.workspace_id,
            name=view.name,
            declaration=view.declaration,
            created_by=view.created_by,
            created_at=view.created_at,
            supersedes=view.supersedes,
            retired_at=view.retired_at,
        )


class AnswerPayload(BaseModel):
    """A value and where it came from — **never one without the other.**

    ⛔ **`provenance` is required on the wire for the same reason it has no
    default in the domain**: a request that could omit it would let a client
    store a guess indistinguishable from a person's answer, and the *Inferred*
    badge the design requires would then be missing exactly where it matters.
    """

    model_config = ConfigDict(frozen=True)

    value: str
    provenance: Provenance


class TeamSizePayload(BaseModel):
    """The one answer that is a number rather than a choice."""

    model_config = ConfigDict(frozen=True)

    #: ⚠️ **Bounded here, on the aggregate and in the database.** Three layers
    #: sounds like duplication and is not: this one turns a bad request into a
    #: `422` with a field name, and the other two hold for anything that never
    #: passes through this schema.
    value: int = Field(ge=MIN_TEAM_SIZE, le=MAX_TEAM_SIZE)
    provenance: Provenance


class ConfirmCompanyRequest(BaseModel):
    """Screen `04`. **Every field optional and omitting one leaves it alone** —
    the step is skippable and partially answerable, and a request meaning to
    change the timezone must not clear the industry."""

    model_config = ConfigDict(frozen=True)

    industry: AnswerPayload | None = None
    company_size: AnswerPayload | None = None
    region: AnswerPayload | None = None
    timezone: AnswerPayload | None = None


class DescribePersonRequest(BaseModel):
    model_config = ConfigDict(frozen=True)

    role: AnswerPayload | None = None
    team_size: TeamSizePayload | None = None


class ChooseGoalsRequest(BaseModel):
    model_config = ConfigDict(frozen=True)

    #: ⛔ **`max_length` rather than a silent truncation.** *"The fourth
    #: selection is disabled, not silently ignored"* — a request carrying four
    #: is refused with the reason rather than quietly having one dropped.
    goals: list[Goal] = Field(default_factory=list, max_length=MAX_GOALS)


class AdvanceOnboardingRequest(BaseModel):
    model_config = ConfigDict(frozen=True)

    step: OnboardingStep


class AnswerResponse(BaseModel):
    model_config = ConfigDict(frozen=True)

    value: str
    provenance: Provenance

    @classmethod
    def from_domain(cls, answer: Answer[Any] | None) -> AnswerResponse | None:
        if answer is None:
            return None
        value = answer.value
        return cls(
            value=str(value.value if isinstance(value, StrEnum) else value),
            provenance=answer.provenance,
        )


class OnboardingRunResponse(BaseModel):
    """What every onboarding screen renders from.

    ⚡ **`features` is on the response and in no table.** The goals imply it
    deterministically, so it is derived on read — a stored copy would be the
    representation that eventually disagrees (§2).
    """

    model_config = ConfigDict(frozen=True)

    workspace_id: UUID
    current_step: OnboardingStep
    completed_steps: list[OnboardingStep]
    industry: AnswerResponse | None
    company_size: AnswerResponse | None
    region: AnswerResponse | None
    timezone: AnswerResponse | None
    role: AnswerResponse | None
    team_size: AnswerResponse | None
    goals: list[Goal]
    features: list[str]
    started_at: datetime
    finished_at: datetime | None
    #: ⚡ **The resume banner reads this**, and it is why *left* is a separate
    #: fact from *finished*.
    skipped_at: datetime | None

    @classmethod
    def from_domain(cls, run: OnboardingRun) -> OnboardingRunResponse:
        return cls(
            workspace_id=run.workspace_id,
            current_step=run.current_step,
            # Sorted for a stable body; the rail draws from the step order it
            # already knows, never from this list's arrangement.
            completed_steps=sorted(
                run.completed_steps, key=lambda s: list(OnboardingStep).index(s)
            ),
            industry=AnswerResponse.from_domain(run.industry),
            company_size=AnswerResponse.from_domain(run.company_size),
            region=AnswerResponse.from_domain(run.region),
            timezone=AnswerResponse.from_domain(run.timezone),
            role=AnswerResponse.from_domain(run.role),
            team_size=AnswerResponse.from_domain(run.team_size),
            goals=list(run.goals),
            features=list(run.features),
            started_at=run.started_at,
            finished_at=run.finished_at,
            skipped_at=run.skipped_at,
        )


class PreferencesResponse(BaseModel):
    """What every profile panel renders from.

    ⚡ **Never partial and never empty.** A person who has never opened the
    screen gets the defaults, so a panel has no *no preferences yet* branch to
    write — and therefore none to get wrong.
    """

    model_config = ConfigDict(frozen=True)

    theme: Theme
    density: Density
    time_format: TimeFormat
    #: ⛔ **`null` means *not chosen*, and the timezone prompt depends on it.**
    #: A default of UTC here would be an answer nobody gave, and the design's
    #: offer could never be shown.
    timezone: str | None
    language: str | None
    pronouns: str | None
    display_name: str | None
    ai_insights: bool
    ai_drafts: bool
    always_show_citations: bool
    answer_style: AnswerStyle
    confidence_floor: int

    #: 🔴 **[TASK-1424] — whether this person has closed the first-run overlay.**
    #: ⛔ **The FACT, not the moment.** The timestamp is stored, and a client
    #: renders on the fact; **a timestamp it does not need is a timestamp it
    #: could display wrongly.**
    first_run_dismissed: bool
    #: 🔴 **[TASK-1424] — whether the invite card is hidden RIGHT NOW.**
    #: ⛔ **The answer, not the moment and not the window.** ⚡ *"Hides them for
    #: 30 days"* is a question about the server's clock, and **a client that
    #: computed it from a timestamp would answer differently on a device whose
    #: clock is wrong.**
    invite_hidden: bool

    @classmethod
    def from_domain(cls, prefs: PersonPreferences, *, now: datetime) -> PreferencesResponse:
        return cls(
            theme=prefs.theme,
            density=prefs.density,
            time_format=prefs.time_format,
            timezone=prefs.timezone,
            language=prefs.language,
            pronouns=prefs.pronouns,
            display_name=prefs.display_name,
            ai_insights=prefs.ai_insights,
            ai_drafts=prefs.ai_drafts,
            always_show_citations=prefs.always_show_citations,
            answer_style=prefs.answer_style,
            confidence_floor=prefs.confidence_floor,
            first_run_dismissed=prefs.first_run_dismissed_at is not None,
            invite_hidden=prefs.invite_is_hidden(now),
        )


class ChangePreferencesRequest(BaseModel):
    """A partial change.

    🔴 **Absent and `null` mean different things, and Pydantic is what keeps
    them apart**: `model_fields_set` records what the request actually carried,
    so *clear my pronouns* and *I am only changing the theme* stay
    distinguishable. ⛔ **Collapsing them would let one panel erase another
    panel's field** simply by not mentioning it.
    """

    model_config = ConfigDict(frozen=True)

    theme: Theme | None = None
    density: Density | None = None
    time_format: TimeFormat | None = None
    timezone: str | None = Field(default=None, max_length=64)
    language: str | None = Field(default=None, max_length=16)
    pronouns: str | None = Field(default=None, max_length=32)
    #: *"Used in mentions and comments. 2–32 characters"* — the design's own
    #: bound, and `min_length` is on the value rather than the field so that
    #: clearing it stays possible.
    display_name: str | None = Field(default=None, min_length=2, max_length=32)
    ai_insights: bool | None = None
    ai_drafts: bool | None = None
    always_show_citations: bool | None = None
    answer_style: AnswerStyle | None = None
    #: ⛔ **Bounded at the edge as well as in the database.** The design's
    #: control offers three values; a floor outside them is one nothing can act
    #: on, and a `422` naming the field beats a row nobody can explain.
    confidence_floor: int | None = Field(
        default=None, ge=MIN_CONFIDENCE_FLOOR, le=MAX_CONFIDENCE_FLOOR
    )


# ── Capability roles (TASK-1479 ⓸, ADR-0410) ────────────────────────────────


class CreateCapabilityRoleRequest(BaseModel):
    name: str = Field(min_length=1, max_length=40)


class RenameCapabilityRoleRequest(BaseModel):
    name: str = Field(min_length=1, max_length=40)


class AssignCapabilityRoleRequest(BaseModel):
    """*Change to Analyst*, and *change back*.

    ⛔ **`role_id: None` is *change back*** and is a deliberate value rather
    than an omission — 📁 which is why this is a `PUT` of the whole assignment
    and not a `PATCH`: there is one field, and *"I did not mention it"* is not
    a state the customer can be in.
    """

    role_id: UUID | None = None


class CapabilityRoleResponse(BaseModel):
    """One capability role.

    ⛔ **No permission list.** 📁 ADR-0410 §2 keeps the grants in `policy.csv`,
    and a copy on this response would be the second authorization model the
    ruling forbids — **stale the moment somebody edits the policy file.**
    """

    role_id: UUID
    name: str
    #: ⚡ **What a *delete* control must ask before offering itself** —
    #: migration `0057` refuses to delete a role people hold.
    holders: int


class CapabilityRoleListResponse(BaseModel):
    """Settings' *Roles & permissions*.

    ⛔ **An empty list is a real answer**, and the ordinary one: a workspace
    that has defined no roles is not a workspace with a broken screen.
    """

    roles: list[CapabilityRoleResponse]


class PermissionResponse(BaseModel):
    resource: str
    action: str


class EffectivePermissionsResponse(BaseModel):
    """*A Member will be able to…*

    📁 **ADR-0410 §3: computed, never stored.** ⚡ **Every entry was asked of
    the same enforcer the request path uses**, so this screen and the
    enforcement point cannot disagree.

    ⚠️ **`role_name` is `None` when the person authorizes as their membership
    role**, including when a role they were assigned no longer resolves — ⛔
    **showing a role they are not effectively holding is the stale claim §3
    forbids, arriving by a different route.**
    """

    user_id: UUID
    role_name: str | None
    permissions: list[PermissionResponse]
