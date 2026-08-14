"""A named, saved grouping — [TASK-1479](../../../docs/BACKLOG.md) slice ⓶b.

🔴 **The subject is the reversal**, which was wrong twice in slice ⓶a and is
the half [TASK-466](../../../docs/BACKLOG.md) says is normally untested:

> *"a batch that applies but cannot be reversed in the window is a defect, not
> a limitation."*
"""

from __future__ import annotations

from uuid import uuid4

import pytest

from modules.commercial_profile.domain.account_segment import (
    MAX_SEGMENT_NAME,
    MAX_SEGMENTS,
    AccountSegment,
    AccountSegmentError,
    SegmentAddition,
    SegmentBatch,
    SegmentDirectory,
    add_to_segment,
)


class TestASegmentHasAnIdentityAndTheNameIsNotIt:
    def test_renaming_keeps_every_account_in_it(self) -> None:
        """⚡ **The id does not move**, which is what separates *rename* from
        *delete and create another* — 📁 the same reasoning `account_tag` and
        `target_accounts` both record."""
        original = AccountSegment(id=uuid4(), name="Board reporting set")

        renamed = original.renamed("Quarterly pack")

        assert renamed.id == original.id
        assert renamed.name == "Quarterly pack"

    def test_surrounding_and_repeated_whitespace_is_not_a_second_segment(self) -> None:
        """⛔ **Normalised on the value rather than by whoever remembered to
        call a helper.**"""
        assert AccountSegment(id=uuid4(), name="  Board   reporting set ").name == (
            "Board reporting set"
        )

    def test_a_segment_with_no_name_is_refused(self) -> None:
        with pytest.raises(AccountSegmentError):
            AccountSegment(id=uuid4(), name="   ")

    def test_a_name_longer_than_the_panel_can_show_is_refused(self) -> None:
        with pytest.raises(AccountSegmentError):
            AccountSegment(id=uuid4(), name="x" * (MAX_SEGMENT_NAME + 1))

    def test_the_longest_name_the_design_draws_fits(self) -> None:
        """⚡ **The limit is checked against the design rather than chosen.**
        ⛔ A bound that refused a name the reference model draws would be this
        file inventing a product rule."""
        assert len("Renewal risk — 90 days") <= MAX_SEGMENT_NAME
        assert len("Board reporting set") <= MAX_SEGMENT_NAME


class TestTwoNamesACustomerCannotTellApartAreOneSegment:
    def test_case_does_not_make_a_second_segment(self) -> None:
        directory = SegmentDirectory(
            segments=(AccountSegment(id=uuid4(), name="Board reporting set"),)
        )

        with pytest.raises(AccountSegmentError):
            directory.added(AccountSegment(id=uuid4(), name="BOARD REPORTING SET"))

    def test_the_folding_rule_is_the_tag_vocabulary_s_and_not_a_second_copy(self) -> None:
        """🔴 **One rule, borrowed rather than reimplemented** ([§2](../../../CLAUDE.md)).

        ⛔ **Asserted BEHAVIOURALLY, on the input where the two candidate
        implementations disagree.** `casefold` and `lower` differ on
        `"STRASSE"` versus `"straße"` — German is the case that separates them
        — **so a segment that had grown its own `lower`-based folding fails
        here and a segment that shares the tag's does not.**

        ⚠️ **An identity assertion — `segment.fold is tag.fold` — was written
        first and is weaker.** It proves one import statement and would pass
        against a copy that had been imported back; **this proves the rule.**
        """
        from modules.commercial_profile.domain.account_tag import fold as tag_fold

        upper = AccountSegment(id=uuid4(), name="STRASSE")
        sharp = AccountSegment(id=uuid4(), name="straße")

        assert upper.key == sharp.key
        assert upper.key == tag_fold("STRASSE")
        assert AccountSegment(id=uuid4(), name=" Board   reporting  set ").key == tag_fold(
            "board reporting set"
        )

    def test_finding_by_name_is_how_a_customer_reaches_one(self) -> None:
        wanted = AccountSegment(id=uuid4(), name="Expansion-ready")
        directory = SegmentDirectory(segments=(wanted,))

        assert directory.find("  expansion-READY ") == wanted
        assert directory.find("Competitive watch") is None

    def test_a_directory_over_the_limit_is_refused(self) -> None:
        too_many = tuple(
            AccountSegment(id=uuid4(), name=f"Segment {n}") for n in range(MAX_SEGMENTS + 1)
        )

        with pytest.raises(AccountSegmentError):
            SegmentDirectory(segments=too_many)


