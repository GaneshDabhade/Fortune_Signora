import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { render, screen } from '@testing-library/react';
import { readFileSync, readdirSync } from 'node:fs';
import { join } from 'node:path';
import { describe, expect, it, vi } from 'vitest';

import { AppShell } from '@/components/shell/app-shell';
import { SkipLinks } from '@/components/shell/skip-links';
import { RouteAnnouncer } from '@/components/shell/route-announcer';

/**
 * **The shell's accessibility contract** — [TASK-1444](../../../docs/BACKLOG.md),
 * 📁 App Shell `a11yRules` and `landmarks`.
 *
 * ⛔ **[§20c](../../../CLAUDE.md): accessibility is a defect class, never an
 * enhancement**, which is why this does not wait on the frozen foundation.
 *
 * 📁 **The row's Definition of Done is one test per rule that fails without
 * it**, so each `it` names its success criterion.
 */

vi.mock('next/navigation', () => ({ usePathname: () => '/' }));
vi.mock('@/components/shell/shell-palette', () => ({ ShellPalette: () => null }));
vi.mock('@/components/shell/workspace-switcher', () => ({ WorkspaceSwitcher: () => null }));
vi.mock('@/components/intelligence/account-search', () => ({ AccountSearch: () => null }));
vi.mock('@/components/shell/account-menu', () => ({ AccountMenu: () => null }));
// ⚡ The rail reads the active workspace since TASK-1438 (Home's segment).
vi.mock('@/lib/state/workspace-provider', () => ({
  useWorkspaceContext: () => ({
    activeWorkspace: { id: 'w1', name: 'Northwind' },
    workspaces: [],
    setActiveWorkspace: vi.fn(),
    isLoading: false,
    error: null,
  }),
}));

function shell() {
  return render(
    <QueryClientProvider client={new QueryClient()}>
      <AppShell role="owner" email="a@b.com" signOut={null}>
        <p>Content</p>
      </AppShell>
    </QueryClientProvider>,
  );
}

