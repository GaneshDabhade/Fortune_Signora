"""Running and reversing a bulk tag from an event — [TASK-466](../../../docs/BACKLOG.md).

**Three properties, and only one of them is the happy path.**

⛔ **A batch this module did not propose is not an error** — the Action Batch
is a shared lifecycle. ⚠️ **A re-delivered event must change nothing** — 📁
[§9](../../../CLAUDE.md): *"event consumers must be idempotent on
`event_id`."* 🔴 **And a reversal reads what CHANGED**, never what was asked.
"""

from __future__ import annotations

from datetime import timedelta
from uuid import UUID, uuid4

import pytest

from modules.commercial_profile.application.tag_use_cases import (
    REVERSIBLE_FOR,
    ApplyTagBatchUseCase,
    ProposeTagBatchInput,
    ProposeTagBatchUseCase,
    ReverseTagBatchUseCase,
    TagBatchStore,
)
from modules.commercial_profile.domain.account_tag import (
    AccountTag,
    AccountTagError,
    TagApplication,
    TagBatch,
    TagTone,
)
from tests.commercial_profile.test_tag_use_cases import FakeTags

pytestmark = pytest.mark.asyncio


class FakeBatches:
    """In memory, and **it counts applications** — two of these tests are
    about a write that must not happen twice."""

    def __init__(self) -> None:
        self.batches: dict[tuple[UUID, UUID], TagBatch] = {}
        self.applications = 0

    async def get(self, workspace_id: UUID, batch_id: UUID) -> TagBatch | None:
        return self.batches.get((workspace_id, batch_id))

    async def record_application(
        self, workspace_id: UUID, batch_id: UUID, application: TagApplication
    ) -> None:
        self.applications += 1
        current = self.batches[(workspace_id, batch_id)]
        self.batches[(workspace_id, batch_id)] = current.with_application(application)


#: ⚡ **Conformance checked by `mypy --strict`**, not by an `isinstance` that a
#: structural `Protocol` would pass regardless.
_PORT_CONFORMANCE: TagBatchStore = FakeBatches()


async def _seed(
    tags: FakeTags, batches: FakeBatches, workspace: UUID, actor: UUID, accounts: tuple[UUID, ...]
) -> tuple[UUID, AccountTag]:
    tag = AccountTag(id=uuid4(), name="At risk", tone=TagTone.RISK)
    await tags.create(workspace, tag, actor_id=actor)
    batch_id = uuid4()
    batches.batches[(workspace, batch_id)] = TagBatch(
        batch_id=batch_id, tag_id=tag.id, requested=accounts
    )
    return batch_id, tag


class TestApplyingWhatTheBatchProposed:
    async def test_it_tags_the_accounts_the_batch_named(self) -> None:
        tags, batches = FakeTags(), FakeBatches()
        workspace, actor = uuid4(), uuid4()
        accounts = (uuid4(), uuid4(), uuid4())
        batch_id, tag = await _seed(tags, batches, workspace, actor, accounts)

        await ApplyTagBatchUseCase(tags=tags, batches=batches).execute(
            workspace, batch_id, actor_id=actor
        )

        assert await tags.accounts_with(workspace, tag.id, among=accounts) == frozenset(accounts)

    async def test_a_batch_this_module_did_not_propose_is_silent(self) -> None:
        """⛔ **Not an error, and this is the shape that matters at scale.**

        The Action Batch is a shared lifecycle; when a second domain proposes
        one, this handler receives that event too. **Raising would put a
        permanent failure into a retry loop that can never succeed.**
        """
        tags, batches = FakeTags(), FakeBatches()

        await ApplyTagBatchUseCase(tags=tags, batches=batches).execute(
            uuid4(), uuid4(), actor_id=uuid4()
        )

        assert tags.writes == 0
        assert batches.applications == 0

    async def test_a_second_delivery_changes_nothing(self) -> None:
        """⚠️ **§9: consumers must be idempotent on `event_id`.**

        ⛔ **And the harm is not a duplicate row** — the primary key would
        refuse that. **It is that a second application would overwrite the
        record a reversal depends on**, so the customer's undo would then
        operate on the wrong set.
        """
        tags, batches = FakeTags(), FakeBatches()
        workspace, actor = uuid4(), uuid4()
        accounts = (uuid4(), uuid4())
        batch_id, _ = await _seed(tags, batches, workspace, actor, accounts)
        apply = ApplyTagBatchUseCase(tags=tags, batches=batches)
        await apply.execute(workspace, batch_id, actor_id=actor)
        writes_after_first = tags.writes

        await apply.execute(workspace, batch_id, actor_id=actor)

        assert batches.applications == 1
        assert tags.writes == writes_after_first

    async def test_it_records_what_changed_rather_than_what_was_asked(self) -> None:
        tags, batches = FakeTags(), FakeBatches()
        workspace, actor = uuid4(), uuid4()
        june = (uuid4(), uuid4(), uuid4())
        now = tuple(uuid4() for _ in range(5))
        batch_id, tag = await _seed(tags, batches, workspace, actor, (*june, *now))
        # June's three were tagged before this batch existed.
        await tags.assign(workspace, tag.id, june, actor_id=actor)

        await ApplyTagBatchUseCase(tags=tags, batches=batches).execute(
            workspace, batch_id, actor_id=actor
        )

        recorded = await batches.get(workspace, batch_id)
        assert recorded is not None and recorded.applied is not None
        assert set(recorded.applied.changed) == set(now)
        assert set(recorded.applied.unchanged) == set(june)


