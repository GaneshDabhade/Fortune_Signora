"""FastAPI routes for the product catalog.

Handlers translate, authorize, delegate. Authentication, membership
verification and RLS context are established by the dependency chain before a
handler runs.

**The first endpoint in Signora that stores something a customer wrote.**
Every other write records a *decision about* the pipeline's output; this one
records the input the pipeline has never had.
"""

from uuid import UUID

from fastapi import APIRouter, status

from apps.api.composition.products import (
    CatalogRead,
    CatalogWrite,
    CommitteeRead,
    CommitteeWrite,
    FocusRead,
    FocusWrite,
    IcpRead,
    IcpWrite,
    SegmentRead,
    TargetAccountsRead,
    TargetAccountsWrite,
)
from modules.commercial_profile.application.declare_committee import (
    DeclareBuyingCommitteeInput,
)
from modules.commercial_profile.application.declare_focus import DeclareFocusInput
from modules.commercial_profile.application.declare_icp import DeclareIcpInput
from modules.commercial_profile.application.declare_target_accounts import (
    DeclareTargetAccountsInput,
)
from modules.commercial_profile.application.publish import PublishProductCatalogInput
from modules.commercial_profile.interface.schemas import (
    BuyingCommitteeResponse,
    CommercialFocusResponse,
    DeclareBuyingCommitteeRequest,
    DeclareFocusRequest,
    DeclareIcpRequest,
    DeclareTargetAccountsRequest,
    IcpDeclarationResponse,
    ProductCatalogResponse,
    PublishProductCatalogRequest,
    SegmentSummaryResponse,
    TargetAccountListResponse,
)
from signora_platform.api import CurrentWorkspace
from signora_platform.api.responses import CursorPage
from signora_platform.authorization import Action, Resource
from signora_platform.pagination import (
    DEFAULT_PAGE_LIMIT,
    MAX_PAGE_LIMIT,
    decode_cursor,
    encode_cursor,
)

router = APIRouter(tags=["commercial profile"])


@router.get(
    "/workspaces/{workspace_id}/products",
    response_model=ProductCatalogResponse,
    summary="What this workspace sells",
)
async def product_catalog(
    context: CurrentWorkspace, catalogs: CatalogRead
) -> ProductCatalogResponse:
    """The catalog in force.

    **Never a 404.** A workspace that has declared nothing gets version 0 and
    an empty list, which is the state every workspace starts in — answering
    with an absence would make the ordinary case look like a fault, and force
    a branch on every caller.
    """
    context.authorize(Resource.PRODUCT, Action.READ)
    catalog = await catalogs.current(context.workspace_id)
    return (
        ProductCatalogResponse.empty()
        if catalog is None
        else ProductCatalogResponse.from_domain(catalog)
    )


@router.put(
    "/workspaces/{workspace_id}/products",
    response_model=ProductCatalogResponse,
    status_code=status.HTTP_200_OK,
    summary="Declare what this workspace sells",
)
async def publish_product_catalog(
    context: CurrentWorkspace,
    publish: CatalogWrite,
    body: PublishProductCatalogRequest,
    workspace_id: UUID,
) -> ProductCatalogResponse:
    """Record a complete statement of the catalog, as a new version.

    **`PUT`, not `POST`/`PATCH`/`DELETE` per product.** The aggregate is the
    catalog, so a version is a whole statement: accepting *"add this one"*
    would make what gets stored depend on what was there when the request
    arrived, which is the lost update two people editing a list produce. It
    is also what makes this endpoint **idempotent** — the client chooses
    product ids, so sending the same body twice yields the same catalog.

    **Nothing is edited.** A revision is a new row naming the one it
    supersedes, and the database holds no `UPDATE` grant on the table. Every
    version a customer ever declared stays readable, which is what lets a
    future citation of a product resolve against the catalog that contained
    it.

    **409 when somebody else saved first**, with the version that is actually
    in force. The alternative — accepting the write — would erase a
    colleague's work and report success to both of them.
    """
    context.authorize(Resource.PRODUCT, Action.UPDATE)
    catalog = await publish.execute(
        PublishProductCatalogInput(
            workspace_id=context.workspace_id,
            products=tuple(product.to_domain() for product in body.products),
            expected_version=body.expected_version,
            # Taken from the verified caller, never from the request. A body
            # able to name its own author could sign somebody else's name to
            # a commercial decision.
            actor_id=context.principal.user_id,
        )
    )
    return ProductCatalogResponse.from_domain(catalog)


