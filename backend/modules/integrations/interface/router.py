"""FastAPI routes for the connections surface."""

from __future__ import annotations

from datetime import UTC, datetime

from fastapi import APIRouter, status

from uuid import UUID

from apps.api.composition.integrations import (
    IntegrationConnect,
    IntegrationDisconnect,
    IntegrationProbe,
    IntegrationRead,
)
from modules.integrations.interface.schemas import (
    ConnectionResponse,
    ConnectRequest,
    DisconnectResponse,
    SystemResponse,
)
from modules.integrations.application.queries import ConnectionView
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


@router.post(
    "/workspaces/{workspace_id}/connections",
    response_model=ConnectionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Start using one of your own systems",
)
async def connect(
    request: ConnectRequest,
    context: CurrentWorkspace,
    connector: IntegrationConnect,
) -> ConnectionResponse:
    """*"Signora may read this."*

    **The last step of a consent the customer already gave elsewhere.** The
    redirect, the consent screen and the authorization-code exchange happen at
    the frontend edge, where
    [18-authentication.md](../../../../docs/architecture/18-authentication.md)
    puts them; this records the result. **Nothing in the request names OAuth** —
    an API key, a service account or a certificate arrives through the same
    door, which is the property that lets a second mechanism ship without a
    second endpoint.

    **Owner only, the same permission as disconnecting.** Handing an
    organization's CRM to a third party and withdrawing it are the same
    decision seen from two sides, and it is not a decision a single member of
    the team makes for everybody.

    **The credential is stored encrypted and is never returned.** The response
    is the connection a customer reads — no `secret_ref`, no grant id, no
    material. A caller that needs to know whether it worked reads `state`.

    **A slug Signora does not understand is refused with `422`**, not stored.
    A connection nothing can ever act on is a permanent row on a customer's
    screen promising something that will never happen.

    **Connecting the same account twice is refused with `409`, and that is the
    schema's decision rather than a rule invented here.** One HubSpot portal is
    one relationship however many times somebody consents to it, and
    `connected_account` is unique on `(workspace, integration, external
    account)` to say so. **Reconnection — a new grant on the existing
    connection — is not built**, so a customer whose credential expired
    disconnects and connects again. Two steps, both of which work, and neither
    of which pretends to be a refresh.
    """
    context.authorize(Resource.INTEGRATION, Action.UPDATE)
    at = datetime.now(UTC)
    connection = await connector.execute(
        request.to_input(
            workspace_id=context.workspace_id, actor_id=context.principal.user_id
        ),
        at=at,
    )
    # Built from what was just written rather than read back, and through the
    # same factory the connections list uses — so `attention` has one
    # derivation, not two that agree today.
    return ConnectionResponse.from_domain(
        ConnectionView.of(
            connection,
            expires_at=request.expires_at,
            refreshable=request.refreshable,
            at=at,
        )
    )


@router.post(
    "/workspaces/{workspace_id}/connections/{connection_id}/check",
    response_model=ConnectionResponse,
    summary="Check whether a connected system still works",
)
async def check_connection(
    workspace_id: UUID,
    connection_id: UUID,
    context: CurrentWorkspace,
    prober: IntegrationProbe,
    queries: IntegrationRead,
) -> ConnectionResponse:
    """*"It says connected — is it actually working?"*

    Everything else on this screen is worked out from records: a credential
    exists, it has not expired, nobody revoked it. **None of that is evidence.**
    The commonest way an integration breaks is a credential that authenticates
    perfectly and has quietly lost a permission, and no record anywhere can see
    it — which is why this makes a real call and reports what came back.

    **A failed check is an answer, not an error.** This returns `200` with the
    connection reading *not working*; it does not fail the request. A `500`
    would say Signora broke, when what actually happened is that the customer's
    system said no.

    **One bad answer is not a verdict.** A timeout or a rate limit establishes
    nothing, so it takes two consecutive inconclusive checks before a connection
    is reported as not working — a vendor having a bad afternoon must not send
    somebody to reconnect a CRM that is fine.

    **Nothing about the customer's data moves.** No record is read into the
    pipeline, nothing is stored about their companies, and no synchronization
    starts. This asks whether the door opens and closes it again.

    **A `POST` because it does something**: it spends a call against the
    customer's own API quota and writes a record of the result. A `GET` that
    did that would be a `GET` a proxy could repeat.
    """
    context.authorize(Resource.INTEGRATION, Action.UPDATE)
    at = datetime.now(UTC)
    await prober.execute(context.workspace_id, connection_id, at=at)
    # Health is derived from the probe *run*, not from the one that just
    # happened — a connection is degraded only once the run says so.
    # Read back through the same query the list uses. **`execute` already
    # refused an unknown connection**, so the row is here; a fallback branch
    # for its absence would be a guard that cannot fail (§2).
    view = next(
        v
        for v in await queries.connections(context.workspace_id, at=at)
        if v.id == connection_id
    )
    return ConnectionResponse.from_domain(view)