class TestTakingItBack:
    async def test_it_leaves_the_accounts_that_were_tagged_first(self) -> None:
        """🔴 **The whole point, through the event path this time.**"""
        tags, batches = FakeTags(), FakeBatches()
        workspace, actor = uuid4(), uuid4()
        june = (uuid4(), uuid4(), uuid4())
        now = tuple(uuid4() for _ in range(5))
        batch_id, tag = await _seed(tags, batches, workspace, actor, (*june, *now))
        await tags.assign(workspace, tag.id, june, actor_id=actor)
        await ApplyTagBatchUseCase(tags=tags, batches=batches).execute(
            workspace, batch_id, actor_id=actor
        )

        await ReverseTagBatchUseCase(tags=tags, batches=batches).execute(workspace, batch_id)

        assert await tags.accounts_with(workspace, tag.id, among=june) == frozenset(june)
        assert await tags.accounts_with(workspace, tag.id, among=now) == frozenset()

    async def test_reversing_a_batch_that_never_applied_touches_nothing(self) -> None:
        """⛔ **Nothing to undo, and `requested` must not be reached for.**

        A batch approved and then reversed before it applied has changed
        nothing — **and a handler that fell back to `requested` would untag
        accounts this batch never touched.**
        """
        tags, batches = FakeTags(), FakeBatches()
        workspace, actor = uuid4(), uuid4()
        accounts = (uuid4(), uuid4())
        batch_id, tag = await _seed(tags, batches, workspace, actor, accounts)
        # Somebody tagged them by hand, before any batch ran.
        await tags.assign(workspace, tag.id, accounts, actor_id=actor)

        await ReverseTagBatchUseCase(tags=tags, batches=batches).execute(workspace, batch_id)

        assert await tags.accounts_with(workspace, tag.id, among=accounts) == frozenset(accounts)

    async def test_reversing_a_batch_this_module_did_not_propose_is_silent(self) -> None:
        tags, batches = FakeTags(), FakeBatches()

        await ReverseTagBatchUseCase(tags=tags, batches=batches).execute(uuid4(), uuid4())

        assert tags.writes == 0

    async def test_reversing_twice_reaches_no_further_than_once(self) -> None:
        tags, batches = FakeTags(), FakeBatches()
        workspace, actor = uuid4(), uuid4()
        accounts = (uuid4(), uuid4())
        batch_id, tag = await _seed(tags, batches, workspace, actor, accounts)
        await ApplyTagBatchUseCase(tags=tags, batches=batches).execute(
            workspace, batch_id, actor_id=actor
        )
        reverse = ReverseTagBatchUseCase(tags=tags, batches=batches)
        await reverse.execute(workspace, batch_id)

        await reverse.execute(workspace, batch_id)

        assert await tags.accounts_with(workspace, tag.id, among=accounts) == frozenset()


class FakeProposer:
    """**Records what it was asked for**, because two of these tests are about
    the name and the count a customer approves."""

    def __init__(self) -> None:
        self.proposals: list[dict[str, object]] = []

    async def propose(
        self,
        *,
        workspace_id: UUID,
        name: str,
        item_count: int,
        proposed_by: UUID,
        reversible_for: timedelta | None = None,
    ) -> UUID:
        batch_id = uuid4()
        self.proposals.append(
            {
                "batch_id": batch_id,
                "name": name,
                "item_count": item_count,
                "reversible_for": reversible_for,
            }
        )
        return batch_id


class RecordingBatches(FakeBatches):
    async def record(self, workspace_id: UUID, batch: TagBatch, *, actor_id: UUID) -> None:
        self.batches[(workspace_id, batch.batch_id)] = batch


