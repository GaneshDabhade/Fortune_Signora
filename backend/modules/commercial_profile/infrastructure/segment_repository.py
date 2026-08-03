"""Reading segments out of four tables as one row.

**Three joins the read model deliberately keeps out of the application layer.**
A segment's current version is the highest `version`, its state is the latest
`sequence`, and its products hang off that version — three "latest of" rules
that belong in one place rather than in whichever caller reassembles them.
"""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import Select, and_, func, select, tuple_
from sqlalchemy.ext.asyncio import AsyncSession

from modules.commercial_profile.application.segment_queries import SegmentSummary
from modules.commercial_profile.domain.icp import EmployeeRange
from modules.commercial_profile.domain.segment import SegmentCriteria, SegmentState
from modules.commercial_profile.infrastructure.models import (
    SegmentModel,
    SegmentProductModel,
    SegmentStateModel,
    SegmentVersionModel,
)
from signora_platform.pagination import CursorPosition


def criteria_from_row(raw: dict[str, object]) -> SegmentCriteria:
    """Rebuild criteria from the stored document.

    Public because the migration writes this shape and a test has to be able
    to assert the round trip without reaching into a private helper.
    """
    employees = raw.get("employees")
    size: EmployeeRange | None = None
    if isinstance(employees, dict):
        minimum, maximum = employees.get("minimum"), employees.get("maximum")
        size = EmployeeRange(
            minimum=minimum if isinstance(minimum, int) else None,
            maximum=maximum if isinstance(maximum, int) else None,
        )
    industries = raw.get("industries")
    countries = raw.get("countries")
    return SegmentCriteria(
        industries=tuple(str(v) for v in industries) if isinstance(industries, list) else (),
        countries=tuple(str(v) for v in countries) if isinstance(countries, list) else (),
        employees=size,
        notes=str(raw.get("notes") or ""),
    )


def _current_version(workspace_id: UUID) -> Select[tuple[UUID, int]]:
    """The highest version of every segment in a workspace.

    **The rule `versioned.latest()` expresses for the single-row declarations**,
    applied per segment rather than per workspace — which is why it is here
    rather than a fourth caller of that helper.
    """
    return (
        select(
            SegmentVersionModel.segment_id.label("segment_id"),
            func.max(SegmentVersionModel.version).label("version"),
        )
        .where(SegmentVersionModel.workspace_id == workspace_id)
        .group_by(SegmentVersionModel.segment_id)
    )


def _current_state(workspace_id: UUID) -> Select[tuple[UUID, int]]:
    """The latest transition of every segment. The status **is** the log."""
    return (
        select(
            SegmentStateModel.segment_id.label("segment_id"),
            func.max(SegmentStateModel.sequence).label("sequence"),
        )
        .where(SegmentStateModel.workspace_id == workspace_id)
        .group_by(SegmentStateModel.segment_id)
    )


class SqlSegmentReader:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def page(
        self,
        *,
        workspace_id: UUID,
        include_archived: bool,
        after: CursorPosition | None,
        limit: int,
    ) -> list[SegmentSummary]:
        versions = _current_version(workspace_id).subquery()
        states = _current_state(workspace_id).subquery()

        statement = (
            select(
                SegmentModel.id,
                SegmentModel.created_at,
                SegmentVersionModel.id.label("version_id"),
                SegmentVersionModel.version,
                SegmentVersionModel.name,
                SegmentVersionModel.created_at.label("published_at"),
                SegmentVersionModel.created_by.label("published_by"),
                SegmentStateModel.state,
                SegmentStateModel.occurred_at,
                SegmentStateModel.actor_id,
            )
            .join(versions, versions.c.segment_id == SegmentModel.id)
            .join(
                SegmentVersionModel,
                and_(
                    SegmentVersionModel.segment_id == SegmentModel.id,
                    SegmentVersionModel.version == versions.c.version,
                ),
            )
            .join(states, states.c.segment_id == SegmentModel.id)
            .join(
                SegmentStateModel,
                and_(
                    SegmentStateModel.segment_id == SegmentModel.id,
                    SegmentStateModel.sequence == states.c.sequence,
                ),
            )
            # Filtered explicitly beside RLS, which is the authoritative
            # control — defence in depth, §8.
            .where(SegmentModel.workspace_id == workspace_id)
            .order_by(SegmentModel.created_at.desc(), SegmentModel.id.desc())
            .limit(limit)
        )
        if not include_archived:
            statement = statement.where(SegmentStateModel.state != SegmentState.ARCHIVED.value)
        if after is not None:
            # Row-wise comparison rather than an OR of two predicates: one
            # expression the planner drives off the index, and one that cannot
            # be got subtly wrong at a tie.
            statement = statement.where(
                tuple_(SegmentModel.created_at, SegmentModel.id) < (after.created_at, after.id)
            )

        rows = (await self._session.execute(statement)).all()
        if not rows:
            return []

        products = await self._products_for({row.version_id for row in rows}, workspace_id)
        return [
            SegmentSummary(
                id=row.id,
                name=row.name,
                state=SegmentState(row.state),
                version=row.version,
                product_ids=tuple(products.get(row.version_id, ())),
                # **The later of the two**, because either can be the last
                # thing that happened: publishing a version, or archiving.
                last_changed_at=max(row.published_at, row.occurred_at),
                last_changed_by=(
                    row.published_by if row.published_at >= row.occurred_at else row.actor_id
                ),
                created_at=row.created_at,
            )
            for row in rows
        ]

    async def _products_for(
        self, version_ids: set[UUID], workspace_id: UUID
    ) -> dict[UUID, list[UUID]]:
        """One query for the whole page.

        **Not one per row.** A products-per-segment lookup inside the loop is
        the N+1 §14 calls a defect at write time rather than a later
        optimization.
        """
        rows = (
            await self._session.execute(
                select(SegmentProductModel.version_id, SegmentProductModel.product_id)
                .where(
                    SegmentProductModel.workspace_id == workspace_id,
                    SegmentProductModel.version_id.in_(version_ids),
                )
                .order_by(SegmentProductModel.created_at, SegmentProductModel.product_id)
            )
        ).all()
        grouped: dict[UUID, list[UUID]] = {}
        for version_id, product_id in rows:
            grouped.setdefault(version_id, []).append(product_id)
        return grouped
