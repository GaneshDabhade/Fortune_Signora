"""The published read side of the ideal customer.

**The module's third published read, and the one sixteen consumers were
waiting for** ([443](../../../../docs/architecture/443-account-matching-capability.md)).
Thirteen views were published before it and not one carried the criteria, so
until now no module could ask what a customer's ideal customer looks like —
which is why a capability nobody could build accumulated dependents.

Separated from `repository.py` on the same terms as the target account and
competitor readers: everything there serves this module's own use cases and
may change freely; everything here is a contract with somebody else and may
not.

**The mapping is the boundary.** A consumer receives `IcpView`, never
`IcpDeclaration` — so this module's validation rules, its `EmployeeRange`
constructor and any future refactor of the aggregate stay entirely its own.
"""

from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from modules.commercial_profile.infrastructure.models import IcpDeclarationModel
from modules.commercial_profile.infrastructure.versioned import latest
from modules.commercial_profile.public import IcpCriteriaView, IcpView


def _bounds(raw: dict[str, Any]) -> tuple[int | None, int | None]:
    """The employee range, flattened to two integers.

    **Absent and unbounded are the same fact here and different from zero.**
    A declaration with no size preference stores no `employees` key at all;
    one that says *"anything over 500"* stores a minimum and no maximum. Both
    arrive as `None` on the side that was not stated, which is what the view
    documents — and neither is `0`, which would mean *"a company with no
    employees"* and match nothing.
    """
    employees = raw.get("employees")
    if not isinstance(employees, dict):
        return None, None
    minimum = employees.get("minimum")
    maximum = employees.get("maximum")
    return (
        minimum if isinstance(minimum, int) else None,
        maximum if isinstance(maximum, int) else None,
    )


class SqlIcpReader:
    """Implements `IcpReader` for the composition root to inject."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def current(self, workspace_id: UUID) -> IcpView | None:
        """The declaration in force, or ``None`` when there has never been one.

        **`None` rather than an empty view**, on the same terms as every other
        reader in this module: a workspace that has never described who buys
        from it is in a state to wait in, not one to reason from.
        """
        result = await self._session.execute(latest(IcpDeclarationModel, workspace_id))
        row = result.scalar_one_or_none()
        if row is None:
            return None

        criteria = []
        for raw in row.profiles:
            minimum, maximum = _bounds(raw)
            criteria.append(
                IcpCriteriaView(
                    product_id=UUID(raw["product_id"]),
                    # Tuples rather than the stored lists: a view a consumer
                    # can append to is a view two consumers can disagree about.
                    industries=tuple(raw.get("industries", ())),
                    countries=tuple(raw.get("countries", ())),
                    employees_minimum=minimum,
                    employees_maximum=maximum,
                )
            )

        return IcpView(
            workspace_id=row.workspace_id,
            version=row.version,
            criteria=tuple(criteria),
        )
