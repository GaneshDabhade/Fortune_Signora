/**
 * What a brand-new account actually sees.
 *
 * **A page-level test, deliberately.** The defect (D36) was not that a
 * component was missing — it was that *every branch on the page tested a
 * falsy value*, so nothing rendered at all. A component test on the empty
 * state would have passed throughout the bug's lifetime.
 *
 * This became testable, and findable, only once somebody could sign in.
 */
import { render, screen } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import type { ReactElement } from 'react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

const workspaceContext = vi.hoisted(() => vi.fn());
const accounts = vi.hoisted(() => vi.fn());
const identities = vi.hoisted(() => vi.fn());
const catalog = vi.hoisted(() => vi.fn());

vi.mock('@/lib/state/workspace-provider', () => ({
  useWorkspaceContext: workspaceContext,
}));

vi.mock('@/lib/query/hooks', () => ({
  useAccounts: accounts,
  useAccountIdentities: identities,
  useSignalCatalog: catalog,
}));

import OpportunitiesPage from '@/app/(app)/opportunities/page';

const IDLE = { data: undefined, isLoading: false, isError: false };

function withQuery(node: ReactElement) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return <QueryClientProvider client={client}>{node}</QueryClientProvider>;
}

beforeEach(() => {
  // Exactly what react-query returns for a disabled query: not loading, not
  // errored, no data. Reproducing that shape is the whole point — it is what
  // made every branch fall through.
  accounts.mockReturnValue(IDLE);
  identities.mockReturnValue(IDLE);
  catalog.mockReturnValue(IDLE);
});

describe('a signed-in reader who belongs to no workspace', () => {
  it('is told why the screen is empty, rather than shown an empty screen', () => {
    workspaceContext.mockReturnValue({
      workspaces: [],
      activeWorkspace: null,
      isLoading: false,
    });

    render(withQuery(<OpportunitiesPage />));

    expect(screen.getByText(/not in a workspace yet/i)).toBeInTheDocument();
  });

  it('is not told anything while the answer is still being fetched', () => {
    // Announcing "you have no workspace" during the first paint would be a
    // confident wrong answer to somebody who has three.
    workspaceContext.mockReturnValue({
      workspaces: [],
      activeWorkspace: null,
      isLoading: true,
    });

    render(withQuery(<OpportunitiesPage />));

    expect(screen.queryByText(/not in a workspace yet/i)).not.toBeInTheDocument();
  });

  it('sees the ordinary empty state once they have one', () => {
    // A workspace with no accounts is a different sentence with a different
    // next action, and the page must not confuse the two.
    workspaceContext.mockReturnValue({
      workspaces: [{ id: 'w1', name: 'Acme' }],
      activeWorkspace: { id: 'w1', name: 'Acme' },
      isLoading: false,
    });
    accounts.mockReturnValue({ data: { items: [] }, isLoading: false, isError: false });

    render(withQuery(<OpportunitiesPage />));

    expect(screen.queryByText(/not in a workspace yet/i)).not.toBeInTheDocument();
  });

  it('never renders a heading and nothing else', () => {
    // **The regression this file exists for.** The page had four branches and
    // all four tested a falsy value, so a reader with no workspace got the
    // title and blank space — indistinguishable from a broken page.
    workspaceContext.mockReturnValue({
      workspaces: [],
      activeWorkspace: null,
      isLoading: false,
    });

    const { container } = render(withQuery(<OpportunitiesPage />));
    const body = (container.textContent ?? '').replace(
      /Opportunities|Accounts your evidence says are worth a look, most pressing first\./g,
      '',
    );

    expect(body.trim().length).toBeGreaterThan(0);
  });
});
