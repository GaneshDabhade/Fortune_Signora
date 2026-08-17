"""Application-layer ports (Python Protocols) that this module's use cases
depend on. Infrastructure implements these; domain and application code
never import SQLAlchemy, FastAPI, or any other infrastructure type directly
— that is what keeps this module's business logic testable with fakes and
free of framework coupling (docs/architecture/15-project-structure.md).
"""

from collections.abc import Sequence
from datetime import datetime
from typing import Any, Protocol
from uuid import UUID

from modules.workspace_tenancy.domain.entities import Membership, Workspace, WorkspaceRole
from modules.workspace_tenancy.domain.invitation import Invitation
from modules.workspace_tenancy.domain.onboarding import OnboardingRun
from modules.workspace_tenancy.domain.preferences import PersonPreferences
from modules.workspace_tenancy.domain.saved_view import SavedView
from signora_platform.pagination import CursorPosition


class WorkspaceRepository(Protocol):
    async def add(self, workspace: Workspace) -> None: ...
    async def get(self, workspace_id: UUID) -> Workspace | None: ...

    async def slug_is_taken(self, slug: str) -> bool:
        """Whether any workspace already holds this URL.

        ⛔ **Deliberately a boolean and not the workspace.** 📁 Screen `03`
        asks *"is this available?"* before anybody is a member of anything, so
        returning the row would hand an unauthenticated-for-that-tenant caller
        a workspace's name — **an enumeration oracle in exchange for nothing
        the screen needs.**

        ⚠️ **This read crosses RLS by design and is the reason it lives here
        rather than being expressed as a `get`**: uniqueness is a property of
        the whole table, and no member of one workspace may see another's row.
        **The implementation restricts itself to one column and one boolean.**
        """
        ...

    async def list_visible(self, *, limit: int, after: CursorPosition | None) -> list[Workspace]:
        """Workspaces the *current session's user* may see, newest first.

        There is no ``user_id`` parameter because there is no ``user_id``
        column to filter on: the ``workspace`` table's RLS policy already
        restricts visibility to workspaces the caller is a member of, using
        ``app.user_id``. Passing a user id would imply the caller could ask
        about someone else, which they cannot.

        Returns up to ``limit`` rows; callers over-fetch by one to determine
        ``has_more`` (see ``signora_platform.api.pagination``).
        """
        ...


class MembershipRepository(Protocol):
    async def add(self, membership: Membership) -> None: ...
    async def get(self, workspace_id: UUID, user_id: UUID) -> Membership | None: ...
    async def get_by_id(self, workspace_id: UUID, membership_id: UUID) -> Membership | None: ...
    async def lock_membership_set(self, workspace_id: UUID) -> None: ...
    async def count_live_owners(self, workspace_id: UUID) -> int: ...
    async def save_role(self, membership: Membership) -> None: ...
    async def end(self, membership: Membership) -> None: ...
    async def list_page_for_workspace(
        self, workspace_id: UUID, *, limit: int, after: CursorPosition | None
    ) -> list[Membership]: ...


class TenantContext(Protocol):
    """Activates RLS workspace scope mid-transaction. Abstracts over the
    concrete ``SET LOCAL``/``set_config`` mechanism in ``signora_platform/db`` so
    the application layer never imports SQLAlchemy directly. Needed because
    workspace creation runs before a workspace_id exists to scope to — see
    the bootstrap pattern in docs/architecture/11-tenancy.md.
    """

    async def activate_workspace(self, workspace_id: UUID) -> None: ...


class EventPublisher(Protocol):
    """Module-local publishing port. The session and producer-module name
    are bound into the infrastructure adapter at construction time, so use
    cases only ever deal in domain events and a correlation id — never a
    database session.
    """

    async def publish(self, events: Sequence[Any], *, correlation_id: UUID) -> None: ...


class InvitationRepository(Protocol):
    async def add(self, invitation: Invitation) -> None: ...
    async def get(self, workspace_id: UUID, invitation_id: UUID) -> Invitation | None: ...
    async def find_live(self, workspace_id: UUID, email: str) -> Invitation | None: ...
    async def list_for_workspace(self, workspace_id: UUID) -> list[Invitation]: ...
    async def settle(self, invitation: Invitation) -> None: ...


class RoleChangeLog(Protocol):
    """Append-only record of what somebody was allowed to do, and when it
    changed. **No update method exists**, and that is the enforcement."""

    async def record(
        self,
        *,
        workspace_id: UUID,
        membership_id: UUID,
        previous_role: WorkspaceRole,
        new_role: WorkspaceRole,
        changed_by: UUID,
        at: datetime,
    ) -> None: ...


class InvitationDelivery(Protocol):
    """How an invitation leaves the process.

    **A port with one adapter today, and it is deliberate rather than
    speculative.** `lib/auth/email.ts` made the same call for verification links
    and its reasoning applies unchanged: the *business* workflow — offer,
    revoke, accept — is identical whoever carries the message, and if delivery
    turns out to belong to Notifications (M14a) only the adapter moves.

    **It cannot fail the invitation.** An offer that was recorded and not
    delivered is recoverable by resending; an offer that was refused because a
    mail server was briefly unreachable is a customer repeating themselves for
    no reason.
    """

    async def send(self, invitation: Invitation, *, workspace_name: str) -> None: ...


class SavedViewRepository(Protocol):
    """Persistence for saved views. **Speaks the aggregate, never the view.**

    ⚡ **The public contract's `SavedViewReader`/`SavedViewWriter` speak
    `SavedViewView`, and this one deliberately does not.** A use case handed a
    view would have no way to run `declare`, `revise` or `retire` — the rules
    live on the aggregate, and a port that skipped it would let a caller write
    a nameless view or revive a retired one. **Other modules get the views;
    this module's own use cases get the type that can refuse.**
    """

    async def add(self, view: SavedView) -> None: ...
    async def get(self, workspace_id: UUID, saved_view_id: UUID) -> SavedView | None: ...

    async def list_live_page(
        self, workspace_id: UUID, *, limit: int, after: CursorPosition | None
    ) -> list[SavedView]:
        """Views in force, newest first. **Superseded and retired excluded.**

        ⛔ **Live is derived here, never stored** — a boolean beside the
        supersession chain would be one fact twice, and the two would disagree
        the first time a version landed.
        """
        ...

    async def mark_retired(self, view: SavedView) -> None:
        """Stamp the retirement the aggregate already decided.

        ⛔ **The only write that touches an existing row**, and it sets a
        timestamp that was `NULL`. A declaration is still never edited.
        """
        ...


class OnboardingRunRepository(Protocol):
    """A person's onboarding run — **TASK-469**.

    ⚡ **`save` rather than `add` and `update`.** The design's autosave sends
    the same run repeatedly (*"every step saves on advance and on blur"*), so
    a split would push *"is this the first save?"* into every caller and make
    a lost race look like a duplicate-key error to a person who simply
    clicked Back.
    """

    async def get(self, workspace_id: UUID, person_id: UUID) -> OnboardingRun | None: ...
    async def save(self, run: OnboardingRun) -> None: ...


class PersonPreferencesRepository(Protocol):
    """A person's preferences — **TASK-470**.

    ⚡ **`get` returns preferences, never `None`.** Somebody who has never
    opened the screen has the defaults, and a port that could answer *nothing*
    would push that reasoning into every caller — the first one to forget it
    renders a blank profile to a new account.
    """

    async def get(self, workspace_id: UUID, person_id: UUID) -> PersonPreferences: ...
    async def save(self, preferences: PersonPreferences) -> None: ...
