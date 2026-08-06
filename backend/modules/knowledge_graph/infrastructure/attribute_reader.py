"""The implementation of `AccountAttributesReader`.

**One binding read, one claim read, three resolutions.** The expensive part of
answering this question is finding which provider subjects an entity is bound
to; doing that once and filtering in memory is what makes a single call cheaper
than three, and it is also what makes the three answers describe **one state of
the graph** rather than three moments.
"""

from __future__ import annotations

from typing import Sequence
from uuid import UUID

from modules.knowledge_graph.application.ports import GraphRepository
from modules.knowledge_graph.domain.identity import IdentityBinding
from modules.knowledge_graph.application.queries import _subjects
from modules.knowledge_graph.domain.attributes import resolve_value
from modules.knowledge_graph.public.attributes import AccountAttributes
from modules.provider_normalization.public import ClaimAttribute, ClaimReader, ClaimView


class SqlAccountAttributesReader:
    """Implements `AccountAttributesReader` for the composition root to inject."""

    def __init__(self, *, repository: GraphRepository, claims: ClaimReader) -> None:
        self._repository = repository
        self._claims = claims

    async def for_accounts(
        self, workspace_id: UUID, entity_ids: Sequence[UUID]
    ) -> dict[UUID, AccountAttributes]:
        """**Two queries for any number of accounts, not two per account.**

        The bindings for every requested entity come back in one read and the
        claims for every resulting subject in a second, then the claims are
        grouped in memory. A loop over `for_account` would be 2n queries, which
        is the N+1 §14 forbids — and the backtest that needed this reads every
        decided account in a workspace.
        """
        if not entity_ids:
            return {}
        bindings = await self._repository.bindings_for_entities(workspace_id, tuple(entity_ids))
        # The read returns one flat tuple; group it by the entity each binding
        # resolved to, so a claim is never attributed to the wrong account.
        grouped: dict[UUID, list[IdentityBinding]] = {}
        for binding in bindings:
            if binding.entity_id is not None:
                grouped.setdefault(binding.entity_id, []).append(binding)
        subjects = {
            entity_id: _subjects(tuple(found)) for entity_id, found in grouped.items()
        }
        every = [s for group in subjects.values() for s in group]
        claims = await self._claims.for_subjects(every) if every else ()
        by_subject: dict[tuple[str, str], list[ClaimView]] = {}
        for claim in claims:
            by_subject.setdefault((claim.provider, claim.subject_external_id), []).append(claim)

        answered: dict[UUID, AccountAttributes] = {}
        for entity_id in entity_ids:
            mine = tuple(
                claim
                for subject in subjects.get(entity_id, [])
                for claim in by_subject.get((subject.provider, subject.provider_external_id), [])
            )
            answered[entity_id] = AccountAttributes(
                entity_id=entity_id,
                industry=resolve_value(_of(mine, ClaimAttribute.INDUSTRY)),
                country=resolve_value(_of(mine, ClaimAttribute.COUNTRY)),
                employee_count=resolve_value(_of(mine, ClaimAttribute.EMPLOYEE_COUNT)),
            )
        return answered

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
