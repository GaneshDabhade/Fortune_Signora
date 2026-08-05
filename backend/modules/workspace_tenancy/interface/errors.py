"""How this module's domain errors surface over HTTP.

Kept here, in the interface layer, because status codes are an HTTP concern:
the domain raises meaning, and this table assigns it a transport
representation. The composition root collects these mappings and registers
them once (19-api-conventions.md).
"""

from fastapi import status

from modules.workspace_tenancy.application.use_cases.accept_invitation import (
    InvitationNotFoundError,
    NotYoursToAcceptError,
    UnverifiedEmailError,
)
from modules.workspace_tenancy.domain.exceptions import (
    DuplicateMembershipError,
    InvalidWorkspaceNameError,
    WorkspaceNotFoundError,
)
from modules.workspace_tenancy.domain.invitation import InvitationNotPendingError
from signora_platform.api import ErrorMapping

ERROR_MAPPING: ErrorMapping = {
    # 404, never 403 — a workspace the caller cannot see must be
    # indistinguishable from one that does not exist, or workspace ids
    # become enumerable (18-authentication.md).
    WorkspaceNotFoundError: (status.HTTP_404_NOT_FOUND, "workspace_not_found"),
    DuplicateMembershipError: (status.HTTP_409_CONFLICT, "membership_already_exists"),
    InvalidWorkspaceNameError: (status.HTTP_422_UNPROCESSABLE_CONTENT, "invalid_workspace_name"),
    # **404, and the same code for both** — an invitation that does not exist
    # and one addressed to somebody else answer identically. Telling them apart
    # would answer *"has this workspace invited this person?"* to somebody who
    # cannot see the workspace, which is a fact about a customer's hiring.
    InvitationNotFoundError: (status.HTTP_404_NOT_FOUND, "invitation_not_found"),
    NotYoursToAcceptError: (status.HTTP_404_NOT_FOUND, "invitation_not_found"),
    # **403, not 404, and it leaks nothing** — unlike the two above, this is
    # the caller's own address and they already know it. Saying so is the only
    # way they can act on it.
    UnverifiedEmailError: (status.HTTP_403_FORBIDDEN, "email_not_verified"),
    # A settled offer, with the aggregate's own sentence: withdrawn, expired
    # and already accepted are different things to say to a person.
    InvitationNotPendingError: (status.HTTP_409_CONFLICT, "invitation_not_pending"),
}
