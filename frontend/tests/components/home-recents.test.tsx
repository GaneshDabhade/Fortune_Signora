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
