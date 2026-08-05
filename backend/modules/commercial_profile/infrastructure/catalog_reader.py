"""The published read side of the product catalog.

**The module's fourth published read**, separated from `repository.py` on the
same terms as the three before it.

**`description` is read from storage and deliberately not published.** The
catalog holds it and this module's own use cases return it; a consumer
inferring which product an account is about needs identity and a name, and a
view carrying prose would invite reasoning from a sentence this module never
promised to keep stable. Widening a view later is a compatible change; taking
a field back is not.
"""

from __future__ import annotations

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from modules.commercial_profile.infrastructure.models import ProductCatalogModel
from modules.commercial_profile.infrastructure.versioned import latest
from modules.commercial_profile.public import ProductCatalogView, ProductView


class SqlProductCatalogReader:
    """Implements `ProductCatalogReader` for the composition root to inject."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def current(self, workspace_id: UUID) -> ProductCatalogView | None:
        """The catalog in force, or ``None`` when nothing has been declared."""
        result = await self._session.execute(latest(ProductCatalogModel, workspace_id))
        row = result.scalar_one_or_none()
        if row is None:
            return None

        return ProductCatalogView(
            workspace_id=row.workspace_id,
            version=row.version,
            products=tuple(
                ProductView(id=UUID(raw["id"]), name=raw["name"]) for raw in row.products
            ),
        )
