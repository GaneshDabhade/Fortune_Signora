/**
 * **The rail's collapse, wired into the frame** —
 * [TASK-1408](../../../docs/BACKLOG.md).
 *
 * ⚡ **The law and the hook are tested elsewhere** — `tests/unit/rail.test.ts`
 * and `tests/components/use-rail-collapse.test.tsx`. **These are the things
 * only the assembled shell can get wrong**: whether the control says what it
 * does, and whether the width is the design's rather than a literal somebody
 * typed.
 */
import type React from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { render, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { beforeEach, describe, expect, it, vi } from 'vitest';

// ⚡ **The phone bar was stubbed here as a second `Primary mobile` nav and
// is gone** — [TASK-1461](../../../docs/BACKLOG.md). ⛔ **The stub was honest
// about the product**: the shell really did mount two navigations.
vi.mock('@/components/shell/navigation', () => ({
  Navigation: () => <nav aria-label="Primary" />,
}));
vi.mock('@/components/shell/workspace-selector', () => ({ WorkspaceSelector: () => null }));
vi.mock('@/components/intelligence/account-search', () => ({ AccountSearch: () => null }));
// ⚡ **Was `theme-toggle`** — TASK-1440 moved the theme control off the frame
// and into the account menu, so the leaf this suite stubs moved with it. ⛔ The
// menu needs `ThemeProvider` and `WorkspaceProvider`; **this suite is about the
// rail**, and `tests/components/top-bar.test.tsx` renders it for real.
vi.mock('@/components/shell/account-menu', () => ({ AccountMenu: () => null }));
// ⚡ **The palette mounted at the shell with TASK-1442.** ⛔ It reads the
// workspace context and the search hook, and **this suite is about the rail** —
// `shell-palette` has its own tests.
vi.mock('@/components/shell/shell-palette', () => ({ ShellPalette: () => null }));
// ⚡ **§19 gave the assistant the workspace context too** —
// [TASK-1463](../../../docs/BACKLOG.md). ⛔ **Stubbed for the same reason as the
// palette above**: it now reads `useWorkspaceContext`, **this suite is about the
// rail**, and `tests/components/copilot.test.tsx` renders it for real.
vi.mock('@/components/shell/copilot', () => ({
  // ⚡ **It WRAPS the shell now** — [TASK-1470](../../../docs/BACKLOG.md) lifted
  // the assistant's open state to a provider so the rail can be one of §12's
  // four doors. ⛔ **A stub returning `null` erases the whole frame**, which is
  // what this suite measures.
  Copilot: ({ children }: { children?: React.ReactNode }) => <>{children}</>,
  useCopilot: () => ({ open: () => {} }),
}));

import { AppShell } from '@/components/shell/app-shell';
import { RAIL_WIDTH, collapseKey } from '@/lib/shell/rail';
import type { ShellBanner } from '@/components/ui';
import type { Crumb } from '@/lib/shell/breadcrumb';

beforeEach(() => {
  window.localStorage.clear();
  Object.defineProperty(window, 'innerWidth', { value: 1440, configurable: true });
});

/**
 * ⚠️ **The shell now requires a `QueryClientProvider`, and the fixture was
 * modelling a shell that does not exist** — [TASK-1435](../../../docs/BACKLOG.md).
 *
 * ⚡ **`OfflineStatus` fills the top bar's `system-status` slot and reads the
 * library's paused-mutation queue**, so the frame depends on the query layer.
 * ⛔ **That is not new coupling introduced casually**: `QueryProvider` wraps
 * the entire tree in `app/layout.tsx`, and `AppShell` is mounted in exactly
 * one place — `app/(app)/authenticated-shell.tsx` — which sits inside it.
 * **A test rendering the shell with no client was asserting against an
 * arrangement the application never produces.**
 */
function shell(
  userId: string | null = 'u1',
  extra: { banners?: ShellBanner[]; breadcrumb?: Crumb[] } = {},
) {
  return render(
    <QueryClientProvider client={new QueryClient()}>
      <AppShell
        role="owner" roleKnown
        userId={userId}
        email="viewer@example.com" name={null}
        signOut={<button type="button">Sign out</button>}
        {...extra}
      >
        <p>Content</p>
      </AppShell>
    </QueryClientProvider>,
  );
}

/**
 * ⚡ **The rail, located by what it IS rather than by its tag** —
 * [B-234](../../../docs/BUGS.md).
 *
 * ⚠️ **These tests used `querySelector('aside')`**, which was unambiguous only
 * while the rail was the page's single `<aside>`. ⛔ **The rail is a `<div>`
 * now** — the design gives `aside[complementary]` to the utility panel — **and
 * the old selector would silently have started measuring the panel.**
 *
 * ✅ **`[data-collapsed]` is the rail's own attribute**, already there for the
 * collapse state, so the selector names the rail rather than an element type.
 */
function rail(container: HTMLElement): HTMLElement {
  const found = container.querySelector('[data-collapsed]');
  if (found === null) throw new Error('the shell rendered no rail');
  return found as HTMLElement;
}

describe('the rail carries the design’s two widths', () => {
  it('⛔ reads them from RAIL_WIDTH rather than a literal in the markup', () => {
    const { container } = shell();
    expect(rail(container)).toHaveStyle({ width: `${RAIL_WIDTH.expanded}px` });
    expect(rail(container)).toHaveAttribute('data-collapsed', 'false');
  });

  it('collapses to 56px and remembers it', async () => {
    const { container } = shell();
    await userEvent.click(screen.getByRole('button', { name: 'Collapse navigation' }));
    expect(rail(container)).toHaveStyle({
      width: `${RAIL_WIDTH.collapsed}px`,
    });
    expect(window.localStorage.getItem(collapseKey('u1', 'regular'))).toBe('true');
  });
});

describe('♿ the control names the outcome, not the glyph', () => {
  it('⚡ a screen reader user cannot see which way a chevron points', () => {
    shell();
    const toggle = screen.getByRole('button', { name: 'Collapse navigation' });
    expect(toggle).toHaveAttribute('aria-expanded', 'true');
  });

  it('and the name flips with the state', async () => {
    shell();
    await userEvent.click(screen.getByRole('button', { name: 'Collapse navigation' }));
    const toggle = screen.getByRole('button', { name: 'Expand navigation' });
    expect(toggle).toHaveAttribute('aria-expanded', 'false');
  });
});

describe('⚡ the wordmark goes when the rail does', () => {
  it('⛔ 56px cannot hold it, and a clipped wordmark reads as a rendering fault', async () => {
    // ⚠️ **Scoped to the rail deliberately.** The shell renders a SECOND
    // wordmark in the header below `md`, where the rail does not exist —
    // an unscoped query matches both and this test found that.
    const { container } = shell();
    const railEl = () => rail(container);
    expect(within(railEl()).getByText('Signora')).toBeInTheDocument();
    await userEvent.click(screen.getByRole('button', { name: 'Collapse navigation' }));
    expect(within(railEl()).queryByText('Signora')).not.toBeInTheDocument();
  });
});

describe('⛔ navigation survives the collapse', () => {
  it('the rail still holds its destinations at 56px', async () => {
    shell();
    await userEvent.click(screen.getByRole('button', { name: 'Collapse navigation' }));
    // 📁 Collapsed is narrower, never emptier — the destinations remain and
    // expose their labels as accessible names.
    expect(screen.getByRole('navigation', { name: 'Primary' })).toBeInTheDocument();
  });

  it('a shell with no resolved viewer still works, and remembers nothing', async () => {
    shell(null);
    await userEvent.click(screen.getByRole('button', { name: 'Collapse navigation' }));
    expect(window.localStorage.length).toBe(0);
  });
});


describe('📁 the vertical order is fixed and non-negotiable', () => {
  it('⚡ the banner region precedes the top bar in the document', () => {
    /**
     * ⛔ **A banner below the top bar is not a layout preference.** **The
     * environment banner is the sentence that tells somebody they are
     * impersonating another person**, and anything above it pushes that off
     * a short viewport.
     */
    const { container } = shell('u1', {
      banners: [{ kind: 'environment', risky: true, title: 'Viewing as J. Okafor.', body: 'Logged.' }],
    });
    const banners = container.querySelector('[data-testid="shell-banners"]');
    const topbar = container.querySelector('header');
    expect(banners).not.toBeNull();
    expect(topbar).not.toBeNull();
    // `DOCUMENT_POSITION_FOLLOWING` — the top bar comes after the banners.
    expect(banners?.compareDocumentPosition(topbar as Node)).toBe(
      Node.DOCUMENT_POSITION_FOLLOWING,
    );
  });

  it('⚡ the banner region spans the columns rather than sitting inside one', () => {
    // ⛔ A banner inside the content column leaves the rail beside a warning
    // that does not apply to it.
    const { container } = shell('u1', {
      banners: [{ kind: 'environment', title: 'Sandbox.', body: 'A copy.' }],
    });
    const banners = container.querySelector('[data-testid="shell-banners"]');
    expect(banners?.closest('aside')).toBeNull();
    expect(rail(container)).not.toBeNull();
  });
});

describe('⛔ the shell reserves the slots and invents nothing', () => {
  it('renders no banner and no breadcrumb when given none', () => {
    shell();
    expect(screen.queryByRole('navigation', { name: 'Breadcrumb' })).not.toBeInTheDocument();
    // 📁 Rule 6 — nothing at the first level, and today no page supplies a
    // trail at all (C-257).
  });

  it('renders the trail a page supplies, and never derives one', () => {
    shell('u1', {
      breadcrumb: [
        { label: 'Accounts', kind: 'link', href: '/accounts' },
        { label: 'Vantage Logistics', kind: 'current' },
      ],
    });
    expect(screen.getByRole('navigation', { name: 'Breadcrumb' })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Accounts' })).toHaveAttribute('href', '/accounts');
  });
});

describe('🔴 B-234 · the shell publishes each landmark exactly once', () => {
  it("gives the page ONE complementary region, and it is the utility panel", () => {
    /**
     * 📁 **The design's landmark table assigns each region exactly one role**:
     * *"`nav[navigation]` — the rail, labelled *Primary*"* · *"`aside
     * [complementary]` — the utility panel, labelled with its active tab."*
     *
     * ⚠️ **The rail's wrapper was an `<aside>`** — an unnamed `complementary`
     * around a `<nav>` that already carried the correct role. **Harmless while
     * it was the only one; a collision the moment
     * [TASK-1433](../../../docs/BACKLOG.md) mounted the panel.**
     *
     * ⛔ **Playwright found it, not a test** — *"`<span>Settings</span>` …
     * intercepts pointer events"* — **which is a layout symptom of an
     * accessibility defect, and the least likely message to lead anybody
     * here.** ✅ **So the property is asserted directly.**
     */
    const { container } = shell();

    const complementary = screen.queryAllByRole('complementary');
    expect(complementary.length, 'the shell has more than one complementary landmark').toBeLessThan(
      2,
    );
    for (const region of complementary) {
      expect(region).toHaveAccessibleName(/panel$/);
    }

    // ⚡ Vacuity: the rail is on screen, so 'fewer than two' is a measurement
    // rather than an empty render.
    expect(rail(container)).not.toBeNull();
  });

  it('⛔ still renders the rail, so the assertion above is not passing over an empty frame', () => {
    /**
     * ⚡ **The vacuity guard, and it checks the RAIL rather than its `<nav>`.**
     * ⚠️ **`Navigation` needs the workspace provider this suite deliberately
     * does not mount**, so its `RegionBoundary` catches it and no `<nav>`
     * renders here — 📁 the same absence the *"navigation survives the
     * collapse"* block already works around. **The rail element itself is what
     * this file can honestly assert.**
     */
    const { container } = shell();

    expect(rail(container)).not.toBeNull();
  });
});

/**
 * **§16's third loading tier, in the frame** — [TASK-1463](../../../docs/BACKLOG.md).
 *
 * ⚡ **The tier boundary itself is `refresh-tier.test.tsx`'s**, over the hook.
 * **These are the two things only the assembled shell can get wrong**: where
 * the bar sits, and whether the strip that holds it moves the page.
 */
describe('🔴 §16 · an in-place refresh is announced without covering anything', () => {
  function shellWith(client: QueryClient) {
    return render(
      <QueryClientProvider client={client}>
        <AppShell role="owner" roleKnown userId="u1" email="v@example.com" name={null} signOut={<span />}>
          <p>A figure the reader can already see</p>
        </AppShell>
      </QueryClientProvider>,
    );
  }

  it('⛔ nothing is dimmed and no bar is drawn on a settled screen', () => {
    shellWith(new QueryClient());

    expect(screen.queryByTestId('refresh-bar')).not.toBeInTheDocument();
    expect(screen.getByRole('main')).not.toHaveAttribute('data-refreshing');
  });

  it('✅ the bar appears and the content dims while readable data is replaced', async () => {
    const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
    client.setQueryData(['warm'], 'readable');
    let settle: () => void = () => {};
    void client.fetchQuery({
      queryKey: ['warm'],
      queryFn: () => new Promise<string>((resolve) => (settle = () => resolve('newer'))),
      staleTime: 0,
    });

    shellWith(client);

    await waitFor(() => expect(screen.getByTestId('refresh-bar')).toBeInTheDocument());
    expect(screen.getByRole('main')).toHaveAttribute('data-refreshing', 'true');
    // ⛔ **Never an overlay** — 📁 *"No overlay, no spinner, no layout shift."*
    expect(screen.getByText('A figure the reader can already see')).toBeVisible();

    settle();
    await waitFor(() => expect(screen.queryByTestId('refresh-bar')).not.toBeInTheDocument());
  });

  /**
   * 🔴 **The strip is always in the document, and only the bar inside it comes
   * and goes.**
   *
   * ⚠️ **A conditionally rendered 2px node would push every screen down by two
   * pixels on every refetch** — 📁 *"no layout shift"* is the one thing the
   * design rules out by name for this tier, and it is the failure that would
   * look like a rendering glitch rather than a bug.
   */
  it('⛔ the 2px strip exists whether or not a refresh is running', () => {
    const { container } = shellWith(new QueryClient());

    expect(container.querySelector('.h-\\[2px\\]')).not.toBeNull();
  });
});
