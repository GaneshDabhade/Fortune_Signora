"""How this module's domain errors surface over HTTP.

Kept here, in the interface layer, because status codes are an HTTP concern:
the domain raises meaning, and this table assigns it a transport
representation. The composition root collects these mappings and registers
them once (19-api-conventions.md).
"""

from fastapi import status

from modules.workspace_tenancy.domain.exceptions import (
    DuplicateMembershipError,
    InvalidWorkspaceNameError,
    WorkspaceNotFoundError,
)
from signora_platform.api import ErrorMapping

ERROR_MAPPING: ErrorMapping = {
    # 404, never 403 — a workspace the caller cannot see must be
    # indistinguishable from one that does not exist, or workspace ids
    # become enumerable (18-authentication.md).
    WorkspaceNotFoundError: (status.HTTP_404_NOT_FOUND, "workspace_not_found"),
    DuplicateMembershipError: (status.HTTP_409_CONFLICT, "membership_already_exists"),
    InvalidWorkspaceNameError: (status.HTTP_422_UNPROCESSABLE_CONTENT, "invalid_workspace_name"),
}
