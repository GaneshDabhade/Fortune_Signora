/**
 * **§07's search focus rule reaches the screen** —
 * [TASK-1474](../../../docs/BACKLOG.md).
 *
 * > 📁 ***"Search — 224 × 32. Opens the palette on click or ⌘K. **Widens to
 * > 320px on focus at ≥1600px**."***
 *
 * 🔴 **Every assertion here is two-sided, and that is the product owner's
 * standard rather than this file's taste**: ⛔ **a one-sided check passes on a
 * search that is always 320px**, and ⚠️ **1599 is asserted beside 1600 because
 * that is where an off-by-one lives.**
 */
import { fireEvent, render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { SEARCH_WIDTH } from '@/lib/shell/top-bar';

vi.mock('@/components/intelligence/account-search', () => ({
  AccountSearch: () => <input aria-label="Search accounts" />,
}));
vi.mock('@/components/shell/account-menu', () => ({ AccountMenu: () => null }));
// ⚡ **Same reason as the account menu above** — the panel reads the workspace
// context and the query client, and **this suite is about the frame**.
vi.mock('@/components/shell/notifications', () => ({ Notifications: () => null }));
vi.mock('@/components/ui', async () => {
  const actual = await vi.importActual<Record<string, unknown>>('@/components/ui');
  // ⚡ **`SystemStatus` joined slot 3 in [TASK-1484](../../../docs/BACKLOG.md) ⓑ**
  // and reads `/ready` through the query client — ⛔ **same reason as the two
  // above: this suite is about the FRAME's widths**, not about what fills it.
  return { ...actual, OfflineStatus: () => null, SystemStatus: () => null };
});

import { TopBar } from '@/components/shell/top-bar';

function at(width: number) {
  Object.defineProperty(window, 'innerWidth', { value: width, configurable: true });
}

function bar() {
  return render(
    <TopBar breadcrumb={[]} role="owner" email="v@example.com" name={null} signOut={<span />} />,
  );
}

/** ⚡ **The slot, by what it IS** — the `search` landmark — rather than by a path. */
function slot() {
  const node = document.querySelector('[data-slot="search"]');
  if (node === null) throw new Error('no search slot');
  return node as HTMLElement;
}

beforeEach(() => at(1600));

describe('🔴 the width is the contract’s, at rest', () => {
  it('✅ 224px before anything is focused', () => {
    bar();

    expect(slot()).toHaveStyle({ width: `${SEARCH_WIDTH.rest}px` });
  });
});

describe('🔴 it widens on focus, and only on the band with room', () => {
  it('✅ 320px at 1600 once the field takes focus', async () => {
    at(1600);
    bar();

    fireEvent.focus(screen.getByLabelText('Search accounts'));

    expect(slot()).toHaveStyle({ width: `${SEARCH_WIDTH.focused}px` });
    expect(slot()).toHaveAttribute('data-widened', 'true');
  });

  /**
   * 🔴 **The other side of the boundary, and the assertion a one-sided test
   * would miss.**
   *
   * ⛔ **At 1599 the same focus must change nothing.** ⚡ **96px taken from the
   * breadcrumb is the cost** — 📁 the design widens the field only where there
   * is room, which is why the rule carries a threshold rather than being
   * unconditional.
   */
  it('⛔ and stays 224px at 1599, where there is no room', () => {
    at(SEARCH_WIDTH.focusWidensAbove - 1);
    bar();

    fireEvent.focus(screen.getByLabelText('Search accounts'));

    expect(slot()).toHaveStyle({ width: `${SEARCH_WIDTH.rest}px` });
    expect(slot()).not.toHaveAttribute('data-widened');
  });

  it('✅ and returns to 224px when focus leaves', () => {
    at(1600);
    bar();
    const field = screen.getByLabelText('Search accounts');

    fireEvent.focus(field);
    expect(slot()).toHaveStyle({ width: `${SEARCH_WIDTH.focused}px` });

    fireEvent.blur(field);

    expect(slot()).toHaveStyle({ width: `${SEARCH_WIDTH.rest}px` });
  });
});

describe('⛔ the numbers are the contract’s and are not restated', () => {
  /**
   * 🔴 **A literal in the markup is the defect this row was told to avoid.**
   *
   * ⚡ **The rule's threshold is `SEARCH_WIDTH.focusWidensAbove`**, so a design
   * change is one edit — ⛔ **and a Tailwind arbitrary value like `w-[320px]`
   * would put the design's number in two places**, which is how the contract
   * and the screen start disagreeing.
   */
  it('🔴 no hard-coded width appears in the slot’s classes', () => {
    bar();

    expect(slot().className).not.toMatch(/\b(w-\[|max-w-\[)/);
  });

  /**
   * ⚠️ **Only the width may animate.** ⛔ **`transition-all` would fade the
   * focus ring in behind the growth**, which is the one part of a focus state
   * that must be immediate for somebody navigating by keyboard.
   */
  it('♿ only the width transitions, so the focus ring is immediate', () => {
    bar();

    expect(slot().classList.contains('transition-[width]')).toBe(true);
    expect(slot().className).not.toContain('transition-all');
    // ⚡ **And nothing animates for a reader who asked for no motion.**
    expect(slot().classList.contains('motion-reduce:transition-none')).toBe(true);
  });
});
