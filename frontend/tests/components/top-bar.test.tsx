import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { render, screen, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it, vi } from 'vitest';

import { TopBar } from '@/components/shell/top-bar';
import { ACCOUNT_MENU_ITEMS } from '@/components/shell/account-menu';
import { THEMES } from '@/lib/design/theme';
import { SEARCH_WIDTH, SLOT_SPEC, TOP_BAR_SLOTS } from '@/lib/shell/top-bar';
import { ThemeProvider } from '@/lib/state/theme-provider';
import { WorkspaceProvider } from '@/lib/state/workspace-provider';

/**
 * **The top bar's five slots** — [TASK-1440](../../../docs/BACKLOG.md).
 *
 * ⛔ **These assertions read `lib/shell/top-bar.ts` rather than restating it.**
 * 📁 [D-137](../../../docs/DECISION_REGISTER.md) — *"the copy is always the one
 * somebody reads"* — applies to a test as much as to a specification: **a test
 * carrying its own copy of the slot order would pass while the component and
 * the law disagreed.**
 */

// ⚡ Leaves this suite is not about. `AccountSearch` and `WorkspaceSelector`
// each need their own network fixtures, and neither is a slot's behaviour.
vi.mock('@/components/intelligence/account-search', () => ({
  AccountSearch: () => <div data-testid="account-search" />,
}));
// ⚡ **Kept after the switcher left the bar, and deliberately.** If a future
// change re-mounts `WorkspaceSelector` here, the assertion below sees it — ⛔ a
// removed mock would make that test pass by accident.
vi.mock('@/components/shell/workspace-selector', () => ({
  WorkspaceSelector: () => <div data-testid="workspace-selector" />,
}));
// ⚡ **The panel reads the workspace context and the query client**, and this
// suite is about the frame — the same reason the account menu is stubbed.
vi.mock('@/components/shell/notifications', () => ({ Notifications: () => null }));

function bar(role: 'owner' | 'member' | null = 'owner') {
  return render(
    <QueryClientProvider client={new QueryClient()}>
      <ThemeProvider>
        <WorkspaceProvider>
          <TopBar
            breadcrumb={[]}
            role={role}
            email="marta@northwind.example" name={null}
            signOut={<button type="button">Sign out</button>}
          />
        </WorkspaceProvider>
      </ThemeProvider>
    </QueryClientProvider>,
  );
}

describe('📁 the slots the design draws', () => {
  it('✅ renders every slot that has something to render, in the design\'s order', () => {
    const { container } = bar();
    const rendered = [...container.querySelectorAll('[data-slot]')].map(
      (el) => el.getAttribute('data-slot') as string,
    );

    // ⛔ **The expected order is DERIVED from the law**, filtered to the slots
    // this row could build. A slot appearing out of order fails here; a slot
    // renamed in `top-bar.ts` and not here fails to compile.
    // ⚡ **`help` joined the buildable set** when [TASK-1420](../../../docs/BACKLOG.md)
    // built `/help` — 📁 [C-275](../../../docs/LANE_COORDINATION.md) had it
    // absent *because no help route existed*, which is now false.
    const buildable = TOP_BAR_SLOTS.filter((s) =>
      (['breadcrumb', 'search', 'system-status', 'help', 'account'] as const).includes(
        s as 'breadcrumb' | 'search' | 'system-status' | 'help' | 'account',
      ),
    );
    expect(rendered).toEqual([...buildable]);
  });

  it('⛔ notifications is still ABSENT, because nothing publishes one', () => {
    /**
     * 🔴 **This asserted TWO absences and now asserts one.** ⚡ **`help` was
     * absent for a reason that stopped being true**: [C-275](../../../docs/LANE_COORDINATION.md)
     * recorded it as having no destination, and
     * [TASK-1420](../../../docs/BACKLOG.md) built `/help`. ✅ **The test was
     * written to be loud on that day and it was.**
     *
     * ⛔ **Notifications has not changed**: nothing in the platform publishes a
     * notification, and a bell opening an empty 400px panel is the defect
     * [TASK-1433](../../../docs/BACKLOG.md) is parked for.
     */
    const { container } = bar();
    expect(container.querySelector('[data-slot="notifications"]')).toBeNull();
    expect(container.querySelector('[data-slot="help"]')).not.toBeNull();
  });

  it('📁 the search slot carries the design\'s resting geometry, from SLOT_SPEC', () => {
    const { container } = bar();
    const search = container.querySelector('[data-slot="search"]') as HTMLElement;
    expect(search.style.width).toBe(`${SEARCH_WIDTH.rest}px`);
    expect(search.style.height).toBe(`${SLOT_SPEC.search.height}px`);
  });

  it('✅ the workspace switcher has LEFT the bar', () => {
    /**
     * 🔴 **This test was written to state today's truth so the day it changed
     * would be loud, and today is that day.** ⚡ It previously asserted the
     * switcher was present and marked *not a slot*.
     *
     * 📁 [TASK-1440](../../../docs/BACKLOG.md) said it should leave and this
     * lane kept it, because [TASK-1441](../../../docs/BACKLOG.md) — the rail's
     * first child, where the design puts it — **was blocked, and removing a
     * control whose destination does not exist deletes it rather than moving
     * it.** ✅ **[D-225](../../../docs/DECISION_REGISTER.md) §4 ruled that
     * reasoning and [C-274](../../../docs/LANE_COORDINATION.md) closes here.**
     *
     * ⛔ **The bar is the design's five slots now**, and the switcher is
     * asserted in `tests/components/workspace-switcher.test.tsx`.
     */
    const { container } = bar();
    expect(screen.queryByTestId('workspace-selector')).toBeNull();
    expect(container.querySelector('[data-not-a-slot="workspace-switcher"]')).toBeNull();
  });
});

