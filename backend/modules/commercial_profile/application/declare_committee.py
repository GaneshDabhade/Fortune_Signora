"""Declaring who decides about what the workspace sells.

The third write in the module, and the same discipline as the first two: it
takes the committee a customer means to have and records it as a new version.
It never patches, merges, reconciles — and it evaluates nobody.

### Why the whole declaration arrives, not a change to it

The aggregate is the declaration, so a version is a complete statement.
Accepting *"add this role"* would make the stored version depend on what was
there when the request arrived, which is exactly the lost update two people
editing the same page produce.

### Why a product must already be in the catalog

A committee cites a product id, and everything read later resolves that id
against the catalog. Accepting one for a product the workspace does not sell
would store a reference that resolves to nothing — the shared rule in
`declaring.py`, because the ideal customer needs the identical guarantee.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID, uuid4

from modules.commercial_profile.application.declaring import (
    CommitteeUnknownProductError,
    sold_products,
)
from modules.commercial_profile.application.ports import (
    BuyingCommitteeRepository,
    ProductCatalogRepository,
)
from modules.commercial_profile.domain.committee import (
    BuyingCommittee,
    ProductCommittee,
    first_committee,
)
from modules.commercial_profile.domain.declaration import (
    UNDECLARED,
    CommercialProfileError,
)


class CommitteeVersionConflictError(CommercialProfileError):
    """Somebody else changed the committee since this caller read it."""

    def __init__(self, *, expected: int, actual: int) -> None:
        self.expected = expected
        self.actual = actual
        super().__init__(
            f"your buying committee is at version {actual}, not {expected}. Somebody "
            "else changed it since you opened this page — reload to see their version "
            "before saving yours, so neither of you loses work."
        )


@dataclass(frozen=True, slots=True)
class DeclareBuyingCommitteeInput:
    workspace_id: UUID
    committees: tuple[ProductCommittee, ...]
    #: The version the caller believes it is replacing. `0` declares the first
    #: committee, and is the only value that may be sent by a caller who has
    #: never read one.
    expected_version: int
    #: Taken from the verified caller by the interface layer. There is no
    #: field a request could use to name somebody else as the author.
    actor_id: UUID


class DeclareBuyingCommittee:
    def __init__(
        self,
        *,
        committees: BuyingCommitteeRepository,
        catalog: ProductCatalogRepository,
    ) -> None:
        self._committees = committees
        self._catalog = catalog

    async def execute(self, request: DeclareBuyingCommitteeInput) -> BuyingCommittee:
        current = await self._committees.current(request.workspace_id)
        actual = current.version if current is not None else UNDECLARED
        # **Version before products**, as everywhere in this module: a stale
        # caller's product list is stale too, so telling them their catalog is
        # wrong would send them to fix the wrong page.
        if actual != request.expected_version:
            raise CommitteeVersionConflictError(expected=request.expected_version, actual=actual)

        sold = await sold_products(self._catalog, request.workspace_id)
        for committee in request.committees:
            if committee.product_id not in sold:
                raise CommitteeUnknownProductError(committee.product_id)

        now = datetime.now(UTC)
        declaration = (
            first_committee(
                request.workspace_id,
                request.committees,
                id=uuid4(),
                by=request.actor_id,
                now=now,
            )
            if current is None
            else current.revise(request.committees, id=uuid4(), by=request.actor_id, now=now)
        )
        await self._committees.save(declaration)
        return declaration
