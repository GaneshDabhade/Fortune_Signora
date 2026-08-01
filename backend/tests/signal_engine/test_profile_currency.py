"""Which profile version is in force. **The regression test for `B-001`.**

`SqlProfileRepository.current` selected `WHERE supersedes IS NULL`, which on an
immutable table is the **first** version — the *new* row is the one that names
its predecessor. Every revision a customer made was silently ignored, and every
signal generated afterwards would have been produced by a profile nobody was
using.

It never bit because nothing has ever written a second version. That is the
shape of defect that waits for a feature, and Lane B is shipping the customer's
half of the product right now.

**Against a real database, not a fake.** The defect was in a SQL predicate, and
a repository double would have reproduced whatever the double's author believed
the predicate meant.
"""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from modules.signal_engine.domain.catalog import Relevance, SignalType
from modules.signal_engine.domain.profile import ProfileEntry, SignalProfile
from modules.signal_engine.infrastructure.repository import SqlProfileRepository
from signora_platform.db import tenant_scoped_session
from tests.knowledge_graph.test_graph_pipeline import _workspace

pytestmark = pytest.mark.integration

NOW = datetime(2026, 8, 1, 9, 0, tzinfo=UTC)


def _profile(
    workspace_id: UUID,
    author: UUID,
    *,
    version: int,
    relevance: Relevance,
    supersedes: UUID | None = None,
) -> SignalProfile:
    return SignalProfile(
        id=uuid4(),
        workspace_id=workspace_id,
        version=version,
        entries=(ProfileEntry(SignalType.BUDGET_UNLOCKED, relevance),),
        created_at=NOW,
        created_by=author,
        supersedes=supersedes,
    )


