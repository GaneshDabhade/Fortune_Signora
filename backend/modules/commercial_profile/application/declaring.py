"""What every declaration that cites a product has in common.

Two of them do now — the ideal customer and the buying committee — and slice
4's priorities will be the third. Each says something *about a product*, and
each therefore has to answer the same question first: **does the workspace
actually sell this?**

**One check, several refusals.** The rule is shared because it is one rule;
the error classes are not, because a customer fixing an ideal customer and a
customer fixing a committee are looking at different pages, and a client that
cannot tell the two apart can only say *"something was wrong"*.
"""

from __future__ import annotations

from uuid import UUID

from modules.commercial_profile.application.ports import ProductCatalogRepository
from modules.commercial_profile.domain.declaration import CommercialProfileError


class UnknownProductError(CommercialProfileError):
    """A declaration names a product the workspace does not currently sell.

    Never raised directly — each declaration raises its own subclass so the
    refusal carries a code naming the page it belongs to.
    """

    def __init__(self, product_id: UUID, *, said: str) -> None:
        self.product_id = product_id
        super().__init__(
            f"you cannot {said} a product you have not said you sell. Add it under Products first."
        )


class IcpUnknownProductError(UnknownProductError):
    def __init__(self, product_id: UUID) -> None:
        super().__init__(product_id, said="describe who buys")


class CommitteeUnknownProductError(UnknownProductError):
    def __init__(self, product_id: UUID) -> None:
        super().__init__(product_id, said="describe who decides about")


async def sold_products(catalog: ProductCatalogRepository, workspace_id: UUID) -> frozenset[UUID]:
    """The products the workspace currently sells.

    An empty set when nothing has been declared, which is the ordinary state
    of a new workspace — and the reason every profile citing a product is
    refused until the catalog exists, rather than the request failing.
    """
    current = await catalog.current(workspace_id)
    return frozenset() if current is None else frozenset(p.id for p in current.products)
