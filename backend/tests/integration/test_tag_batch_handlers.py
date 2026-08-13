"""The tag batch handlers, driven by real envelopes — [TASK-466](../../../docs/BACKLOG.md).

🔴 **The wiring the unit tests cannot reach.** Those prove the use cases; these
prove the handler opens a **tenant-scoped** session, reads `batch_id` out of a
payload it did not construct, and commits.

⚠️ **And the tenancy half is the one worth the round trip**: a handler that
forgot `tenant_scoped_session` would write nothing and raise nothing, because
RLS would simply match no rows — 📁 **a silent no-op is the worst possible
failure mode for an undo.**
"""

from collections.abc import AsyncIterator
from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from modules.commercial_profile.domain.account_tag import AccountTag, TagBatch, TagTone
from modules.commercial_profile.infrastructure.composition import (
    build_apply_tag_batch,
    build_reverse_tag_batch,
)
from modules.commercial_profile.infrastructure.tag_repository import (
    SqlAccountTagRepository,
    SqlTagBatchStore,
)
from modules.commercial_profile.interface.tag_batch_handlers import (
    apply_tag_batch,
    reverse_tag_batch,
)
from signora_platform.event_bus import EventEnvelope
from tests.conftest import DEFAULT_APP_DATABASE_URL

pytestmark = pytest.mark.integration


@pytest.fixture
async def sessions() -> AsyncIterator[async_sessionmaker[AsyncSession]]:
    engine = create_async_engine(DEFAULT_APP_DATABASE_URL)
    yield async_sessionmaker(engine, expire_on_commit=False)
    await engine.dispose()


def _envelope(workspace_id: UUID, batch_id: UUID, event_type: str) -> EventEnvelope:
    """**Built by hand, exactly as the relay would hand it over** — and the
    payload carries `batch_id` and nothing else the handler trusts."""
    payload: dict[str, Any] = {"batch_id": str(batch_id), "name": "Tag 8 companies"}
    return EventEnvelope(
        event_id=uuid4(),
        event_type=event_type,
        event_version=1,
        workspace_id=workspace_id,
        occurred_at=datetime(2026, 8, 13, 9, 14, tzinfo=UTC),
        producer_module="action_batch",
        correlation_id=uuid4(),
        causation_id=None,
        payload=payload,
    )


async def _seed(
    sessions: async_sessionmaker[AsyncSession],
    workspace: UUID,
    actor: UUID,
    *,
    requested: tuple[UUID, ...],
    already_tagged: tuple[UUID, ...] = (),
) -> tuple[UUID, AccountTag]:
    """Create a tag and a proposed batch, **the way the propose step will**."""
    async with sessions() as session:
        await session.execute(text(f"SET LOCAL app.workspace_id = '{workspace}'"))
        tags = SqlAccountTagRepository(session)
        store = SqlTagBatchStore(session)
        tag = AccountTag(id=uuid4(), name="At risk", tone=TagTone.RISK)
        await tags.create(workspace, tag, actor_id=actor)
        if already_tagged:
            await tags.assign(workspace, tag.id, already_tagged, actor_id=actor)
        batch_id = uuid4()
        await store.record(
            workspace,
            TagBatch(batch_id=batch_id, tag_id=tag.id, requested=requested),
            actor_id=actor,
        )
        await session.commit()
    return batch_id, tag


async def _tagged(
    sessions: async_sessionmaker[AsyncSession],
    workspace: UUID,
    tag_id: UUID,
    among: tuple[UUID, ...],
) -> frozenset[UUID]:
    async with sessions() as session:
        await session.execute(text(f"SET LOCAL app.workspace_id = '{workspace}'"))
        return await SqlAccountTagRepository(session).accounts_with(
            workspace, tag_id, among=among
        )


