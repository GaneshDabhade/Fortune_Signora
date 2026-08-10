import { render, screen, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it, vi } from 'vitest';

import { Navigation, RAIL_DESTINATIONS } from '@/components/shell/navigation';
import { MAX_DEPTH, MAX_DESTINATIONS, railViolations } from '@/lib/shell/rail';
import { workspaceHome } from '@/lib/entry';

/**
 * **The navigation rail** — [TASK-1439](../../../docs/BACKLOG.md), under
 * [D-225](../../../docs/DECISION_REGISTER.md).
 *
 * ⛔ **These read [`lib/shell/rail.ts`](../../lib/shell/rail.ts) rather than
 * restating it.** ⚠️ **Six of that file's exports had ZERO production callers
 * before this row** — the rail's rules were written, tested, and never
 * consulted by the rail. **A test that carried its own copy of the limits
 * would have kept that true.**
 */

// ⚡ The rail reads the current route to mark the active destination. `/` is
// Attention's, so the active-state assertion below has something to assert.
vi.mock('next/navigation', () => ({ usePathname: () => '/' }));

/**
 * ⚡ **The rail reads the active workspace since
 * [TASK-1438](../../../docs/BACKLOG.md)** — Home's `[workspace]` segment is
 * filled from it. ⛔ **Stubbed rather than wrapped in the real provider**:
 * this suite is about the rail's own rules, and the provider brings a query
 * client and a network fixture with it.
 */
let activeWorkspace: { id: string; name: string } | null = {
  id: 'w1',
  name: 'Northwind',
};
vi.mock('@/lib/state/workspace-provider', () => ({
  useWorkspaceContext: () => ({
    activeWorkspace,
    workspaces: [],
    setActiveWorkspace: vi.fn(),
    isLoading: false,
    error: null,
  }),
}));

describe('🔴 the rail obeys its own law', () => {
  it('✅ the real destination list passes railViolations', () => {
    // ⚡ **Against the SHIPPED list, not a fixture.** `railViolations` existed
    // and nothing ran it; this is what makes it a rule.
    expect(railViolations(RAIL_DESTINATIONS)).toEqual([]);
  });

  it('⛔ and railViolations can still fail, so the check is not decorative', () => {
    /**
     * 📁 [§2](../../../CLAUDE.md) — **a guard that cannot fail is
     * documentation pretending to be code.** ⚡ Each clause is provoked
     * separately so a passing suite means three rules hold, not one.
     */
    const tooMany = Array.from({ length: MAX_DESTINATIONS + 1 }, (_, i) => ({
      id: `d${i}`,
      label: `Destination ${i}`,
      depth: 1,
    }));
    expect(railViolations(tooMany)).toHaveLength(1);

    const tooDeep = [{ id: 'x', label: 'Too deep', depth: MAX_DEPTH + 1 }];
    expect(railViolations(tooDeep)).toHaveLength(1);

    // 📁 *"a dot means unread and only Signals uses it."*
    const wrongDot = [{ id: 'business', label: 'Your business', depth: 1, unread: true }];
    expect(railViolations(wrongDot)).toHaveLength(1);
  });
});

