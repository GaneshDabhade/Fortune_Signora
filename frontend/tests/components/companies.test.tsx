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
// ⚡ **The Companies page reads its arrangement from the URL** — the design's
// mechanic: *"sort is part of the saved view and the URL"* — **so the router
// hooks are mocked here, the same way every other route's suite mocks them.**
vi.mock('next/navigation', () => ({
  useSearchParams: () => new URLSearchParams(),
  useRouter: () => ({ push: vi.fn(), replace: vi.fn() }),
  usePathname: () => '/accounts',
}));

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

import { ToastProvider } from '@/components/ui/toast';
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
    // ⛔ **All three null, deliberately.** ⚡ **This is the state the product
    // is actually in** — the read path exists and no customer system is
    // connected — **and a builder that invented an ACV would make the
    // never-fabricate rule untestable.**
    commercial: { open_acv: null, renewal_date: null, stage: null },
  };
}

function page(items: ListedAccount[], hasMore = false, cursor: string | null = null) {
  return { items, next_cursor: cursor, has_more: hasMore };
}

function renderPage() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={client}>
      {/* ⚡ **The provider the real tree has and this one did not.** 📁
          `app/layout.tsx` mounts `ToastProvider` above every route, so a page
          calling `useToast` is correct and this render was the incomplete
          one. ⛔ **`useToast` is NOT made tolerant of a missing provider** —
          that would hide the same omission everywhere else. */}
      <ToastProvider>
        <CompaniesPage />
      </ToastProvider>
    </QueryClientProvider>,
  );
}

/**
 * ⚡ **Pages answered by PATH rather than by call order** —
 * [TASK-466](../../../docs/BACKLOG.md).
 *
 * ⛔ **The Tags vocabulary is read on every visit.** The bulk bar's *Add tag*
 * needs it, and gating it on the Tags COLUMN meant the control never rendered
 * — 📁 **found by the Playwright journey, not by this suite.**
 *
 * ⚠️ **A `mockResolvedValueOnce` queue takes precedence over any
 * implementation**, so it cannot be routed *behind*: the vocabulary consumed
 * one of the pages and the second page arrived as a tag list. ✅ **So the
 * ordered stub becomes an explicit sequence keyed to the read it belongs to**,
 * which is what it always meant.
 */
function servePages(...pages: readonly unknown[]): void {
  let served = 0;
  apiRequest.mockImplementation((path: unknown) => {
    if (typeof path === 'string' && path.includes('/account-tags')) {
      return Promise.resolve({ tags: [], assignments: {} });
    }
    /**
     * 🔴 **Saved views are routed BEFORE the page queue, and that is a repair.**
     *
     * ⛔ **The catch-all below answered `/saved-views` with a page of
     * ACCOUNTS** — which have no `id`, so the tab strip rendered children keyed
     * `undefined` and React warned on every run. ⚠️ **And it is worse than
     * noise**: the queue is positional, so the saved-views call **consumed one
     * of the paginated account pages**, silently shifting which page an
     * assertion below was looking at.
     *
     * ⚡ **A mock that answers every path is the too-wide-and-silent
     * instrument** — it never errors, and it manufactures findings that look
     * like the subject's.
     */
    if (typeof path === 'string' && path.includes('/saved-views')) {
      return Promise.resolve({ items: [], next_cursor: null, has_more: false });
    }
    const next = pages[Math.min(served, pages.length - 1)];
    served += 1;
    return Promise.resolve(next);
  });
}

/**
 * 🔴 **Answer ONE page, and route the calls that are not the list.**
 *
 * ⛔ **A bare `mockResolvedValue` answers EVERY path with a page of
 * accounts** — including `/saved-views`, whose items then have no `id`, so
 * the tab strip renders children keyed `undefined` and React warns.
 *
 * ⚡ **A mock that answers every path is the too-wide-and-silent instrument**:
 * it never errors, and it manufactures findings that look like the subject's.
 */
function serveOne(rows: ListedAccount[], hasMore = false): void {
  apiRequest.mockImplementation((path: unknown) => {
    const at = typeof path === 'string' ? path : '';
    if (at.includes('/account-tags')) {
      return Promise.resolve({ tags: [], assignments: {} });
    }
    if (at.includes('/saved-views')) {
      return Promise.resolve({ items: [], next_cursor: null, has_more: false });
    }
    return Promise.resolve(page(rows, hasMore));
  });
}

beforeEach(() => apiRequest.mockReset());

describe('⛔ an empty book is a designed state, not a blank', () => {
  it('✅ it names the one thing that puts a company here', async () => {
    serveOne([]);

    renderPage();

    await waitFor(() => expect(screen.getByText('No companies yet')).toBeInTheDocument());
    // ⛔ **Never *"coming soon"*.** ⚡ **Somebody who wants rows must learn what
    // produces them**, or the screen is a dead end.
    //
    // ⚠️ **Scoped to the empty state's own copy.** The header now says the same
    // thing to the same person for the same reason, so an unscoped match found
    // two elements — ✅ **the collision is a sign both say it, which is right**,
    // and the assertion names which one it is about.
    expect(
      screen.getByText(/Connect a source and the first ones arrive with it/i),
    ).toBeInTheDocument();
  });
});

