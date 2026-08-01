"""What the Commercial Profile needs from infrastructure.

One port per declaration, each the same method pair. **No update and no
delete** — a declaration is superseded by a new version, and the absent
methods are what stop anybody writing code the database would refuse
(migrations `0019` and `0020` grant no `UPDATE`).
"""

from __future__ import annotations

from typing import Protocol
from uuid import UUID

from modules.commercial_profile.domain.catalog import ProductCatalog
from modules.commercial_profile.domain.icp import IcpDeclaration


class ProductCatalogRepository(Protocol):
    async def current(self, workspace_id: UUID) -> ProductCatalog | None:
        """The catalog in force, or ``None`` when nothing has been declared.

        ``None`` rather than an empty catalog: *"they have declared nothing"*
        and *"they declared an empty list"* are different facts, and only the
        second has an author and a moment.
        """
        ...

    async def save(self, catalog: ProductCatalog) -> None: ...


class IcpDeclarationRepository(Protocol):
    async def current(self, workspace_id: UUID) -> IcpDeclaration | None:
        """The declaration in force, or ``None`` when nothing has been said.

        ``None`` rather than an empty declaration: *"they have described
        nobody"* and *"they described nobody, deliberately, on Tuesday"* are
        different facts, and only the second has an author and a moment.
        """
        ...

    async def save(self, declaration: IcpDeclaration) -> None: ...
