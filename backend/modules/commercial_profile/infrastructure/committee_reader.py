"""The published read side of the buying committee.

**The module's third published read**, on the same terms as the two before it:
everything in `repository.py` serves this module's own use cases and may change
freely; everything here is a contract with somebody else and may not.

The mapping is the boundary. A consumer receives `BuyingCommitteeView`, never
`BuyingCommittee`, so this module's validation rules — one committee per
product, no two roles sharing a title, at least one seat — stay entirely its
own. **`part` crosses as the string it is stored as**, which is the same string
the aggregate's enum carries; publishing the enum would export a vocabulary
this module intends to extend.
"""

from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from modules.commercial_profile.domain.committee import seat_id
from modules.commercial_profile.infrastructure.models import BuyingCommitteeModel
from modules.commercial_profile.infrastructure.versioned import latest
from modules.commercial_profile.public import (
    BuyingCommitteeRoleView,
    BuyingCommitteeView,
    ProductCommitteeView,
)


def _to_committee(raw: dict[str, Any]) -> ProductCommitteeView:
    """One product's seats, each carrying the id a consumer cites.

    **A function rather than a nested comprehension**, because the seat id
    needs the product id and a comprehension cannot see the value its outer
    level parsed — and parsing it twice would be two chances to parse it
    differently.
    """
    product_id = UUID(raw["product_id"])
    return ProductCommitteeView(
        product_id=product_id,
        roles=tuple(
            BuyingCommitteeRoleView(
                # **Derived on read, from the stored product and title.**
                # Nothing on disk holds it, which is why a declaration written
                # in July answers the same as one written today.
                id=seat_id(product_id, role["title"]),
                title=role["title"],
                part=role["part"],
            )
            for role in raw["roles"]
        ),
    )


class SqlBuyingCommitteeReader:
    """Implements `BuyingCommitteeReader` for the composition root to inject."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def current(self, workspace_id: UUID) -> BuyingCommitteeView | None:
        """The declaration in force, or ``None`` when there has never been one.

        **`None` and an empty tuple are different answers**, as they are for
        the two readers beside this one: a workspace that has never said how a
        purchase gets decided is not the same as one that said something.
        """
        result = await self._session.execute(latest(BuyingCommitteeModel, workspace_id))
        row = result.scalar_one_or_none()
        if row is None:
            return None

        return BuyingCommitteeView(
            workspace_id=row.workspace_id,
            version=row.version,
            committees=tuple(_to_committee(raw) for raw in row.committees),
        )