describe('✅ the list renders what the contract publishes', () => {
  it('📁 the name, through the shared renderer', async () => {
    serveOne([listed('a1', 'Databricks'), listed('a2', 'Vantage')]);

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
    serveOne([listed('a1', 'Databricks'), person]);

    renderPage();

    // ⚠️ **Scoped to the table** — [TASK-1475](../../../docs/BACKLOG.md) gave the
    // toolbar a `Kind` filter, so `person` is now legitimately on the page twice:
    // once as a row's value and once as a filter option. ⛔ **The claim is about
    // the ROW**, and a page-wide query would pass on the option alone.
    // ⚠️ **`Kind` is no longer a default column** — the default set is the
    // design's — so the column is turned on before the row's value is read.
    // ⛔ **The claim is unchanged**: the row states its own kind rather than
    // the screen assuming every row is a company.
    const table = await screen.findByRole('table');
    await userEvent.click(await screen.findByText(/^Columns · /));
    await userEvent.click(screen.getByRole('checkbox', { name: 'Kind' }));

    await waitFor(() => expect(within(table).getByText('person')).toBeInTheDocument());
  });

  it('🔴 it counts what arrived and never claims a total it was not told', async () => {
    // ⛔ **The design prints *"8,412 total · 312 in view"* and the read
    // publishes no total.** ⚠️ **Printing one would be inventing the number a
    // seller trusts most.**
    serveOne([listed('a1', 'Databricks')]);

    renderPage();

    await waitFor(() =>
      expect(screen.getByTestId('companies-count')).toHaveTextContent('1 loaded'),
    );
    expect(screen.queryByText(/8,412/)).not.toBeInTheDocument();
  });

  it('⛔ and it draws no column the contract does not publish', async () => {
    serveOne([listed('a1', 'Databricks')]);

    renderPage();

    await waitFor(() => expect(screen.getByText('Databricks')).toBeInTheDocument());
    // 🔴 **[§20c](../../../CLAUDE.md): never introduce mock business data.**
    //
    // ⚠️ **This list was `['Score', 'Owner', 'Stage', 'Value']` and three of
    // the four have since gained a source** — 📁 Owner on ADR-0411, Open ACV
    // and Renewal on **[ADR-0409](../../../docs/architecture/adr/0409-commercial-account-facts.md)**,
    // ratified 2026-08-12. ⛔ **A guard asserting they are absent would now be
    // asserting a lie**, so it is corrected rather than deleted (§2).
    //
    // ⚡ **`Signora score` is the one the design draws that nothing publishes**,
    // and it is still the whole subject of this test.
    for (const absent of ['Score', 'Signora score', 'Value', 'Trend']) {
      expect(screen.queryByRole('columnheader', { name: absent })).not.toBeInTheDocument();
    }
  });

  it('✅ and it tells the reader those columns are absent rather than broken', async () => {
    serveOne([listed('a1', 'Databricks')]);

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
    serveOne([listed('a1', 'Databricks')], false);

    renderPage();

    await waitFor(() => expect(screen.getByText('Databricks')).toBeInTheDocument());
    expect(screen.queryByRole('button', { name: /load more/i })).not.toBeInTheDocument();
  });

  it('🔴 it echoes the cursor back rather than computing an offset', async () => {
    servePages(
      page([listed('a1', 'Databricks')], true, 'CURSOR_ONE'),
      page([listed('a2', 'Vantage')], false),
    );

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
    // ⚡ **Selected by PATH, not by call index.** ⛔ The page reads more than
    // one thing now, and `calls[1]` was the tag vocabulary — an index into a
    // call log is a hidden dependency on how many reads a screen happens to
    // make (§2).
    const listReads = apiRequest.mock.calls
      .map((call) => call[0] as string)
      .filter((path) => path.includes('/accounts-list'));
    const second = listReads[1];
    expect(second).toContain('cursor=CURSOR_ONE');
    expect(second).not.toContain('offset');
  });
});

/**
 * 🔴 **The design draws three header actions and Signora has one.**
 *
 * ⛔ **The screen previously CLAIMED, in a code comment, that the absence was
 * stated in the description — and the description said nothing about it.** 📁
 * [§2](../../../CLAUDE.md): the repository must not assert something that is
 * not true of it, ⚠️ **and this screen has already shipped one false
 * self-description** (*"score, owner, value and renewal are not on this list"*,
 * while it drew three of the four).
 *
 * ⚡ **So the sentence is asserted rather than trusted.**
 */
describe('⛔ the two header actions with no capability behind them', () => {
  it('✅ are stated as unavailable, never drawn as dead buttons', async () => {
    servePages(page([listed('a1', 'Vantage')]));
    renderPage();
    await screen.findByText('Vantage');

    // 📁 [B-255](../../../docs/BUGS.md): a control that silently does nothing
    // is worse than one that is absent.
    expect(screen.queryByRole('button', { name: /^Import$/ })).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: /^New company$/i })).not.toBeInTheDocument();

    expect(
      screen.getByText(/Importing a file and adding one by hand are not available yet/),
    ).toBeInTheDocument();
  });

  /**
   * ⚡ **A customer whose list is empty needs the route in, not an apology** —
   * so the sentence names the capability that DOES exist and links to it.
   */
  it('✅ and the sentence names how companies actually arrive', async () => {
    servePages(page([listed('a1', 'Vantage')]));
    renderPage();
    await screen.findByText('Vantage');

    expect(screen.getByRole('link', { name: 'connect a source' })).toHaveAttribute(
      'href',
      '/settings/connections',
    );
  });
});
