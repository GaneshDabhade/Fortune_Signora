import { render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

import { Navigation, RAIL_DESTINATIONS } from '@/components/shell/navigation';
import { ShortcutsReference } from '@/components/shell/shortcuts-reference';

/**
 * **The rail's pinned utility group is the design's three** —
 * [TASK-1458](../../../docs/BACKLOG.md), against 📁 `Fortune Signora App
 * Shell.dc.html`'s `railUtility`.
 *
 * ## 🔴 Why this file exists at all
 *
 * ⚠️ **[TASK-1439](../../../docs/BACKLOG.md) required that *"the rendered
 * entries and their order are asserted against the design's list"*, and for the
 * UTILITY group nothing asserted it.** 📁 `rail.test.ts` exercises
 * `railViolations` against synthetic fixtures and never reads the real group —
 * ⛔ **so `Shortcuts` could have been added, misspelled, or ordered wrongly
 * without a single test moving.**
 *
 * ⚡ **Found by adding the entry and watching 2782 tests stay green.**
 */

vi.mock('next/navigation', () => ({ usePathname: () => '/' }));
vi.mock('@/lib/state/workspace-provider', () => ({
  useWorkspaceContext: () => ({
    activeWorkspace: { id: 'w1', name: 'Playground', role: 'owner' },
    workspaces: [],
    setActiveWorkspace: vi.fn(),
    isLoading: false,
    error: null,
  }),
}));

/** 📁 `railUtility`, verbatim and in the design's order. */
const THE_DESIGNS_THREE = ['Settings', 'Shortcuts', 'Docs & support'];

function railWithShell() {
  return render(
    <ShortcutsReference>
      <Navigation role="owner" roleKnown collapsed={false} />
    </ShortcutsReference>,
  );
}

describe('the pinned utility group', () => {
  it("renders the design's three, in the design's order", () => {
    railWithShell();
    const nav = screen.getByRole('navigation', { name: 'Primary' });

    const rendered = THE_DESIGNS_THREE.map((label) =>
      nav.textContent?.indexOf(label) ?? -1,
    );

    for (const [i, at] of rendered.entries()) {
      expect(at, THE_DESIGNS_THREE[i]).toBeGreaterThan(-1);
    }
    // ⛔ **Order is the design's and is asserted**, not left to reading order.
    expect(rendered).toEqual([...rendered].sort((a, b) => a - b));
  });

  /**
   * ⛔ **A `<button>`, not a link.** 📁 The design gives it `meta: '?'` — it
   * opens the reference rather than going anywhere — and ⚠️ **a screen reader
   * announcing a link that never changes the page is the control lying about
   * itself.**
   */
  it('offers Shortcuts as a button that opens a dialog', () => {
    railWithShell();
    const control = screen.getByRole('button', { name: 'Shortcuts' });
    expect(control).toHaveAttribute('aria-haspopup', 'dialog');
    expect(screen.queryByRole('link', { name: 'Shortcuts' })).toBeNull();
  });

  /**
   * ♿ **The row's own accessibility requirement**: *"reachable by keyboard; the
   * `?` meta is not the only affordance."*
   */
  it('names itself without relying on the ? glyph', () => {
    railWithShell();
    const control = screen.getByRole('button', { name: 'Shortcuts' });
    control.focus();
    expect(control).toHaveFocus();
  });
});

describe('what the other surfaces may read', () => {
  /**
   * ⛔ **The palette and the phone bar both render anchors.** ⚡ **An entry that
   * opens an overlay has no `href`**, so it must not reach either — and this is
   * the assertion that keeps the union honest at its consumers.
   */
  it('publishes only entries that go somewhere', () => {
    for (const item of RAIL_DESTINATIONS) {
      expect(typeof item.href, item.id).toBe('string');
    }
    expect(RAIL_DESTINATIONS.some((item) => item.id === 'shortcuts')).toBe(false);
  });
});

describe('without the shell above it', () => {
  /**
   * ⛔ **The entry is omitted rather than rendered dead.** 📁
   * [C-269](../../../docs/LANE_COORDINATION.md): an entry that leads nowhere is
   * not rendered — ⚠️ **and a rail mounted without the provider would otherwise
   * show a button that silently does nothing.**
   */
  it('omits Shortcuts rather than rendering a control that does nothing', () => {
    render(<Navigation role="owner" roleKnown collapsed={false} />);
    expect(screen.queryByRole('button', { name: 'Shortcuts' })).toBeNull();
    // ⚡ And the other two are unaffected — the omission is scoped.
    expect(screen.getByRole('link', { name: 'Settings' })).toBeInTheDocument();
  });
});
