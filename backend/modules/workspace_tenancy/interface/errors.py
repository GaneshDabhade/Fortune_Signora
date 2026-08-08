"""How this module's domain errors surface over HTTP.

Kept here, in the interface layer, because status codes are an HTTP concern:
the domain raises meaning, and this table assigns it a transport
representation. The composition root collects these mappings and registers
them once (19-api-conventions.md).
"""

from fastapi import status

from modules.workspace_tenancy.application.use_cases.accept_invitation import (
    InvitationNotFoundError,
    UnverifiedEmailError,
)
from modules.workspace_tenancy.application.use_cases.leave_workspace import NotAMemberError
from modules.workspace_tenancy.domain.entities import LastOwnerCannotLeaveError
from modules.workspace_tenancy.domain.exceptions import (
    DuplicateMembershipError,
    EmptyDeclarationError,
    InvalidSavedViewNameError,
    InvalidWorkspaceNameError,
    OnboardingRunAlreadyFinishedError,
    OnboardingRunNotFoundError,
    SavedViewAlreadyRetiredError,
    SavedViewNotFoundError,
    TeamSizeOutOfRangeError,
    TooManyGoalsError,
    WorkspaceNotFoundError,
)
from modules.workspace_tenancy.domain.invitation import InvitationNotPendingError
from signora_platform.api import ErrorMapping

ERROR_MAPPING: ErrorMapping = {
    # 404, never 403 — a workspace the caller cannot see must be
    # indistinguishable from one that does not exist, or workspace ids
    # become enumerable (18-authentication.md).
    WorkspaceNotFoundError: (status.HTTP_404_NOT_FOUND, "workspace_not_found"),
    SavedViewNotFoundError: (status.HTTP_404_NOT_FOUND, "saved_view_not_found"),
    InvalidSavedViewNameError: (status.HTTP_422_UNPROCESSABLE_CONTENT, "invalid_saved_view_name"),
    # **422 rather than 400**: the request is well-formed and the declaration
    # is empty, which is a semantic refusal. ⛔ It is the *only* thing this
    # module may say about a declaration's contents (D-091).
    EmptyDeclarationError: (status.HTTP_422_UNPROCESSABLE_CONTENT, "empty_declaration"),
    SavedViewAlreadyRetiredError: (status.HTTP_409_CONFLICT, "saved_view_already_retired"),
    # **404 rather than an invented empty run.** A run nobody started is
    # genuinely absent, and answering with a blank one would make the resume
    # banner permanent — there would be no state in which nobody had begun.
    OnboardingRunNotFoundError: (status.HTTP_404_NOT_FOUND, "onboarding_run_not_found"),
    # **409, because the request is well-formed and the state refuses it.**
    # Onboarding answers become settings the moment the run ends, and the
    # Settings screens own them from there.
    OnboardingRunAlreadyFinishedError: (
        status.HTTP_409_CONFLICT,
        "onboarding_run_already_finished",
    ),
    # ⚠️ **422 and not a clamp.** Somebody typing `0` is telling the product
    # something; answering `1` would overwrite them silently.
    TeamSizeOutOfRangeError: (status.HTTP_422_UNPROCESSABLE_CONTENT, "team_size_out_of_range"),
    # ⛔ *"The fourth selection is disabled, not silently ignored."*
    TooManyGoalsError: (status.HTTP_422_UNPROCESSABLE_CONTENT, "too_many_goals"),
    DuplicateMembershipError: (status.HTTP_409_CONFLICT, "membership_already_exists"),
    InvalidWorkspaceNameError: (status.HTTP_422_UNPROCESSABLE_CONTENT, "invalid_workspace_name"),
    # **404, covering never invited, already accepted and withdrawn alike.**
    # Telling them apart would answer *"has this workspace invited this
    # person?"* to anybody who can sign in, which is a fact about a customer's
    # hiring. Expiry is the deliberate exception below — it is the one refusal
    # that tells somebody what to do next.
    InvitationNotFoundError: (status.HTTP_404_NOT_FOUND, "invitation_not_found"),
    # **403, not 404, and it leaks nothing** — unlike the two above, this is
    # the caller's own address and they already know it. Saying so is the only
    # way they can act on it.
    UnverifiedEmailError: (status.HTTP_403_FORBIDDEN, "email_not_verified"),
    # A settled offer, with the aggregate's own sentence: withdrawn, expired
    # and already accepted are different things to say to a person.
    InvitationNotPendingError: (status.HTTP_409_CONFLICT, "invitation_not_pending"),
    # **409, and the mapping is the point of the row that added it.** The
    # domain has raised this since M1 — from `end`, from `change_role`, and now
    # from leaving — and it was mapped nowhere, so the platform's fail-closed
    # handler turned *"Make somebody else an owner first"* into **500 "An
    # unexpected error occurred."** A refusal a customer can act on, delivered
    # as a fault they cannot.
    #
    # **A conflict with the workspace's state rather than a bad request**: the
    # request is well-formed and would be correct the moment a second owner
    # exists, which is exactly what 409 means and what the sentence tells them
    # to go and do.
    LastOwnerCannotLeaveError: (status.HTTP_409_CONFLICT, "last_owner_cannot_leave"),
    # **404, consistent with every other *"you cannot see this"* in this
    # module.** Reachable when a second tab has already left, or an
    # administrator removed the caller mid-request.
    NotAMemberError: (status.HTTP_404_NOT_FOUND, "not_a_member"),
}
