import { fireEvent, render, screen } from '@testing-library/react';
import { beforeAll, describe, expect, it } from 'vitest';

import { ShortcutsReference } from '@/components/shell/shortcuts-reference';
import { allShortcuts, pressable } from '@/lib/shell/shortcuts';

/**
 * **`?` opens the reference, and the reference tells the truth** —
 * [TASK-1445](../../../docs/BACKLOG.md).
 *
 * ⛔ **The load-bearing assertion is not that it renders.** It is that a
 * shortcut nothing binds is **visibly marked**, in text — 🔴 **because the
 * whole hazard of a keyboard reference is that reading it is free and
 * disproving it costs a keypress and a moment of doubt about the product.**
 */

/**
 * ⚠️ **Openness is the `<dialog>`'s own state, never the presence of the
 * markup.** 📁 [`Dialog`](../../components/ui/dialog.tsx) always renders its
 * element and calls `showModal()`/`close()` — ⛔ **so asserting the title is
 * absent would pass against a dialog that is open**, and this test would have
 * been decorative ([§2](../../../CLAUDE.md)).
 *
 * ⚡ **jsdom implements neither method**, so both are stubbed to move the
 * `open` attribute the way a browser does. **The journey is what exercises the
 * real element.**
 */
function isOpen(): boolean {
  return document.querySelector('dialog')?.hasAttribute('open') === true;
}

beforeAll(() => {
  HTMLDialogElement.prototype.showModal = function showModal(this: HTMLDialogElement) {
    this.setAttribute('open', '');
  };
  HTMLDialogElement.prototype.close = function close(this: HTMLDialogElement) {
    this.removeAttribute('open');
  };
});

describe('opening it', () => {
  it('opens on ? from anywhere', () => {
    render(<ShortcutsReference />);
    expect(isOpen()).toBe(false);

    fireEvent.keyDown(window, { key: '?' });
    expect(isOpen()).toBe(true);
  });

  /**
   * ⛔ **`?` is a character somebody types.** 📁 The same guard `[` and `⌘.`
   * already carry — ⚠️ **a reference that opens mid-sentence is one people
   * learn to fear, and the modifier-free chords are exactly the ones at risk.**
   */
  it('stays shut while a field has focus', () => {
    render(
      <>
        <input aria-label="search" />
        <ShortcutsReference />
      </>,
    );
    const field = screen.getByLabelText('search');
    field.focus();

    fireEvent.keyDown(field, { key: '?' });
    expect(isOpen()).toBe(false);
  });

  it('ignores ? with a modifier, which is a different chord', () => {
    render(<ShortcutsReference />);
    fireEvent.keyDown(window, { key: '?', metaKey: true });
    expect(isOpen()).toBe(false);
  });
});

describe('what it shows', () => {
  const open = () => {
    render(<ShortcutsReference />);
    fireEvent.keyDown(window, { key: '?' });
  };

  it("lists every one of the design's eighteen, including the dead ones", () => {
    open();
    for (const shortcut of allShortcuts()) {
      expect(screen.getByText(shortcut.what), shortcut.id).toBeInTheDocument();
    }
  });

  it("names the design's three groups", () => {
    open();
    expect(screen.getByText('Surfaces')).toBeInTheDocument();
    expect(screen.getByText('Navigate')).toBeInTheDocument();
    expect(screen.getByText('Work')).toBeInTheDocument();
  });

  /**
   * 🔴 **The row's Definition of Done.** ⛔ **One mark per unbound shortcut, in
   * TEXT** — **a dimmed chip carries the whole meaning in contrast, and a
   * person who cannot see the contrast reads ten dead keys as live**
   * ([§20c](../../../CLAUDE.md): accessibility is a defect class).
   */
  it('marks every unbound shortcut, once each, as text', () => {
    open();
    const dead = allShortcuts().filter((shortcut) => !pressable(shortcut));
    expect(dead.length).toBeGreaterThan(0);
    expect(screen.getAllByText('Not bound')).toHaveLength(dead.length);
  });

  it('says where a partial shortcut works, rather than calling it dead', () => {
    open();
    for (const shortcut of allShortcuts().filter((s) => s.state === 'partial')) {
      expect(screen.getAllByText(shortcut.limit as string).length).toBeGreaterThan(0);
    }
  });

  /**
   * ⚠️ **The count is the sentence most likely to go stale**, so it is asserted
   * against the registry rather than against a literal.
   */
  it('states how many work, counted from the registry', () => {
    open();
    const working = allShortcuts().filter(pressable).length;
    expect(
      screen.getByText(new RegExp(`${working} of these 18 shortcuts work today`)),
    ).toBeInTheDocument();
  });

  it('never says coming soon', () => {
    open();
    expect(document.body.textContent?.toLowerCase()).not.toContain('coming soon');
  });
});
