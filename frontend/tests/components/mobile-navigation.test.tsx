/**
 * The product has navigation on a phone. **CX-07 · [B-203](../../../docs/BUGS.md).**
 *
 * **Below `768px` there was none at all.** The shell hides the sidebar and
 * nothing replaced it, so a signed-in customer on a phone could reach the
 * screen they landed on and nothing else. It sat 🟠 and *undecided* — *"whether
 * it is a defect or a non-goal depends on a product decision nobody has made"*
 * — until [C-205](../../../docs/LANE_COORDINATION.md) was ruled: **a phone is
 * in scope.**
 *
 * **No test could have caught it, and that is the more useful finding.** Every
 * component test renders at one implied width and asserts what is on screen;
 * *what disappears at a breakpoint* is invisible to jsdom, which has no layout.
 * So these assert the two things that **are** checkable — that the markup
 * exists and that the same guard applies to it — and the viewport half is
 * named here as a known limit rather than left to look covered.
 */
import { render, screen, within } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

import { MobileNavigation } from '@/components/shell/navigation';

vi.mock('next/navigation', () => ({ usePathname: () => '/' }));

/**
 * 🔴 **[B-233](../../../docs/BUGS.md)** — ⚠️ **this mock did not exist, and its
 * absence is why the defect shipped.** ⛔ **`MobileNavigation` mapped
 * `RAIL_DESTINATIONS` raw**, so `/w/[workspace]/home` reached a `<Link>` as a
 * literal — **and a dynamic href THROWS in the App Router**, taking the whole
 * navigation region down on every authenticated screen at every width, because
 * the phone bar is hidden by CSS and still mounted.
 *
 * ⚡ **Stubbed the way [`navigation-rail.test.tsx`](navigation-rail.test.tsx)
 * stubs it** — the real provider brings a query client and a network fixture.
 */
let activeWorkspace: { id: string; name: string } | null = { id: 'w1', name: 'Northwind' };
vi.mock('@/lib/state/workspace-provider', () => ({
  useWorkspaceContext: () => ({
    activeWorkspace,
    workspaces: [],
    setActiveWorkspace: vi.fn(),
    isLoading: false,
    error: null,
  }),
}));

describe('a phone has a way to get somewhere else', () => {
  it('offers the same destinations the sidebar does', () => {
    render(<MobileNavigation role="owner" />);

    const bar = screen.getByRole('navigation', { name: /primary/i });
    expect(within(bar).getByRole('link', { name: /attention/i })).toBeInTheDocument();
    expect(within(bar).getByRole('link', { name: /your business/i })).toBeInTheDocument();
    expect(within(bar).getByRole('link', { name: /settings/i })).toBeInTheDocument();
  });

  it('keeps the labels rather than asking a first-time reader to decode an icon', () => {
    // *Your business* is not a word a briefcase carries, and a customer who
    // has to guess what a control does is a customer who does not press it.
    render(<MobileNavigation role="owner" />);

    expect(screen.getByText('Your business')).toBeVisible();
  });

  it('tells a screen reader which destination it is on', () => {
    render(<MobileNavigation role="owner" />);

    expect(screen.getByRole('link', { name: /attention/i })).toHaveAttribute(
      'aria-current',
      'page',
    );
  });
});

