"""SQLAlchemy models for the People context.

**`infrastructure/` only**, as everywhere: `domain/`, `application/` and
`public/` never import this file, so the aggregate stays free of the table it
happens to be stored in.
"""

from __future__ import annotations

from datetime import date
from uuid import UUID

from sqlalchemy import CheckConstraint, Date, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from signora_platform.db.base import AuditMixin, Base, TimestampMixin, WorkspaceScopedMixin


class PersonModel(Base, WorkspaceScopedMixin, TimestampMixin, AuditMixin):
    """An identity and its tenant. **Deliberately nothing else** — every
    attribute anybody would want either belongs to an affiliation or does not
    exist in this repository at all (C-221)."""

    __tablename__ = "person"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True)


class AffiliationModel(Base, WorkspaceScopedMixin, TimestampMixin, AuditMixin):
    """**person × company × title × interval.**

    `ended_on` is nullable and `NULL` means *no departure has been observed* —
    not *"they still work there"*. There is no `current_employer` column here
    or anywhere, which is the whole point of the table (ADR-0400).
    """

    __tablename__ = "affiliation"
    __table_args__ = (
        CheckConstraint(
            "ended_on IS NULL OR ended_on >= started_on",
            name="ck_affiliation_ends_after_it_starts",
        ),
        CheckConstraint("length(trim(title)) > 0", name="ck_affiliation_title_is_not_blank"),
    )

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True)
    person_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("person.id", ondelete="CASCADE"), nullable=False
    )
    #: The Knowledge Graph's company id, carried and never constrained — a
    #: foreign key here would make one bounded context's migration depend on
    #: another's table shape.
    company_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    title: Mapped[str] = mapped_column(String(length=200), nullable=False)
    seniority: Mapped[str] = mapped_column(String(length=64), nullable=False)
    started_on: Mapped[date] = mapped_column(Date(), nullable=False)
    ended_on: Mapped[date | None] = mapped_column(Date(), nullable=True)
