"""A customer's own labels — [TASK-466](../../../docs/BACKLOG.md), against
[ADR-0411](../../../docs/architecture/adr/0411-customer-organized-account-metadata.md).

**The tests worth reading first are the reversal ones.** Everything else here
guards a rule a reviewer can see; `test_reversing_leaves_a_prior_tag_alone`
guards one that only shows up on a customer's screen, three weeks later, as
*"why did the undo remove a tag I set in June?"*
"""

from __future__ import annotations

from uuid import UUID, uuid4

import pytest

from modules.commercial_profile.domain.account_tag import (
    MAX_TAG_NAME,
    MAX_VOCABULARY,
    AccountTag,
    AccountTagError,
    TagApplication,
    TagBatch,
    TagTone,
    TagVocabulary,
    apply_tag,
    fold,
)


def tag(name: str = "At risk", tone: TagTone = TagTone.RISK, id: UUID | None = None) -> AccountTag:
    return AccountTag(id=id or uuid4(), name=name, tone=tone)


class TestATagIsALabelWithAnIdentity:
    def test_a_tag_needs_a_name(self) -> None:
        with pytest.raises(AccountTagError):
            tag(name="   ")

    def test_a_name_is_bounded(self) -> None:
        with pytest.raises(AccountTagError):
            tag(name="x" * (MAX_TAG_NAME + 1))

    def test_the_boundary_itself_is_allowed(self) -> None:
        assert tag(name="x" * MAX_TAG_NAME).name == "x" * MAX_TAG_NAME

    def test_whitespace_is_normalised_into_the_value(self) -> None:
        # Not merely folded for comparison — written back, so two objects a
        # customer would call the same tag are equal rather than merely
        # matching under a function somebody has to remember to call.
        assert tag(name="  At   risk ").name == "At risk"

    def test_renaming_keeps_the_identity(self) -> None:
        """The rule that makes a rename a rename.

        Without it, a workspace renaming *At risk* to *Churn risk* would lose
        the tag from every account it was on — indistinguishable, to the data,
        from deleting one tag and creating another.
        """
        original = tag(name="At risk")

        renamed = original.renamed("Churn risk")

        assert renamed.id == original.id
        assert renamed.name == "Churn risk"
        assert renamed.tone is original.tone

    def test_retoning_keeps_the_identity_and_the_name(self) -> None:
        original = tag(name="Stalling", tone=TagTone.WARN)

        assert original.retoned(TagTone.RISK) == AccountTag(
            id=original.id, name="Stalling", tone=TagTone.RISK
        )


class TestTheToneIsTheCustomersAndAiIsNotAmongIt:
    def test_the_four_the_design_gives_a_customer(self) -> None:
        assert {t.value for t in TagTone} == {"risk", "warn", "pos", "neutral"}

    def test_ai_is_not_a_tone_a_customer_can_choose(self) -> None:
        """Signora's own mark, and a human opinion must not be able to wear it.

        The design's palette has five entries and `ai` is reserved for what
        the platform inferred. This asserts the absence, so nobody adds it
        back for symmetry with the stylesheet.
        """
        assert "ai" not in {t.value for t in TagTone}
        with pytest.raises(ValueError):
            TagTone("ai")


class TestUniquenessIsDecidedOnTheFoldAndNotOnTheDisplay:
    def test_two_names_a_customer_cannot_tell_apart_are_one_tag(self) -> None:
        vocabulary = TagVocabulary(tags=(tag(name="At risk"),))

        with pytest.raises(AccountTagError):
            vocabulary.added(tag(name="at  RISK"))

    def test_the_fold_is_casefold_rather_than_lower(self) -> None:
        # `lower("STRASSE")` != `lower("straße")`; `casefold` makes them one,
        # which is the point for customers who are not writing English.
        assert fold("STRASSE") == fold("straße")

    def test_find_returns_the_tag_a_customer_means(self) -> None:
        wanted = tag(name="At risk")
        vocabulary = TagVocabulary(tags=(wanted, tag(name="Strategic", tone=TagTone.NEUTRAL)))

        assert vocabulary.find("  at risk  ") == wanted
        assert vocabulary.find("nothing like it") is None

    def test_a_vocabulary_cannot_be_built_already_broken(self) -> None:
        with pytest.raises(AccountTagError):
            TagVocabulary(tags=(tag(name="At risk"), tag(name="AT RISK")))

    def test_nor_with_one_tag_twice(self) -> None:
        once = tag(name="At risk")
        with pytest.raises(AccountTagError):
            TagVocabulary(tags=(once, once))

    def test_the_same_id_under_two_names_is_not_a_collision(self) -> None:
        """A replace-in-place must not trip the uniqueness rule against itself."""
        original = tag(name="At risk")
        vocabulary = TagVocabulary(tags=(original,))

        assert vocabulary.replaced(original.renamed("Churn risk")).tags[0].name == "Churn risk"

    def test_a_vocabulary_is_bounded(self) -> None:
        with pytest.raises(AccountTagError):
            TagVocabulary(tags=tuple(tag(name=f"tag {n}") for n in range(MAX_VOCABULARY + 1)))


