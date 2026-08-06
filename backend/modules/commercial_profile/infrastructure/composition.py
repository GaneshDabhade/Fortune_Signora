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
from modules.commercial_profile.application.declare_competitors import DeclareCompetitors
from modules.commercial_profile.application.declare_focus import DeclareFocus
from modules.commercial_profile.application.declare_icp import DeclareIcp
from modules.commercial_profile.application.declare_target_accounts import (
    DeclareTargetAccounts,
)
from modules.commercial_profile.application.publish import PublishProductCatalog
from modules.commercial_profile.application.segment_queries import SegmentQueries
from modules.commercial_profile.infrastructure.competitor_reader import (
    SqlDeclaredCompetitorReader,
)
from modules.commercial_profile.infrastructure.repository import (
    SqlBuyingCommitteeRepository,
    SqlCommercialFocusRepository,
    SqlDeclaredCompetitorsRepository,
    SqlIcpDeclarationRepository,
    SqlProductCatalogRepository,
    SqlTargetAccountListRepository,
)
from modules.commercial_profile.infrastructure.catalog_reader import SqlProductCatalogReader
from modules.commercial_profile.infrastructure.committee_reader import SqlBuyingCommitteeReader
from modules.commercial_profile.infrastructure.icp_reader import SqlIcpReader
from modules.commercial_profile.infrastructure.segment_repository import SqlSegmentReader
from modules.commercial_profile.infrastructure.target_account_reader import (
    SqlTargetAccountReader,
)
from signora_platform.event_bus import EventPublisher


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


def build_focuses(session: AsyncSession) -> SqlCommercialFocusRepository:
    return SqlCommercialFocusRepository(session)


def build_declare_focus(session: AsyncSession) -> DeclareFocus:
    return DeclareFocus(
        focuses=SqlCommercialFocusRepository(session),
        catalog=SqlProductCatalogRepository(session),
    )


def build_target_accounts(session: AsyncSession) -> SqlTargetAccountListRepository:
    return SqlTargetAccountListRepository(session)


def build_declare_target_accounts(
    session: AsyncSession, *, publisher: EventPublisher
) -> DeclareTargetAccounts:
    """The module's only write that announces itself.

    **The publisher writes to the outbox on this same session**, so the row
    and the event announcing it commit together or not at all. Injected rather
    than constructed here, because which publisher is in use is the
    composition root's decision and a test's to substitute.
    """
    return DeclareTargetAccounts(
        repository=SqlTargetAccountListRepository(session),
        publisher=publisher,
        session=session,
    )


def build_target_account_reader(session: AsyncSession) -> SqlTargetAccountReader:
    """The module's published read side.

    **Built here so another module never constructs it.** A consumer depends
    on the `TargetAccountReader` Protocol in `public/`; its composition root
    calls this, and the consumer never learns that any of it is backed by SQL.
    """
    return SqlTargetAccountReader(session)


def build_segment_queries(session: AsyncSession) -> SegmentQueries:
    """The segments read surface. One level deep, like everything here."""
    return SegmentQueries(SqlSegmentReader(session))


def build_competitors(session: AsyncSession) -> SqlDeclaredCompetitorsRepository:
    return SqlDeclaredCompetitorsRepository(session)


def build_declare_competitors(session: AsyncSession) -> DeclareCompetitors:
    return DeclareCompetitors(competitors=build_competitors(session))


def build_declared_competitor_reader(session: AsyncSession) -> SqlDeclaredCompetitorReader:
    """The module's second published read side.

    Built here for the reason the first one is: a consumer depends on the
    `DeclaredCompetitorReader` Protocol in `public/`, its composition root
    calls this, and the consumer never learns that any of it is backed by SQL.
    """
    return SqlDeclaredCompetitorReader(session)


def build_buying_committee_reader(session: AsyncSession) -> SqlBuyingCommitteeReader:
    """The module's third published read side.

    Built here for the reason the first two are: Sales Engagement depends on
    the `BuyingCommitteeReader` Protocol in `public/`, its composition root
    calls this, and it never learns that any of it is backed by SQL.
    """
    return SqlBuyingCommitteeReader(session)


def build_product_catalog_reader(session: AsyncSession) -> SqlProductCatalogReader:
    """The module's fourth published read side."""
    return SqlProductCatalogReader(session)


def build_icp_reader(session: AsyncSession) -> SqlIcpReader:
    """The ideal customer, for whoever needs to evaluate an account against it.

    **Published at TASK-434, and the reader is only half of the capability.**
    The other half is `domain/evaluation.evaluate`, which is pure and takes the
    observed attributes as an argument — so a consumer reads the criteria
    through this port and supplies the facts itself. That split is what keeps
    the comparison in the module that owns the vocabulary without that module
    ever reaching into the pipeline.
    """
    return SqlIcpReader(session)