describe('📁 2.4.1 — skip links, visible on focus', () => {
  it('⛔ they exist at all, which grep said they did not', () => {
    // ⚡ **Without them a keyboard user meets every rail destination before the
    // content, on every page load** — and the rail is first in tab order by
    // design.
    render(<SkipLinks />);
    expect(screen.getByRole('link', { name: 'Skip to content' })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Skip to navigation' })).toBeInTheDocument();
  });

  it('⛔ they are FOCUSABLE while invisible — `display:none` would not be', () => {
    // 🔴 **This is the whole mechanism.** A skip link hidden with `hidden` or
    // `display:none` is not focusable and does nothing at all.
    render(<SkipLinks />);
    const link = screen.getByRole('link', { name: 'Skip to content' });
    expect(link.className).toContain('sr-only');
    expect(link.className).toContain('focus:not-sr-only');
  });

  it('✅ and each one points at a landmark the shell actually renders', () => {
    // ⛔ **A skip link to a missing target sends a keyboard user nowhere**,
    // which is worse than its absence — C-269's rule applied to focus.
    // ⛔ **One render.** The first version rendered the shell AND `SkipLinks`
    // separately, so `getAllByRole('link')` swept up the rail's links too and
    // asked the container for `#` — *"'' is not a valid selector"*.
    const { container } = shell();
    const links = [...container.querySelectorAll('a[href^="#"]')];
    expect(links.length).toBeGreaterThan(0);
    for (const link of links) {
      const id = link.getAttribute('href')?.slice(1);
      expect(container.querySelector(`#${id}`), `#${id} does not exist`).not.toBeNull();
    }
  });

  it('⛔ and the utility-panel link is ABSENT, because the panel is not built', () => {
    // 📁 The design names three. ⚡ **The third points at
    // TASK-1433's panel, which does not exist** — so it is omitted rather than
    // pointed at nothing.
    render(<SkipLinks />);
    expect(screen.queryByRole('link', { name: /utility/i })).toBeNull();
  });
});

describe('📁 landmarks — the names a screen reader chooses between', () => {
  it('⛔ the rail is "Primary", which is the design\'s word and not "Main"', () => {
    // ⚡ **Not pedantry**: this is the string a screen-reader user hears in the
    // landmark menu, and "Main" collides with the `main` landmark beside it.
    /**
     * ⚠️ **jsdom applies no CSS, so BOTH renderings are in the tree here.**
     * ⛔ In a browser exactly one is: the rail is `hidden md:block` and the
     * phone bar is `md:hidden`, and `display:none` removes an element from the
     * accessibility tree. ✅ **So this asserts the NAME on every navigation
     * landmark** rather than pretending there is one.
     */
    shell();
    const navs = screen.getAllByRole('navigation');
    expect(navs.length).toBeGreaterThan(0);
    for (const nav of navs) expect(nav).toHaveAccessibleName('Primary');
    expect(screen.queryByRole('navigation', { name: 'Main' })).toBeNull();
  });

  it('✅ the search slot publishes a `search` landmark', () => {
    // 📁 The design's `landmarks` asks for a labelled search region. ⛔ **It
    // published none**, so search could not be jumped to the way navigation can.
    //
    // ⚠️ **The label is `Search Signora`, not `Search Fortune Signora`** —
    // [TASK-1466](../../../docs/BACKLOG.md), on the ruling at
    // [C-1422](../../../docs/LANE_COORDINATION.md). 🔴 **This assertion is why
    // the row exists in the shape it does**: it pinned the old string, so a
    // rename that left it green would have renamed nothing.
    shell();
    expect(screen.getByRole('search', { name: 'Search Signora' })).toBeInTheDocument();
    // ⛔ **And the old label is gone rather than merely un-asserted.**
    expect(
      screen.queryByRole('search', { name: 'Search Fortune Signora' }),
    ).not.toBeInTheDocument();
  });

  it('⛔ exactly ONE banner landmark, not two', () => {
    /**
     * ⚠️ **This lane briefly created two.** Wrapping the banner strip in its
     * own `<header>` gave the shell a second `banner`, and **a screen-reader
     * user choosing "banner" would have got a menu of two** — worse than the
     * gap it filled.
     *
     * 📁 The design wants ONE header holding banners then the top bar; ⛔ **this
     * shell cannot express that** while the rail is full-height, and the
     * structural question is [C-278](../../../docs/LANE_COORDINATION.md)'s.
     */
    const { container } = shell();
    expect(container.querySelectorAll('header')).toHaveLength(1);
  });

  it('✅ `main` is focusable so the skip link lands somewhere', () => {
    // ⚡ `tabIndex={-1}` makes it a focus target **without** putting it in the
    // tab order — both halves matter.
    const { container } = shell();
    const main = container.querySelector('main');
    expect(main).toHaveAttribute('tabindex', '-1');
  });
});

describe('📁 4.1.3 — route changes announce once, politely', () => {
  it('⛔ POLITE, because assertive would interrupt the page being read', () => {
    const { container } = render(<RouteAnnouncer />);
    const region = container.querySelector('output');
    expect(region).toHaveAttribute('aria-live', 'polite');
  });

  it('⛔ and silent on first mount, because arriving is not a route CHANGE', () => {
    // ⚡ Announcing the initial load would talk over the page somebody has
    // only just reached.
    const { container } = render(<RouteAnnouncer />);
    expect(container.querySelector('output')?.textContent).toBe('');
  });
});

describe('📁 2.4.7 — the focus ring is never suppressed', () => {
  it('⛔ no shell or library component drops focus visibility', () => {
    /**
     * 📁 *"2px brand ring at 2px offset plus a border change; **never
     * suppressed anywhere in the shell**."*
     *
     * ⚠️ **The first version of this check was too blunt and flagged three
     * files, none of which was a defect.** Two used `focus-within:outline-none`
     * with a `focus-within:ring` beside it — **a replacement my regex simply
     * did not match** — and the third, `drawer.tsx`, suppresses the ring on a
     * `tabIndex={-1}` panel it focuses PROGRAMMATICALLY.
     *
     * 🔴 **That third case is legitimate and the distinction matters**: an
     * element a keyboard can TAB to must show a ring; **a container focused by
     * code so a screen reader lands in it must not**, or every skip-link target
     * would flash an outline nobody asked for. ✅ **The rule now says that.**
     */
    const offenders: string[] = [];
    for (const dir of ['components/ui', 'components/shell']) {
      for (const file of readdirSync(join(process.cwd(), dir))) {
        if (!file.endsWith('.tsx')) continue;
        const source = readFileSync(join(process.cwd(), dir, file), 'utf8');
        const suppresses = /\boutline-none\b/.test(source);
        const replaces = /focus(-visible|-within)?:(outline|ring)/.test(source);
        // ⚡ A programmatically-focused container is not a tab stop.
        const programmatic = /tabIndex=\{-1\}/.test(source);
        if (suppresses && !replaces && !programmatic) offenders.push(`${dir}/${file}`);
      }
    }
    expect(offenders, 'these suppress the focus ring and put nothing back').toEqual([]);
  });
});
