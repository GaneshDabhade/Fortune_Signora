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
from modules.commercial_profile.domain.committee import BuyingCommittee
from modules.commercial_profile.domain.competitors import DeclaredCompetitors
from modules.commercial_profile.domain.focus import CommercialFocus
from modules.commercial_profile.domain.icp import IcpDeclaration
from modules.commercial_profile.domain.target_accounts import TargetAccountList


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


class BuyingCommitteeRepository(Protocol):
    async def current(self, workspace_id: UUID) -> BuyingCommittee | None:
        """The committee in force, or ``None`` when nothing has been said."""
        ...

    async def save(self, committee: BuyingCommittee) -> None: ...


class CommercialFocusRepository(Protocol):
    async def current(self, workspace_id: UUID) -> CommercialFocus | None:
        """The focus in force, or ``None`` when nothing has been declared."""
        ...

    async def save(self, focus: CommercialFocus) -> None: ...


class TargetAccountListRepository(Protocol):
    async def current(self, workspace_id: UUID) -> TargetAccountList | None:
        """The list in force, or ``None`` when nothing has been declared."""
        ...

    async def save(self, accounts: TargetAccountList) -> None: ...


class DeclaredCompetitorsRepository(Protocol):
    async def current(self, workspace_id: UUID) -> DeclaredCompetitors | None:
        """The declaration in force, or ``None`` when nothing has been declared.

        **`None` and an empty declaration are different answers**, and both are
        legitimate: nobody has said anything, versus somebody said *"we do not
        track competitors"*. A caller that collapses them reports an empty
        result where the truth is an empty input.
        """
        ...

    async def save(self, competitors: DeclaredCompetitors) -> None: ...
