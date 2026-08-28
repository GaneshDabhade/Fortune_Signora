/**
 * **One navigation, in two positions** — [TASK-1461](../../../docs/BACKLOG.md).
 *
 * ## 🔴 The assertion the shell has never had
 *
 * ⛔ **The shell mounted two `nav[aria-label="Primary"]` elements and hid one
 * with `display:none`.** ⚠️ **Nothing caught it, and the reason is mechanical:
 * `getByRole` cannot see a `display:none` node** — it is removed from the
 * accessibility tree — **so every existing rail test resolved exactly one nav
 * and passed while the DOM carried two.**
 *
 * 📁 **[B-180](../../../docs/BUGS.md) is what that cost outside this suite**:
 * QE's overlap guard used `querySelector`, got the 0×0 one, skipped it as
 * zero-size, and **could not fail at any width on any page.**
 *
 * ✅ **So the count here is a DOM query and never a role query.** ⚡ **It is the
 * one assertion in this file that would have gone red before the row**, and it
 * is fire-tested: restoring a second `<nav aria-label="Primary">` anywhere in
 * the frame turns it red immediately.
 */
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { beforeEach, describe, expect, it, vi } from 'vitest';

// ⛔ **The rail and the switcher both read the workspace context**, and this
// suite is about neither — 📁 the same stub `rail-utilities.test.tsx` uses.
vi.mock('@/lib/state/workspace-provider', () => ({
  useWorkspaceContext: () => ({
    activeWorkspace: { id: 'w1', name: 'Playground', role: 'owner' },
    workspaces: [],
    setActiveWorkspace: vi.fn(),
    isLoading: false,
    error: null,
  }),
}));
vi.mock('@/components/shell/workspace-switcher', () => ({ WorkspaceSwitcher: () => null }));
vi.mock('@/components/intelligence/account-search', () => ({ AccountSearch: () => null }));
vi.mock('@/components/shell/account-menu', () => ({ AccountMenu: () => null }));
vi.mock('@/components/shell/shell-palette', () => ({ ShellPalette: () => null }));

import { AppShell } from '@/components/shell/app-shell';

/**
 * ⚡ **`Navigation` is NOT stubbed here.** ⛔ **The real rail is the subject**:
 * a stub that renders one `<nav>` would make the central count pass by
 * construction, which is the [§2](../../../CLAUDE.md) failure this row exists
 * to remove rather than to reproduce in its own test.
 */
function shell() {
  return render(
    <QueryClientProvider client={new QueryClient()}>
      <AppShell
        role="owner" roleKnown
        userId="u1"
        email="viewer@example.com" name={null}
        signOut={<button type="button">Sign out</button>}
      >
        <p>Content</p>
      </AppShell>
    </QueryClientProvider>,
  );
}

/**
 * ⛔ **`useRailCollapse` reads `window.innerWidth` in an effect**, so the band
 * is set before the render rather than asserted after it.
 */
function atWidth(px: number) {
  Object.defineProperty(window, 'innerWidth', { value: px, configurable: true });
}

/** 🔴 **The DOM, not the accessibility tree** — see the note above. */
function primaryNavigations(): NodeListOf<Element> {
  return document.querySelectorAll('nav[aria-label="Primary"]');
}

/**
 * ⚡ **The rail's container, by its own attribute rather than by walking up
 * from the `<nav>`.**
 *
 * ⚠️ **`parentElement` is what this file used first, and one layout fix broke
 * every assertion that used it** — a wrapper was inserted between the boundary
 * and the nav, and six tests failed for a reason that had nothing to do with
 * what they were asserting. 📁 **`[data-collapsed]` is the selector
 * `app-shell-rail.test.tsx` already settled on** ([B-234](../../../docs/BUGS.md)),
 * for the same reason: **name the thing, never the path to it.**
 */
function sheetContainer(): HTMLElement {
  const found = document.querySelector('[data-collapsed]');
  if (found === null) throw new Error('the shell rendered no rail');
  return found as HTMLElement;
}

beforeEach(() => {
  window.localStorage.clear();
});

