"""Persistence for the customer's declarations.

Each offers `current` and `save` and **nothing else**. No update, no delete: a
declaration is superseded by a new version, and not offering the method means
nobody writes code the database would refuse at runtime.

**The read every one of them performs lives in `versioned.py`**, not here.
Three hand-written copies of *"the row in force is the highest version"* would
be three chances for the fourth to be written the way `signal_profile` wrote
it, which is backwards.
"""

from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from modules.commercial_profile.domain.catalog import Product, ProductCatalog
from modules.commercial_profile.domain.committee import (
    BuyingCommittee,
    CommitteePart,
    CommitteeRole,
    ProductCommittee,
)
from modules.commercial_profile.domain.competitors import (
    Competitor,
    DeclaredCompetitors,
)
from modules.commercial_profile.domain.focus import CommercialFocus
from modules.commercial_profile.domain.icp import (
    EmployeeRange,
    IcpDeclaration,
    ProductIcp,
)
from modules.commercial_profile.domain.target_accounts import (
    TargetAccount,
    TargetAccountList,
)
from modules.commercial_profile.infrastructure.models import (
    BuyingCommitteeModel,
    CommercialFocusModel,
    DeclaredCompetitorsModel,
    IcpDeclarationModel,
    ProductCatalogModel,
    TargetAccountListModel,
)
from modules.commercial_profile.infrastructure.versioned import latest


def _to_product(raw: dict[str, Any]) -> Product:
    return Product(
        id=UUID(raw["id"]),
        name=raw["name"],
        description=raw.get("description", ""),
    )


def _to_catalog(row: ProductCatalogModel) -> ProductCatalog:
    return ProductCatalog(
        id=row.id,
        workspace_id=row.workspace_id,
        version=row.version,
        products=tuple(_to_product(raw) for raw in row.products),
        created_at=row.created_at,
        created_by=row.created_by,
        supersedes=row.supersedes,
    )


class SqlProductCatalogRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def current(self, workspace_id: UUID) -> ProductCatalog | None:
        result = await self._session.execute(latest(ProductCatalogModel, workspace_id))
        row = result.scalar_one_or_none()
        return None if row is None else _to_catalog(row)

    async def save(self, catalog: ProductCatalog) -> None:
        """Insert the new version. Nothing is updated, ever.

        **`uq_product_catalog_version` is the concurrency control.** Two
        callers who read version 3 simultaneously both build version 4, and
        the second insert violates the constraint rather than silently
        winning. `expected_version` refuses the ordinary case politely; the
        constraint is what catches the genuine race, and it needs no `UPDATE`
        grant to do it.
        """
        self._session.add(
            ProductCatalogModel(
                id=catalog.id,
                workspace_id=catalog.workspace_id,
                version=catalog.version,
                products=[
                    {
                        "id": str(product.id),
                        "name": product.name,
                        "description": product.description,
                    }
                    for product in catalog.products
                ],
                supersedes=catalog.supersedes,
                created_by=catalog.created_by,
                updated_by=catalog.created_by,
            )
        )
        await self._session.flush()


def _to_range(raw: dict[str, Any] | None) -> EmployeeRange | None:
    return (
        None
        if raw is None
        else EmployeeRange(minimum=raw.get("minimum"), maximum=raw.get("maximum"))
    )


def _to_profile(raw: dict[str, Any]) -> ProductIcp:
    return ProductIcp(
        product_id=UUID(raw["product_id"]),
        industries=tuple(raw.get("industries", ())),
        countries=tuple(raw.get("countries", ())),
        employees=_to_range(raw.get("employees")),
        notes=raw.get("notes", ""),
    )


def _to_declaration(row: IcpDeclarationModel) -> IcpDeclaration:
    return IcpDeclaration(
        id=row.id,
        workspace_id=row.workspace_id,
        version=row.version,
        profiles=tuple(_to_profile(raw) for raw in row.profiles),
        created_at=row.created_at,
        created_by=row.created_by,
        supersedes=row.supersedes,
    )


class SqlIcpDeclarationRepository:
    """Persistence for the ideal customer, on the catalog's terms exactly."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def current(self, workspace_id: UUID) -> IcpDeclaration | None:
        result = await self._session.execute(latest(IcpDeclarationModel, workspace_id))
        row = result.scalar_one_or_none()
        return None if row is None else _to_declaration(row)

    async def save(self, declaration: IcpDeclaration) -> None:
        """Insert the new version. Nothing is updated, ever.

        `uq_icp_declaration_version` is the concurrency control: two callers
        who read version 3 both build version 4, and the second insert is
        refused by the constraint rather than silently winning.
        """
        self._session.add(
            IcpDeclarationModel(
                id=declaration.id,
                workspace_id=declaration.workspace_id,
                version=declaration.version,
                profiles=[
                    {
                        "product_id": str(profile.product_id),
                        "industries": list(profile.industries),
                        "countries": list(profile.countries),
                        "employees": (
                            None
                            if profile.employees is None
                            else {
                                "minimum": profile.employees.minimum,
                                "maximum": profile.employees.maximum,
                            }
                        ),
                        "notes": profile.notes,
                    }
                    for profile in declaration.profiles
                ],
                supersedes=declaration.supersedes,
                created_by=declaration.created_by,
                updated_by=declaration.created_by,
            )
        )
        await self._session.flush()


def _to_role(raw: dict[str, Any]) -> CommitteeRole:
    return CommitteeRole(title=raw["title"], part=CommitteePart(raw["part"]))


def _to_committee(raw: dict[str, Any]) -> ProductCommittee:
    return ProductCommittee(
        product_id=UUID(raw["product_id"]),
        roles=tuple(_to_role(role) for role in raw["roles"]),
    )


def _to_buying_committee(row: BuyingCommitteeModel) -> BuyingCommittee:
    return BuyingCommittee(
        id=row.id,
        workspace_id=row.workspace_id,
        version=row.version,
        committees=tuple(_to_committee(raw) for raw in row.committees),
        created_at=row.created_at,
        created_by=row.created_by,
        supersedes=row.supersedes,
    )


class SqlBuyingCommitteeRepository:
    """Persistence for the buying committee, on the same terms as the rest."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def current(self, workspace_id: UUID) -> BuyingCommittee | None:
        result = await self._session.execute(latest(BuyingCommitteeModel, workspace_id))
        row = result.scalar_one_or_none()
        return None if row is None else _to_buying_committee(row)

    async def save(self, committee: BuyingCommittee) -> None:
        """Insert the new version. Nothing is updated, ever.

        `uq_buying_committee_version` is the concurrency control: two callers
        who read version 3 both build version 4, and the second insert is
        refused by the constraint rather than silently winning.
        """
        self._session.add(
            BuyingCommitteeModel(
                id=committee.id,
                workspace_id=committee.workspace_id,
                version=committee.version,
                committees=[
                    {
                        "product_id": str(entry.product_id),
                        "roles": [
                            {"title": role.title, "part": role.part.value} for role in entry.roles
                        ],
                    }
                    for entry in committee.committees
                ],
                supersedes=committee.supersedes,
                created_by=committee.created_by,
                updated_by=committee.created_by,
            )
        )
        await self._session.flush()


