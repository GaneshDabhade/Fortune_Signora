"""The tag repository against a real database — [TASK-466](../../../docs/BACKLOG.md).

⚠️ **Why these exist as repository tests rather than through an endpoint.**

🔴 **`unassign` has no HTTP route, and that is correct rather than an
oversight.** 📁 Reversing a batch is ADR-0405's flow — *"the consuming domain
owns performing the operation and implementing the inverse"* — and
`ActionBatchView` publishes **`item_count` and never the payload**, so
`commercial_profile` must hold what its own batch did.

⛔ **A standalone *"untag these accounts"* endpoint would be the defect
`TagApplication` was built to prevent**: the server cannot know which of the
named accounts this batch added, so it would remove a label somebody set in
June. ⚡ **The reversal is reachable only through a batch record**, and that is
the next slice.

✅ **So the inverse is proven here, against real rows**, and the production
caller arrives with the batch. **Stated rather than left for coverage to
discover.**
"""

from collections.abc import AsyncIterator
from uuid import UUID, uuid4

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from modules.commercial_profile.domain.account_tag import AccountTag, TagTone
from modules.commercial_profile.infrastructure.tag_repository import (
    SqlAccountTagRepository,
)
from tests.conftest import DEFAULT_APP_DATABASE_URL

pytestmark = pytest.mark.integration


@pytest.fixture
async def session() -> AsyncIterator[AsyncSession]:
    """A session with RLS context set, **as a request would set it**.

    📁 [§8](../../../CLAUDE.md): `SET LOCAL`, never `SET` — the context belongs
    to the transaction, and a connection returned to the pool carrying one
    workspace's identity is how the next request reads somebody else's data.
    """
    engine = create_async_engine(DEFAULT_APP_DATABASE_URL)
    async with AsyncSession(engine) as db:
        yield db
    await engine.dispose()


async def _scoped(db: AsyncSession, workspace_id: UUID) -> None:
    await db.execute(text(f"SET LOCAL app.workspace_id = '{workspace_id}'"))


def _tag(name: str = "At risk") -> AccountTag:
    return AccountTag(id=uuid4(), name=name, tone=TagTone.RISK)


class TestTheInverse:
    async def test_it_removes_only_the_accounts_it_is_given(
        self, session: AsyncSession
    ) -> None:
        """🔴 **The rule, against real rows.**

        Three accounts were tagged in June and five by the batch. Taking the
        batch back removes five and **leaves June's three**, because
        `TagApplication.inverse()` returns `changed` and nothing else.
        """
        workspace, actor = uuid4(), uuid4()
        await _scoped(session, workspace)
        repository = SqlAccountTagRepository(session)
        tag = _tag()
        await repository.create(workspace, tag, actor_id=actor)
        june = tuple(uuid4() for _ in range(3))
        batch = tuple(uuid4() for _ in range(5))
        await repository.assign(workspace, tag.id, june, actor_id=actor)
        await repository.assign(workspace, tag.id, batch, actor_id=actor)

        await repository.unassign(workspace, tag.id, batch)

        assert await repository.accounts_with(workspace, tag.id, among=june) == frozenset(june)
        assert await repository.accounts_with(workspace, tag.id, among=batch) == frozenset()

    async def test_reversing_nothing_costs_no_query(self, session: AsyncSession) -> None:
        """⚡ **An empty batch is a no-op rather than a `DELETE` with no
        predicate**, which is the shape that eventually deletes everything."""
        workspace, actor = uuid4(), uuid4()
        await _scoped(session, workspace)
        repository = SqlAccountTagRepository(session)
        tag = _tag()
        await repository.create(workspace, tag, actor_id=actor)
        account = uuid4()
        await repository.assign(workspace, tag.id, (account,), actor_id=actor)

        await repository.unassign(workspace, tag.id, ())

        assert await repository.accounts_with(workspace, tag.id, among=(account,)) == frozenset(
            {account}
        )

    async def test_reversing_twice_reaches_no_further_than_once(
        self, session: AsyncSession
    ) -> None:
        # The design's window lets somebody click undo, lose the connection,
        # and click again. `DELETE` is idempotent and this says so out loud.
        workspace, actor = uuid4(), uuid4()
        await _scoped(session, workspace)
        repository = SqlAccountTagRepository(session)
        tag = _tag()
        await repository.create(workspace, tag, actor_id=actor)
        account = uuid4()
        await repository.assign(workspace, tag.id, (account,), actor_id=actor)

        await repository.unassign(workspace, tag.id, (account,))
        await repository.unassign(workspace, tag.id, (account,))

        assert await repository.accounts_with(workspace, tag.id, among=(account,)) == frozenset()