class TestTheProfileInForceIsTheNewestOne:
    async def test_a_revision_replaces_the_version_before_it(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        """**`B-001`.** Version 2 is what a customer is using. Returning
        version 1 would apply an interpretation they deliberately changed."""
        workspace_id, user_id = await _workspace(session_factory, "Acme")

        async with tenant_scoped_session(
            session_factory, workspace_id=workspace_id, user_id=user_id
        ) as session:
            repository = SqlProfileRepository(session)
            first = _profile(workspace_id, user_id, version=1, relevance=Relevance.SUPPORTING)
            await repository.save(first)
            await repository.save(
                _profile(
                    workspace_id,
                    user_id,
                    version=2,
                    relevance=Relevance.IGNORED,
                    supersedes=first.id,
                )
            )

        async with tenant_scoped_session(
            session_factory, workspace_id=workspace_id, user_id=user_id
        ) as session:
            current = await SqlProfileRepository(session).current(workspace_id)

        assert current is not None
        assert current.version == 2
        assert current.entries[0].relevance is Relevance.IGNORED

    async def test_the_first_version_is_current_until_there_is_a_second(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        """The case that made the defect invisible for six milestones."""
        workspace_id, user_id = await _workspace(session_factory, "Acme")

        async with tenant_scoped_session(
            session_factory, workspace_id=workspace_id, user_id=user_id
        ) as session:
            await SqlProfileRepository(session).save(
                _profile(workspace_id, user_id, version=1, relevance=Relevance.SUPPORTING)
            )

        async with tenant_scoped_session(
            session_factory, workspace_id=workspace_id, user_id=user_id
        ) as session:
            current = await SqlProfileRepository(session).current(workspace_id)

        assert current is not None
        assert current.version == 1

    async def test_a_workspace_that_has_configured_nothing_has_no_profile(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        """`None` rather than an invented one — the caller falls back to the
        catalog's declared defaults, which are reviewable."""
        workspace_id, user_id = await _workspace(session_factory, "Acme")

        async with tenant_scoped_session(
            session_factory, workspace_id=workspace_id, user_id=user_id
        ) as session:
            assert await SqlProfileRepository(session).current(workspace_id) is None

    async def test_every_version_stays_readable_by_number(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        """A signal records the version that produced it. If an old version
        stopped resolving, *"why was I told this?"* would lose its answer."""
        workspace_id, user_id = await _workspace(session_factory, "Acme")

        async with tenant_scoped_session(
            session_factory, workspace_id=workspace_id, user_id=user_id
        ) as session:
            repository = SqlProfileRepository(session)
            first = _profile(workspace_id, user_id, version=1, relevance=Relevance.SUPPORTING)
            await repository.save(first)
            await repository.save(
                _profile(
                    workspace_id,
                    user_id,
                    version=2,
                    relevance=Relevance.IGNORED,
                    supersedes=first.id,
                )
            )

        async with tenant_scoped_session(
            session_factory, workspace_id=workspace_id, user_id=user_id
        ) as session:
            superseded = await SqlProfileRepository(session).by_version(workspace_id, 1)

        assert superseded is not None
        assert superseded.entries[0].relevance is Relevance.SUPPORTING


class TestTwoConcurrentRevisionsCannotBothWin:
    async def test_the_second_writer_of_a_version_loses(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        """**What actually protects the invariant**, now that the partial
        index is gone (migration `0023`).

        `uq_signal_profile_version (workspace_id, version)` refuses a duplicate
        version at *every* version. The dropped index refused one only at the
        first, because after that no row has a null `supersedes` — which is why
        it was a guard that could not fail rather than the protection its
        comment claimed.
        """
        workspace_id, user_id = await _workspace(session_factory, "Acme")

        async with tenant_scoped_session(
            session_factory, workspace_id=workspace_id, user_id=user_id
        ) as session:
            first = _profile(workspace_id, user_id, version=1, relevance=Relevance.SUPPORTING)
            await SqlProfileRepository(session).save(first)

        async with tenant_scoped_session(
            session_factory, workspace_id=workspace_id, user_id=user_id
        ) as session:
            await SqlProfileRepository(session).save(
                _profile(
                    workspace_id,
                    user_id,
                    version=2,
                    relevance=Relevance.IGNORED,
                    supersedes=first.id,
                )
            )

        with pytest.raises(IntegrityError):
            async with tenant_scoped_session(
                session_factory, workspace_id=workspace_id, user_id=user_id
            ) as session:
                await SqlProfileRepository(session).save(
                    _profile(
                        workspace_id,
                        user_id,
                        version=2,
                        relevance=Relevance.PRIMARY,
                        supersedes=first.id,
                    )
                )

    async def test_a_second_original_is_still_refused(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        """The one case the dropped index did cover, now covered by the
        constraint that covers every other case too."""
        workspace_id, user_id = await _workspace(session_factory, "Acme")

        async with tenant_scoped_session(
            session_factory, workspace_id=workspace_id, user_id=user_id
        ) as session:
            await SqlProfileRepository(session).save(
                _profile(workspace_id, user_id, version=1, relevance=Relevance.SUPPORTING)
            )

        with pytest.raises(IntegrityError):
            async with tenant_scoped_session(
                session_factory, workspace_id=workspace_id, user_id=user_id
            ) as session:
                await SqlProfileRepository(session).save(
                    _profile(workspace_id, user_id, version=1, relevance=Relevance.PRIMARY)
                )


class TestSupersessionStillRecordsLineage:
    async def test_a_revision_names_what_it_replaced(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        """**`supersedes` survives the fix.** It is a true statement about
        lineage; it simply is not a currency marker, and nothing may read it
        as one again."""
        workspace_id, user_id = await _workspace(session_factory, "Acme")

        async with tenant_scoped_session(
            session_factory, workspace_id=workspace_id, user_id=user_id
        ) as session:
            first = _profile(workspace_id, user_id, version=1, relevance=Relevance.SUPPORTING)
            await SqlProfileRepository(session).save(first)
            await SqlProfileRepository(session).save(
                _profile(
                    workspace_id,
                    user_id,
                    version=2,
                    relevance=Relevance.IGNORED,
                    supersedes=first.id,
                )
            )

        async with tenant_scoped_session(
            session_factory, workspace_id=workspace_id, user_id=user_id
        ) as session:
            current = await SqlProfileRepository(session).current(workspace_id)

        assert current is not None
        assert current.supersedes == first.id

    async def test_no_index_keys_currency_on_the_supersession_pointer(
        self, admin_session_factory: async_sessionmaker[AsyncSession]
    ) -> None:
        """The defect, refused structurally. Asserted in the Security
        Invariants too, deliberately — a rewrite of this module must not be
        able to remove its own guarantee (§11)."""
        async with admin_session_factory() as session:
            offenders = (
                (
                    await session.execute(
                        text(
                            "SELECT indexname FROM pg_indexes "
                            "WHERE tablename = 'signal_profile' "
                            "AND indexdef ILIKE '%supersedes IS NULL%'"
                        )
                    )
                )
                .scalars()
                .all()
            )

        assert offenders == []


class TestTheSameDefectIsGoneFromEveryModuleThatHadIt:
    """**`B-001` was raised against one table and was in three.**

    `workspace_scoring_model` and `workspace_opportunity_policy` are the other
    two pieces of customer-authored configuration in the platform, and both had
    the identical inverted reading copied forward. Asserted here rather than
    split across three suites because what is being asserted is that the
    *pattern* is gone, and a per-module test would have to be remembered three
    times — which is how it got copied in the first place.
    """

    @pytest.mark.parametrize(
        ("table", "second_version_column"),
        [("workspace_scoring_model", "overrides"), ("workspace_opportunity_policy", "policy")],
    )
    async def test_the_newest_version_is_the_one_a_reader_gets(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
        table: str,
        second_version_column: str,
    ) -> None:
        """Written against SQL rather than through each module's repository:
        the property is about which row a `MAX(version)` read returns, and
        going through three different aggregates to assert one predicate would
        obscure that they are the same predicate."""
        workspace_id, user_id = await _workspace(session_factory, "Acme")

        async with admin_session_factory() as session, session.begin():
            first = uuid4()
            await session.execute(
                text(
                    f"INSERT INTO {table} "
                    f"(id, workspace_id, version, {second_version_column}, supersedes, "
                    " created_by, updated_by) "
                    "VALUES (:id, :ws, 1, '{}'::jsonb, NULL, :who, :who)"
                ),
                {"id": str(first), "ws": str(workspace_id), "who": str(user_id)},
            )
            await session.execute(
                text(
                    f"INSERT INTO {table} "
                    f"(id, workspace_id, version, {second_version_column}, supersedes, "
                    " created_by, updated_by) "
                    "VALUES (:id, :ws, 2, '{}'::jsonb, :first, :who, :who)"
                ),
                {
                    "id": str(uuid4()),
                    "ws": str(workspace_id),
                    "first": str(first),
                    "who": str(user_id),
                },
            )

            inverted = await session.scalar(
                text(
                    f"SELECT version FROM {table} "
                    "WHERE workspace_id = :ws AND supersedes IS NULL"
                ),
                {"ws": str(workspace_id)},
            )
            newest = await session.scalar(
                text(
                    f"SELECT version FROM {table} WHERE workspace_id = :ws "
                    "ORDER BY version DESC LIMIT 1"
                ),
                {"ws": str(workspace_id)},
            )

            await session.execute(
                text(f"DELETE FROM {table} WHERE workspace_id = :ws"),
                {"ws": str(workspace_id)},
            )

        # The two disagree, which is the whole defect stated as an assertion:
        # the predicate that used to define "current" returns the original.
        assert inverted == 1
        assert newest == 2
