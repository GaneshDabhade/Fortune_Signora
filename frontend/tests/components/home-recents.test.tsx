/**
 * 📁 **`card.recents`** — `Fortune Signora Home.dc.html` §04, rendered per
 * `Fortune Signora Authenticated Entry.dc.html` §05, produced by
 * `Fortune Signora Session Continuity.dc.html` tier 4.
 */
import { render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

const recents = vi.hoisted(() => vi.fn());
const identities = vi.hoisted(() => vi.fn());

vi.mock('@/lib/state/workspace-provider', () => ({
  useWorkspaceContext: () => ({ activeWorkspace: { id: 'w1' } }),
}));
vi.mock('@/lib/query/hooks/recently-viewed', () => ({ useRecentlyViewed: recents }));
vi.mock('@/lib/query/hooks', () => ({ useAccountIdentities: identities }));

import { RecentsCard } from '@/components/home/recents-card';

const DAY = 86_400_000;
function viewed(id: string, daysAgo: number) {
  return {
    entity_id: id,
    kind: 'account' as const,
    viewed_at: new Date(Date.now() - daysAgo * DAY).toISOString(),
  };
}

beforeEach(() => {
  vi.clearAllMocks();
  identities.mockReturnValue({
    data: new Map([
      ['a1', { name: 'Vantage Logistics' }],
      ['a2', { name: 'Norvell Energy' }],
    ]),
  });
});

describe('📁 the list is what the person opened', () => {
  it('✅ names each record and links to it', () => {
    recents.mockReturnValue({
      data: [viewed('a1', 0), viewed('a2', 2)],
      isPending: false,
      isError: false,
      error: null,
    });

    render(<RecentsCard />);

    expect(screen.getByText('Vantage Logistics')).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /Vantage Logistics/ })).toHaveAttribute(
      'href',
      '/accounts/a1',
    );
  });

  it('⛔ says "Today" and "Yesterday" rather than a bare date', () => {
    recents.mockReturnValue({
      data: [viewed('a1', 0), viewed('a2', 1)],
      isPending: false, isError: false, error: null,
    });
    render(<RecentsCard />);
    expect(screen.getByText('Today')).toBeInTheDocument();
    expect(screen.getByText('Yesterday')).toBeInTheDocument();
  });

  it('🔴 a record older than a week gets a DATE, not a weekday', () => {
    /**
     * ⛔ ***"Friday"* eleven days later names the wrong Friday** — the one way
     * this line can state something false.
     */
    recents.mockReturnValue({
      data: [viewed('a1', 11)],
      isPending: false, isError: false, error: null,
    });
    render(<RecentsCard />);
    expect(screen.queryByText(/^(Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)$/))
      .not.toBeInTheDocument();
  });
});

describe('🔴 B-1033 — adjacent rows are separated, or two links read as one control', () => {
  /**
   * 🔴 **[B-1033](../../../docs/BUGS.md) — 0px between two adjacent 37px links
   * on a phone**, measured by QE in a browser on `8ceff5d6`.
   *
   * ⚠️ **QE cited WCAG 2.5.8 as one violation and it has three clauses with
   * different subjects.** ⛔ **`24 × 24` — 37px clears it.** ⛔ **`44px on
   * mobile` applies to PRIMARY actions only, and whether a recents row is
   * primary collides with the design's own `1fr × 160px` footprint** — 📁 five
   * rows at 44px is 220px before padding, **so the design states two things
   * that cannot both hold** ([C-1553](../../../docs/LANE_COORDINATION.md)),
   * and this lane did not resolve it by shrinking a row.
   *
   * ✅ **The separation clause is the one that unambiguously failed**, and it
   * is fixed. ⛔ **It was NOT witnessed** — the fix is on `origin/integration`
   * and nothing here asserts it, **so it could be removed by a spacing tidy-up
   * and nothing would say so.**
   *
   * ⚡ **`gap-2` is 8px, which is the clause's own number** — 📁 §05 draws the
   * rows at `gap:0` with a rule between, **and a divider is not a gap**: two
   * links flush against one another are one target to a coarse pointer.
   */
  it('⛔ puts real space between rows, not only a dividing rule', () => {
    recents.mockReturnValue({
      data: [viewed('a1', 0), viewed('a2', 2)],
      isPending: false,
      isError: false,
      error: null,
    });

    render(<RecentsCard />);

    const rows = screen.getAllByRole('link');
    expect(rows.length, 'two rows, or the separation below has no subject').toBe(2);

    const list = rows[0]?.parentElement;
    // ⚡ **`classList`, never `toContain`** — 📁 [B-1062](../../../docs/BUGS.md)
    // is the row where `toContain('col-span-7')` matched
    // `smalllaptop:col-span-7` and could not see the property it named.
    expect(list?.classList.contains('gap-2')).toBe(true);
    expect(list?.classList.contains('gap-0')).toBe(false);
  });
});

describe('🔴 an unread history and an empty one are different answers', () => {
  it('⛔ a failed read never says there were none', () => {
    // 📁 Session Continuity tier 4: "recents unavailable… no fabricated history."
    recents.mockReturnValue({ data: undefined, isPending: false, isError: true, error: null });
    render(<RecentsCard />);
    expect(screen.getByText(/could not read what you opened/i)).toBeInTheDocument();
    expect(screen.queryByText(/Nothing opened yet/i)).not.toBeInTheDocument();
  });

  it('⛔ a pending read does not claim emptiness either', () => {
    recents.mockReturnValue({ data: undefined, isPending: true, isError: false, error: null });
    render(<RecentsCard />);
    expect(screen.queryByText(/Nothing opened yet/i)).not.toBeInTheDocument();
  });

  it('✅ a genuinely empty history says so, using no banned string', () => {
    recents.mockReturnValue({ data: [], isPending: false, isError: false, error: null });
    render(<RecentsCard />);
    // 📁 Banned on Home: "No data available".
    expect(screen.getByText(/Nothing opened yet/i)).toBeInTheDocument();
    expect(screen.queryByText(/No data available/i)).not.toBeInTheDocument();
  });
});
