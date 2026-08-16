/**
 * **A failed read is not an empty book** — [TASK-440](../../../docs/BACKLOG.md).
 *
 * 🔴 **[P-A](../../../docs/DOMAIN_DISCOVERY_REGISTER.md) ·
 * [C-226](../../../docs/LANE_COORDINATION.md)**: ***a failed read must never
 * render as an empty result*** — ⛔ **and Companies is where it bites hardest.**
 * **8,412 rows and none look identical to a seller when the difference is an
 * outage**, and the wrong one costs somebody a morning of believing their book
 * of business is gone.
 *
 * ## ⚠️ Why the HOOK is stubbed here rather than the request rejected
 *
 * ⛔ **Rejecting `apiRequest` produced an unhandled rejection that failed the
 * test while its assertions passed** — React discards a render, the promise
 * react-query created for it is never awaited, and vitest reports the noise
 * rather than the result.
 *
 * ✅ **And stubbing the hook is the more honest test anyway**: 📁 what P-A
 * governs is **the page's rendering decision** — *given a read that failed,
 * what does the customer see* — **not react-query's transport.** ⚡ **The
 * hook's own contract, that it echoes the server's cursor rather than
 * computing one, is asserted against a real request in
 * [`companies.test.tsx`](companies.test.tsx).**
 *
 * 📁 **The same split [`attention-failed-read.test.tsx`](attention-failed-read.test.tsx)
 * already draws** for [B-237](../../../docs/BUGS.md): it fails the *context*,
 * not the network.
 */
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

// ⚡ **The Companies page reads its arrangement from the URL** — the design's
// mechanic: *"sort is part of the saved view and the URL"* — **so the router
// hooks are mocked here, the same way every other route's suite mocks them.**
vi.mock('next/navigation', () => ({
  useSearchParams: () => new URLSearchParams(),
  useRouter: () => ({ push: vi.fn(), replace: vi.fn() }),
  usePathname: () => '/accounts',
}));

vi.mock('@/lib/state/workspace-provider', () => ({
  useWorkspaceContext: () => ({
    activeWorkspace: { id: 'w1', name: 'Northwind', role: 'owner' },
    workspaces: [],
    setActiveWorkspace: vi.fn(),
    isLoading: false,
    error: null,
  }),
}));

vi.mock('@/lib/query/hooks/accounts-list', () => ({
  useAccountsList: () => ({
    data: undefined,
    isError: true,
    isLoading: false,
    hasNextPage: false,
    isFetchingNextPage: false,
    fetchNextPage: vi.fn(),
  }),
}));

import CompaniesPage from '@/app/(app)/accounts/page';

function renderPage() {
  return render(
    <QueryClientProvider client={new QueryClient()}>
      <CompaniesPage />
    </QueryClientProvider>,
  );
}

describe('🔴 the outage is stated, never rendered as an empty book', () => {
  it('⛔ it does NOT say "no companies yet"', () => {
    renderPage();

    // 🔴 **The load-bearing assertion.** ⚠️ **An empty state here tells a seller
    // their book is empty**, which is a claim about their business rather than
    // about Signora, and it is false.
    expect(screen.queryByText('No companies yet')).not.toBeInTheDocument();
  });

  it('✅ it names what could not be loaded', () => {
    renderPage();

    // ⛔ **`getAllByText`** — the page variant states it in a heading and in a
    // sentence, and a single-match query would fail on a correct render.
    expect(screen.getAllByText(/could not load/i).length).toBeGreaterThan(0);
  });

  it('✅ and it answers the fear the failure actually creates', () => {
    renderPage();

    // ⛔ **Not *"something went wrong"*.** 📁 The fear a failed read creates is
    // that the data is gone — ⚡ **and it is the fear that makes people re-enter
    // work they never lost.**
    expect(screen.getByText(/no account has been removed/i)).toBeInTheDocument();
  });

  it('⛔ and it draws no table at all, rather than an empty one', () => {
    renderPage();

    // ⚠️ **A table with a header row and no body reads as *"you have none"***,
    // which is the same lie in a different shape.
    expect(screen.queryByRole('table')).not.toBeInTheDocument();
  });
});
