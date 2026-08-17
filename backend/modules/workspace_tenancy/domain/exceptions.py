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


class InvalidWorkspaceSlugError(WorkspaceTenancyError):
    """📁 Screen `03`'s URL field refused.

    ⚠️ **One error for every reason** — too short, wrong characters, reserved.
    ⛔ **The screen tells somebody what a valid slug looks like rather than
    which rule they broke**: three separate messages would teach the rules one
    failure at a time, and the field is two words long.
    """

    def __init__(self, slug: str) -> None:
        super().__init__(
            f"A workspace URL is 3–63 characters of lowercase letters, "
            f"numbers and hyphens, got: {slug!r}"
        )
        self.slug = slug


class WorkspaceSlugTakenError(WorkspaceTenancyError):
    """⚡ **Somebody else has it.** ⛔ Distinct from `InvalidWorkspaceSlugError`
    because the answers differ: one is *fix the text*, the other is *that text
    is fine and gone*. 📁 The design writes the second one out — *"That URL was
    taken while you were typing. Your other answers are saved."*"""

    def __init__(self, slug: str) -> None:
        super().__init__(f"The workspace URL {slug!r} is already taken")
        self.slug = slug


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


class OnboardingRunNotFoundError(WorkspaceTenancyError):
    """Nobody has started onboarding here.

    ⛔ **Distinct from a run that was skipped**, which exists and is
    resumable — the design's banner offers to continue something, and offering
    to continue nothing is how a first-run experience reappears forever.
    """


class OnboardingRunAlreadyFinishedError(WorkspaceTenancyError):
    """The run completed, so this is a settings change wearing onboarding's hat.

    ⚡ **Onboarding answers become settings the moment the run ends**, and the
    Settings screens own them from there. Editing through this path afterwards
    would give one fact two write paths ([§2](../../../../CLAUDE.md)).
    """


class TeamSizeOutOfRangeError(WorkspaceTenancyError):
    """Outside 1–10,000, refused rather than clamped.

    ⚠️ **Zero is the case worth naming.** The design answers it with copy —
    *"Zero explains that they count"* — and a clamp to `1` would answer the
    person by overwriting what they typed.
    """


class TooManyGoalsError(WorkspaceTenancyError):
    """More than three outcomes.

    ⛔ **The screen disables the fourth and this refuses it**, deliberately
    both: *"The fourth selection is disabled, not silently ignored."* A limit
    kept only in the client is a limit a request body does not have.
    """
