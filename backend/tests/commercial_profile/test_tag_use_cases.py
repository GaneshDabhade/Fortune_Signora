"""Applying and reversing a tag — [TASK-466](../../../docs/BACKLOG.md).

**The reversal tests are the ones worth reading.** The rest guard rules a
reviewer can see in the diff; those guard the one a customer meets three weeks
later as *"why did the undo remove a tag I set in June?"*
"""

from __future__ import annotations

from uuid import UUID, uuid4

import pytest

from modules.commercial_profile.application.tag_use_cases import (
    AccountTagRepository,
    ApplyTagInput,
    ApplyTagUseCase,
    CreateTagInput,
    CreateTagUseCase,
    RenameTagInput,
    RenameTagUseCase,
    ReverseTagApplicationUseCase,
)
from modules.commercial_profile.domain.account_tag import (
    AccountTag,
    AccountTagError,
    TagTone,
    TagVocabulary,
)

pytestmark = pytest.mark.asyncio


class FakeTags:
    """In memory, and **it records who wrote what**, because two of these
    tests are about a write that must not happen and one is about a write that
    must not overwrite an attribution."""

    def __init__(self) -> None:
        self.tags: dict[UUID, dict[UUID, AccountTag]] = {}
        self.assignments: dict[tuple[UUID, UUID], set[UUID]] = {}
        self.first_tagged_by: dict[tuple[UUID, UUID, UUID], UUID] = {}
        self.writes = 0

    async def vocabulary(self, workspace_id: UUID) -> TagVocabulary:
        return TagVocabulary(tags=tuple(self.tags.get(workspace_id, {}).values()))

    async def create(self, workspace_id: UUID, tag: AccountTag, *, actor_id: UUID) -> None:
        self.writes += 1
        self.tags.setdefault(workspace_id, {})[tag.id] = tag

    async def rename(self, workspace_id: UUID, tag: AccountTag, *, actor_id: UUID) -> None:
        self.writes += 1
        self.tags.setdefault(workspace_id, {})[tag.id] = tag

    async def tags_for(
        self, workspace_id: UUID, accounts: tuple[UUID, ...]
    ) -> dict[UUID, tuple[UUID, ...]]:
        held: dict[UUID, list[UUID]] = {}
        for (ws, tag_id), assigned in self.assignments.items():
            if ws != workspace_id:
                continue
            for account_id in assigned & set(accounts):
                held.setdefault(account_id, []).append(tag_id)
        return {account: tuple(tag_ids) for account, tag_ids in held.items()}

    async def accounts_with(
        self, workspace_id: UUID, tag_id: UUID, *, among: tuple[UUID, ...]
    ) -> frozenset[UUID]:
        held = self.assignments.get((workspace_id, tag_id), set())
        return frozenset(account for account in among if account in held)

    async def assign(
        self, workspace_id: UUID, tag_id: UUID, accounts: tuple[UUID, ...], *, actor_id: UUID
    ) -> None:
        """⛔ **Refuses a pair it already holds, because the table does.**

        🔴 **This line is here because fire-testing caught the test above it
        being useless.** The fake used `setdefault`, so *"who first tagged
        it"* was preserved **by the fake** — and a use case that re-inserted
        the whole selection passed the assertion. **The test was checking the
        double, not the code.**

        ⚡ `account_tag_assignment`'s primary key is `(tag_id, account_id)`, so
        a duplicate `INSERT` raises in Postgres. **The fake raises too**, which
        is what makes every test above it capable of failing.
        """
        held = self.assignments.setdefault((workspace_id, tag_id), set())
        duplicate = held & set(accounts)
        if duplicate:
            raise AssertionError(
                f"duplicate key on account_tag_assignment for {len(duplicate)} account(s) — "
                "the same violation Postgres would raise"
            )
        self.writes += 1
        held.update(accounts)
        for account in accounts:
            self.first_tagged_by[(workspace_id, tag_id, account)] = actor_id

    async def unassign(
        self, workspace_id: UUID, tag_id: UUID, accounts: tuple[UUID, ...]
    ) -> None:
        self.writes += 1
        self.assignments.get((workspace_id, tag_id), set()).difference_update(accounts)


