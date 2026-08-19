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

from pydantic import BaseModel, ConfigDict, Field, field_validator

from modules.workspace_tenancy.application.capability_use_cases import (
    EffectivePermissionsView,
    RoleChangeView,
)
from modules.workspace_tenancy.application.use_cases.organization_history import (
    HistoryEntry,
    HistoryKind,
)
from modules.workspace_tenancy.domain.activation import ActivationStep
from modules.workspace_tenancy.domain.entities import (
    MAX_WORKSPACE_NAME_LENGTH,
    RoleChange,
    MAX_WORKSPACE_SLUG_LENGTH,
    MIN_WORKSPACE_SLUG_LENGTH,
    Membership,
    Workspace,
    WorkspaceRole,
)
from modules.workspace_tenancy.domain.invitation import Invitation, InvitationState
from modules.workspace_tenancy.domain.notification_state import (
    CAP as NOTIFICATION_CAP,
)
from modules.workspace_tenancy.domain.notification_state import UnreadCount
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
from modules.workspace_tenancy.domain.recently_viewed import ViewedKind, ViewedRecord
from modules.workspace_tenancy.domain.preferences import (
    HOME_COMPOSITIONS,
    MAX_CARD_ID_LENGTH,
    MAX_LAID_OUT_CARDS,
    HomeCardLayout,
    MAX_CONFIDENCE_FLOOR,
    MIN_CONFIDENCE_FLOOR,
    AnswerStyle,
    Density,
    PersonPreferences,
    ScreenReaderVerbosity,
    TextSize,
    Theme,
    TimeFormat,
)
from modules.workspace_tenancy.domain.saved_view import SavedView
from modules.workspace_tenancy.domain.notification import FeedItem
from signora_platform.pagination import MAX_PAGE_LIMIT


class CreateWorkspaceRequest(BaseModel):
    model_config = ConfigDict(frozen=True)

    name: str = Field(min_length=1, max_length=MAX_WORKSPACE_NAME_LENGTH)
    #: 📁 Screen `03` — *"Workspace URL … Permanent once created."*
    #: ⛔ **Bounds only here; the SHAPE is the domain's.** A regex duplicated in
    #: this layer would be a second definition of what a slug is, and the two
    #: would eventually disagree ([§2](../../../../CLAUDE.md)).
    slug: str = Field(min_length=MIN_WORKSPACE_SLUG_LENGTH, max_length=MAX_WORKSPACE_SLUG_LENGTH)


class SlugAvailabilityResponse(BaseModel):
    """📁 Screen `03`'s *Available* marker.

    ⚡ **Three states in two fields** — available · taken · malformed — because
    a screen given one boolean would have to say *"taken"* about text that is
    not a slug at all.
    """

    model_config = ConfigDict(frozen=True)

    slug: str
    available: bool
    reason: str | None


class AddMemberRequest(BaseModel):
    model_config = ConfigDict(frozen=True)

    user_id: UUID
    role: WorkspaceRole


