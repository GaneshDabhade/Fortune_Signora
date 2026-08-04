"""How Integrations' domain refusals reach a caller.

**Domain and application layers never know an HTTP status** (§7); the mapping
lives here and is registered centrally, so the use cases stay callable from a
worker that has no notion of a response code.

Missing until the first test to call the disconnect route with a connection id
from another organization: `ConnectionNotFound` was raised correctly and then
escaped as an unhandled `500`, which tells a caller the platform broke when in
fact it refused them. Found by [B-024](../../../../docs/BUGS.md)'s coverage
work rather than by reading the router.
"""

from __future__ import annotations

from fastapi import status

from modules.integrations.application.connect import AlreadyConnected, UnknownIntegration
from modules.integrations.application.disconnect import ConnectionNotFound
from signora_platform.api import ErrorMapping

ERROR_MAPPING: ErrorMapping = {
    # **404, never 403.** A caller who names a connection they cannot see must
    # not learn whether it exists — the same rule that makes a non-member's
    # request for a workspace read as "no such workspace"
    # ([18-authentication.md](../../../../docs/architecture/18-authentication.md)).
    ConnectionNotFound: (status.HTTP_404_NOT_FOUND, "connection_not_found"),
    # 422 rather than 404: the *route* exists and the request is well-formed;
    # what does not exist is a system Signora understands. A caller fixes this
    # by naming a different one, which is a different action from retrying.
    UnknownIntegration: (
        status.HTTP_422_UNPROCESSABLE_CONTENT,
        "unknown_integration",
    ),
    # 409 rather than 422: the request is valid and would have been correct
    # a moment earlier. What a caller does about it is different too — not
    # *fix the request* but *this already exists, and here is the one you
    # meant*, which is the distinction the status codes carry.
    AlreadyConnected: (status.HTTP_409_CONFLICT, "integration_already_connected"),
}