describe('📁 D-225 §4 — currently reachable navigation is not removed', () => {
  it('🔴 / and /business survive the rebuild, though the design names neither', () => {
    /**
     * ⛔ ***"Do not remove currently valid, reachable navigation that is
     * required for an existing user role."*** ⚡ **This lane argued it in
     * [C-269](../../../docs/LANE_COORDINATION.md) and
     * [D-225](../../../docs/DECISION_REGISTER.md) ruled it**, so the
     * assertion is against a ruling rather than a preference.
     */
    render(<Navigation role="owner" />);
    const rail = screen.getByRole('navigation', { name: 'Primary' });

    expect(within(rail).getByRole('link', { name: 'Attention' })).toHaveAttribute('href', '/');
    expect(within(rail).getByRole('link', { name: 'Your business' })).toHaveAttribute(
      'href',
      '/business',
    );
  });

  it('⛔ nothing without a destination is rendered', () => {
    /**
     * 📁 Nine of the design's thirteen entries have no route
     * ([C-269](../../../docs/LANE_COORDINATION.md)). ⚡ **This file paid the
     * price of the alternative once**: at M12.3, *three of six said `coming
     * soon` on the screen a customer sees first.*
     *
     * ⚠️ **Vacuity guard first** — if the rail rendered nothing at all, the
     * absence checks below would pass over an empty frame.
     */
    render(<Navigation role="owner" />);
    const rail = screen.getByRole('navigation', { name: 'Primary' });
    expect(within(rail).getAllByRole('link').length).toBeGreaterThan(2);

    // ⚡ **`Home` LEFT this list** — [TASK-1438](../../../docs/BACKLOG.md) built
    // `/w/:workspace/home`, so the design's first entry finally has somewhere
    // to go. ⛔ **The other six still have no route and stay absent.**
    for (const absent of ['Forecast', 'Pipeline', 'Deals', 'Conversations', 'Reports']) {
      expect(within(rail).queryByText(absent), `${absent} has no route`).toBeNull();
    }
  });
});

describe('🔴 Home, and the segment it is resolved from', () => {
  it('✅ it links to the ACTIVE workspace, not to the declared template', () => {
    /**
     * ⚡ **The list declares `/w/[workspace]/home`** — the form
     * `infra/reachability.py` can see, since its `href:` pattern matches
     * quoted strings only and a backtick template would be invisible. ⛔ **But
     * a customer must never be handed that literal**: it is a 404 with a
     * plausible shape.
     */
    render(<Navigation role="owner" />);
    const home = screen.getByRole('link', { name: 'Home' });
    expect(home).toHaveAttribute('href', '/w/w1/home');
    expect(home.getAttribute('href')).not.toContain('[workspace]');
  });

  it('⛔ and it is DROPPED when no workspace is known', () => {
    // ⚡ Half a path is worse than no entry: `/w//home` is a 404 that looks
    // like a link.
    activeWorkspace = null;
    render(<Navigation role="owner" />);
    expect(screen.queryByRole('link', { name: 'Home' })).toBeNull();
    // The rest of the rail is unaffected.
    expect(screen.getByRole('link', { name: 'Attention' })).toBeInTheDocument();
    activeWorkspace = { id: 'w1', name: 'Northwind' };
  });

  it('📁 the path is `workspaceHome`\'s, so the two cannot drift', () => {
    // ⛔ **The declared template is not a second definition of the route.**
    // `lib/entry/rules.ts` is the authority — *"the one authenticated landing
    // route"* — and this asserts the rail agrees with it.
    expect(workspaceHome('w1')).toBe('/w/w1/home');
    render(<Navigation role="owner" />);
    expect(screen.getByRole('link', { name: 'Home' })).toHaveAttribute(
      'href',
      workspaceHome('w1'),
    );
  });
});

