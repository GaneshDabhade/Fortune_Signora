/**
 * What the *Your business* page says when something goes wrong.
 *
 * **A page-level test, deliberately, and for the same reason `first-run` is
 * one** (D36): the defect was never inside a component. Each of the four
 * sections renders only when its own query has produced data, and only the
 * catalog's failure produced any copy — so a failed request made a section
 * *absent*, and an outage was indistinguishable from a feature the customer
 * did not have. Every component test passed throughout.
 *
 * B-006.
 */
import { render, screen } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import type { ReactElement } from 'react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

const workspaceContext = vi.hoisted(() => vi.fn());
const products = vi.hoisted(() => vi.fn());
const icp = vi.hoisted(() => vi.fn());
const committee = vi.hoisted(() => vi.fn());
const focus = vi.hoisted(() => vi.fn());

vi.mock('@/lib/state/workspace-provider', () => ({
  useWorkspaceContext: workspaceContext,
}));

vi.mock('@/lib/query/hooks/commercial', () => ({
  useProductCatalog: products,
  useIcpDeclaration: icp,
  useBuyingCommittee: committee,
  useCommercialFocus: focus,
  usePublishProductCatalog: () => ({ mutate: vi.fn(), isPending: false, isError: false }),
  useDeclareIcp: () => ({ mutate: vi.fn(), isPending: false, isError: false }),
  useDeclareBuyingCommittee: () => ({
    mutate: vi.fn(),
    isPending: false,
    isError: false,
  }),
  useDeclareFocus: () => ({ mutate: vi.fn(), isPending: false, isError: false }),
}));

import YourBusinessPage from '@/app/(app)/settings/products/page';

const WORKSPACE = 'aaaaaaaa-1111-4111-8111-111111111111';
const IDLE = { data: undefined, isLoading: false, isError: false };
const FAILED = { data: undefined, isLoading: false, isError: true };

const CATALOG = {
  data: {
    version: 1,
    products: [{ id: 'bbbbbbbb-2222-4222-8222-222222222222', name: 'Revenue Cloud', description: '' }],
    updated_at: '2026-08-01T09:00:00Z',
    updated_by: 'cccccccc-3333-4333-8333-333333333333',
  },
  isLoading: false,
  isError: false,
};

function withQuery(node: ReactElement) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return <QueryClientProvider client={client}>{node}</QueryClientProvider>;
}

beforeEach(() => {
  workspaceContext.mockReturnValue({
    workspaces: [{ id: WORKSPACE, name: 'Acme' }],
    activeWorkspace: { id: WORKSPACE, name: 'Acme' },
    isLoading: false,
  });
  products.mockReturnValue(CATALOG);
  icp.mockReturnValue(IDLE);
  committee.mockReturnValue(IDLE);
  focus.mockReturnValue(IDLE);
});

describe('a section that could not be loaded', () => {
  it.each([
    ['ideal customer', icp],
    ['buying committee', committee],
    ['focus', focus],
  ])('says so, for the %s', (what, query) => {
    // **Absence is the defect.** Without this the section simply is not there,
    // and the customer has no way to tell an outage from a capability they
    // were never given.
    query.mockReturnValue(FAILED);

    render(withQuery(<YourBusinessPage />));

    expect(
      screen.getByText(new RegExp(`Your ${what} could not be loaded`, 'i')),
    ).toBeInTheDocument();
  });

  it('says nothing has been lost, because nothing has', () => {
    icp.mockReturnValue(FAILED);

    render(withQuery(<YourBusinessPage />));

    expect(
      screen.getByText(/a fault in Signora, not a missing declaration/i),
    ).toBeInTheDocument();
  });

  it('reports each failure separately when several fail at once', () => {
    icp.mockReturnValue(FAILED);
    committee.mockReturnValue(FAILED);
    focus.mockReturnValue(FAILED);

    render(withQuery(<YourBusinessPage />));

    expect(screen.getAllByText(/could not be loaded/i)).toHaveLength(3);
  });

  it('leaves the sections that did load alone', () => {
    icp.mockReturnValue(FAILED);

    render(withQuery(<YourBusinessPage />));

    expect(screen.getByText('Products')).toBeInTheDocument();
    expect(screen.getByText('Revenue Cloud')).toBeInTheDocument();
  });
});

describe('a page where everything loaded', () => {
  it('reports no failure at all', () => {
    render(withQuery(<YourBusinessPage />));

    expect(screen.queryByText(/could not be loaded/i)).not.toBeInTheDocument();
  });
});