describe('🔴 what left the frame, and it must not come back', () => {
  it('⛔ no theme control and no sign-out button sit in the bar itself', () => {
    const { container } = bar();
    const header = container.querySelector('header') as HTMLElement;

    // 📁 Shell rule 02 — *"No module may add anything to the top bar"* — which
    // `lib/shell/constitution.ts` exports as code while the frame beside it
    // broke it. Both controls are now one click behind the avatar.
    expect(within(header).queryByRole('group', { name: 'Theme' })).toBeNull();
    expect(within(header).queryByRole('button', { name: 'Sign out' })).toBeNull();
  });
});

describe('📁 slot five — the account menu', () => {
  it('✅ opens on the avatar and states the identity', async () => {
    bar('owner');
    await userEvent.click(
      screen.getByRole('button', { name: /Account menu for marta@northwind.example/ }),
    );
    expect(screen.getByRole('menu', { name: 'Account' })).toBeInTheDocument();
    expect(screen.getByText('marta@northwind.example')).toBeInTheDocument();
    // 📁 *"Role is a brand-tint chip so permission questions are answered
    // without navigating."*
    expect(screen.getByText('owner')).toBeInTheDocument();
  });

  it('✅ Sign out and the three-way theme control are inside it', async () => {
    bar();
    await userEvent.click(screen.getByRole('button', { name: /Account menu/ }));
    const menu = screen.getByRole('menu', { name: 'Account' });
    expect(within(menu).getByRole('button', { name: 'Sign out' })).toBeInTheDocument();

    // 📁 *"Theme as a three-way control makes 'follow the OS' discoverable
    // rather than hidden."*
    //
    // ⛔ **The control is `ThemeToggle`, reused rather than reimplemented**, so
    // this asserts the count against the canonical `THEMES` and does not
    // restate its labels — ⚡ **an assertion naming 'System' would have been a
    // second copy of a caption `theme-toggle.tsx` already owns**, and it was
    // wrong: the accessible name is *"Match system theme"*.
    const group = within(menu).getByRole('group', { name: 'Theme' });
    expect(within(group).getAllByRole('button')).toHaveLength(THEMES.length);
    expect(within(group).getByRole('button', { pressed: true })).toBeInTheDocument();
  });

  it('⛔ the three items with no destination are absent, not disabled', async () => {
    bar();
    await userEvent.click(screen.getByRole('button', { name: /Account menu/ }));
    const menu = screen.getByRole('menu', { name: 'Account' });

    const withHref = ACCOUNT_MENU_ITEMS.filter((i) => i.href !== null);
    const without = ACCOUNT_MENU_ITEMS.filter((i) => i.href === null);

    // ⚡ **Vacuity guard.** If every item gained an href the second loop would
    // assert nothing, so the split itself is asserted first.
    expect(withHref.length).toBeGreaterThan(0);
    expect(without.length).toBeGreaterThan(0);

    for (const item of withHref) {
      expect(within(menu).getByRole('menuitem', { name: item.label })).toHaveAttribute(
        'href',
        item.href as string,
      );
    }
    for (const item of without) {
      expect(within(menu).queryByText(item.label)).toBeNull();
    }
  });

  it('♿ Escape closes it and returns focus to the avatar', async () => {
    bar();
    const avatar = screen.getByRole('button', { name: /Account menu/ });
    await userEvent.click(avatar);
    expect(screen.getByRole('menu', { name: 'Account' })).toBeInTheDocument();

    // 📁 *"Esc closes and returns focus to the avatar."* ⚡ The second half is
    // the one usually dropped, so it is the one asserted.
    await userEvent.keyboard('{Escape}');
    expect(screen.queryByRole('menu', { name: 'Account' })).toBeNull();
    expect(avatar).toHaveFocus();
  });

  it('⛔ a null role renders no chip rather than guessing one', async () => {
    bar(null);
    await userEvent.click(screen.getByRole('button', { name: /Account menu/ }));
    const menu = screen.getByRole('menu', { name: 'Account' });
    expect(within(menu).queryByText('owner')).toBeNull();
    expect(within(menu).queryByText('member')).toBeNull();
  });
});