class WorkspaceResponse(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: UUID
    name: str
    slug: str
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_domain(cls, workspace: Workspace) -> WorkspaceResponse:
        return cls(
            id=workspace.id,
            name=workspace.name,
            slug=workspace.slug,
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


class HomeCardLayoutPayload(BaseModel):
    """One composition's arrangement, over the wire.

    🔴 **Home §10's *Customise* drawer**, and `U-05`'s interim: *"reorder and
    remove only."*

    ⛔ **Card ids are bounded, never enumerated.** 📁 Home is the composition
    authority and its registry is the frontend's — **a catalogue here would be a
    second copy that rejects every card Signora ships after it**
    ([§2](../../../../CLAUDE.md)). ✅ **What this validates is shape and size**,
    which is the boundary's own job.
    """

    model_config = ConfigDict(frozen=True)

    #: Every card this person arranged, in the order they left it.
    order: list[str] = Field(default_factory=list, max_length=MAX_LAID_OUT_CARDS)
    #: The subset they removed. ⛔ **Still present in `order`**, so restoring one
    #: puts it back where it was rather than at the end.
    hidden: list[str] = Field(default_factory=list, max_length=MAX_LAID_OUT_CARDS)

    @field_validator("order", "hidden")
    @classmethod
    def _card_ids_are_slugs(cls, value: list[str]) -> list[str]:
        """⛔ **Bounded so a client cannot store prose in a preference.**"""
        for card in value:
            if not card or len(card) > MAX_CARD_ID_LENGTH:
                raise ValueError(f"a card id must be 1–{MAX_CARD_ID_LENGTH} characters")
        return value

    def to_domain(self) -> HomeCardLayout:
        return HomeCardLayout(order=tuple(self.order), hidden=tuple(self.hidden))


class WorkspaceEntryResponse(BaseModel):
    """What entering a workspace tells the caller about the entry itself.

    🔴 **Home hierarchy 2 and state 13.** 📁 Entry rule 12's confirmation strip is
    *"dismissible, never blocking, and **gone on the second visit that day**"*, and
    Home's state 13 renders *"identical to state 06 with the workspace confirmation
    strip suppressed — **Home does not congratulate people for returning**."*

    ⛔ **One field, and it is an answer rather than a moment.** ⚡ *"The same
    calendar day"* is a question about a zone and a clock the server owns; a
    client computing it from `last_entered_at` would answer differently on a device
    whose clock or timezone is wrong — the same reasoning `invite_hidden` records.
    """

    model_config = ConfigDict(frozen=True)

    #: 📁 `True` on the first entry of this person's day in this workspace.
    #: ⛔ **Read before the entry was recorded**, which is the only order in which
    #: the question has a useful answer.
    first_entry_today: bool
    #: 🔴 **Authenticated Entry rule 22** — *"the new workspace becomes active,
    #: with a **welcome strip**"*, and the strip *"replaces the confirmation
    #: strip"*. ⚡ **`True` on somebody's very first arrival here**, which is what
    #: tells the two strips apart.
    first_entry_ever: bool = False
    #: 🔴 **Authenticated Entry rule 21** — *"Home, with a notice naming what
    #: changed and by whom. The composition may differ from yesterday and **that
    #: must not be silent**."*
    #: ⛔ **`None` when nothing changed since this person was last here**, which
    #: is every ordinary arrival.
    role_change: RoleChangePayload | None = None


class RoleChangePayload(BaseModel):
    """What somebody's role became, and who changed it — Entry rule 21.

    ⚠️ **`changed_by_email` rather than a name.** 📁 ADR-0026 puts identity in
    Better Auth, in the Next.js tier, so **the Python API has no name to give** —
    the same absence `MembershipResponse.member_email` already carries, and
    `None` for a membership added by identifier.
    """

    model_config = ConfigDict(frozen=True)

    previous_role: WorkspaceRole
    new_role: WorkspaceRole
    changed_by: UUID
    changed_by_email: str | None
    at: datetime

    @classmethod
    def of(cls, change: RoleChange) -> RoleChangePayload:
        return cls(
            previous_role=change.previous_role,
            new_role=change.new_role,
            changed_by=change.changed_by,
            changed_by_email=change.changed_by_email,
            at=change.at,
        )


class ViewerRoleResponse(BaseModel):
    """The signed-in person's own standing in this workspace.

    🔴 **[B-284](../../../../docs/BUGS.md).** The shell used to answer *"what am
    I here?"* by fetching the member list and searching it — and the list is a
    **page**. `DEFAULT_PAGE_LIMIT` is 50 and the ordering is newest-first, so
    the 51st-oldest member fell off the end and their own role resolved to
    *"not a member"*. **An owner was shown a locked Settings.**

    **Deliberately not `MembershipResponse`.** That type answers *"who is in
    this workspace?"* and carries the membership row's id, its creation date
    and the member's email address — 📁 facts the members list already
    publishes to somebody entitled to read it. **This answers a different
    question, for the person who is the subject of it**, and the smallest
    honest answer is the role itself.
    """

    model_config = ConfigDict(frozen=True)

    workspace_id: UUID
    user_id: UUID
    role: WorkspaceRole


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
    #: 📁 **The other half of screen `06`'s sentence** — *"and leave Marketing
    #: attribution off"*. ⛔ **Derived server-side for the same reason
    #: `features` is**: a client computing the complement would need its own
    #: copy of the goal table to know what the universe is.
    features_off: list[str]
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
            features_off=list(run.features_off),
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
    #: 📁 **Home's rule 2.** `None` means *not set* — the resolver then falls
    #: through to the role rules.
    home_composition: str | None
    date_format: str | None
    number_format: str | None
    week_starts_on: str | None
    reduce_motion: bool
    increase_contrast: bool
    always_show_focus_ring: bool
    underline_links: bool
    text_size: TextSize
    screen_reader_verbosity: ScreenReaderVerbosity

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
    #: 🔴 **Home state 04 — whether this person has already been told setup
    #: finished.** ⛔ **The fact, not the moment**, matching `first_run_dismissed`
    #: above: a client renders on *has this been shown*, and a timestamp it does
    #: not need is a timestamp it could display wrongly.
    setup_complete_seen: bool
    #: 🔴 **Home §10's *Customise* arrangement, per composition** — 📁 `3.2.3`'s
    #: *"card order within a composition is stable across visits."*
    #: ⛔ **An absent key is *never customised***, which renders the registry's own
    #: order — not the same as *customised to nothing*, which would render an
    #: empty Home.
    home_layout: dict[str, HomeCardLayoutPayload]

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
            home_composition=prefs.home_composition,
            date_format=prefs.date_format,
            number_format=prefs.number_format,
            week_starts_on=prefs.week_starts_on,
            reduce_motion=prefs.reduce_motion,
            increase_contrast=prefs.increase_contrast,
            always_show_focus_ring=prefs.always_show_focus_ring,
            underline_links=prefs.underline_links,
            text_size=prefs.text_size,
            screen_reader_verbosity=prefs.screen_reader_verbosity,
            first_run_dismissed=prefs.first_run_dismissed_at is not None,
            invite_hidden=prefs.invite_is_hidden(now),
            setup_complete_seen=prefs.setup_complete_seen_at is not None,
            home_layout={
                name: HomeCardLayoutPayload(order=list(layout.order), hidden=list(layout.hidden))
                for name, layout in prefs.home_layout.items()
            },
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
    #: 📁 **Home's rule 2** — a start-page composition. ⛔ **Validated against
    #: the design's closed four**, so a client cannot store a composition Home
    #: has no way to render.
    home_composition: str | None = Field(default=None, max_length=32)

    @field_validator("home_composition")
    @classmethod
    def _a_composition_home_can_render(cls, value: str | None) -> str | None:
        """⛔ **Refused rather than ignored.** A stored composition Home does not
        know would fall through to the role rules silently, and the person would
        keep setting a preference that never took effect."""
        if value is not None and value not in HOME_COMPOSITIONS:
            raise ValueError(f"home_composition must be one of {sorted(HOME_COMPOSITIONS)}")
        return value

    #: 📁 **Language & region.** ⛔ **No enum**: the design shows one value each
    #: and lists no options, so constraining them here would decide which
    #: formats Signora supports — a product question, not a schema one.
    date_format: str | None = Field(default=None, max_length=120)
    number_format: str | None = Field(default=None, max_length=120)
    week_starts_on: str | None = Field(default=None, max_length=120)
    #: 📁 **Accessibility.** ⚡ `reduce_motion` is the OVERRIDE — the device's
    #: own `prefers-reduced-motion` already drives the shell and is not stored.
    reduce_motion: bool | None = None
    increase_contrast: bool | None = None
    always_show_focus_ring: bool | None = None
    underline_links: bool | None = None
    text_size: TextSize | None = None
    screen_reader_verbosity: ScreenReaderVerbosity | None = None


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


class HeldCapabilityRolesResponse(BaseModel):
    """Who holds which role, for the whole roster, in one answer.

    ⛔ **Somebody who holds none is ABSENT rather than mapped to `null`.** ⚡
    The request named a workspace and the answer covers everybody in it who has
    one — **so *"we looked and they hold nothing"* needs no key**, the same
    shape `account_tag` assignments use one module over.

    ⚠️ **Keys are user ids as strings**, because JSON has no other kind.
    """

    assignments: dict[str, str]


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

    @classmethod
    def from_domain(
        cls, view: EffectivePermissionsView, *, user_id: UUID
    ) -> EffectivePermissionsResponse:
        return cls(
            user_id=user_id,
            role_name=view.role_name,
            permissions=[
                PermissionResponse(resource=p.resource, action=p.action)
                for p in view.permissions
            ],
        )


class RoleChangePreviewResponse(BaseModel):
    """*Change role — Member → Analyst*, before anybody commits to it.

    📁 **The design: *"Both directions are shown, because a role change is a
    trade rather than a promotion."*** ⚡ **Two resolved answers**, each asked of
    the enforcer that decides the request path.

    ⛔ **No `gains`/`loses` fields.** They are the set difference of these two
    lists, and a third representation of one fact is the duplication §2 forbids
    — **the screen derives them, once.**
    """

    user_id: UUID
    current: EffectivePermissionsResponse
    proposed: EffectivePermissionsResponse

    @classmethod
    def from_domain(cls, view: RoleChangeView, *, user_id: UUID) -> RoleChangePreviewResponse:
        return cls(
            user_id=user_id,
            current=EffectivePermissionsResponse.from_domain(view.current, user_id=user_id),
            proposed=EffectivePermissionsResponse.from_domain(view.proposed, user_id=user_id),
        )


class UnreadBadgeResponse(BaseModel):
    """The shell's notification badge — **[TASK-480](../../../../docs/BACKLOG.md)**.

    ⚡ **Two fields rather than one number**, because the shell renders `9+`.
    ⛔ **Returning a bare `int` would push *is this capped* to the caller**, and
    the first one to compare against `9` itself has written the cap down twice
    ([§2](../../../../CLAUDE.md), *behaviour exists exactly once*).
    """

    model_config = ConfigDict(frozen=True)

    unread: int = Field(
        description="How many of the notifications you asked about this person has "
        "not read. Never above `cap`."
    )
    capped: bool = Field(
        description="True when the real number is at least `cap`, so the badge reads "
        "`9+` rather than a figure. Read this rather than comparing `unread` to `cap`."
    )
    cap: int = Field(
        description="The ceiling the count stops at. Published so a client never "
        "hard-codes it — the query is bounded by this, so counting past it is not "
        "something the server declined to do, it is something it never did."
    )

    @classmethod
    def from_domain(cls, badge: UnreadCount) -> UnreadBadgeResponse:
        return cls(unread=badge.value, capped=badge.capped, cap=NOTIFICATION_CAP)


class MarkNotificationsReadRequest(BaseModel):
    """**Which notifications this person has read.**

    ⛔ **No `user_id` field, and its absence is the guarantee.** ⚡ **The person
    is the caller's own verified id** — 📁 the same rule `PreferencesResponse`
    records: *"there is no parameter that could ask for another's."*
    """

    model_config = ConfigDict(frozen=True)

    notification_ids: list[UUID] = Field(
        min_length=1,
        max_length=MAX_PAGE_LIMIT,
        description="The notifications now read. Bounded by a page, because the "
        "realistic use is 'mark what I am looking at' and a larger request is "
        "either a mistake or a scrape.",
    )


class NotificationResponse(BaseModel):
    """One item in the panel — **[TASK-495](../../../../docs/BACKLOG.md)**.

    ## 🔴 No actor name, and that is [C-203](../../../../docs/LANE_COORDINATION.md)

    ⛔ **`actor_person_id` is an identity and there is no `actor_name` beside
    it.** 📁 **C-203 is `DEFERRED` with a concrete trigger** — *"Nothing in the product can
    render a person's name"* — **and its impact line names notifications.** ⚡
    **Better Auth is the sole Authentication Authority and the Python tier only
    verifies** ([ADR-0026](../../../../docs/architecture/adr/0026-jwt-boundary-architecture.md)),
    **so this tier has no name to return.**

    ⚠️ **A field here would have answered C-203 by accident, for Timeline,
    comments, audit history, AI attribution and mentions at the same time** — 📁
    37 says exactly that about the Team page, and this is the same shortcut one
    surface along.

    ✅ **`actor_agent_name` IS returned**, because an agent has no Better Auth
    identity to resolve: the platform authored the name.

    ## ⛔ And no subject title

    ⚡ **Identity only** — 📁 *events carry identity; ports carry payload*. **A
    cached account name would render one that changed last week**, and the
    surface already holds the account.
    """

    model_config = ConfigDict(frozen=True)

    id: UUID
    category: str = Field(
        description="Which tab this belongs to: `needs_you` or `mention`. There is "
        "deliberately no `all` — `All` is the absence of a filter, never a third kind."
    )
    actor_kind: str = Field(
        description="`person` or `agent`. Carries the design's intelligence hue as a "
        "fact rather than a styling hint, so a generated nudge never reads as a "
        "colleague's request."
    )
    actor_person_id: UUID | None = Field(
        description="Who acted, when a person did. An identity, never a name — see C-203."
    )
    actor_agent_name: str | None = Field(
        description="What acted, when an agent did. A capability's name — never a model "
        "or a vendor."
    )
    subject_kind: str
    subject_id: UUID
    summary: str = Field(description="What happened, in the customer's vocabulary.")
    expectation: str = Field(
        description="What is expected of the reader. Not a button label — the design "
        "asks every item to say what it wants."
    )
    occurred_at: datetime = Field(
        description="When it happened. Always timezone-aware: the panel groups by day, "
        "and a naive moment is the one item that could land under the wrong one."
    )
    read_at: datetime | None = Field(
        default=None,
        description=(
            "When this person read it, or null if they have not. The panel draws "
            "its unread mark from this rather than from the badge count, which "
            "says how many without saying which."
        ),
    )

    @classmethod
    def from_domain(cls, item: FeedItem) -> "NotificationResponse":
        return cls(
            read_at=item.read_at,
            id=item.notification.id,
            category=item.notification.category.value,
            actor_kind=item.notification.actor.kind.value,
            actor_person_id=item.notification.actor.person_id,
            actor_agent_name=item.notification.actor.agent_name,
            subject_kind=item.notification.subject.kind,
            subject_id=item.notification.subject.id,
            summary=item.notification.summary,
            expectation=item.notification.expectation,
            occurred_at=item.notification.occurred_at,
        )


class NotificationFeedResponse(BaseModel):
    """The panel's page — **newest first, bounded.**

    ⚡ **A plain list rather than a cursor page**, deliberately: 📁 the design is
    *"a 400px popover, not a page"*, and 19's cursor pagination exists for
    collections a customer scrolls. ⛔ **A popover that paginated would be the
    *Notification Center* screen**, which is Workflow 17's own decomposition and
    explicitly not this row's.
    """

    model_config = ConfigDict(frozen=True)

    notifications: list[NotificationResponse]


class RecordViewRequest(BaseModel):
    """*"I opened this record."*

    📁 **Session Continuity tier 4.** ⛔ **The person is NOT in the body** — it
    is the verified caller, exactly as `workspace_id` is the path's. A body that
    could name a person would be a route to writing into somebody else's
    reading history (§7).
    """

    model_config = ConfigDict(frozen=True)

    entity_id: UUID = Field(description="The record that was opened.")
    kind: ViewedKind = Field(
        description=(
            "What sort of record. Bounded by the enum at the edge and by a check "
            "constraint in the table — a kind nothing can open is a row the card "
            "would render with nowhere to go."
        )
    )


class ViewedRecordResponse(BaseModel):
    """One record this person opened, newest first.

    ⛔ **Carries no title.** 📁 An account's name is the Knowledge Graph's to
    state and moves without this module hearing about it; **storing or
    returning it here would be a second representation of a fact that changes**
    ([§2](../../../../CLAUDE.md)). ✅ **Home resolves names through the identity
    surface**, exactly as its attention card already does.
    """

    model_config = ConfigDict(frozen=True)

    entity_id: UUID
    kind: ViewedKind
    viewed_at: datetime

    @classmethod
    def from_domain(cls, record: ViewedRecord) -> "ViewedRecordResponse":
        return cls(
            entity_id=record.entity_id, kind=record.kind, viewed_at=record.viewed_at
        )


class ActivationStepResponse(BaseModel):
    """One step this module asks a new workspace to take.

    **The same three fields the connections surface publishes**, deliberately:
    a client composes several modules' steps into one ordered list, and it can
    only do that if every module answers the question the same way. 📁 §7 —
    *"do not invent a new response envelope per module."*
    """

    model_config = ConfigDict(frozen=True)

    id: str = Field(
        description=(
            "Stable, and the identifier a client keys its own presentation "
            "from."
        )
    )
    priority: int = Field(
        description=(
            "Lower is earlier. Clients order by this integer rather than by "
            "array position."
        )
    )
    blocking: bool = Field(
        description=(
            "Whether Signora can conclude anything without it. A non-blocking "
            "step makes conclusions weaker rather than impossible."
        )
    )

    @classmethod
    def from_domain(cls, step: ActivationStep) -> ActivationStepResponse:
        return cls(id=step.id, priority=step.priority, blocking=step.blocking)