@router.get(
    "/workspaces/{workspace_id}/icp",
    response_model=IcpDeclarationResponse,
    summary="Who buys what this workspace sells",
)
async def icp_declaration(
    context: CurrentWorkspace, declarations: IcpRead
) -> IcpDeclarationResponse:
    """The ideal customer in force.

    **Never a 404**, and never a match. It reports what the customer stated
    about who buys their products — comparing a real company against it is
    somebody else's work, and this endpoint has no way to express the result.
    """
    context.authorize(Resource.ICP, Action.READ)
    declaration = await declarations.current(context.workspace_id)
    return (
        IcpDeclarationResponse.empty()
        if declaration is None
        else IcpDeclarationResponse.from_domain(declaration)
    )


@router.put(
    "/workspaces/{workspace_id}/icp",
    response_model=IcpDeclarationResponse,
    status_code=status.HTTP_200_OK,
    summary="Describe who buys what this workspace sells",
)
async def declare_icp(
    context: CurrentWorkspace, declare: IcpWrite, body: DeclareIcpRequest
) -> IcpDeclarationResponse:
    """Record a complete description of the ideal customer, as a new version.

    **`PUT`, and the whole description.** The aggregate is the declaration, so
    a version is a whole statement — accepting *"describe this one product"*
    would make what gets stored depend on what was there when the request
    arrived, which is the lost update two people editing a page produce.

    **422 when a profile names a product the workspace does not sell.** The
    reference would resolve to nothing, in the module whose whole job is being
    citable later.

    **409 when somebody else saved first**, with the version actually in
    force. Accepting the write would erase a colleague's work and report
    success to both of them.
    """
    context.authorize(Resource.ICP, Action.UPDATE)
    declaration = await declare.execute(
        DeclareIcpInput(
            workspace_id=context.workspace_id,
            profiles=tuple(profile.to_domain() for profile in body.profiles),
            expected_version=body.expected_version,
            # Taken from the verified caller, never from the request.
            actor_id=context.principal.user_id,
        )
    )
    return IcpDeclarationResponse.from_domain(declaration)


@router.get(
    "/workspaces/{workspace_id}/buying-committee",
    response_model=BuyingCommitteeResponse,
    summary="Who decides about what this workspace sells",
)
async def buying_committee(
    context: CurrentWorkspace, committees: CommitteeRead
) -> BuyingCommitteeResponse:
    """The committee in force.

    **Never a 404, and never an assessment.** It reports the roles the
    customer said are involved in a purchase. Whether a particular company's
    committee is complete, who to contact, or how much any seat matters are
    conclusions about a real deal — none of them is this module's, and this
    response has no field that could carry one.
    """
    context.authorize(Resource.BUYING_COMMITTEE, Action.READ)
    declaration = await committees.current(context.workspace_id)
    return (
        BuyingCommitteeResponse.empty()
        if declaration is None
        else BuyingCommitteeResponse.from_domain(declaration)
    )


@router.put(
    "/workspaces/{workspace_id}/buying-committee",
    response_model=BuyingCommitteeResponse,
    status_code=status.HTTP_200_OK,
    summary="Declare who decides about what this workspace sells",
)
async def declare_buying_committee(
    context: CurrentWorkspace,
    declare: CommitteeWrite,
    body: DeclareBuyingCommitteeRequest,
) -> BuyingCommitteeResponse:
    """Record a complete statement of the committee, as a new version.

    **`PUT`, and the whole declaration**, for the third time in this module
    and the same reason each time: the aggregate is the declaration, so
    accepting *"add this role"* would make what gets stored depend on what was
    there when the request arrived.

    **422 when a committee names a product the workspace does not sell**, and
    **409 when somebody else saved first** — with the version actually in
    force, because accepting the write would erase a colleague's work and
    report success to both of them.
    """
    context.authorize(Resource.BUYING_COMMITTEE, Action.UPDATE)
    declaration = await declare.execute(
        DeclareBuyingCommitteeInput(
            workspace_id=context.workspace_id,
            committees=tuple(entry.to_domain() for entry in body.committees),
            expected_version=body.expected_version,
            # Taken from the verified caller, never from the request.
            actor_id=context.principal.user_id,
        )
    )
    return BuyingCommitteeResponse.from_domain(declaration)


@router.get(
    "/workspaces/{workspace_id}/focus",
    response_model=CommercialFocusResponse,
    summary="What this workspace is pushing right now",
)
async def commercial_focus(
    context: CurrentWorkspace, focuses: FocusRead
) -> CommercialFocusResponse:
    """The focus in force.

    **Never a 404, and never applied to anything.** It reports which products
    the customer said they are pushing. Nothing here weights a score, ranks an
    account, or filters a list — a consumer may one day do those things, and
    this reports only that the customer said it, when, and who.
    """
    context.authorize(Resource.COMMERCIAL_FOCUS, Action.READ)
    focus = await focuses.current(context.workspace_id)
    return (
        CommercialFocusResponse.empty()
        if focus is None
        else CommercialFocusResponse.from_domain(focus)
    )


