"""Composition root for the Commercial Profile.

**One line deep, and it will stay that way.** The module declares what a
customer sells; it reads no other module, calls no provider, and computes
nothing — so there is nothing to inject but a session. That shallowness is
the boundary working, not an omission.
"""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from modules.commercial_profile.application.declare_committee import (
    DeclareBuyingCommittee,
)
from modules.commercial_profile.application.declare_icp import DeclareIcp
from modules.commercial_profile.application.publish import PublishProductCatalog
from modules.commercial_profile.infrastructure.repository import (
    SqlBuyingCommitteeRepository,
    SqlIcpDeclarationRepository,
    SqlProductCatalogRepository,
)


def build_catalogs(session: AsyncSession) -> SqlProductCatalogRepository:
    """Customer-authored declaration, deliberately reachable on its own — it
    is not derived data and a pipeline rebuild must not touch it."""
    return SqlProductCatalogRepository(session)


def build_publish_product_catalog(session: AsyncSession) -> PublishProductCatalog:
    return PublishProductCatalog(repository=SqlProductCatalogRepository(session))


def build_icp_declarations(session: AsyncSession) -> SqlIcpDeclarationRepository:
    return SqlIcpDeclarationRepository(session)


def build_declare_icp(session: AsyncSession) -> DeclareIcp:
    """**Two repositories, both this module's.** Describing who buys a product
    requires knowing the workspace sells it, and both aggregates live in this
    bounded context — no other module is read, and none could be."""
    return DeclareIcp(
        declarations=SqlIcpDeclarationRepository(session),
        catalog=SqlProductCatalogRepository(session),
    )


def build_buying_committees(session: AsyncSession) -> SqlBuyingCommitteeRepository:
    return SqlBuyingCommitteeRepository(session)


def build_declare_buying_committee(session: AsyncSession) -> DeclareBuyingCommittee:
    return DeclareBuyingCommittee(
        committees=SqlBuyingCommitteeRepository(session),
        catalog=SqlProductCatalogRepository(session),
    )
