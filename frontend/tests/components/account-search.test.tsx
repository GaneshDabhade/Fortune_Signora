/**
 * *"Show me Databricks."* — A1.
 *
 * The second question of every evaluation, and the one a ranked list
 * structurally cannot answer. These assert what a customer would notice, plus
 * two things they would only notice once it had cost them: that the highlight
 * does not stay where it was after the answer changed, and that a result found
 * under a former name is still listed under the current one.
 */
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { AccountSearch } from '@/components/intelligence/account-search';
import type { AccountIdentity, SearchResult } from '@/lib/api/types';

const push = vi.hoisted(() => vi.fn());
vi.mock('next/navigation', () => ({ useRouter: () => ({ push }) }));

const workspaceContext = vi.hoisted(() => vi.fn());
vi.mock('@/lib/state/workspace-provider', () => ({
  useWorkspaceContext: workspaceContext,
}));

const search = vi.hoisted(() => vi.fn());
vi.mock('@/lib/query/hooks/search', async () => {
  const actual = await vi.importActual<typeof import('@/lib/query/hooks/search')>(
    '@/lib/query/hooks/search',
  );
  return { ...actual, useAccountSearch: search };
});

function identity(id: string, name: string | null): AccountIdentity {
  return {
    account_id: id,
    name,
    agreement: 'agreed',
    source_count: 1,
    source: 'apollo',
    observed_at: '2026-07-01T00:00:00Z',
    last_observed_at: '2026-07-20T00:00:00Z',
  };
}

/** A result matched under the name it is being shown by — the ordinary case,
 * and the one that needs no explanation on the row. */
function result(id: string, name: string | null, matched?: string): SearchResult {
  return {
    account: identity(id, name),
    result_type: 'company',
    matched_name: matched ?? name ?? '',
    is_renamed: matched !== undefined && matched !== name,
    matched_source: 'apollo',
  };
}

/**
 * What the API actually returns — **groups, not a flat list.**
 *
 * ⚠️ **This helper used to return `rows` directly, and that is how
 * [B-208] survived**: the component was tested against a shape the endpoint
 * stopped sending at TASK-408, so the surface threw on the first real match
 * and every test passed. **A mock is a claim about the contract**, and this
 * one was wrong for as long as nobody made it match.
 */
function found(...rows: SearchResult[]) {
  return {
    data: [
      { result_type: 'company' as const, coverage: 'searched' as const, results: rows },
    ],
    isFetching: false,
  };
}

/** A group Signora did not search, which is a different answer from one that
 * matched nothing. */
function group(
  result_type: 'company' | 'technology',
  coverage: 'searched' | 'not_applicable' | 'not_requested',
  ...rows: SearchResult[]
) {
  return { result_type, coverage, results: rows };
}

beforeEach(() => {
  push.mockReset();
  workspaceContext.mockReturnValue({ activeWorkspace: { id: 'ws-1' } });
  search.mockReturnValue(found());
});