class TestTheAppliedHandler:
    async def test_it_tags_what_the_batch_proposed(
        self, sessions: async_sessionmaker[AsyncSession]
    ) -> None:
        workspace, actor = uuid4(), uuid4()
        accounts = (uuid4(), uuid4(), uuid4())
        batch_id, tag = await _seed(sessions, workspace, actor, requested=accounts)

        await apply_tag_batch(
            _envelope(workspace, batch_id, "action_batch.applied"),
            session_factory=sessions,
            apply=build_apply_tag_batch,
        )

        assert await _tagged(sessions, workspace, tag.id, accounts) == frozenset(accounts)

    async def test_an_event_for_somebody_else_s_batch_is_silent(
        self, sessions: async_sessionmaker[AsyncSession]
    ) -> None:
        """⛔ **The ordinary case, not an error.** The Action Batch is a shared
        lifecycle; raising would put a permanent failure into a retry loop that
        can never succeed."""
        await apply_tag_batch(
            _envelope(uuid4(), uuid4(), "action_batch.applied"),
            session_factory=sessions,
            apply=build_apply_tag_batch,
        )

    async def test_a_second_delivery_does_not_overwrite_the_record(
        self, sessions: async_sessionmaker[AsyncSession]
    ) -> None:
        """⚠️ **§9 idempotence, and the harm is not a duplicate row.**

        🔴 **It is that a second application overwrites the record the reversal
        reads** — so an undo would then operate on the wrong set.
        """
        workspace, actor = uuid4(), uuid4()
        june = (uuid4(), uuid4())
        now = (uuid4(), uuid4(), uuid4())
        batch_id, tag = await _seed(
            sessions, workspace, actor, requested=(*june, *now), already_tagged=june
        )
        envelope = _envelope(workspace, batch_id, "action_batch.applied")
        await apply_tag_batch(
            envelope, session_factory=sessions, apply=build_apply_tag_batch
        )

        await apply_tag_batch(
            envelope, session_factory=sessions, apply=build_apply_tag_batch
        )

        async with sessions() as session:
            await session.execute(text(f"SET LOCAL app.workspace_id = '{workspace}'"))
            recorded = await SqlTagBatchStore(session).get(workspace, batch_id)
        assert recorded is not None and recorded.applied is not None
        # ⚡ **Still the three the batch changed** — not five, and not zero.
        assert set(recorded.applied.changed) == set(now)


class TestTheReversedHandler:
    async def test_it_leaves_the_accounts_that_were_tagged_first(
        self, sessions: async_sessionmaker[AsyncSession]
    ) -> None:
        """🔴 **The whole row's hardest guarantee, end to end through events
        and a real database.**"""
        workspace, actor = uuid4(), uuid4()
        june = (uuid4(), uuid4(), uuid4())
        now = (uuid4(), uuid4(), uuid4(), uuid4(), uuid4())
        batch_id, tag = await _seed(
            sessions, workspace, actor, requested=(*june, *now), already_tagged=june
        )
        await apply_tag_batch(
            _envelope(workspace, batch_id, "action_batch.applied"),
            session_factory=sessions,
            apply=build_apply_tag_batch,
        )

        await reverse_tag_batch(
            _envelope(workspace, batch_id, "action_batch.reversed"),
            session_factory=sessions,
            reverse=build_reverse_tag_batch,
        )

        assert await _tagged(sessions, workspace, tag.id, june) == frozenset(june)
        assert await _tagged(sessions, workspace, tag.id, now) == frozenset()

    async def test_reversing_a_batch_that_never_applied_touches_nothing(
        self, sessions: async_sessionmaker[AsyncSession]
    ) -> None:
        """⛔ **A handler that fell back to `requested` would untag accounts
        this batch never touched.**"""
        workspace, actor = uuid4(), uuid4()
        accounts = (uuid4(), uuid4())
        batch_id, tag = await _seed(
            sessions, workspace, actor, requested=accounts, already_tagged=accounts
        )

        await reverse_tag_batch(
            _envelope(workspace, batch_id, "action_batch.reversed"),
            session_factory=sessions,
            reverse=build_reverse_tag_batch,
        )

        assert await _tagged(sessions, workspace, tag.id, accounts) == frozenset(accounts)

    async def test_an_event_for_somebody_else_s_batch_is_silent(
        self, sessions: async_sessionmaker[AsyncSession]
    ) -> None:
        await reverse_tag_batch(
            _envelope(uuid4(), uuid4(), "action_batch.reversed"),
            session_factory=sessions,
            reverse=build_reverse_tag_batch,
        )
