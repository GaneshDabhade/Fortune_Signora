"""Domain-level errors for the Workspace & Tenancy module.

These are raised by domain and application code and are translated to
HTTP problem responses at the interface layer (added in a later feature) —
domain code never knows about HTTP status codes.
"""

from uuid import UUID


class WorkspaceTenancyError(Exception):
    """Base class for every domain error raised by this module."""


class InvalidWorkspaceNameError(WorkspaceTenancyError):
    def __init__(self, name: str) -> None:
        super().__init__(f"Workspace name must be a non-empty string, got: {name!r}")
        self.name = name


class WorkspaceNotFoundError(WorkspaceTenancyError):
    def __init__(self, workspace_id: UUID) -> None:
        super().__init__(f"Workspace {workspace_id} does not exist")
        self.workspace_id = workspace_id


class DuplicateMembershipError(WorkspaceTenancyError):
    def __init__(self, workspace_id: UUID, user_id: UUID) -> None:
        super().__init__(f"User {user_id} is already a member of workspace {workspace_id}")
        self.workspace_id = workspace_id
        self.user_id = user_id


class InvalidSavedViewNameError(WorkspaceTenancyError):
    """The name is the customer's own words, so it has to be some words."""


class EmptyDeclarationError(WorkspaceTenancyError):
    """A saved view records a question, and this one asks nothing.

    ⛔ **The only thing this module may say about a declaration's contents.**
    [D-091](../../../../docs/DECISION_REGISTER.md) puts interpretation outside
    `workspace_tenancy` entirely — so this reports *that it is absent*, never
    that it is wrong, and there is deliberately no `InvalidDeclarationError`
    beside it.
    """


class SavedViewNotFoundError(WorkspaceTenancyError):
    """No such view in this workspace — **and the two are one answer.**

    ⛔ **Deliberately not split into *absent* and *another workspace's*.** Under
    RLS a view outside the caller's workspace reads as absent, and an error
    that could tell them apart would confirm the id exists somewhere — the
    enumeration `WorkspaceNotFoundError` refuses for the same reason.
    """

    def __init__(self, saved_view_id: UUID) -> None:
        super().__init__(f"Saved view {saved_view_id} does not exist")
        self.saved_view_id = saved_view_id


class SavedViewAlreadyRetiredError(WorkspaceTenancyError):
    """Retired once, and the first timestamp is the one that happened."""

    def __init__(self, saved_view_id: UUID) -> None:
        super().__init__(f"Saved view {saved_view_id} is already retired")
        self.saved_view_id = saved_view_id
