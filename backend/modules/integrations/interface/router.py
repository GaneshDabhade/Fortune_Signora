"""FastAPI routes for the connections surface."""

from __future__ import annotations

from datetime import UTC, datetime

from fastapi import APIRouter

from uuid import UUID

from apps.api.composition.integrations import IntegrationDisconnect, IntegrationRead
from modules.integrations.interface.schemas import (
    ConnectionResponse,
    DisconnectResponse,
    SystemResponse,
)
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


@router.get(
    "/workspaces/{workspace_id}/integrations",
    response_model=list[SystemResponse],
    summary="What Signora can connect to, and what you have connected",
)
async def list_systems(
    context: CurrentWorkspace,
    queries: IntegrationRead,
) -> list[SystemResponse]:
    """*"Can I trust that Signora is connected to the systems that run my
    business, and if not, what do I need to do?"*

    Every system Signora understands — **including the ones you have not
    connected**, because a screen built only from what somebody already did
    cannot answer *"what are we missing?"*

    Each row says what connecting it gives you, whether it is working now, and
    whether anything needs doing. **`working` is not the same as having a
    connection**: a connection whose permission was withdrawn is still a
    connection, and answering *"is my CRM connected?"* with *yes* would be the
    worst thing this screen could say.

    **Capabilities listed are only ones Signora can act on today.** Anything
    waiting on work that does not exist is absent rather than shown greyed out
    — advertising a capability the platform cannot execute is a promise the
    product cannot keep.
    """
    context.authorize(Resource.INTEGRATION, Action.READ)
    systems = await queries.systems(context.workspace_id, at=datetime.now(UTC))
    return [SystemResponse.from_domain(system) for system in systems]


@router.post(
    "/workspaces/{workspace_id}/connections/{connection_id}/disconnect",
    response_model=DisconnectResponse,
    summary="Stop using a connected system",
)
async def disconnect(
    connection_id: UUID,
    context: CurrentWorkspace,
    disconnector: IntegrationDisconnect,
) -> DisconnectResponse:
    """*"Stop reading from this."*

    **Always succeeds locally, even when the other system is unreachable.**
    Withdrawing access is exactly what somebody does in a hurry, and a
    disconnect that failed because the vendor was down would hold a security
    action hostage to the system it protects them from.

    The credential is destroyed rather than forgotten — after this, Signora has
    nothing left to read with.

    **Idempotent.** Disconnecting something already disconnected is a customer
    clicking twice, and it changes nothing.
    """
    context.authorize(Resource.INTEGRATION, Action.UPDATE)
    result = await disconnector.execute(
        context.workspace_id,
        connection_id,
        at=datetime.now(UTC),
        actor_id=context.principal.user_id,
    )
    return DisconnectResponse.from_domain(result)
