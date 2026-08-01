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

from modules.commercial_profile.application.ports import ProductCatalogRepository
from modules.commercial_profile.application.publish import PublishProductCatalog
from modules.commercial_profile.infrastructure.composition import (
    build_catalogs,
    build_publish_product_catalog,
)
from signora_platform.api import CurrentWorkspace


def catalogs(context: CurrentWorkspace) -> ProductCatalogRepository:
    """The read side, typed as the **port** so the router reaches the one
    method it needs and no implementation detail."""
    return build_catalogs(context.session)


def publish_catalog(context: CurrentWorkspace) -> PublishProductCatalog:
    return build_publish_product_catalog(context.session)


CatalogRead = Annotated[ProductCatalogRepository, Depends(catalogs)]
CatalogWrite = Annotated[PublishProductCatalog, Depends(publish_catalog)]

__all__ = ["CatalogRead", "CatalogWrite", "catalogs", "publish_catalog"]
