/**
 * **The Companies workspace: views, density, columns, filters, paging, export**
 * — [TASK-1475](../../../docs/BACKLOG.md), against 📁
 * `Fortune Signora Companies.dc.html`.
 *
 * 🔴 **Every assertion is on the SCREEN**, not on
 * [`table.ts`](../../lib/accounts/table.ts) — 📁
 * [B-191](../../../docs/BUGS.md): *a guard belongs at the seam that failed, not
 * at the component downstream of it.* **The law has its own unit tests; these
 * prove the screen calls it.**
 */
import { render, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { beforeEach, describe, expect, it, vi } from 'vitest';

const apiRequest = vi.hoisted(() => vi.fn());
// ⚡ **The Companies page reads its arrangement from the URL** — the design's
// mechanic: *"sort is part of the saved view and the URL"* — **so the router
// hooks are mocked here, the same way every other route's suite mocks them.**
vi.mock('next/navigation', () => ({
  useSearchParams: () => new URLSearchParams(),
  useRouter: () => ({ push: vi.fn(), replace: vi.fn() }),
  usePathname: () => '/accounts',
}));

vi.mock('@/lib/api/client', () => ({ apiRequest }));
vi.mock('@/lib/state/workspace-provider', () => ({
  useWorkspaceContext: () => ({ activeWorkspace: { id: 'w1', name: 'Northwind' } }),
}));

import { ToastProvider } from '@/components/ui/toast';
import CompaniesPage from '@/app/(app)/accounts/page';
import type { ListedAccount } from '@/lib/api/types';

function listed(id: string, name: string, over: Partial<ListedAccount['account']> = {}, kind = 'company'): ListedAccount {
  return {
    kind: kind as ListedAccount['kind'],
    // ⛔ **All three null, deliberately.** ⚡ **This is the state the product
    // is actually in** — the read path exists and no customer system is
    // connected — **and a builder that invented an ACV would make the
    // never-fabricate rule untestable.**
    commercial: { open_acv: null, renewal_date: null, stage: null },
    account: {
      account_id: id,
      name,
      agreement: 'agreed' as ListedAccount['account']['agreement'],
      source_count: 2,
      source: 'apollo',
      observed_at: null,
      last_observed_at: '2026-08-10T12:00:00.000Z',
      ...over,
    },
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

const THREE = [
  listed('a1', 'Vantage Logistics'),
  listed('a2', 'Ashgrove Retail', { source: 'crunchbase' }),
  listed('a3', 'Meridian Freight', { last_observed_at: null }, 'technology'),
];

/**
 * ⚡ **Pages answered by PATH rather than by call order** —
 * [TASK-466](../../../docs/BACKLOG.md).
 *
 * ⛔ **The Tags vocabulary is read on every visit**, and a
 * `mockResolvedValueOnce` queue takes precedence over any implementation — so
 * it consumed one of the pages and the second arrived as a tag list. ✅ **The
 * ordered stub becomes a sequence keyed to the read it belongs to.**
 */
function servePages(...pages: readonly unknown[]): void {
  let served = 0;
  apiRequest.mockImplementation((path: unknown) => {
    if (typeof path === 'string' && path.includes('/account-tags')) {
      return Promise.resolve({ tags: [], assignments: {} });
    }
    const next = pages[Math.min(served, pages.length - 1)];
    served += 1;
    return Promise.resolve(next);
  });
}

beforeEach(() => {
  apiRequest.mockReset();
  servePages(page(THREE));
});

describe('📁 Table and Cards are one view of one selection', () => {
  it('✅ cards render the same rows the table does', async () => {
    renderPage();
    await screen.findByRole('table');

    await userEvent.click(screen.getByRole('button', { name: 'cards' }));

    const cards = await screen.findByTestId('accounts-cards');
    expect(within(cards).getByText('Vantage Logistics')).toBeInTheDocument();
    expect(within(cards).getByText('Meridian Freight')).toBeInTheDocument();
    // ⛔ **One surface at a time** — not a table hidden behind a card grid.
    expect(screen.queryByRole('table')).not.toBeInTheDocument();
  });

  /**
   * 📁 **`Design Documents/Fortune Signora Companies.html`** — the card's
   * fields are `name · initials · segment · status · ACV · score · renewal ·
   * owner · trend`.
   *
   * 🔴 **It drew `Kind` and `Sources` instead**, and neither is on the design's
   * card: they are graph provenance, not the commercial facts a seller scans a
   * card for. ⛔ **An extension the final design does not support**, so it is
   * removed rather than kept because it rendered.
   *
   * ⛔ **`Signora score` stays absent** for the reason it is absent from the
   * table — `ListedAccount` carries none (C-289).
   */
  it('⛔ the card draws the design’s fields, not the graph provenance it used to', async () => {
    renderPage();
    await screen.findByRole('table');

    await userEvent.click(screen.getByRole('button', { name: 'cards' }));
    const cards = await screen.findByTestId('accounts-cards');

    expect(within(cards).queryByText('Kind')).toBeNull();
    expect(within(cards).queryByText('Sources')).toBeNull();
  });

  /**
   * ⛔ **Absent, never dashed** — 📁 [ADR-0409](../../../docs/architecture/adr/0409-commercial-account-facts.md)
   * §5. ⚠️ **A table cell prints `—` because a grid must keep its columns
   * aligned; a card has no such obligation**, so it says less rather than
   * saying nothing truthfully.
   */
  it('✅ a card states Open ACV when a source has, and omits it when none has', async () => {
    servePages(
      page([
        {
          ...listed('11111111-1111-4111-8111-111111111111', 'Vantage Logistics'),
          commercial: {
            open_acv: { amount: 1_240_000, currency: 'USD' },
            renewal_date: null,
            stage: null,
          },
        },
        listed('22222222-2222-4222-8222-222222222222', 'Meridian Freight'),
      ]),
    );

    renderPage();
    await screen.findByRole('table');
    await userEvent.click(screen.getByRole('button', { name: 'cards' }));
    const cards = await screen.findByTestId('accounts-cards');

    // ⚡ **Stated once, on the card that has it.**
    expect(within(cards).getAllByText('Open ACV')).toHaveLength(1);
    // ⛔ **And no dash on the one that does not** — a zero-filled ACV is a
    // figure a seller would act on.
    expect(within(cards).queryByText('—')).toBeNull();
  });

  /**
   * 🔴 **The design's rule, and the reason cards are a VIEW**: *"same data,
   * same filters, same selection."* ⛔ **A filter that applied to one and not
   * the other would make them two screens.**
   */
  it('🔴 a filter set in the table still holds in cards', async () => {
    renderPage();
    await screen.findByRole('table');

    await userEvent.type(screen.getByLabelText('Name contains'), 'grove');
    await userEvent.click(screen.getByRole('button', { name: 'cards' }));

    const cards = await screen.findByTestId('accounts-cards');
    expect(within(cards).getByText('Ashgrove Retail')).toBeInTheDocument();
    expect(within(cards).queryByText('Vantage Logistics')).not.toBeInTheDocument();
  });
});

describe('⚡ columns are configurable and Company is not', () => {
  it('✅ turning a column off removes its header', async () => {
    renderPage();
    const table = await screen.findByRole('table');
    // ⚠️ **`Segment`, not `Kind`.** ⛔ **The default set is the design's now**
    // — Company · Segment · Open ACV · Renewal · Owner · Tags — **and `Kind`
    // is available rather than shown**, so a test that turned it off was
    // turning off a column that was not on.
    expect(within(table).getByRole('columnheader', { name: 'Segment' })).toBeInTheDocument();

    await userEvent.click(screen.getByText(/^Columns · /));
    await userEvent.click(screen.getByRole('checkbox', { name: 'Segment' }));

    await waitFor(() =>
      expect(
        within(table).queryByRole('columnheader', { name: 'Segment' }),
      ).not.toBeInTheDocument(),
    );
  });

  /**
   * 🔴 **Company cannot be turned off**, and the control says so rather than
   * accepting the click and ignoring it — 📁 the design pins it left.
   */
  it('🔴 Company’s checkbox is disabled, not merely ineffective', async () => {
    renderPage();
    await screen.findByRole('table');

    await userEvent.click(screen.getByText(/^Columns · /));

    expect(screen.getByRole('checkbox', { name: 'Company' })).toBeDisabled();
  });
});

describe('🔴 the count never claims a total it was not told', () => {
  it('⛔ it says what has loaded, and what a filter narrowed it to', async () => {
    renderPage();
    await screen.findByRole('table');

    expect(screen.getByTestId('companies-count')).toHaveTextContent('3 loaded');

    await userEvent.type(screen.getByLabelText('Name contains'), 'grove');

    expect(screen.getByTestId('companies-count')).toHaveTextContent('1 of 3 loaded');
  });

  /**
   * ⛔ **A filter matching nothing is not an empty book.** ⚡ **Two different
   * sentences, and this screen has both** — the design's empty state says no
   * company exists; this says the narrowing excluded them.
   */
  it('🔴 an over-narrow filter says so, and does not say “no companies yet”', async () => {
    renderPage();
    await screen.findByRole('table');

    await userEvent.type(screen.getByLabelText('Name contains'), 'zzzz');

    expect(await screen.findByText('No companies match these filters')).toBeInTheDocument();
    expect(screen.queryByText('No companies yet')).not.toBeInTheDocument();
  });
});

describe('🔴 Previous / Next, never a fabricated total', () => {
  /**
   * 📁 [C-1431](../../../docs/LANE_COORDINATION.md): the mock draws numbered
   * pages; the endpoint is keyset. ⛔ **A page NUMBER is honest; a page COUNT
   * is not** — keyset cannot know how many pages exist without reading them.
   */
  it('🔴 the pager shows a page number and no denominator', async () => {
    renderPage();
    const pager = await screen.findByTestId('accounts-pager');

    // ⚠️ **The wording moved to the design's** — *"Rows 1–8 of 312"* replaced
    // *"Page 1"* — **and the claim did not.** ⛔ **The current page is marked
    // and its neighbours do not exist**: keyset cannot reach page 3 without
    // walking 1 and 2, so a numbered button would be a control that could not
    // work.
    expect(within(pager).getByText('1')).toHaveAttribute('aria-current', 'page');
    expect(pager).toHaveTextContent(/Rows 1–\d/);
    // ⛔ **No denominator here**, because this test does not answer the count —
    // ⚡ **and the loaded figure is never printed in its place.**
    expect(pager.textContent).not.toMatch(/of \d/);
    expect(within(pager).queryByRole('button', { name: '2' })).not.toBeInTheDocument();
  });

  it('⛔ Previous is refused on the first page rather than absent', async () => {
    renderPage();
    const pager = await screen.findByTestId('accounts-pager');

    expect(within(pager).getByRole('button', { name: 'Previous' })).toBeDisabled();
  });

  it('✅ Next moves forward and Previous comes back to the page held', async () => {
    apiRequest.mockReset();
    servePages(
      page([listed('a1', 'Vantage Logistics')], true, 'CURSOR_ONE'),
      page([listed('a2', 'Ashgrove Retail')], false),
    );

    renderPage();
    await screen.findByText('Vantage Logistics');

    await userEvent.click(screen.getByRole('button', { name: 'Next' }));
    await screen.findByText('Ashgrove Retail');
    expect(within(screen.getByTestId('accounts-pager')).getByText('2')).toHaveAttribute(
      'aria-current',
      'page',
    );

    await userEvent.click(screen.getByRole('button', { name: 'Previous' }));
    await screen.findByText('Vantage Logistics');
    // ⛔ **No second request** — the page was held, and Previous never refetches.
    // ⚡ **Counting the LIST reads, not every call the screen makes.** ⛔ A
    // total-call assertion is a hidden dependency on how many things a page
    // happens to read (§2) — the Tags vocabulary added one and this test would
    // have failed for a reason it is not about.
    const listReads = apiRequest.mock.calls
      .map((call) => call[0] as string)
      .filter((path) => path.includes('/accounts-list'));
    expect(listReads).toHaveLength(2);
  });
});

describe('📁 export is what is on screen', () => {
  it('✅ it exports the filtered rows and the visible columns', async () => {
    // ⚠️ **jsdom has no `URL.createObjectURL`**, so it is defined rather than
    // spied — ⛔ **a spy on an absent method throws**, which is the failure
    // this shape avoids and the reason the assertion is on the Blob's text
    // rather than on the call.
    // ⚠️ **jsdom's `Blob` has no `.text()` either**, so the CSV is captured
    // from the constructor rather than read back — ⛔ **the assertion is about
    // what was written, and reading it back would be testing jsdom.**
    const written: string[] = [];
    const RealBlob = globalThis.Blob;
    vi.spyOn(globalThis, 'Blob').mockImplementation((parts?: BlobPart[]) => {
      written.push((parts ?? []).join(''));
      return new RealBlob(parts ?? []);
    });
    Object.defineProperty(URL, 'createObjectURL', {
      configurable: true,
      value: () => 'blob:x',
    });
    Object.defineProperty(URL, 'revokeObjectURL', { configurable: true, value: () => undefined });

    renderPage();
    await screen.findByRole('table');
    await userEvent.type(screen.getByLabelText('Name contains'), 'grove');
    await userEvent.click(screen.getByRole('button', { name: 'Export' }));

    expect(written).toHaveLength(1);
    const text = written[0]!;
    expect(text).toContain('Ashgrove Retail');
    // ⛔ **Not the rows the filter excluded** — an export that quietly carried
    // more than the screen showed would be wrong in the direction nobody checks.
    expect(text).not.toContain('Vantage Logistics');
  });
});