class TestChangingTheVocabulary:
    def test_a_genuinely_new_name_is_added(self) -> None:
        first = tag(name="At risk")
        second = tag(name="Strategic", tone=TagTone.NEUTRAL)

        vocabulary = TagVocabulary(tags=(first,)).added(second)

        assert vocabulary.tags == (first, second)

    def test_adding_does_not_mutate_the_vocabulary_it_came_from(self) -> None:
        # The whole module is frozen dataclasses; this asserts the property a
        # reader would otherwise have to infer from the decorators.
        original = TagVocabulary(tags=(tag(name="At risk"),))

        original.added(tag(name="Strategic", tone=TagTone.NEUTRAL))

        assert len(original.tags) == 1

    def test_removing_a_tag_that_is_not_there_is_refused(self) -> None:
        with pytest.raises(AccountTagError):
            TagVocabulary(tags=()).removed(uuid4())

    def test_replacing_a_tag_that_is_not_there_is_refused(self) -> None:
        with pytest.raises(AccountTagError):
            TagVocabulary(tags=()).replaced(tag())

    def test_removing_leaves_the_rest(self) -> None:
        kept, going = tag(name="Strategic", tone=TagTone.NEUTRAL), tag(name="At risk")
        vocabulary = TagVocabulary(tags=(kept, going))

        assert vocabulary.removed(going.id).tags == (kept,)


class TestWhatABulkAddActuallyDid:
    def test_an_account_that_already_had_it_is_not_a_change(self) -> None:
        already, fresh = uuid4(), uuid4()

        application = apply_tag(
            uuid4(), accounts=(already, fresh), already_tagged=frozenset({already})
        )

        assert application.changed == (fresh,)
        assert application.unchanged == (already,)

    def test_the_confirmation_can_tell_the_truth_about_the_count(self) -> None:
        """*"38 tagged, 3 already had it"* rather than *"41 tagged"*."""
        already = frozenset(uuid4() for _ in range(3))
        fresh = tuple(uuid4() for _ in range(38))

        application = apply_tag(uuid4(), accounts=(*already, *fresh), already_tagged=already)

        assert application.applied_count == 38
        assert application.total_count == 41

    def test_selecting_one_row_twice_is_one_change(self) -> None:
        # A duplicated selection would otherwise inflate the count on the
        # confirmation and make the inverse untag the same account twice.
        account = uuid4()

        application = apply_tag(uuid4(), accounts=(account, account), already_tagged=frozenset())

        assert application.changed == (account,)

    def test_order_is_the_callers_and_is_preserved(self) -> None:
        first, second, third = uuid4(), uuid4(), uuid4()

        application = apply_tag(
            uuid4(), accounts=(first, second, third), already_tagged=frozenset({second})
        )

        assert application.changed == (first, third)

    def test_an_application_cannot_be_built_self_contradicting(self) -> None:
        both = uuid4()
        with pytest.raises(AccountTagError):
            TagApplication(tag_id=uuid4(), changed=(both,), unchanged=(both,))

    def test_nor_with_one_account_listed_twice(self) -> None:
        twice = uuid4()
        with pytest.raises(AccountTagError):
            TagApplication(tag_id=uuid4(), changed=(twice, twice), unchanged=())
        with pytest.raises(AccountTagError):
            TagApplication(tag_id=uuid4(), changed=(), unchanged=(twice, twice))


