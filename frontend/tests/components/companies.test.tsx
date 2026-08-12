/**
 * **Companies renders what the contract publishes, and says so about the rest**
 * — [TASK-440](../../../docs/BACKLOG.md).
 *
 * 🔴 **The assertion that matters most here is the failure path.** 📁
 * [P-A](../../../docs/DOMAIN_DISCOVERY_REGISTER.md) ·
 * [C-226](../../../docs/LANE_COORDINATION.md): *a failed read must never render
 * as an empty result* — ⛔ **and on this screen the two are indistinguishable
 * to a seller.** *"8,412 rows"* and *"none"* look the same when the difference
 * is an outage, and the wrong one costs somebody a morning of believing their
 * book of business is gone.
 */
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { render, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { beforeEach, describe, expect, it, vi } from 'vitest';

const apiRequest = vi.fn();
vi.mock('@/lib/api/client', async () => {
  const actual = await vi.importActual<Record<string, unknown>>('@/lib/api/client');
  return { ...actual, apiRequest: (...args: unknown[]) => apiRequest(...args) };
});
vi.mock('@/lib/state/workspace-provider', () => ({
  useWorkspaceContext: () => ({
    activeWorkspace: { id: 'w1', name: 'Northwind', role: 'owner' },
    workspaces: [],
    setActiveWorkspace: vi.fn(),
    isLoading: false,
    error: null,
  }),
}));

import CompaniesPage from '@/app/(app)/accounts/page';
import type { ListedAccount } from '@/lib/api/types';

function listed(id: string, name: string | null): ListedAccount {
  return {
    account: {
      account_id: id,
      name,
      agreement: 'agreed',
      source_count: 2,
      source: 'hubspot',
      observed_at: null,
      last_observed_at: null,
    },
    kind: 'company',
  };
}

function page(items: ListedAccount[], hasMore = false, cursor: string | null = null) {
  return { items, next_cursor: cursor, has_more: hasMore };
}

function renderPage() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={client}>
      <CompaniesPage />
    </QueryClientProvider>,
  );
}

beforeEach(() => apiRequest.mockReset());

describe('⛔ an empty book is a designed state, not a blank', () => {
  it('✅ it names the one thing that puts a company here', async () => {
    apiRequest.mockResolvedValue(page([]));

    renderPage();

    await waitFor(() => expect(screen.getByText('No companies yet')).toBeInTheDocument());
    // ⛔ **Never *"coming soon"*.** ⚡ **Somebody who wants rows must learn what
    // produces them**, or the screen is a dead end.
    expect(screen.getByText(/connect a source/i)).toBeInTheDocument();
  });
});

describe('✅ the list renders what the contract publishes', () => {
  it('📁 the name, through the shared renderer', async () => {
    apiRequest.mockResolvedValue(page([listed('a1', 'Databricks'), listed('a2', 'Vantage')]));

    renderPage();

    await waitFor(() => expect(screen.getByText('Databricks')).toBeInTheDocument());
    expect(screen.getByText('Vantage')).toBeInTheDocument();
  });

  it('⛔ it reads `kind` rather than assuming every row is a company', async () => {
    // 📁 The endpoint's own words: *"the list answers for companies today and
    // the graph knows more kinds than it can search."* ⚠️ **A screen that
    // hard-codes the word is wrong the first time the graph lists anything
    // else, and wrong silently.**
    const person: ListedAccount = { ...listed('a3', 'Acme'), kind: 'person' };
    apiRequest.mockResolvedValue(page([listed('a1', 'Databricks'), person]));

    renderPage();

    // ⚠️ **Scoped to the table** — [TASK-1475](../../../docs/BACKLOG.md) gave the
    // toolbar a `Kind` filter, so `person` is now legitimately on the page twice:
    // once as a row's value and once as a filter option. ⛔ **The claim is about
    // the ROW**, and a page-wide query would pass on the option alone.
    const table = await screen.findByRole('table');
    await waitFor(() => expect(within(table).getByText('person')).toBeInTheDocument());
  });

  it('🔴 it counts what arrived and never claims a total it was not told', async () => {
    // ⛔ **The design prints *"8,412 total · 312 in view"* and the read
    // publishes no total.** ⚠️ **Printing one would be inventing the number a
    // seller trusts most.**
    apiRequest.mockResolvedValue(page([listed('a1', 'Databricks')]));

    renderPage();

    await waitFor(() =>
      expect(screen.getByTestId('companies-count')).toHaveTextContent('1 loaded'),
    );
    expect(screen.queryByText(/8,412/)).not.toBeInTheDocument();
  });

  it('⛔ and it draws no column the contract does not publish', async () => {
    apiRequest.mockResolvedValue(page([listed('a1', 'Databricks')]));

    renderPage();

    await waitFor(() => expect(screen.getByText('Databricks')).toBeInTheDocument());
    // 🔴 **[§20c](../../../CLAUDE.md): never introduce mock business data.**
    // ⛔ **A column of `—` is worse than no column** — it says Signora looked
    // and found nothing, when nothing was ever asked.
    for (const absent of ['Score', 'Owner', 'Stage', 'Value']) {
      expect(screen.queryByRole('columnheader', { name: absent })).not.toBeInTheDocument();
    }
  });

  it('✅ and it tells the reader those columns are absent rather than broken', async () => {
    apiRequest.mockResolvedValue(page([listed('a1', 'Databricks')]));

    renderPage();

    // ⚡ **A table silently drawing two of nine columns reads as broken.** ✅ One
    // that says what it does not have yet reads as honest.
    await waitFor(() =>
      expect(screen.getByText(/not on this list yet/i)).toBeInTheDocument(),
    );
  });
});

describe('⚡ paging walks the server’s cursor and never computes one', () => {
  it('✅ Load more appears only while the server says there is more', async () => {
    apiRequest.mockResolvedValue(page([listed('a1', 'Databricks')], false));

    renderPage();

    await waitFor(() => expect(screen.getByText('Databricks')).toBeInTheDocument());
    expect(screen.queryByRole('button', { name: /load more/i })).not.toBeInTheDocument();
  });

  it('🔴 it echoes the cursor back rather than computing an offset', async () => {
    apiRequest
      .mockResolvedValueOnce(page([listed('a1', 'Databricks')], true, 'CURSOR_ONE'))
      .mockResolvedValueOnce(page([listed('a2', 'Vantage')], false));

    renderPage();

    await waitFor(() => expect(screen.getByText('Databricks')).toBeInTheDocument());
    // ⚡ **`Next`, not `Load more`** — [TASK-1475](../../../docs/BACKLOG.md)
    // replaced the accumulating control with the design's pager, on
    // [C-1431](../../../docs/LANE_COORDINATION.md). ✅ **The claim this test
    // makes is unchanged and is the important one**: the cursor is echoed back
    // rather than computed.
    await userEvent.click(screen.getByRole('button', { name: 'Next' }));

    await waitFor(() => expect(screen.getByText('Vantage')).toBeInTheDocument());
    // ⛔ **And the first page is GONE, not appended** — that is the difference
    // between a pager and `Load more`, and it is what the design draws.
    expect(screen.queryByText('Databricks')).not.toBeInTheDocument();
    // ⛔ **The cursor is opaque by contract.** ⚡ **An offset page would skip or
    // repeat rows** — the graph is written continuously, so a resolution can
    // insert an account between two requests.
    const second = apiRequest.mock.calls[1]?.[0] as string;
    expect(second).toContain('cursor=CURSOR_ONE');
    expect(second).not.toContain('offset');
  });
});
