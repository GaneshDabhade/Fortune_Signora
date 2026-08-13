/**
 * **Selecting companies to act on together** — [TASK-466](../../../docs/BACKLOG.md).
 *
 * 🔴 **The design draws two different *all*s and the tests are mostly about
 * keeping them apart**: the header checkbox selects the rows on screen, and
 * *"Select all 312"* selects the whole filtered set. ⛔ **A bulk action given
 * the wrong one touches accounts the customer never saw.**
 */
import { describe, expect, it } from 'vitest';

import {
  NOTHING_SELECTED,
  headerState,
  isEmpty,
  isSelected,
  offersSelectAll,
  resolvedIds,
  selectAllMatching,
  selectOnScreen,
  selectedCount,
  toggle,
} from '@/lib/accounts/selection';

const SCREEN = ['a', 'b', 'c'];

describe('⚡ picking rows one at a time', () => {
  it('starts empty', () => {
    expect(isEmpty(NOTHING_SELECTED)).toBe(true);
    expect(selectedCount(NOTHING_SELECTED)).toBe(0);
  });

  it('adds and removes', () => {
    const one = toggle(NOTHING_SELECTED, 'a', SCREEN);
    expect(selectedCount(one)).toBe(1);

    expect(selectedCount(toggle(one, 'a', SCREEN))).toBe(0);
  });

  it('⛔ does not mutate the selection it came from', () => {
    const one = toggle(NOTHING_SELECTED, 'a', SCREEN);

    toggle(one, 'b', SCREEN);

    expect(selectedCount(one)).toBe(1);
  });
});

describe('🔴 the header checkbox and “Select all N” are different things', () => {
  it('the checkbox selects what is on screen', () => {
    const selection = selectOnScreen(SCREEN);

    expect(selection.kind).toBe('explicit');
    expect(selectedCount(selection)).toBe(3);
  });

  it('“Select all” selects a set the client cannot enumerate', () => {
    /**
     * ⚡ **312 rows the customer has not looked at.** The set is whatever the
     * filters match, which the server resolves — **so the selection names a
     * count and no ids.**
     */
    const selection = selectAllMatching(312);

    expect(selection.kind).toBe('all-matching');
    expect(selectedCount(selection)).toBe(312);
    expect(resolvedIds(selection)).toBeNull();
  });

  it('🔴 an action cannot be handed the rows on screen when 312 are selected', () => {
    /**
     * ⛔ **The assertion this whole type exists for.** The bar says 312 and
     * the client holds 50; **returning the 50 would apply the action to a
     * sixth of what the customer was told**, silently and plausibly.
     *
     * ✅ `null` is what makes that unforgettable at every call site.
     */
    expect(resolvedIds(selectAllMatching(312))).toBeNull();
    expect(resolvedIds(selectOnScreen(SCREEN))).toEqual(SCREEN);
  });

  it('every row reads as selected while “all” is in force', () => {
    // ⚡ **So the tick stays as the customer pages**, which is what they asked
    // for and what the design shows.
    const selection = selectAllMatching(312);

    expect(isSelected(selection, 'anything-at-all')).toBe(true);
  });
});

describe('🔴 un-ticking one row leaves “all”, rather than subtracting from it', () => {
  it('collapses to the rows on screen, minus that one', () => {
    /**
     * ⛔ **There is no *"all 312 except this one"*** in a set the client cannot
     * enumerate. ⚡ **The count dropping from 312 to 2 is honest**: the
     * customer no longer has the filtered set selected, and a bar that kept
     * saying 311 would describe a set nothing could produce.
     */
    const after = toggle(selectAllMatching(312), 'b', SCREEN);

    expect(after.kind).toBe('explicit');
    expect(resolvedIds(after)).toEqual(['a', 'c']);
    expect(selectedCount(after)).toBe(2);
  });
});

describe('⚡ the header checkbox has three states and “mixed” is a real one', () => {
  it('none, some, all', () => {
    expect(headerState(NOTHING_SELECTED, SCREEN)).toBe('none');
    expect(headerState(toggle(NOTHING_SELECTED, 'a', SCREEN), SCREEN)).toBe('some');
    expect(headerState(selectOnScreen(SCREEN), SCREEN)).toBe('all');
    expect(headerState(selectAllMatching(312), SCREEN)).toBe('all');
  });

  it('⛔ an empty table reads none rather than all', () => {
    // ⚡ **Every row of zero is selected is vacuously true and useless.** A
    // ticked box over no rows invites an action on nothing.
    expect(headerState(NOTHING_SELECTED, [])).toBe('none');
    expect(headerState(selectOnScreen([]), [])).toBe('none');
  });

  it('⛔ and selecting rows from another page does not tick this one', () => {
    const elsewhere = toggle(NOTHING_SELECTED, 'z', ['z']);

    expect(headerState(elsewhere, SCREEN)).toBe('none');
  });
});

describe('🔴 “Select all N” is offered only where it would change something', () => {
  it('⛔ not when the whole filtered set is already on screen', () => {
    /**
     * ⚡ **A control that changes nothing is worse than an absent one**: a
     * person who presses it and sees no count move reasonably concludes the
     * product is broken.
     */
    expect(offersSelectAll(toggle(NOTHING_SELECTED, 'a', SCREEN), SCREEN, 3)).toBe(false);
  });

  it('✅ and yes when there are accounts they have not seen', () => {
    expect(offersSelectAll(toggle(NOTHING_SELECTED, 'a', SCREEN), SCREEN, 312)).toBe(true);
  });

  it('⛔ not when it is already in force', () => {
    expect(offersSelectAll(selectAllMatching(312), SCREEN, 312)).toBe(false);
  });

  it('⛔ and not on an empty table', () => {
    expect(offersSelectAll(NOTHING_SELECTED, [], 312)).toBe(false);
  });
});