describe('📁 restricted destinations stay visible', () => {
  it('🔴 a member sees Settings, locked — not hidden and not a link', () => {
    /**
     * ⛔ **This reverses what this component used to do**, and the reversal is
     * the design's: 📁 *"restricted destinations stay visible at 45% with a
     * lock and explain on click."* ⚡ `rail.ts` rule ① already carried the
     * reasoning the component was contradicting.
     */
    render(<Navigation role="member" />);
    const rail = screen.getByRole('navigation', { name: 'Primary' });

    expect(within(rail).queryByRole('link', { name: 'Settings' })).toBeNull();
    expect(within(rail).getByLabelText(/Settings — restricted/)).toBeInTheDocument();
  });

  it('✅ and it explains on click, naming who can grant it', async () => {
    // 📁 The design's own reason: a person who is only refused *"asks for the
    // wrong thing or asks nobody."*
    render(<Navigation role="member" />);
    await userEvent.click(screen.getByLabelText(/Settings — restricted/));
    expect(screen.getByText(/available to an owner/i)).toBeInTheDocument();
  });

  it('✅ an owner gets it as an ordinary link', () => {
    render(<Navigation role="owner" />);
    const rail = screen.getByRole('navigation', { name: 'Primary' });
    expect(within(rail).getByRole('link', { name: 'Settings' })).toHaveAttribute(
      'href',
      '/settings',
    );
  });

  it('⛔ an unresolved role is treated as restricted, which fails closed', () => {
    // 📁 `can(null, …)` is false by construction. ⚡ The rail still renders —
    // a frame that blanks while a membership loads is the defect
    // `authenticated-shell.tsx` documents at length.
    render(<Navigation role={null} />);
    const rail = screen.getByRole('navigation', { name: 'Primary' });
    expect(within(rail).queryByRole('link', { name: 'Settings' })).toBeNull();
    expect(within(rail).getByRole('link', { name: 'Attention' })).toBeInTheDocument();
  });
});

describe('📁 the design\'s structure', () => {
  it('✅ the utility group is pinned below the destinations', () => {
    // 📁 *"Utilities and the assistant pin to the bottom above the fold"* —
    // *"utilities at the bottom keep the funnel order uninterrupted at the
    // top."* ⚡ Asserted as ORDER, which is the part a customer perceives.
    render(<Navigation role="owner" />);
    const rail = screen.getByRole('navigation', { name: 'Primary' });
    const labels = within(rail)
      .getAllByRole('link')
      .map((el) => el.textContent);

    // ⚡ **`Docs & support` joined the utility group** when
    // [TASK-1420](../../../docs/BACKLOG.md) built `/help` — 📁
    // [C-269](../../../docs/LANE_COORDINATION.md) had it absent *for want of a
    // route*. ⛔ **The assertion is that the group is LAST, not that one entry
    // is** — naming a single label would have to change every time the group
    // grows, which is not the property the design states.
    const utilities = labels.slice(-2);
    expect(utilities[0]).toContain('Settings');
    expect(utilities[1]).toContain('Docs & support');
  });

  it('✅ collapsed hides the label and keeps the accessible name', async () => {
    /**
     * 📁 *"Collapsed items expose their label as an accessible name and a
     * 300ms tooltip."* 🔴 **The accessible name is the half that gets
     * dropped**, and dropping it makes the collapsed rail unusable with a
     * screen reader while looking fine.
     */
    render(<Navigation role="owner" collapsed />);
    const rail = screen.getByRole('navigation', { name: 'Primary' });

    const attention = within(rail).getByRole('link', { name: 'Attention' });
    expect(attention).toBeInTheDocument();
    // The visible text is gone…
    expect(within(rail).queryByText('Attention')).toBeNull();

    /**
     * ⚡ **…and the tooltip is now a COMPONENT rather than a `title`** —
     * [TASK-1448](../../../docs/BACKLOG.md). ⛔ **`title` was the honest thing
     * to ship before it existed**, but 📁 the rule names *a 300ms tooltip* and
     * the browser's delay is its own and varies between engines.
     *
     * ✅ **The accessible name is what this test is really about, and it is
     * unchanged** — the tooltip DESCRIBES, and a tooltip that were the only
     * name would be unreachable by touch.
     */
    expect(attention).not.toHaveAttribute('title');
    await userEvent.hover(attention);
    expect(await screen.findByRole('tooltip')).toHaveTextContent('Attention');
  });

  it('✅ the active destination is marked for assistive technology', () => {
    // 📁 *"Active: brand tint, 600 label, brand icon."* ⛔ Colour alone never
    // carries it — `aria-current` is what a screen reader reads.
    render(<Navigation role="owner" />);
    expect(screen.getByRole('link', { name: 'Attention' })).toHaveAttribute(
      'aria-current',
      'page',
    );
  });
});