#: ⚡ **Conformance to the port, checked by `mypy --strict` rather than by a
#: test.** If `FakeTags` drifts from `AccountTagRepository`, this annotation
#: fails the type gate. ⛔ **A runtime `isinstance` here would be Decorative
#: Logic** ([§2](../../../CLAUDE.md)) — a `Protocol` is structural, so the
#: check would pass whatever the fake's methods looked like, **and a suite
#: proving a shape the database never produces is exactly what `fakes.py`
#: warns about one module over.**
_PORT_CONFORMANCE: AccountTagRepository = FakeTags()


class TestCreatingALabel:
    async def test_a_new_name_is_created(self) -> None:
        tags = FakeTags()
        ws, me = uuid4(), uuid4()

        tag = await CreateTagUseCase(tags=tags).execute(
            CreateTagInput(workspace_id=ws, actor_id=me, name="At risk", tone=TagTone.RISK)
        )

        assert tag.name == "At risk"
        assert (await tags.vocabulary(ws)).find("At risk") == tag

    async def test_typing_an_existing_name_selects_it_and_writes_nothing(self) -> None:
        """⚡ **What makes the design's *Add tag* safe to use twice.**

        ⛔ Asserting only that the returned id matches would pass against an
        implementation that re-created the row — so the write count is the
        assertion, the same shape [B-196](../../../docs/BUGS.md) needed.
        """
        tags = FakeTags()
        ws, me = uuid4(), uuid4()
        create = CreateTagUseCase(tags=tags)
        first = await create.execute(
            CreateTagInput(workspace_id=ws, actor_id=me, name="At risk", tone=TagTone.RISK)
        )
        writes_after_first = tags.writes

        again = await create.execute(
            # A different tone deliberately: selecting an existing tag must not
            # quietly restyle it under somebody else's hand.
            CreateTagInput(workspace_id=ws, actor_id=me, name="  at RISK ", tone=TagTone.WARN)
        )

        assert again == first
        assert again.tone is TagTone.RISK
        assert tags.writes == writes_after_first

    async def test_a_name_the_domain_refuses_never_reaches_the_repository(self) -> None:
        tags = FakeTags()

        with pytest.raises(AccountTagError):
            await CreateTagUseCase(tags=tags).execute(
                CreateTagInput(
                    workspace_id=uuid4(), actor_id=uuid4(), name="  ", tone=TagTone.NEUTRAL
                )
            )

        assert tags.writes == 0


class TestRenamingALabel:
    async def test_a_rename_keeps_the_tag_on_every_account(self) -> None:
        tags = FakeTags()
        ws, me, account = uuid4(), uuid4(), uuid4()
        tag = await CreateTagUseCase(tags=tags).execute(
            CreateTagInput(workspace_id=ws, actor_id=me, name="At risk", tone=TagTone.RISK)
        )
        await ApplyTagUseCase(tags=tags).execute(
            ApplyTagInput(workspace_id=ws, actor_id=me, tag_id=tag.id, accounts=(account,))
        )

        await RenameTagUseCase(tags=tags).execute(
            RenameTagInput(
                workspace_id=ws, actor_id=me, tag_id=tag.id, name="Churn risk", tone=TagTone.RISK
            )
        )

        assert await tags.accounts_with(ws, tag.id, among=(account,)) == frozenset({account})

    async def test_renaming_onto_a_name_already_in_use_is_refused(self) -> None:
        """⛔ **Refused here rather than by the index.**

        The database's unique index is the arbiter of two concurrent renames;
        a customer typing a name that is plainly taken should get a sentence,
        not a 500 from a constraint violation.
        """
        tags = FakeTags()
        ws, me = uuid4(), uuid4()
        create = CreateTagUseCase(tags=tags)
        first = await create.execute(
            CreateTagInput(workspace_id=ws, actor_id=me, name="At risk", tone=TagTone.RISK)
        )
        await create.execute(
            CreateTagInput(workspace_id=ws, actor_id=me, name="Churn risk", tone=TagTone.RISK)
        )

        with pytest.raises(AccountTagError):
            await RenameTagUseCase(tags=tags).execute(
                RenameTagInput(
                    workspace_id=ws,
                    actor_id=me,
                    tag_id=first.id,
                    name="churn RISK",
                    tone=TagTone.RISK,
                )
            )

    async def test_renaming_something_that_is_not_there_is_refused(self) -> None:
        with pytest.raises(AccountTagError):
            await RenameTagUseCase(tags=FakeTags()).execute(
                RenameTagInput(
                    workspace_id=uuid4(),
                    actor_id=uuid4(),
                    tag_id=uuid4(),
                    name="Anything",
                    tone=TagTone.NEUTRAL,
                )
            )


