"""What the Commercial Profile needs from infrastructure.

One port, one method pair. **No update and no delete** — a catalog is
superseded by a new version, and the absent methods are what stop anybody
writing code the database would refuse (migration `0019` grants no `UPDATE`).
"""

from __future__ import annotations

from typing import Protocol
from uuid import UUID

from modules.commercial_profile.domain.catalog import ProductCatalog


class ProductCatalogRepository(Protocol):
    async def current(self, workspace_id: UUID) -> ProductCatalog | None:
        """The catalog in force, or ``None`` when nothing has been declared.

        ``None`` rather than an empty catalog: *"they have declared nothing"*
        and *"they declared an empty list"* are different facts, and only the
        second has an author and a moment.
        """
        ...

    async def save(self, catalog: ProductCatalog) -> None: ...
