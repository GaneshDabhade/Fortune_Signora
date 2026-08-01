"""Composition root for the Commercial Profile.

**One line deep, and it will stay that way.** The module declares what a
customer sells; it reads no other module, calls no provider, and computes
nothing — so there is nothing to inject but a session. That shallowness is
the boundary working, not an omission.
"""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from modules.commercial_profile.application.publish import PublishProductCatalog
from modules.commercial_profile.infrastructure.repository import (
    SqlProductCatalogRepository,
)


def build_catalogs(session: AsyncSession) -> SqlProductCatalogRepository:
    """Customer-authored declaration, deliberately reachable on its own — it
    is not derived data and a pipeline rebuild must not touch it."""
    return SqlProductCatalogRepository(session)


def build_publish_product_catalog(session: AsyncSession) -> PublishProductCatalog:
    return PublishProductCatalog(repository=SqlProductCatalogRepository(session))