class TestApplyingItToSeveralAccountsAtOnce:
    async def test_a_tag_from_another_workspace_is_refused(self) -> None:
        """🔴 **The tenancy check at the layer above the policy.**

        RLS is the authoritative control and holds regardless; this is the
        first of the two guards §8 requires, and it fails with a sentence
        rather than with an empty result.
        """
        tags = FakeTags()
        theirs = await CreateTagUseCase(tags=tags).execute(
            CreateTagInput(
                workspace_id=uuid4(), actor_id=uuid4(), name="At risk", tone=TagTone.RISK
            )
        )

        with pytest.raises(AccountTagError):
            await ApplyTagUseCase(tags=tags).execute(
                ApplyTagInput(
                    workspace_id=uuid4(),
                    actor_id=uuid4(),
                    tag_id=theirs.id,
                    accounts=(uuid4(),),
                )
            )

    async def test_it_reports_what_changed_rather_than_what_was_asked(self) -> None:
        tags = FakeTags()
        ws, me = uuid4(), uuid4()
        tag = await CreateTagUseCase(tags=tags).execute(
            CreateTagInput(workspace_id=ws, actor_id=me, name="At risk", tone=TagTone.RISK)
        )
        apply = ApplyTagUseCase(tags=tags)
        june = (uuid4(), uuid4(), uuid4())
        await apply.execute(
            ApplyTagInput(workspace_id=ws, actor_id=me, tag_id=tag.id, accounts=june)
        )
        now = tuple(uuid4() for _ in range(38))

        application = await apply.execute(
            ApplyTagInput(workspace_id=ws, actor_id=me, tag_id=tag.id, accounts=(*june, *now))
        )

        assert application.applied_count == 38
        assert application.total_count == 41

    async def test_a_batch_that_changes_nothing_writes_nothing(self) -> None:
        tags = FakeTags()
        ws, me, account = uuid4(), uuid4(), uuid4()
        tag = await CreateTagUseCase(tags=tags).execute(
            CreateTagInput(workspace_id=ws, actor_id=me, name="At risk", tone=TagTone.RISK)
        )
        apply = ApplyTagUseCase(tags=tags)
        await apply.execute(
            ApplyTagInput(workspace_id=ws, actor_id=me, tag_id=tag.id, accounts=(account,))
        )
        writes_before = tags.writes

        application = await apply.execute(
            ApplyTagInput(workspace_id=ws, actor_id=me, tag_id=tag.id, accounts=(account,))
        )

        assert application.applied_count == 0
        assert tags.writes == writes_before

    async def test_re_applying_never_attempts_the_row_that_exists(self) -> None:
        """⚡ **Why the write is scoped to `changed`, and how this test earned
        the right to say so.**

        🔴 **It was written as *"the first tagger is preserved"* and it could
        not fail** — the fake used `setdefault`, so the fake was doing the
        preserving and a use case that re-wrote the whole selection passed.
        **Found by fire-testing, not by review.**

        ⛔ **The real protection is that the insert is never attempted.**
        `(tag_id, account_id)` is a primary key: a second write of an existing
        pair raises in Postgres, so *"upsert and let it sort itself out"* is
        not a working alternative — it is a 500 on a bulk action. **The fake
        now raises the same violation**, which is what makes this red when the
        scoping is removed.
        """
        tags = FakeTags()
        ws, first_person, second_person, account = uuid4(), uuid4(), uuid4(), uuid4()
        tag = await CreateTagUseCase(tags=tags).execute(
            CreateTagInput(
                workspace_id=ws, actor_id=first_person, name="At risk", tone=TagTone.RISK
            )
        )
        apply = ApplyTagUseCase(tags=tags)
        await apply.execute(
            ApplyTagInput(
                workspace_id=ws, actor_id=first_person, tag_id=tag.id, accounts=(account,)
            )
        )

        await apply.execute(
            ApplyTagInput(
                workspace_id=ws, actor_id=second_person, tag_id=tag.id, accounts=(account,)
            )
        )

        assert tags.first_tagged_by[(ws, tag.id, account)] == first_person