describe('there is exactly one Primary landmark, at every width', () => {
  // 📁 **The design's four bands** — App Shell `breakpoints`: `< 1024px`,
  // `1024–1279`, `1280–1599`, `≥ 1600px`. ⚡ **390 is a phone; the other three
  // are one from each remaining band.**
  for (const width of [390, 1024, 1280, 1600]) {
    it(`🔴 ${width}px — one \`nav[aria-label="Primary"]\` in the DOM`, () => {
      atWidth(width);
      shell();

      expect(primaryNavigations()).toHaveLength(1);
    });
  }

  it('⛔ and no fixed bottom bar survives anywhere in the frame', () => {
    atWidth(390);
    const { container } = shell();

    // 📁 **The deleted bar was `fixed inset-x-0 bottom-0`.** ⚡ **Asserted as a
    // SHAPE rather than by component name**, because a component that no longer
    // exists cannot be imported to prove it is absent — and the shape is what a
    // customer actually met.
    expect(container.querySelector('.fixed.bottom-0')).toBeNull();
  });

  it('⛔ and `main` reserves no room for one', () => {
    atWidth(390);
    const { container } = shell();

    // 📁 `pb-20` reserved 80px at the foot of every screen below 1024, for a
    // bar that is gone. ⚠️ **[B-180](../../../docs/BUGS.md) measured that
    // padding covering the bar exactly**, which is why removing one without the
    // other would be visible rather than harmless.
    expect(container.querySelector('main')?.className).not.toContain('pb-20');
  });
});

describe('below 1024 the rail is a sheet, and the top bar opens it', () => {
  beforeEach(() => atWidth(390));

  it('📁 the trigger the design names exists — *"a top-bar button"*', () => {
    shell();

    expect(screen.getByRole('button', { name: 'Open navigation' })).toBeVisible();
  });

  it('⛔ it is closed until somebody opens it', () => {
    shell();

    // ⚡ **`invisible` is the load-bearing class and not decoration**:
    // `visibility: hidden` is what removes the sheet from the tab order and the
    // accessibility tree. ⛔ **A translate alone would leave every rail link
    // reachable by keyboard, off the side of the screen** — which is a worse
    // defect than the one this row fixes, because it is invisible to the eye.
    const sheet = sheetContainer();
    expect(sheet.classList.contains('invisible')).toBe(true);
    expect(sheet.classList.contains('-translate-x-full')).toBe(true);
  });

  it('✅ the trigger opens it', async () => {
    shell();

    await userEvent.click(screen.getByRole('button', { name: 'Open navigation' }));

    const sheet = sheetContainer();
    expect(sheet.className).not.toContain('invisible');
    expect(sheet.classList.contains('translate-x-0')).toBe(true);
  });

  it('✅ and opening it does not create a second navigation', async () => {
    shell();

    await userEvent.click(screen.getByRole('button', { name: 'Open navigation' }));

    // 🔴 **The whole row, in one line.** ⛔ **A sheet built as its own component
    // would have made this 2** — which is precisely how the product arrived at
    // two generations in the first place.
    expect(primaryNavigations()).toHaveLength(1);
  });

  it('✅ Escape closes it', async () => {
    shell();
    await userEvent.click(screen.getByRole('button', { name: 'Open navigation' }));

    await userEvent.keyboard('{Escape}');

    expect(sheetContainer().classList.contains('invisible')).toBe(true);
  });

  it('✅ its own close control closes it', async () => {
    shell();
    await userEvent.click(screen.getByRole('button', { name: 'Open navigation' }));

    // ⛔ **Escape and a backdrop are not discoverable.** ⚡ **A pointer user who
    // opened it must be able to close it the way they opened it.**
    await userEvent.click(screen.getByRole('button', { name: 'Close navigation' }));

    expect(sheetContainer().classList.contains('invisible')).toBe(true);
  });

  it('⛔ the sheet is never the 56px collapsed rail', async () => {
    // 📁 The band gives the rail `railW: 0` and then shows it whole. ⚠️ **A
    // stored collapse preference must not follow it into the sheet**: 56px of
    // icons sliding over the content is neither the rail nor the sheet.
    window.localStorage.setItem('signora.rail.collapsed.u1.compact', 'true');
    shell();

    await userEvent.click(screen.getByRole('button', { name: 'Open navigation' }));

    const sheet = sheetContainer();
    expect(sheet.style.width).toBe('232px');
  });
});

describe('at and above 1024 the rail is in flow, and nothing opens over it', () => {
  beforeEach(() => atWidth(1280));

  it('⛔ the sheet trigger is not offered', () => {
    shell();

    // ⚡ **`smalllaptop:hidden` is a CSS rule jsdom does not apply**, so this
    // asserts the class rather than visibility — ⛔ **the honest assertion,
    // and the browser journey is what proves the rule takes effect.**
    expect(screen.getByRole('button', { name: 'Open navigation' }).className).toContain(
      'smalllaptop:hidden',
    );
  });

  it('✅ the rail collapses, which is what `[` and the chevron do here', async () => {
    shell();

    const sheet = sheetContainer();
    expect(sheet.style.width).toBe('232px');

    await userEvent.click(screen.getByRole('button', { name: 'Collapse navigation' }));

    expect(sheet.style.width).toBe('56px');
  });
});
