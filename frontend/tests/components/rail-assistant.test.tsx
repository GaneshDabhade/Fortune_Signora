/**
 * **`Ask Signora` is the first item of the rail's pinned group** —
 * [TASK-1470](../../../docs/BACKLOG.md), §12 door `01`.
 *
 * 🔴 **The row's own warning is the whole design of this file**: *"a test that
 * only checks `Ask Signora` exists passes against the current defect."* ⛔ **The
 * defect was ORDERING** — it sat below the utilities, mounted outside the rail
 * — **so every assertion here is about POSITION.**
 *
 * ⚠️ **This lane has shipped the weaker test before.** 📁
 * [TASK-1458](../../../docs/BACKLOG.md) found the utility group **unasserted**:
 * 2782 tests stayed green while an entry was missing, because nothing checked
 * the group at all.
 */
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { beforeEach, describe, expect, it, vi } from 'vitest';

const openAssistant = vi.hoisted(() => vi.fn());
const openShortcuts = vi.hoisted(() => vi.fn());
const copilot = vi.hoisted(() => vi.fn());

vi.mock('@/lib/state/workspace-provider', () => ({
  useWorkspaceContext: () => ({
    activeWorkspace: { id: 'w1', name: 'Northwind' },
    workspaces: [{ id: 'w1', name: 'Northwind' }],
    isLoading: false,
  }),
}));
vi.mock('@/components/shell/shortcuts-reference', () => ({
  useShortcutsReference: () => ({ open: openShortcuts }),
}));
vi.mock('@/components/shell/copilot', () => ({ useCopilot: copilot }));

import { Navigation } from '@/components/shell/navigation';

/** ⚡ **The pinned group, by the divider that defines it** — the design's own
 *  structure, rather than an index into the rail. */
function pinnedGroup() {
  const rail = screen.getByRole('navigation', { name: 'Primary' });
  const group = rail.querySelector('.border-t');
  if (group === null) throw new Error('no pinned group');
  return group as HTMLElement;
}

/** The group's entries, in document order, by their accessible names. */
function pinnedOrder() {
  return Array.from(pinnedGroup().querySelectorAll('a, button')).map(
    (node) => node.getAttribute('aria-label') ?? node.textContent?.trim() ?? '',
  );
}

beforeEach(() => {
  openAssistant.mockClear();
  openShortcuts.mockClear();
  copilot.mockReturnValue({ open: openAssistant });
});

describe('🔴 position, not presence', () => {
  /**
   * 🔴 **The assertion the defect failed, and the one a presence check passes.**
   *
   * 📁 The design's rail renders `Ask Signora` immediately after the divider,
   * **then** `railUtility` — Settings, Shortcuts, Docs & support.
   */
  it('🔴 the assistant is FIRST, above the utilities', () => {
    render(<Navigation role="owner" />);

    expect(pinnedOrder()[0]).toBe('Ask Signora');
  });

  it('✅ and the design’s order holds for the whole group', () => {
    render(<Navigation role="owner" />);

    expect(pinnedOrder()).toEqual([
      'Ask Signora',
      'Settings',
      'Shortcuts',
      'Docs & support',
    ]);
  });

  /**
   * ⛔ **A presence check would pass against the defect, and this proves it.**
   *
   * ⚡ **The entry existed before this row** — mounted outside the rail, below
   * everything — **so *"Ask Signora is in the document"* was TRUE while the
   * design was violated.** ✅ **Being inside the rail is the claim.**
   */
  it('🔴 it is inside the rail, not merely somewhere on the page', () => {
    render(<Navigation role="owner" />);

    const entry = screen.getByRole('button', { name: 'Ask Signora' });
    expect(screen.getByRole('navigation', { name: 'Primary' })).toContainElement(entry);
  });
});

describe('⚡ it opens the room rather than going somewhere', () => {
  it('✅ pressing it opens the assistant', async () => {
    render(<Navigation role="owner" />);

    await userEvent.click(screen.getByRole('button', { name: 'Ask Signora' }));

    expect(openAssistant).toHaveBeenCalledTimes(1);
    // ⛔ **And it is not the other door** — the union's `opens` is what makes
    // the two impossible to confuse.
    expect(openShortcuts).not.toHaveBeenCalled();
  });

  it('⛔ it is not a link, because there is no `/assistant` route', () => {
    render(<Navigation role="owner" />);

    const entry = screen.getByRole('button', { name: 'Ask Signora' });
    expect(entry.tagName).toBe('BUTTON');
    expect(entry).toHaveAttribute('aria-haspopup', 'dialog');
  });

  /**
   * ⛔ **No room means no door.** ⚡ **A control that silently does nothing is
   * worse than one that is absent** — 📁 [§2](../../../CLAUDE.md), and the rule
   * `Copilot` and `ShortcutsReference` both already keep.
   */
  it('🔴 no entry at all when nothing can open it', () => {
    copilot.mockReturnValue(null);

    render(<Navigation role="owner" />);

    expect(screen.queryByRole('button', { name: 'Ask Signora' })).not.toBeInTheDocument();
    // ✅ **And the rest of the group is unaffected** — one absent door does not
    // take the utilities with it.
    expect(pinnedOrder()).toEqual(['Settings', 'Shortcuts', 'Docs & support']);
  });
});

describe('📁 the design tints it, and only it', () => {
  /**
   * 📁 The design's rail row uses `var(--ai-ink)` on `var(--ai-tint)` for the
   * assistant and `var(--ink-2)` for the utilities. ⛔ **Tokens, never
   * literals** ([§20c](../../../CLAUDE.md)).
   */
  it('✅ the assistant carries the intelligence tint and Settings does not', () => {
    render(<Navigation role="owner" />);

    expect(screen.getByRole('button', { name: 'Ask Signora' }).className).toContain('ai');
    expect(screen.getByRole('link', { name: 'Settings' }).className).not.toContain('ai');
  });
});
