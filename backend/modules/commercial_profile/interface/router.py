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

from apps.api.composition.products import CatalogRead, CatalogWrite
from modules.commercial_profile.application.publish import PublishProductCatalogInput
from modules.commercial_profile.interface.schemas import (
    ProductCatalogResponse,
    PublishProductCatalogRequest,
)
from signora_platform.api import CurrentWorkspace
from signora_platform.authorization import Action, Resource

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


__all__ = ["router"]