class TestTakingTheBatchBack:
    async def test_it_leaves_a_tag_set_before_the_batch(self) -> None:
        """🔴 **The defect the whole `TagApplication` type exists to prevent**,
        now proven through the use cases rather than only in the domain."""
        tags = FakeTags()
        ws, me = uuid4(), uuid4()
        tag = await CreateTagUseCase(tags=tags).execute(
            CreateTagInput(workspace_id=ws, actor_id=me, name="At risk", tone=TagTone.RISK)
        )
        apply = ApplyTagUseCase(tags=tags)
        june = (uuid4(), uuid4(), uuid4())
        await apply.execute(
            ApplyTagInput(workspace_id=ws, actor_id=me, tag_id=tag.id, accounts=june)
        )
        now = tuple(uuid4() for _ in range(5))
        application = await apply.execute(
            ApplyTagInput(workspace_id=ws, actor_id=me, tag_id=tag.id, accounts=(*june, *now))
        )

        await ReverseTagApplicationUseCase(tags=tags).execute(ws, application)

        assert await tags.accounts_with(ws, tag.id, among=june) == frozenset(june)
        assert await tags.accounts_with(ws, tag.id, among=now) == frozenset()

    async def test_reversing_a_batch_that_changed_nothing_writes_nothing(self) -> None:
        tags = FakeTags()
        ws, me, account = uuid4(), uuid4(), uuid4()
        tag = await CreateTagUseCase(tags=tags).execute(
            CreateTagInput(workspace_id=ws, actor_id=me, name="At risk", tone=TagTone.RISK)
        )
        apply = ApplyTagUseCase(tags=tags)
        await apply.execute(
            ApplyTagInput(workspace_id=ws, actor_id=me, tag_id=tag.id, accounts=(account,))
        )
        application = await apply.execute(
            ApplyTagInput(workspace_id=ws, actor_id=me, tag_id=tag.id, accounts=(account,))
        )
        writes_before = tags.writes

        await ReverseTagApplicationUseCase(tags=tags).execute(ws, application)

        assert tags.writes == writes_before
        assert await tags.accounts_with(ws, tag.id, among=(account,)) == frozenset({account})

    async def test_reversing_twice_is_not_worse_than_reversing_once(self) -> None:
        # The design's window lets somebody click undo, lose the connection,
        # and click it again. Neither the second call nor a stale application
        # may reach further than the first did.
        tags = FakeTags()
        ws, me, account = uuid4(), uuid4(), uuid4()
        tag = await CreateTagUseCase(tags=tags).execute(
            CreateTagInput(workspace_id=ws, actor_id=me, name="At risk", tone=TagTone.RISK)
        )
        application = await ApplyTagUseCase(tags=tags).execute(
            ApplyTagInput(workspace_id=ws, actor_id=me, tag_id=tag.id, accounts=(account,))
        )
        reverse = ReverseTagApplicationUseCase(tags=tags)
        await reverse.execute(ws, application)

        await reverse.execute(ws, application)

        assert await tags.accounts_with(ws, tag.id, among=(account,)) == frozenset()