describe('finding an account by name', () => {
  it('opens the account it was asked for', async () => {
    search.mockReturnValue(found(result('acc-1', 'Databricks, Inc.')));

    render(<AccountSearch />);
    await userEvent.type(screen.getByRole('combobox'), 'databr');
    await userEvent.click(screen.getByRole('option', { name: /Databricks/ }));

    expect(push).toHaveBeenCalledWith('/accounts/acc-1');
  });

  it('is operable without a mouse, from typing to arriving', async () => {
    // **The keyboard path is the product, not the accessible alternative to
    // it.** A seller who has learned this control never touches the mouse.
    search.mockReturnValue(
      found(result('acc-1', 'Acme Corporation'), result('acc-2', 'Acme Software')),
    );

    render(<AccountSearch />);
    await userEvent.type(screen.getByRole('combobox'), 'acme');
    await userEvent.keyboard('{ArrowDown}{Enter}');

    expect(push).toHaveBeenCalledWith('/accounts/acc-2');
  });

  it('moves the highlight back to the top when the answer changes', async () => {
    /** **Enter would otherwise open an account nobody chose.** Arrow down to
     * the second result, type one more letter, and the list is a different
     * list — but the highlight was on index 1, so Enter opens whatever has
     * arrived in that position. Silent, and wrong every time. */
    search.mockReturnValue(
      found(result('acc-1', 'Acme Corporation'), result('acc-2', 'Acme Software')),
    );

    render(<AccountSearch />);
    const box = screen.getByRole('combobox');
    await userEvent.type(box, 'acme');
    await userEvent.keyboard('{ArrowDown}');

    search.mockReturnValue(found(result('acc-9', 'Acmex Holdings')));
    await userEvent.type(box, 'x');
    await userEvent.keyboard('{Enter}');

    expect(push).toHaveBeenCalledWith('/accounts/acc-9');
  });

  it('lists a renamed company under what it is called now, and says why it is there', async () => {
    // Searched by a name the server matched on a historical claim; the row
    // shows the current one. **The list never highlights a matched substring**
    // for exactly this reason — the match is sometimes not in the text — so
    // the matched name is stated instead of pointed at.
    search.mockReturnValue(found(result('acc-1', 'Northwind Group', 'Northwind Traders')));

    render(<AccountSearch />);
    await userEvent.type(screen.getByRole('combobox'), 'Traders');

    const row = screen.getByRole('option', { name: /Northwind Group/ });
    expect(row).toHaveTextContent('Northwind Group');
    expect(row).toHaveTextContent('matched “Northwind Traders”');
  });

  it('says nothing extra about a row that matched under its own name', async () => {
    /** **The half of the feature that keeps it readable.** A list that
     * explains every row is one people stop reading, so only a row whose
     * match is invisible in its own text gets a second line. */
    search.mockReturnValue(found(result('acc-1', 'Databricks, Inc.')));

    render(<AccountSearch />);
    await userEvent.type(screen.getByRole('combobox'), 'databr');

    expect(screen.getByRole('option', { name: /Databricks/ })).not.toHaveTextContent('matched');
  });

  it('still offers an account nobody has named', async () => {
    // It is a company the pipeline is watching. Hiding it would make search
    // quietly disagree with the list that shows it.
    search.mockReturnValue(found(result('acc-1', null)));

    render(<AccountSearch />);
    await userEvent.type(screen.getByRole('combobox'), 'acme');

    expect(screen.getByText('Unnamed account')).toBeInTheDocument();
  });

  it('says nothing matched, in the words the customer used', async () => {
    render(<AccountSearch />);
    await userEvent.type(screen.getByRole('combobox'), 'zzzz');

    expect(await screen.findByRole('status')).toHaveTextContent(
      'Nothing in accounts matches “zzzz”',
    );
  });

  it('shows no list at all until a question has been asked', async () => {
    // One character is not a question. The server refuses it too — this stops
    // the browser sending a request it knows will be refused.
    search.mockReturnValue(found(result('acc-1', 'Acme Corporation')));

    render(<AccountSearch />);
    await userEvent.type(screen.getByRole('combobox'), 'a');

    expect(screen.queryByRole('listbox')).not.toBeInTheDocument();
  });

  it('closes on Escape without navigating anywhere', async () => {
    search.mockReturnValue(found(result('acc-1', 'Acme Corporation')));

    render(<AccountSearch />);
    await userEvent.type(screen.getByRole('combobox'), 'acme');
    expect(screen.getByRole('listbox')).toBeInTheDocument();

    await userEvent.keyboard('{Escape}');

    await waitFor(() => expect(screen.queryByRole('listbox')).not.toBeInTheDocument());
    expect(push).not.toHaveBeenCalled();
  });

  it('renders nothing before a workspace is chosen', () => {
    // The shell mounts this on every page, including the ones a customer
    // reaches before they belong to a workspace. A search box that cannot
    // search is worse than no search box.
    workspaceContext.mockReturnValue({ activeWorkspace: null });

    const { container } = render(<AccountSearch />);

    expect(container).toBeEmptyDOMElement();
  });
});

describe('four kinds of answer, and each emptiness is its own — TASK-460, B-208', () => {
  it('renders the groups the API actually sends', async () => {
    /** ⚠️ **[B-208]: it did not.** The endpoint has returned groups since
     * TASK-408 and this surface read them as results, so `row.account` was
     * `undefined` and the dropdown threw on the first match. Nothing caught
     * it: `tsc` saw a type parameter on a JSON call, which is a claim rather
     * than a check, and the mock here asserted the shape that preceded the
     * change. */
    const user = userEvent.setup();
    search.mockReturnValue({
      data: [
        group('company', 'searched', result('acc-1', 'Databricks, Inc.')),
        group('technology', 'not_applicable'),
      ],
      isFetching: false,
    });
    render(<AccountSearch />);

    await user.type(screen.getByRole('combobox'), 'data');

    expect(screen.getByText('Accounts')).toBeInTheDocument();
    expect(screen.getByText('Databricks, Inc.')).toBeInTheDocument();
  });

  it('a kind that was not searched says so, rather than looking empty', async () => {
    /** *"The absence of results and the absence of the group represent
     * different business meanings"* — product owner, 2026-08-05. **Reading
     * `results` without `coverage` collapses the two**, which is the exact
     * thing the group exists to prevent. */
    const user = userEvent.setup();
    search.mockReturnValue({
      data: [group('technology', 'not_applicable')],
      isFetching: false,
    });
    render(<AccountSearch />);

    await user.type(screen.getByRole('combobox'), 'data');

    expect(screen.getByText(/does not search technologies by name/i)).toBeInTheDocument();
  });

  it('a kind that matched nothing says something different again', async () => {
    const user = userEvent.setup();
    search.mockReturnValue({
      data: [group('technology', 'searched')],
      isFetching: false,
    });
    render(<AccountSearch />);

    await user.type(screen.getByRole('combobox'), 'data');

    expect(screen.getByText(/Nothing in technologies matches/i)).toBeInTheDocument();
  });

  it('the keyboard moves through matches and never through headings', async () => {
    /** **The index counts matches, not rendered rows.** A heading that could
     * take focus would make the arrow keys count things a customer cannot
     * choose. */
    const user = userEvent.setup();
    search.mockReturnValue({
      data: [
        group('company', 'searched', result('acc-1', 'Alpha'), result('acc-2', 'Beta')),
        group('technology', 'not_applicable'),
      ],
      isFetching: false,
    });
    render(<AccountSearch />);

    await user.type(screen.getByRole('combobox'), 'a');
    await user.keyboard('{ArrowDown}{Enter}');

    expect(push).toHaveBeenCalledWith('/accounts/acc-2');
  });
});