class TestTheReversalIsDerivedFromWhatChanged:
    """🔴 The half TASK-466 says is normally untested.

    > *"a batch that applies but cannot be reversed in the window is a defect,
    > not a limitation."*
    """

    def test_reversing_leaves_a_prior_tag_alone(self) -> None:
        """⛔ The defect this whole type exists to prevent.

        Three of the forty-one selected companies were tagged *At risk* in
        June. The batch tagged the other thirty-eight. Taking the batch back
        must leave June's three tagged — **they were not this batch's doing,
        and removing them destroys a fact the customer authored and never
        asked to undo.**

        The naive inverse — *remove the tag from every account the batch
        named* — passes every count assertion above and fails exactly here.
        """
        june = frozenset(uuid4() for _ in range(3))
        selected_now = tuple(uuid4() for _ in range(38))

        application = apply_tag(
            uuid4(), accounts=(*june, *selected_now), already_tagged=june
        )

        assert set(application.inverse()) == set(selected_now)
        assert not set(application.inverse()) & june

    def test_the_inverse_of_a_batch_that_changed_nothing_is_nothing(self) -> None:
        """Every selected account already had the tag.

        A reversal here must be a no-op rather than an untag, and a caller
        that looped over *what was asked* would strip all three.
        """
        already = frozenset(uuid4() for _ in range(3))

        application = apply_tag(uuid4(), accounts=tuple(already), already_tagged=already)

        assert application.inverse() == ()
        assert application.applied_count == 0
        assert application.total_count == 3

    def test_the_inverse_reads_changed_and_nothing_else(self) -> None:
        # Stated as an assertion rather than left to the implementation, so a
        # future edit that starts folding `unchanged` in fails here.
        application = TagApplication(
            tag_id=uuid4(), changed=(a := uuid4(),), unchanged=(uuid4(), uuid4())
        )

        assert application.inverse() == (a,)


class TestABatchRecordsWhatItAskedAndWhatItDid:
    def test_a_batch_names_at_least_one_account(self) -> None:
        with pytest.raises(AccountTagError):
            TagBatch(batch_id=uuid4(), tag_id=uuid4(), requested=())

    def test_before_it_runs_there_is_nothing_to_reverse(self) -> None:
        """⛔ **`None` is not the same as empty**, and this is the first of the
        two states a boolean could not tell apart."""
        batch = TagBatch(batch_id=uuid4(), tag_id=uuid4(), requested=(uuid4(),))

        assert batch.is_applied is False
        assert batch.to_reverse() == ()

    def test_applied_and_changed_nothing_is_a_different_state(self) -> None:
        """⛔ **The second.** Every selected account already carried the tag, so
        the batch ran and there is still nothing to undo — **and a caller that
        treated *nothing to reverse* as *never applied* would offer the undo
        control on a batch that had already finished.**"""
        tag_id = uuid4()
        already = uuid4()
        batch = TagBatch(batch_id=uuid4(), tag_id=tag_id, requested=(already,))

        ran = batch.with_application(
            apply_tag(tag_id, accounts=(already,), already_tagged=frozenset({already}))
        )

        assert ran.is_applied is True
        assert ran.to_reverse() == ()

    def test_the_reversal_reads_changed_and_never_requested(self) -> None:
        """🔴 **The defect this whole record exists to prevent**, at the type a
        caller actually holds."""
        tag_id = uuid4()
        june = frozenset(uuid4() for _ in range(3))
        now = tuple(uuid4() for _ in range(5))
        batch = TagBatch(batch_id=uuid4(), tag_id=tag_id, requested=(*june, *now))

        ran = batch.with_application(
            apply_tag(tag_id, accounts=batch.requested, already_tagged=june)
        )

        assert set(ran.to_reverse()) == set(now)
        assert not set(ran.to_reverse()) & june
        # ⚡ **`requested` is kept and is NOT what a reversal reads.**
        assert set(ran.requested) == june | set(now)

    def test_a_batch_cannot_be_applied_twice(self) -> None:
        """⛔ **The second application would overwrite the record a reversal
        depends on**, so the customer's undo would operate on the wrong set."""
        tag_id, account = uuid4(), uuid4()
        batch = TagBatch(batch_id=uuid4(), tag_id=tag_id, requested=(account,))
        ran = batch.with_application(
            apply_tag(tag_id, accounts=(account,), already_tagged=frozenset())
        )

        with pytest.raises(AccountTagError):
            ran.with_application(
                apply_tag(tag_id, accounts=(account,), already_tagged=frozenset())
            )

    def test_a_batch_cannot_apply_a_different_tag_than_it_proposed(self) -> None:
        # ⚡ **Unrepresentable rather than tested elsewhere**: an applied-handler
        # that looked up the wrong row would otherwise write a coherent-looking
        # record whose reversal untagged the wrong label.
        account = uuid4()
        with pytest.raises(AccountTagError):
            TagBatch(
                batch_id=uuid4(),
                tag_id=uuid4(),
                requested=(account,),
                applied=apply_tag(uuid4(), accounts=(account,), already_tagged=frozenset()),
            )