class TestTheReversalRemovesWhatItAddedAndNothingElse:
    """🔴 **The defect this whole type exists to prevent.**

    ⛔ **Reversing *Add to segment* is NOT *remove those accounts from the
    segment*.** An account curated into *Board reporting set* in June, then
    caught in a forty-one row bulk add in August, must still be in it after the
    customer presses *take it back*.
    """

    def test_an_account_already_in_the_segment_survives_the_reversal(self) -> None:
        segment, already_there, newly_added = uuid4(), uuid4(), uuid4()

        addition = add_to_segment(
            segment,
            accounts=(already_there, newly_added),
            already_in=frozenset({already_there}),
        )

        assert addition.inverse() == (newly_added,)
        assert already_there not in addition.inverse()

    def test_the_confirmation_can_tell_the_truth_about_what_moved(self) -> None:
        """⚡ *"38 added, 3 already there"* rather than *"41 updated"* — ⛔ **a
        number the customer could disprove by looking.**"""
        segment = uuid4()
        already = frozenset(uuid4() for _ in range(3))
        fresh = tuple(uuid4() for _ in range(38))

        addition = add_to_segment(segment, accounts=(*already, *fresh), already_in=already)

        assert addition.added_count == 38
        assert addition.total_count == 41

    def test_one_row_selected_twice_is_one_addition(self) -> None:
        """⛔ **Otherwise the count is wrong and the inverse removes it
        twice.**"""
        segment, account = uuid4(), uuid4()

        addition = add_to_segment(segment, accounts=(account, account), already_in=frozenset())

        assert addition.added == (account,)

    def test_an_account_cannot_be_both_added_and_unchanged(self) -> None:
        with pytest.raises(AccountSegmentError):
            SegmentAddition(segment_id=uuid4(), added=(shared := uuid4(),), unchanged=(shared,))

    def test_adding_nobody_is_representable_and_reverses_to_nothing(self) -> None:
        """⚡ **Every selected account was already in it.** ✅ A real outcome,
        distinct from *not applied* — and it reverses to nothing rather than
        failing."""
        segment = uuid4()
        already = frozenset({uuid4()})

        addition = add_to_segment(segment, accounts=tuple(already), already_in=already)

        assert addition.added == ()
        assert addition.inverse() == ()


class TestABatchKnowsWhetherItHasRun:
    def test_an_unapplied_batch_has_nothing_to_reverse(self) -> None:
        """⛔ **`None` and `()` are different facts.** ⚠️ Only the first is
        still waiting for somebody to approve it."""
        batch = SegmentBatch(batch_id=uuid4(), segment_id=uuid4(), requested=(uuid4(),))

        assert batch.is_applied is False
        assert batch.to_reverse() == ()

    def test_an_applied_batch_that_moved_nobody_is_a_different_state(self) -> None:
        segment = uuid4()
        account = uuid4()
        batch = SegmentBatch(batch_id=uuid4(), segment_id=segment, requested=(account,))

        applied = batch.with_application(
            add_to_segment(segment, accounts=(account,), already_in=frozenset({account}))
        )

        assert applied.is_applied is True
        assert applied.to_reverse() == ()

    def test_a_batch_applies_once(self) -> None:
        """⛔ **A second application overwrites the record the reversal depends
        on**, so the customer's undo would operate on the wrong set — 📁
        [ADR-0405](../../../docs/architecture/adr/0405-an-action-is-approved-before-it-is-effective.md):
        a batch applies at one moment."""
        segment, account = uuid4(), uuid4()
        batch = SegmentBatch(
            batch_id=uuid4(), segment_id=segment, requested=(account,)
        ).with_application(
            add_to_segment(segment, accounts=(account,), already_in=frozenset())
        )

        with pytest.raises(AccountSegmentError):
            batch.with_application(
                add_to_segment(segment, accounts=(account,), already_in=frozenset())
            )

    def test_a_batch_cannot_apply_a_different_segment_than_it_proposed(self) -> None:
        """🔴 **The approval named a segment and the application must be that
        one.** ⛔ Otherwise an approved *Add to Board reporting set* could apply
        *Dormant enterprise*, and the customer approved a sentence that is not
        what ran."""
        proposed = uuid4()

        with pytest.raises(AccountSegmentError):
            SegmentBatch(
                batch_id=uuid4(),
                segment_id=proposed,
                requested=(uuid4(),),
                applied=SegmentAddition(segment_id=uuid4(), added=(), unchanged=()),
            )

    def test_an_empty_selection_is_a_defect_rather_than_a_no_op(self) -> None:
        """⛔ **A successful no-op would let a broken selection look like a
        completed action** — 📁 [P-A](../../../docs/DOMAIN_DISCOVERY_REGISTER.md)'s
        shape one layer up."""
        with pytest.raises(AccountSegmentError):
            SegmentBatch(batch_id=uuid4(), segment_id=uuid4(), requested=())