@router.put(
    "/workspaces/{workspace_id}/focus",
    response_model=CommercialFocusResponse,
    status_code=status.HTTP_200_OK,
    summary="Declare what this workspace is pushing right now",
)
async def declare_focus(
    context: CurrentWorkspace, declare: FocusWrite, body: DeclareFocusRequest
) -> CommercialFocusResponse:
    """Record a complete statement of the focus, as a new version.

    **`PUT`, and the whole focus**, for the fourth time in this module and the
    same reason each time: the aggregate is the declaration.

    **An empty focus is accepted**, and is how a customer says they are not
    pushing anything in particular — it has an author and a moment, which is
    what makes it different from never having said anything.

    **422 when a product is not one the workspace sells**, and **409 when
    somebody else saved first**, with the version actually in force.
    """
    context.authorize(Resource.COMMERCIAL_FOCUS, Action.UPDATE)
    focus = await declare.execute(
        DeclareFocusInput(
            workspace_id=context.workspace_id,
            products=body.products,
            objective=body.objective,
            expected_version=body.expected_version,
            # Taken from the verified caller, never from the request.
            actor_id=context.principal.user_id,
        )
    )
    return CommercialFocusResponse.from_domain(focus)


@router.get(
    "/workspaces/{workspace_id}/target-accounts",
    response_model=TargetAccountListResponse,
    summary="Which companies this workspace watches",
)
async def target_accounts(
    context: CurrentWorkspace, accounts: TargetAccountsRead
) -> TargetAccountListResponse:
    """The list in force.

    **Never a 404, and never a status.** It reports the companies the customer
    named. Whether Signora has looked at any of them yet, what it found, and
    when it will look again are Provider Platform's facts — this response has
    no field that could carry one.
    """
    context.authorize(Resource.TARGET_ACCOUNT, Action.READ)
    declaration = await accounts.current(context.workspace_id)
    return (
        TargetAccountListResponse.empty()
        if declaration is None
        else TargetAccountListResponse.from_domain(declaration)
    )


@router.put(
    "/workspaces/{workspace_id}/target-accounts",
    response_model=TargetAccountListResponse,
    status_code=status.HTTP_200_OK,
    summary="Declare which companies this workspace watches",
)
async def declare_target_accounts(
    context: CurrentWorkspace,
    declare: TargetAccountsWrite,
    body: DeclareTargetAccountsRequest,
) -> TargetAccountListResponse:
    """Record a complete statement of the watch list, as a new version.

    **The only write in this module that anybody downstream hears about.** It
    publishes `commercial_profile.target_accounts_changed` on the request's own
    transaction, so the row and the announcement commit together or not at all.

    **The endpoint returns once the declaration is durably recorded**, not once
    anything has been synchronized. Nothing about providers happens inside this
    request, and the response says nothing about what will (§7, ADR-0036).

    **409 when somebody else saved first**, with the version actually in force.
    """
    context.authorize(Resource.TARGET_ACCOUNT, Action.UPDATE)
    declaration = await declare.execute(
        DeclareTargetAccountsInput(
            workspace_id=context.workspace_id,
            accounts=tuple(account.to_domain() for account in body.accounts),
            expected_version=body.expected_version,
            # Taken from the verified caller, never from the request.
            actor_id=context.principal.user_id,
        ),
        correlation_id=context.correlation_id,
    )
    return TargetAccountListResponse.from_domain(declaration)


__all__ = ["router"]


@router.get(
    "/workspaces/{workspace_id}/icp-segments",
    response_model=CursorPage[SegmentSummaryResponse],
    summary="Every customer segment this workspace sells to",
)
async def list_segments(
    context: CurrentWorkspace,
    segments: SegmentRead,
    include_archived: bool = False,
    cursor: str | None = None,
    limit: int = DEFAULT_PAGE_LIMIT,
) -> CursorPage[SegmentSummaryResponse]:
    """*"Who do we sell to?"*

    **The question the product could not answer until now.** An ideal customer
    used to be reachable only through the product it belonged to, so there was
    no page that showed everything a workspace had said about its buyers.

    **One product may be bought by several segments, and one segment may buy
    several products.** A company selling a suite to one kind of buyer says
    that once here; previously it had to say it once per product and keep the
    copies in step by hand.

    **Archived segments are excluded unless asked for.** They are retired, not
    deleted — everything Signora found under one was found *because* of it, so
    they stay reachable and simply do not answer *"who do we sell to?"*
    """
    context.authorize(Resource.ICP, Action.READ)
    page = await segments.page(
        workspace_id=context.workspace_id,
        include_archived=include_archived,
        after=decode_cursor(cursor) if cursor else None,
        limit=min(limit, MAX_PAGE_LIMIT),
    )
    return CursorPage(
        items=[SegmentSummaryResponse.from_domain(s) for s in page.items],
        next_cursor=(
            encode_cursor(position)
            if page.has_more and (position := page.next_position) is not None
            else None
        ),
        has_more=page.has_more,
    )