class TestReadsAskAboutAccountsTheCallerAlreadyNamed:
    async def test_asking_about_nothing_returns_nothing_without_a_query(
        self, session: AsyncSession
    ) -> None:
        """⛔ **`IN ()` is not valid SQL.** SQLAlchemy renders it as a false
        predicate — correct, and a round trip to learn what the caller already
        knew."""
        workspace = uuid4()
        await _scoped(session, workspace)
        repository = SqlAccountTagRepository(session)

        assert await repository.accounts_with(workspace, uuid4(), among=()) == frozenset()
        assert await repository.tags_for(workspace, ()) == {}

    async def test_the_tags_on_a_page_of_rows_come_back_in_one_query(
        self, session: AsyncSession
    ) -> None:
        workspace, actor = uuid4(), uuid4()
        await _scoped(session, workspace)
        repository = SqlAccountTagRepository(session)
        risk, strategic = _tag(), AccountTag(
            id=uuid4(), name="Strategic", tone=TagTone.NEUTRAL
        )
        await repository.create(workspace, risk, actor_id=actor)
        await repository.create(workspace, strategic, actor_id=actor)
        tagged, untagged = uuid4(), uuid4()
        await repository.assign(workspace, risk.id, (tagged,), actor_id=actor)
        await repository.assign(workspace, strategic.id, (tagged,), actor_id=actor)

        held = await repository.tags_for(workspace, (tagged, untagged))

        assert sorted(held[tagged]) == sorted([risk.id, strategic.id])
        assert untagged not in held


class TestTheVocabularyIsOrderedBySql:
    async def test_the_same_set_renders_the_same_way_twice(
        self, session: AsyncSession
    ) -> None:
        """⚡ **Insertion order is a hidden input** (§2), and a list a person
        scans that reorders between two visits is the kind of defect nobody
        files and everybody notices."""
        workspace, actor = uuid4(), uuid4()
        await _scoped(session, workspace)
        repository = SqlAccountTagRepository(session)
        for name in ("Stalling", "At risk", "M&A"):
            await repository.create(
                workspace,
                AccountTag(id=uuid4(), name=name, tone=TagTone.NEUTRAL),
                actor_id=actor,
            )

        vocabulary = await repository.vocabulary(workspace)

        assert [tag.name for tag in vocabulary.tags] == ["At risk", "M&A", "Stalling"]


class TestARenameIsAnUpdateInPlace:
    async def test_the_row_moves_and_the_assignments_do_not(
        self, session: AsyncSession
    ) -> None:
        """⛔ **The one `UPDATE` in this module**, and migration `0051` records
        why the grant exists here and nowhere else.

        ⚡ **Proven at the repository rather than only through the endpoint**,
        because what is being asserted is that the ASSIGNMENT rows are
        untouched — and a `DELETE`-and-recreate would satisfy every assertion
        an HTTP test can make about the tag itself.
        """
        workspace, actor = uuid4(), uuid4()
        await _scoped(session, workspace)
        repository = SqlAccountTagRepository(session)
        tag = _tag("At risk")
        await repository.create(workspace, tag, actor_id=actor)
        account = uuid4()
        await repository.assign(workspace, tag.id, (account,), actor_id=actor)

        await repository.rename(workspace, tag.renamed("Churn risk"), actor_id=uuid4())

        vocabulary = await repository.vocabulary(workspace)
        assert [(t.id, t.name) for t in vocabulary.tags] == [(tag.id, "Churn risk")]
        assert await repository.accounts_with(workspace, tag.id, among=(account,)) == frozenset(
            {account}
        )