def _to_focus(row: CommercialFocusModel) -> CommercialFocus:
    return CommercialFocus(
        id=row.id,
        workspace_id=row.workspace_id,
        version=row.version,
        products=tuple(UUID(raw) for raw in row.products),
        objective=row.objective,
        created_at=row.created_at,
        created_by=row.created_by,
        supersedes=row.supersedes,
    )


class SqlCommercialFocusRepository:
    """Persistence for the focus, on the same terms as the rest."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def current(self, workspace_id: UUID) -> CommercialFocus | None:
        result = await self._session.execute(latest(CommercialFocusModel, workspace_id))
        row = result.scalar_one_or_none()
        return None if row is None else _to_focus(row)

    async def save(self, focus: CommercialFocus) -> None:
        """Insert the new version. Nothing is updated, ever."""
        self._session.add(
            CommercialFocusModel(
                id=focus.id,
                workspace_id=focus.workspace_id,
                version=focus.version,
                products=[str(product_id) for product_id in focus.products],
                objective=focus.objective,
                supersedes=focus.supersedes,
                created_by=focus.created_by,
                updated_by=focus.created_by,
            )
        )
        await self._session.flush()


def _to_account(raw: dict[str, Any]) -> TargetAccount:
    return TargetAccount(id=UUID(raw["id"]), name=raw["name"])


def _to_account_list(row: TargetAccountListModel) -> TargetAccountList:
    return TargetAccountList(
        id=row.id,
        workspace_id=row.workspace_id,
        version=row.version,
        accounts=tuple(_to_account(raw) for raw in row.accounts),
        created_at=row.created_at,
        created_by=row.created_by,
        supersedes=row.supersedes,
    )


class SqlTargetAccountListRepository:
    """Persistence for the watch list, on the same terms as the rest."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def current(self, workspace_id: UUID) -> TargetAccountList | None:
        result = await self._session.execute(latest(TargetAccountListModel, workspace_id))
        row = result.scalar_one_or_none()
        return None if row is None else _to_account_list(row)

    async def save(self, accounts: TargetAccountList) -> None:
        """Insert the new version. Nothing is updated, ever.

        **No flush of the event here.** The caller publishes on the same
        session afterwards, and both land in one transaction — which is the
        only arrangement in which a consumer can never see an announcement of
        something that did not happen.
        """
        self._session.add(
            TargetAccountListModel(
                id=accounts.id,
                workspace_id=accounts.workspace_id,
                version=accounts.version,
                accounts=[
                    {"id": str(account.id), "name": account.name} for account in accounts.accounts
                ],
                supersedes=accounts.supersedes,
                created_by=accounts.created_by,
                updated_by=accounts.created_by,
            )
        )
        await self._session.flush()


def _to_competitor(raw: dict[str, Any]) -> Competitor:
    return Competitor(id=UUID(raw["id"]), name=raw["name"])


def _to_competitors(row: DeclaredCompetitorsModel) -> DeclaredCompetitors:
    return DeclaredCompetitors(
        id=row.id,
        workspace_id=row.workspace_id,
        version=row.version,
        competitors=tuple(_to_competitor(raw) for raw in row.competitors),
        created_at=row.created_at,
        created_by=row.created_by,
        supersedes=row.supersedes,
    )


class SqlDeclaredCompetitorsRepository:
    """Persistence for the competitor list, on the same terms as the rest."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def current(self, workspace_id: UUID) -> DeclaredCompetitors | None:
        result = await self._session.execute(latest(DeclaredCompetitorsModel, workspace_id))
        row = result.scalar_one_or_none()
        return None if row is None else _to_competitors(row)

    async def save(self, competitors: DeclaredCompetitors) -> None:
        """Insert the new version. Nothing is updated, ever."""
        self._session.add(
            DeclaredCompetitorsModel(
                id=competitors.id,
                workspace_id=competitors.workspace_id,
                version=competitors.version,
                competitors=[
                    {"id": str(entry.id), "name": entry.name}
                    for entry in competitors.competitors
                ],
                supersedes=competitors.supersedes,
                created_by=competitors.created_by,
                updated_by=competitors.created_by,
            )
        )
        await self._session.flush()
