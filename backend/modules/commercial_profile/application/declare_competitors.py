"""Declaring who the workspace is up against.

The sixth write in the module, and the same discipline as the first five: it
takes the competitor list a customer means to have and records it as a new
version. It never patches, merges, reconciles — and it applies the list to
nothing.

### Why the whole list arrives, not a change to it

The aggregate is the declaration, so a version is a complete statement.
Accepting *"add this competitor"* would make the stored version depend on what
was there when the request arrived, which is exactly the lost update two
people editing the same page produce.

### Why nothing is checked against the catalog

The three product-citing declarations share `sold_products` because a product
id must resolve to something the customer sells. **A competitor is not a
product of theirs and not an entity this module can see** — the import
contract *"commercial_profile declares; it never reads the pipeline"* is what
makes that a boundary rather than an omission. The name is recorded as typed
and resolved by whoever consumes it.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID, uuid4

from modules.commercial_profile.application.ports import DeclaredCompetitorsRepository
from modules.commercial_profile.domain.competitors import (
    Competitor,
    DeclaredCompetitors,
    first_competitors,
)
from modules.commercial_profile.domain.declaration import (
    UNDECLARED,
    CommercialProfileError,
)


class CompetitorsVersionConflictError(CommercialProfileError):
    """Somebody else changed the competitor list since this caller read it."""

    def __init__(self, *, expected: int, actual: int) -> None:
        self.expected = expected
        self.actual = actual
        super().__init__(
            f"your competitor list is at version {actual}, not {expected}. Somebody else "
            "changed it since you opened this page — reload to see their version before "
            "saving yours, so neither of you loses work."
        )


@dataclass(frozen=True, slots=True)
class DeclareCompetitorsInput:
    workspace_id: UUID
    competitors: tuple[Competitor, ...]
    #: The version the caller believes it is replacing. `0` declares the first
    #: list, and is the only value that may be sent by a caller who has never
    #: read one.
    expected_version: int
    #: Taken from the verified caller by the interface layer. There is no field
    #: a request could use to name somebody else as the author.
    actor_id: UUID


class DeclareCompetitors:
    def __init__(self, *, competitors: DeclaredCompetitorsRepository) -> None:
        self._competitors = competitors

    async def execute(self, request: DeclareCompetitorsInput) -> DeclaredCompetitors:
        current = await self._competitors.current(request.workspace_id)
        actual = current.version if current is not None else UNDECLARED
        if actual != request.expected_version:
            raise CompetitorsVersionConflictError(
                expected=request.expected_version, actual=actual
            )

        now = datetime.now(UTC)
        declared = (
            first_competitors(
                request.workspace_id,
                request.competitors,
                id=uuid4(),
                by=request.actor_id,
                now=now,
            )
            if current is None
            else current.revise(
                request.competitors,
                id=uuid4(),
                by=request.actor_id,
                now=now,
            )
        )
        await self._competitors.save(declared)
        return declared
