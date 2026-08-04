"""The one implementation of the claim read port.

Every query filters `workspace_id` explicitly even though RLS already
scopes the session. RLS is the authoritative control; the explicit filter
is defense in depth, per CLAUDE.md §8.
"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import func, select, tuple_
from sqlalchemy.ext.asyncio import AsyncSession

from modules.provider_normalization.domain.vocabulary import ClaimAttribute
from modules.provider_normalization.infrastructure.models import ClaimModel
from modules.provider_normalization.public.claims import ClaimView, NameMatch, SubjectRef


def _escape_like(text: str) -> str:
    """Neutralise the wildcards a customer did not know they typed.

    `_` and `%` are `LIKE` syntax, so an unescaped search for `Acme_Corp`
    matches `AcmeXCorp` and a search containing `%` matches every account in
    the workspace. The backslash is escaped first, or escaping the others
    would produce a dangling escape.
    """
    return text.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


def _view(row: ClaimModel) -> ClaimView:
    stored: dict[str, Any] = row.value
    return ClaimView(
        id=row.id,
        provider=row.provider,
        attribute=ClaimAttribute(row.attribute),
        value=stored.get("v"),
        observed_at=row.observed_at,
        subject_external_id=row.subject_external_id,
        subject_domain=row.subject_domain,
        subject_legal_name=row.subject_legal_name,
        payload_provenance=row.payload_provenance,
    )


class SqlClaimReader:
    def __init__(self, session: AsyncSession, *, workspace_id: UUID) -> None:
        self._session = session
        self._workspace_id = workspace_id

    async def for_record(self, raw_record_id: UUID) -> tuple[ClaimView, ...]:
        rows = await self._session.execute(
            select(ClaimModel)
            .where(
                ClaimModel.workspace_id == self._workspace_id,
                ClaimModel.raw_record_id == raw_record_id,
            )
            .order_by(ClaimModel.observed_at, ClaimModel.id)
        )
        return tuple(_view(row) for row in rows.scalars())

    async def for_subjects(
        self,
        subjects: Sequence[SubjectRef],
        *,
        attribute: ClaimAttribute | None = None,
    ) -> tuple[ClaimView, ...]:
        if not subjects:
            return ()

        statement = select(ClaimModel).where(
            ClaimModel.workspace_id == self._workspace_id,
            tuple_(ClaimModel.provider, ClaimModel.subject_external_id).in_(
                [(s.provider, s.provider_external_id) for s in subjects]
            ),
        )
        if attribute is not None:
            statement = statement.where(ClaimModel.attribute == attribute.value)

        # Ordered oldest-first so a consumer reading a claim set sees the
        # trajectory in the order it happened, rather than in whatever order
        # the planner returned rows.
        rows = await self._session.execute(
            statement.order_by(ClaimModel.observed_at, ClaimModel.id)
        )
        return tuple(_view(row) for row in rows.scalars())

    async def subjects_named_like(self, text: str, *, limit: int) -> tuple[NameMatch, ...]:
        pattern = f"%{_escape_like(text)}%"
        name = ClaimModel.value["v"].astext

        rows = await self._session.execute(
            select(ClaimModel.provider, ClaimModel.subject_external_id, name)
            .where(
                ClaimModel.workspace_id == self._workspace_id,
                ClaimModel.attribute == ClaimAttribute.LEGAL_NAME.value,
                # `escape` is not optional. Without it a customer searching for
                # a name containing `_` matches any character, and one
                # containing `%` matches everything in the workspace.
                name.ilike(pattern, escape="\\"),
            )
            .distinct()
            .order_by(name, ClaimModel.provider, ClaimModel.subject_external_id)
            .limit(limit)
        )
        # The matched name was always read — it is what `order_by` sorts on —
        # and was discarded one line later. Carrying it is what lets a caller
        # say *why* a row is in the list rather than only that it is.
        return tuple(
            NameMatch(
                subject=SubjectRef(provider=provider, provider_external_id=external_id),
                name=matched,
            )
            for provider, external_id, matched in rows.all()
        )

    async def latest_observed_at(
        self, subjects: Sequence[SubjectRef]
    ) -> dict[SubjectRef, datetime]:
        if not subjects:
            return {}

        rows = await self._session.execute(
            select(
                ClaimModel.provider,
                ClaimModel.subject_external_id,
                func.max(ClaimModel.observed_at),
            )
            .where(
                ClaimModel.workspace_id == self._workspace_id,
                tuple_(ClaimModel.provider, ClaimModel.subject_external_id).in_(
                    [(s.provider, s.provider_external_id) for s in subjects]
                ),
            )
            .group_by(ClaimModel.provider, ClaimModel.subject_external_id)
        )
        return {
            SubjectRef(provider=provider, provider_external_id=external_id): observed_at
            for provider, external_id, observed_at in rows.all()
        }
