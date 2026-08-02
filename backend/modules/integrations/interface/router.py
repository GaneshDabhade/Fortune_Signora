"""FastAPI routes for the connections surface."""

from __future__ import annotations

from datetime import UTC, datetime

from fastapi import APIRouter

from apps.api.composition.integrations import IntegrationRead
from modules.integrations.interface.schemas import ConnectionResponse
from signora_platform.api import CurrentWorkspace
from signora_platform.authorization import Action, Resource

router = APIRouter(tags=["integrations"])


@router.get(
    "/workspaces/{workspace_id}/connections",
    response_model=list[ConnectionResponse],
    summary="The systems you have connected",
)
async def list_connections(
    context: CurrentWorkspace,
    queries: IntegrationRead,
) -> list[ConnectionResponse]:
    """*"What have we connected, and is any of it broken?"*

    Every system this organization has connected to Signora, in every state —
    **including the broken ones, which is the point.** A revoked connection is
    the most important row here, and a list that quietly omitted it would leave
    somebody believing their data was still flowing.

    Each row says whether anything needs doing and why. **That is worked out
    when you ask**, from the connection and its credential, so a credential that
    expired overnight reads correctly the next morning without anything having
    run.

    **Not paginated, deliberately.** A customer connects a handful of systems,
    not thousands; a cursor here would be ceremony over a list that fits on one
    screen. If that ever stops being true, it becomes a collection like any
    other ([19-api-conventions.md](../../../../docs/architecture/19-api-conventions.md)).
    """
    context.authorize(Resource.INTEGRATION, Action.READ)
    views = await queries.connections(context.workspace_id, at=datetime.now(UTC))
    return [ConnectionResponse.from_domain(view) for view in views]
