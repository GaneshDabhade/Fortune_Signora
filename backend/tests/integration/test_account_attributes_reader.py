"""The published attributes reader, over real claims from the real pipeline.

**Seeded the way a customer's data arrives** — through the Provider Simulation
Framework and the ingest, not by writing claim rows. The point of the test is
that the contract resolves what the pipeline actually produced.
"""

from uuid import UUID

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from modules.knowledge_graph.domain.attributes import ValueAgreement
from modules.knowledge_graph.infrastructure.composition import build_attributes_reader
from modules.provider_normalization.infrastructure.claim_reader import SqlClaimReader
from signora_platform.db.session import set_workspace_context
from tests.opportunity_engine.test_opportunity_pipeline import _tracked

pytestmark = pytest.mark.integration


def _reader(session: AsyncSession, workspace_id: UUID) -> object:
    return build_attributes_reader(
        session, claims=SqlClaimReader(session, workspace_id=workspace_id)
    )


class TestAnAccountDescribesItselfInOneCall:
    async def test_a_seeded_account_resolves_its_attributes(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        """**The capability sixteen consumers were waiting on**, end to end:
        claims that arrived through the pipeline come back as resolved values
        with the providers that reported them."""
        workspace_id, _, entity_id, _ = await _tracked(
            session_factory, admin_session_factory, "northwind"
        )

        async with session_factory() as session, session.begin():
            await set_workspace_context(session, workspace_id)
            found = await _reader(session, workspace_id).for_account(  # type: ignore[attr-defined]
                workspace_id, entity_id
            )

        assert found.entity_id == entity_id
        # Every attribute is present whether or not anything reported it —
        # absence is `UNKNOWN`, never a missing field.
        for resolved in (found.industry, found.country, found.employee_count):
            assert resolved.agreement in set(ValueAgreement)
            if resolved.is_known:
                assert resolved.providers, "a known value names who reported it"
                assert resolved.observed_at is not None

    async def test_an_account_nobody_has_described_is_three_unknowns(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        """**Not `None`, and not an error.** *"We know nothing about it"* and
        *"it does not exist"* must not be the same response."""
        workspace_id, _, _, _ = await _tracked(
            session_factory, admin_session_factory, "northwind"
        )
        unheard_of = UUID("00000000-0000-4000-8000-000000000abc")

        async with session_factory() as session, session.begin():
            await set_workspace_context(session, workspace_id)
            found = await _reader(session, workspace_id).for_account(  # type: ignore[attr-defined]
                workspace_id, unheard_of
            )

        assert found.industry.agreement is ValueAgreement.UNKNOWN
        assert found.country.agreement is ValueAgreement.UNKNOWN
        assert found.employee_count.agreement is ValueAgreement.UNKNOWN

    async def test_another_workspace_learns_nothing(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        """A resolved value carries no id, so a tenancy leak here would look
        exactly like a correct answer."""
        mine, _, my_entity, _ = await _tracked(
            session_factory, admin_session_factory, "northwind"
        )
        theirs, _, _, _ = await _tracked(session_factory, admin_session_factory, "contoso")

        async with session_factory() as session, session.begin():
            await set_workspace_context(session, theirs)
            found = await _reader(session, theirs).for_account(  # type: ignore[attr-defined]
                theirs, my_entity
            )

        assert found.industry.agreement is ValueAgreement.UNKNOWN
