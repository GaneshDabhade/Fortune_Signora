"""Persistence for the product catalog.

Offers `current` and `save` and **nothing else**. No update, no delete: a
catalog is superseded by a new version, and not offering the method means
nobody writes code the database would refuse at runtime.
"""

from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from modules.commercial_profile.domain.catalog import Product, ProductCatalog
from modules.commercial_profile.domain.icp import (
    EmployeeRange,
    IcpDeclaration,
    ProductIcp,
)
from modules.commercial_profile.infrastructure.models import (
    IcpDeclarationModel,
    ProductCatalogModel,
)


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
        """The highest version this workspace has declared.

        **Highest version, deliberately — not `supersedes IS NULL`.** On an
        immutable table the new row is the one that names its predecessor, so
        the row with a null `supersedes` is the *first* version and stays
        that way forever. `signal_profile` reads itself that way today and
        would return version 1 after any revision; the defect is latent only
        because nothing has ever written a second one (see the M12.5 review).

        Ordering by version is also the rule the uniqueness constraint
        already enforces, so the reader and the database agree by
        construction rather than by coincidence.
        """
        result = await self._session.execute(
            select(ProductCatalogModel)
            .where(ProductCatalogModel.workspace_id == workspace_id)
            .order_by(ProductCatalogModel.version.desc())
            .limit(1)
        )
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
    """Persistence for the ideal customer, on the catalog's terms exactly.

    `current` and `save`, no update and no delete. The duplication with
    `SqlProductCatalogRepository` is deliberate at two instances: what the two
    share is *the shape of an immutable versioned declaration*, and extracting
    that from two examples would be guessing at the third.
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def current(self, workspace_id: UUID) -> IcpDeclaration | None:
        """The highest version this workspace has declared.

        **Highest version, not `supersedes IS NULL`** — on an immutable table
        the new row is the one that names its predecessor, so a null
        `supersedes` marks the *first* version permanently. The same defect
        `signal_profile` still carries, and the same avoidance the catalog
        already uses.
        """
        result = await self._session.execute(
            select(IcpDeclarationModel)
            .where(IcpDeclarationModel.workspace_id == workspace_id)
            .order_by(IcpDeclarationModel.version.desc())
            .limit(1)
        )
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
