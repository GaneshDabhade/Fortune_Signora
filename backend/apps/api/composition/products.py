"""Composing the Commercial Profile's read and write surfaces.

**One level deep — the shallowest composition in the repository**, and that
is the boundary rather than an omission. The module records what a customer
declares: it reads no other module, calls no provider, and computes nothing,
so there is nothing to assemble but a session.

Its own file, like every other surface: a router inherits every import the
module it imports makes, and a shared composition would hand this one a
transitive dependency on the ten-stage pipeline it deliberately knows nothing
about.
"""

from typing import Annotated

from fastapi import Depends

from modules.commercial_profile.application.declare_icp import DeclareIcp
from modules.commercial_profile.application.ports import (
    IcpDeclarationRepository,
    ProductCatalogRepository,
)
from modules.commercial_profile.application.publish import PublishProductCatalog
from modules.commercial_profile.infrastructure.composition import (
    build_catalogs,
    build_declare_icp,
    build_icp_declarations,
    build_publish_product_catalog,
)
from signora_platform.api import CurrentWorkspace


def catalogs(context: CurrentWorkspace) -> ProductCatalogRepository:
    """The read side, typed as the **port** so the router reaches the one
    method it needs and no implementation detail."""
    return build_catalogs(context.session)


def publish_catalog(context: CurrentWorkspace) -> PublishProductCatalog:
    return build_publish_product_catalog(context.session)


def icp_declarations(context: CurrentWorkspace) -> IcpDeclarationRepository:
    return build_icp_declarations(context.session)


def declare_icp(context: CurrentWorkspace) -> DeclareIcp:
    return build_declare_icp(context.session)


CatalogRead = Annotated[ProductCatalogRepository, Depends(catalogs)]
CatalogWrite = Annotated[PublishProductCatalog, Depends(publish_catalog)]
IcpRead = Annotated[IcpDeclarationRepository, Depends(icp_declarations)]
IcpWrite = Annotated[DeclareIcp, Depends(declare_icp)]

__all__ = [
    "CatalogRead",
    "CatalogWrite",
    "IcpRead",
    "IcpWrite",
    "catalogs",
    "declare_icp",
    "icp_declarations",
    "publish_catalog",
]