class TestProposingABulkAddTag:
    async def test_it_proposes_and_records_the_payload(self) -> None:
        tags, batches, proposer = FakeTags(), RecordingBatches(), FakeProposer()
        workspace, actor = uuid4(), uuid4()
        tag = AccountTag(id=uuid4(), name="At risk", tone=TagTone.RISK)
        await tags.create(workspace, tag, actor_id=actor)
        accounts = (uuid4(), uuid4(), uuid4())

        batch_id = await ProposeTagBatchUseCase(
            tags=tags, batches=batches, proposer=proposer
        ).execute(
            ProposeTagBatchInput(
                workspace_id=workspace, actor_id=actor, tag_id=tag.id, accounts=accounts
            )
        )

        recorded = await batches.get(workspace, batch_id)
        assert recorded is not None
        assert recorded.requested == accounts
        # ⛔ **Proposed, not applied.** Approval is a human decision on a
        # screen, and nothing is tagged until somebody accepts it.
        assert recorded.applied is None
        assert tags.writes == 1  # the tag itself, and nothing since

    async def test_the_name_a_customer_approves_names_the_act(self) -> None:
        """📁 *"What the customer called it — their words, so a history reads
        as a record of decisions rather than a list of identifiers."*"""
        tags, batches, proposer = FakeTags(), RecordingBatches(), FakeProposer()
        workspace, actor = uuid4(), uuid4()
        tag = AccountTag(id=uuid4(), name="At risk", tone=TagTone.RISK)
        await tags.create(workspace, tag, actor_id=actor)

        await ProposeTagBatchUseCase(tags=tags, batches=batches, proposer=proposer).execute(
            ProposeTagBatchInput(
                workspace_id=workspace,
                actor_id=actor,
                tag_id=tag.id,
                accounts=(uuid4(), uuid4()),
            )
        )

        assert proposer.proposals[0]["name"] == 'Tag 2 companies “At risk”'

    async def test_the_count_is_companies_and_not_clicks(self) -> None:
        """🔴 **De-duplicated BEFORE the count is taken.**

        ⛔ **A customer approving *"Tag 3 companies"* when two are the same row
        has approved a sentence that is false** — and the batch's `item_count`
        is what the Action Batch reports for the rest of its life.
        """
        tags, batches, proposer = FakeTags(), RecordingBatches(), FakeProposer()
        workspace, actor = uuid4(), uuid4()
        tag = AccountTag(id=uuid4(), name="At risk", tone=TagTone.RISK)
        await tags.create(workspace, tag, actor_id=actor)
        twice = uuid4()

        batch_id = await ProposeTagBatchUseCase(
            tags=tags, batches=batches, proposer=proposer
        ).execute(
            ProposeTagBatchInput(
                workspace_id=workspace,
                actor_id=actor,
                tag_id=tag.id,
                accounts=(twice, uuid4(), twice),
            )
        )

        assert proposer.proposals[0]["item_count"] == 2
        assert proposer.proposals[0]["name"] == 'Tag 2 companies “At risk”'
        recorded = await batches.get(workspace, batch_id)
        assert recorded is not None and len(recorded.requested) == 2

    async def test_a_window_is_declared_so_reversal_is_offered_at_all(self) -> None:
        """⛔ **`None` would mean *reversal was never offered***, and
        [TASK-466](../../../docs/BACKLOG.md) calls a batch that cannot be
        reversed a defect rather than a limitation.

        ⚠️ **The number is the design's only stated batch window and it is
        stated for IMPORTS** — 📁 [C-1506](../../../docs/LANE_COORDINATION.md)
        asks whether it carries here.
        """
        tags, batches, proposer = FakeTags(), RecordingBatches(), FakeProposer()
        workspace, actor = uuid4(), uuid4()
        tag = AccountTag(id=uuid4(), name="At risk", tone=TagTone.RISK)
        await tags.create(workspace, tag, actor_id=actor)

        await ProposeTagBatchUseCase(tags=tags, batches=batches, proposer=proposer).execute(
            ProposeTagBatchInput(
                workspace_id=workspace, actor_id=actor, tag_id=tag.id, accounts=(uuid4(),)
            )
        )

        assert proposer.proposals[0]["reversible_for"] == REVERSIBLE_FOR
        assert proposer.proposals[0]["reversible_for"] is not None

    async def test_a_tag_from_another_workspace_proposes_nothing(self) -> None:
        tags, batches, proposer = FakeTags(), RecordingBatches(), FakeProposer()

        with pytest.raises(AccountTagError):
            await ProposeTagBatchUseCase(
                tags=tags, batches=batches, proposer=proposer
            ).execute(
                ProposeTagBatchInput(
                    workspace_id=uuid4(),
                    actor_id=uuid4(),
                    tag_id=uuid4(),
                    accounts=(uuid4(),),
                )
            )

        # ⛔ **Nothing proposed**, so no approvable action exists for a tag the
        # workspace does not have.
        assert proposer.proposals == []

    async def test_an_empty_selection_proposes_nothing(self) -> None:
        tags, batches, proposer = FakeTags(), RecordingBatches(), FakeProposer()
        workspace, actor = uuid4(), uuid4()
        tag = AccountTag(id=uuid4(), name="At risk", tone=TagTone.RISK)
        await tags.create(workspace, tag, actor_id=actor)

        with pytest.raises(AccountTagError):
            await ProposeTagBatchUseCase(
                tags=tags, batches=batches, proposer=proposer
            ).execute(
                ProposeTagBatchInput(
                    workspace_id=workspace, actor_id=actor, tag_id=tag.id, accounts=()
                )
            )

        assert proposer.proposals == []