describe('the guard is the same one, applied to the same list', () => {
  it('shows Settings to a member as RESTRICTED, not as a link and not hidden', () => {
    /**
     * 🔴 **REVERSED by TASK-1439, and the old assertion passed through the
     * change without noticing** — which is why it is rewritten rather than
     * deleted. It queried for a `link` named Settings; the restricted
     * rendering is a `span`, **so the query kept returning null and the test
     * kept passing while the behaviour it named had inverted.**
     *
     * ⚠️ **A test that survives the reversal of its own subject is asserting
     * the wrong thing** ([§2](../../../CLAUDE.md)), and the fix is to assert
     * the property rather than the absence of one element type.
     *
     * 📁 The design, carried in [`lib/shell/rail.ts`](../../lib/shell/rail.ts)
     * rule ①: *"Restricted destinations stay visible at 45% with a lock…
     * a hidden destination teaches a person the feature does not exist, so
     * they ask for the wrong thing or ask nobody."*
     *
     * ⛔ **Still not reachable**: it is not a link, so there is nothing to
     * follow — and 📁 Casbin refuses the request regardless
     * ([§20c](../../../CLAUDE.md)). **One list, two renderings**, and the
     * restriction rule is the design's rather than the desktop's.
     */
    render(<MobileNavigation role="member" />);

    // Present…
    expect(screen.getByLabelText(/settings — restricted/i)).toBeInTheDocument();
    // …and not followable.
    expect(screen.queryByRole('link', { name: /settings/i })).not.toBeInTheDocument();
  });

  it('still offers a member the destinations they can reach', () => {
    render(<MobileNavigation role="member" />);

    expect(screen.getByRole('link', { name: /attention/i })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /your business/i })).toBeInTheDocument();
  });

  it('offers nothing at all before a role has resolved', () => {
    // `can(null, …)` fails closed, and an unguarded route stays open — so this
    // asserts the shape rather than emptiness: Settings is the guarded one.
    render(<MobileNavigation role={null} />);

    expect(screen.queryByRole('link', { name: /settings/i })).not.toBeInTheDocument();
  });
});

describe('it is built for a thumb, not a cursor', () => {
  it('gives every destination a touch-sized target', () => {
    // **Roughly 44px is the floor** a thumb reliably hits. Asserted on the
    // class rather than on layout because jsdom computes none — the honest
    // half of a check whose other half needs a real viewport.
    render(<MobileNavigation role="owner" />);

    for (const link of screen.getAllByRole('link')) {
      expect(link.className).toContain('min-h-11');
    }
  });

  it('clears the home indicator on a phone that has one', () => {
    const { container } = render(<MobileNavigation role="owner" />);

    expect(container.querySelector('nav')?.className).toContain('safe-area-inset-bottom');
  });

  it('is hidden once the sidebar exists, so there is never a second navigation', () => {
    /**
     * ⚡ **The band moved from `md` to `smalllaptop`** —
     * [TASK-1443](../../../docs/BACKLOG.md). ⛔ **`md:` was Tailwind's 768**,
     * so the rail vanished 256px earlier than the design says and this bar
     * appeared on a small laptop that should have had the collapsed rail
     * instead. 📁 The design's band is *"< 1024px: rail becomes a sheet"*.
     *
     * ✅ **The property is unchanged and is what this test is about**: the two
     * navigations are never both visible.
     */
    const { container } = render(<MobileNavigation role="owner" />);
    expect(container.querySelector('nav')?.className).toContain('smalllaptop:hidden');
  });
});

describe('🔴 B-233 · the phone bar resolves `[workspace]` exactly as the rail does', () => {
  it('fills the segment from the active workspace', () => {
    render(<MobileNavigation role="owner" />);

    const home = screen.getByRole('link', { name: /home/i });
    expect(home).toHaveAttribute('href', '/w/w1/home');
  });

  it('⛔ drops the entry when no workspace is known, rather than linking half a path', () => {
    activeWorkspace = null;
    render(<MobileNavigation role="owner" />);

    expect(screen.queryByRole('link', { name: /home/i })).toBeNull();
    // The rest of the bar is unaffected.
    expect(screen.getByRole('link', { name: /attention/i })).toBeInTheDocument();
    activeWorkspace = { id: 'w1', name: 'Northwind' };
  });

  it('🔴 NO rendered href carries an unresolved segment — the general form of the defect', () => {
    /**
     * ⚡ **Asserted over every link rather than over `Home`**, because the
     * defect was not about Home: **it was about one renderer not applying a
     * resolution the other did.** ⛔ **A `[` in a rendered href is a dynamic
     * route pattern that escaped**, whichever entry grows one next.
     */
    render(<MobileNavigation role="owner" />);

    for (const link of screen.getAllByRole('link')) {
      expect(link.getAttribute('href'), link.textContent ?? '').not.toContain('[');
    }
  });
});
