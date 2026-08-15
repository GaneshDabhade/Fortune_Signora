"""The seam between an approved batch and the domain that applies it.

**Four handlers, and none of them had a test** — the two ADR-0411 owner
handlers from [TASK-1479](../../../docs/BACKLOG.md) ⓶a and the two segment
handlers from ⓶b. **`tag_batch_handlers.py` sat at 67%**, and the uncovered
part was the seam itself: *"the subscription is wired"* rested on reading it.

🔴 **The use cases' own decisions are tested elsewhere.** These assert only
what the seam is responsible for, and it is exactly three things:

**which field it reads from the envelope · which it does NOT trust · that it
opens its own tenant-scoped session.**

⛔ **All three would break a subscription silently without breaking a single
application-layer test**, which is why this file exists at all.

**No database.** `tenant_scoped_session` is handed a factory yielding a
recorded double, because what these functions do with a session is pass it to
a builder — and a real one would be testing PostgreSQL rather than the seam.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from typing import Any
from unittest.mock import patch
from uuid import UUID, uuid4

import pytest

from modules.commercial_profile.interface import tag_batch_handlers
from modules.commercial_profile.interface.tag_batch_handlers import (
    SYSTEM_USER_ID,
    apply_assignment_batch,
    apply_segment_batch,
    reverse_assignment_batch,
    reverse_segment_batch,
)
from signora_platform.event_bus import EventEnvelope

WORKSPACE = UUID("11111111-1111-4111-8111-111111111111")
BATCH = UUID("33333333-3333-4333-8333-333333333333")
SESSION = object()


def _envelope(*, batch_id: UUID = BATCH, extra: dict[str, Any] | None = None) -> EventEnvelope:
    return EventEnvelope(
        event_id=uuid4(),
        event_type="action_batch.applied",
        event_version=1,
        workspace_id=WORKSPACE,
        occurred_at=datetime(2026, 8, 15, tzinfo=UTC),
        producer_module="action_batch",
        correlation_id=uuid4(),
        causation_id=None,
        # ⚡ **A `str`, as JSON delivers it.** The handler coerces, and asserting
        # that here is the difference between a test that passes on a Python
        # object and a handler that works on the wire.
        payload={"batch_id": str(batch_id), **(extra or {})},
    )


class _Scope:
    """What `tenant_scoped_session` was asked to open."""

    def __init__(self) -> None:
        self.opened: list[dict[str, Any]] = []

    @asynccontextmanager
    async def __call__(self, factory: Any, **kwargs: Any) -> AsyncIterator[Any]:
        self.opened.append(kwargs)
        yield SESSION


class _UseCase:
    """Records the call, and asserts nothing about it here."""

    def __init__(self) -> None:
        self.calls: list[tuple[UUID, UUID, UUID | None]] = []
        self.sessions: list[Any] = []

    async def execute(
        self, workspace_id: UUID, batch_id: UUID, *, actor_id: UUID | None = None
    ) -> None:
        self.calls.append((workspace_id, batch_id, actor_id))


def _factory(use_case: _UseCase) -> Any:
    def build(session: Any) -> _UseCase:
        use_case.sessions.append(session)
        return use_case

    return build


@pytest.fixture
def scope() -> AsyncIterator[_Scope]:
    recorder = _Scope()
    with patch.object(tag_batch_handlers, "tenant_scoped_session", recorder):
        yield recorder


class TestTheSeamReadsOneFieldAndTrustsNothingElse:
    """⛔ ***Events carry identity; ports carry payload.***

    **The `batch_id` is the whole of what the handler takes from the
    envelope** — the accounts come from this module's own row. ⚡ **A replayed
    event therefore cannot apply a selection somebody has since changed**, and
    these assert that the extra fields are genuinely ignored rather than
    merely absent today.
    """

    async def test_the_segment_apply_handler_reads_only_the_batch_id(
        self, scope: _Scope
    ) -> None:
        use_case = _UseCase()

        await apply_segment_batch(
            _envelope(extra={"account_ids": ["not", "trusted"], "segment_id": str(uuid4())}),
            session_factory=object(),
            apply=_factory(use_case),
        )

        assert use_case.calls == [(WORKSPACE, BATCH, SYSTEM_USER_ID)]

    async def test_the_segment_reverse_handler_reads_only_the_batch_id(
        self, scope: _Scope
    ) -> None:
        """⚡ **And it passes no `actor_id`** — the reversal restores what the
        batch did, and there is no field on a membership row for a person to
        change."""
        use_case = _UseCase()

        await reverse_segment_batch(
            _envelope(extra={"account_ids": ["not", "trusted"]}),
            session_factory=object(),
            reverse=_factory(use_case),
        )

        assert use_case.calls == [(WORKSPACE, BATCH, None)]

    async def test_the_assignment_apply_handler_reads_only_the_batch_id(
        self, scope: _Scope
    ) -> None:
        use_case = _UseCase()

        await apply_assignment_batch(
            _envelope(extra={"member_user_id": str(uuid4())}),
            session_factory=object(),
            apply=_factory(use_case),
        )

        assert use_case.calls == [(WORKSPACE, BATCH, SYSTEM_USER_ID)]

    async def test_the_assignment_reverse_handler_reads_only_the_batch_id(
        self, scope: _Scope
    ) -> None:
        use_case = _UseCase()

        await reverse_assignment_batch(
            _envelope(), session_factory=object(), reverse=_factory(use_case)
        )

        assert use_case.calls == [(WORKSPACE, BATCH, SYSTEM_USER_ID)]


class TestTheSeamOpensItsOwnTenantScopedSession:
    """🔴 **A worker has no request, so nothing sets the RLS context for it.**

    ⛔ **A handler that used an unscoped session would read every workspace's
    rows** — and every application-layer test would still pass, because they
    are handed a session that was scoped by a fixture.
    """

    @pytest.mark.parametrize(
        "handler,keyword",
        [
            (apply_segment_batch, "apply"),
            (reverse_segment_batch, "reverse"),
            (apply_assignment_batch, "apply"),
            (reverse_assignment_batch, "reverse"),
        ],
    )
    async def test_it_scopes_to_the_envelope_s_workspace_and_the_system_user(
        self, scope: _Scope, handler: Any, keyword: str
    ) -> None:
        use_case = _UseCase()

        await handler(
            _envelope(), session_factory=object(), **{keyword: _factory(use_case)}
        )

        assert scope.opened == [{"workspace_id": WORKSPACE, "user_id": SYSTEM_USER_ID}]
        # ⚡ **The session the scope opened is the one the use case was built
        # with.** A handler that opened a scope and then built against a
        # different session would pass every assertion above and still read
        # across tenants.
        assert use_case.sessions == [SESSION]

    async def test_the_actor_is_the_system_and_never_the_person_who_proposed(
        self, scope: _Scope
    ) -> None:
        """⚠️ **The batch was approved by a person and is applied by the
        platform.** ⛔ Attributing the write to the proposer would say they
        made a change at a moment they were not present for — 📁 §10's
        truthful-attribution rule, applied to an audit column."""
        use_case = _UseCase()
        proposer = uuid4()

        await apply_segment_batch(
            _envelope(extra={"proposed_by": str(proposer)}),
            session_factory=object(),
            apply=_factory(use_case),
        )

        assert use_case.calls[0][2] == SYSTEM_USER_ID
        assert use_case.calls[0][2] != proposer
