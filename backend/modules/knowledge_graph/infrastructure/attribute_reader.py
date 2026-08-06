"""The implementation of `AccountAttributesReader`.

**One binding read, one claim read, three resolutions.** The expensive part of
answering this question is finding which provider subjects an entity is bound
to; doing that once and filtering in memory is what makes a single call cheaper
than three, and it is also what makes the three answers describe **one state of
the graph** rather than three moments.
"""

from __future__ import annotations

from uuid import UUID

from modules.knowledge_graph.application.ports import GraphRepository
from modules.knowledge_graph.application.queries import _subjects
from modules.knowledge_graph.domain.attributes import resolve_value
from modules.knowledge_graph.public.attributes import AccountAttributes
from modules.provider_normalization.public import ClaimAttribute, ClaimReader, ClaimView


class SqlAccountAttributesReader:
    """Implements `AccountAttributesReader` for the composition root to inject."""

    def __init__(self, *, repository: GraphRepository, claims: ClaimReader) -> None:
        self._repository = repository
        self._claims = claims

    async def for_account(self, workspace_id: UUID, entity_id: UUID) -> AccountAttributes:
        bindings = await self._repository.bindings_for_entity(workspace_id, entity_id)
        # **Every claim once, not one query per attribute.** Three reads would
        # be three round trips and three moments, and an account whose industry
        # was resolved before a sync and whose country was resolved after it
        # would be described by a state that never existed.
        claims = await self._claims.for_subjects(_subjects(bindings))
        return AccountAttributes(
            entity_id=entity_id,
            industry=resolve_value(_of(claims, ClaimAttribute.INDUSTRY)),
            country=resolve_value(_of(claims, ClaimAttribute.COUNTRY)),
            employee_count=resolve_value(_of(claims, ClaimAttribute.EMPLOYEE_COUNT)),
        )


def _of(claims: tuple[ClaimView, ...], attribute: ClaimAttribute) -> tuple[ClaimView, ...]:
    return tuple(claim for claim in claims if claim.attribute is attribute)
