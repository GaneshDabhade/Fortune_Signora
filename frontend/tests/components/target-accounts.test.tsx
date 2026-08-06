/**
 * The screen that finally points Signora at something.
 *
 * These assert the rules that keep the platform's *input* honest: that the
 * list is saved whole, that a company's name is stored exactly as typed, that
 * an entry keeps its identity, that a concurrent save is refused rather than
 * resolved — and, the one that matters most here, **that the screen promises
 * nothing the platform is not yet doing.**
 */
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import type { ReactElement } from 'react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { TargetAccountsEditor } from '@/components/commercial/target-accounts';
import type {
  SubjectCoverage,
  TargetAccount,
  TargetAccountList,
} from '@/lib/api/types';

const request = vi.hoisted(() => vi.fn());

vi.mock('@/lib/api/client', async () => {
  const actual =
    await vi.importActual<typeof import('@/lib/api/client')>('@/lib/api/client');
  return { ...actual, apiRequest: request };
});

const WORKSPACE = 'aaaaaaaa-1111-4111-8111-111111111111';
const NORTHWIND = 'bbbbbbbb-2222-4222-8222-222222222222';

function accounts(overrides: Partial<TargetAccountList> = {}): TargetAccountList {
  return {
    version: 3,
    accounts: [{ id: NORTHWIND, name: 'Northwind Health' }],
    updated_at: '2026-08-01T09:00:00Z',
    updated_by: 'cccccccc-3333-4333-8333-333333333333',
    ...overrides,
  };
}

function withQuery(node: ReactElement) {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  return <QueryClientProvider client={client}>{node}</QueryClientProvider>;
}

function editor(overrides: Partial<TargetAccountList> = {}) {
  return withQuery(
    <TargetAccountsEditor accounts={accounts(overrides)} workspaceId={WORKSPACE} />,
  );
}

function sent(): { path: string; method?: string; body: Record<string, unknown> } {
  const call = declarations()[0];
  expect(call, 'nothing was sent to the API').toBeDefined();
  const [path, options] = call as [
    string,
    { method?: string; body: Record<string, unknown> },
  ];
  return { path, method: options.method, body: options.body };
}

/**
 * The calls that declare the list, without the ones that ask about it.
 *
 * **A7 added a second request from this screen**, to a different module, and
 * the assertions about *what was saved* must not start matching it — `sent()`
 * read `calls[0]` and the coverage read can arrive first.
 */
function declarations() {
  return request.mock.calls.filter(
    ([path]) => !String(path).includes('target-account-coverage'),
  );
}

/** Whatever the coverage endpoint should answer for this test. */
let coverage: SubjectCoverage[] = [];

beforeEach(() => {
  request.mockReset();
  coverage = [];
  // **Routed by path, not by call order.** One mock now stands in for two
  // modules, and answering the coverage read with a declaration would be the
  // test asserting against a shape the API cannot return.
  request.mockImplementation((path: string) =>
    Promise.resolve(
      String(path).includes('target-account-coverage')
        ? coverage
        : accounts({ version: 4 }),
    ),
  );
});

describe('a workspace watching nobody', () => {
  it('invites the first company rather than showing an error', () => {
    render(editor({ version: 0, accounts: [], updated_at: null, updated_by: null }));

    expect(screen.getByText('No accounts yet')).toBeInTheDocument();
  });

  it('claims no author or date it does not have', () => {
    const { container } = render(
      editor({ version: 0, accounts: [], updated_at: null, updated_by: null }),
    );

    expect(container.textContent).not.toMatch(/version 0/i);
    expect(container.textContent).not.toMatch(/last changed/i);
  });
});

describe('the list is saved whole', () => {
  it('sends every company, not just the new one', async () => {
    const user = userEvent.setup();
    render(editor());

    await user.type(screen.getByLabelText('Company'), 'Contoso');
    await user.click(screen.getByRole('button', { name: 'Add' }));

    await waitFor(() => expect(declarations()).not.toHaveLength(0));
    const body = sent().body as { accounts: TargetAccount[] };
    expect(body.accounts.map((entry) => entry.name)).toEqual([
      'Northwind Health',
      'Contoso',
    ]);
  });

  it('quotes the version it is replacing', async () => {
    const user = userEvent.setup();
    render(editor());

    await user.type(screen.getByLabelText('Company'), 'Contoso');
    await user.click(screen.getByRole('button', { name: 'Add' }));

    await waitFor(() => expect(declarations()).not.toHaveLength(0));
    expect(sent().body.expected_version).toBe(3);
    expect(sent().method).toBe('PUT');
    expect(sent().path).toBe(`/workspaces/${WORKSPACE}/target-accounts`);
  });

  it('removing one sends the rest, never a delete', async () => {
    const user = userEvent.setup();
    render(
      editor({
        accounts: [
          { id: NORTHWIND, name: 'Northwind Health' },
          { id: 'dddddddd-4444-4444-8444-444444444444', name: 'Contoso' },
        ],
      }),
    );

    await user.click(
      screen.getByRole('button', { name: 'Stop watching Northwind Health' }),
    );

    await waitFor(() => expect(declarations()).not.toHaveLength(0));
    const body = sent().body as { accounts: TargetAccount[] };
    expect(body.accounts.map((entry) => entry.name)).toEqual(['Contoso']);
    expect(sent().method).toBe('PUT');
  });
});

describe('a company is a name somebody typed', () => {
  it('keeps their capitalisation and punctuation', async () => {
    // Signora does not tidy a company name. Working out which company it is
    // happens later, and somewhere else.
    const user = userEvent.setup();
    render(editor({ accounts: [] }));

    await user.type(screen.getByLabelText('Company'), 'ACME Corp.');
    await user.click(screen.getByRole('button', { name: 'Add' }));

    await waitFor(() => expect(declarations()).not.toHaveLength(0));
    const body = sent().body as { accounts: TargetAccount[] };
    expect(body.accounts[0]?.name).toBe('ACME Corp.');
  });

  it('gives each entry an id, so a rename is not a re-add', async () => {
    const user = userEvent.setup();
    render(editor({ accounts: [] }));

    await user.type(screen.getByLabelText('Company'), 'Contoso');
    await user.click(screen.getByRole('button', { name: 'Add' }));

    await waitFor(() => expect(declarations()).not.toHaveLength(0));
    const body = sent().body as { accounts: TargetAccount[] };
    expect(body.accounts[0]?.id).toMatch(/^[0-9a-f-]{36}$/i);
  });

  it('does not add the same company twice', async () => {
    const user = userEvent.setup();
    render(editor());

    await user.type(screen.getByLabelText('Company'), 'northwind health');
    await user.click(screen.getByRole('button', { name: 'Add' }));

    expect(declarations()).toHaveLength(0);
  });

  it('asks for nothing but a name', () => {
    // **No domain, no country, no registration number.** Asking for one would
    // ask the customer to do resolution, and resolution is Signora's job.
    render(editor());

    expect(screen.getByLabelText('Company')).toBeInTheDocument();
    for (const asked of [/domain/i, /website/i, /country/i, /industry/i]) {
      expect(screen.queryByLabelText(asked)).not.toBeInTheDocument();
    }
  });
});

describe('it shows what is true, and promises nothing more', () => {
  it('still promises nothing about what was found or what happens next', async () => {
    /** ⚡ **Narrowed by A7, and deliberately not deleted.**
     *
     * This asserted that the screen reported **no** synchronization status,
     * including *last checked* — correct while nothing recorded when a
     * provider looked. `attempted_at` now does, so *checked* is a claim the
     * repository supports and it ships here (`51 §A7`: *"only ship the word
     * checked once it is true"*).
     *
     * **What the assertion protected is unchanged and is what remains**: a
     * watch list looks like a job queue, and the fields that would arrive next
     * are the ones no table can answer. *What was found* is still nowhere, and
     * *when Signora will look again* is not scheduled — a screen implying
     * either would be back to promising what the platform is not doing.
     */
    coverage = [
      {
        subject: 'Northwind Health',
        last_attempt: new Date(Date.now() - 3 * 86_400_000).toISOString(),
        stored_anything: true,
      },
    ];
    const { container } = render(editor());
    // Asserted with the line **present**, not absent — a screen that rendered
    // nothing would pass every one of these vacuously.
    await screen.findByText(/checked/i);

    for (const promise of [
      /\bsyncing\b/i,
      /\bmonitoring\b/i,
      /\bup to date\b/i,
      /\bin progress\b/i,
      /\bnext check\b/i,
      /\bwill check\b/i,
    ]) {
      expect(container.textContent).not.toMatch(promise);
    }
  });

  it('does not claim Signora has started watching', () => {
    // Nothing downstream consumes the announcement yet. A screen promising
    // monitoring the platform is not doing would be the product asserting
    // something untrue — worse than under-promising.
    const { container } = render(editor());

    expect(container.textContent).not.toMatch(/will (?:now )?(?:start|begin) (?:watching|monitoring)/i);
  });
});

describe('a refusal is shown, never resolved', () => {
  it('reports what the server said when a colleague saved first', async () => {
    const user = userEvent.setup();
    const { ApiError } = await import('@/lib/api/client');
    request.mockImplementation((path: string) =>
      String(path).includes('target-account-coverage')
        ? Promise.resolve([])
        : Promise.reject(
            new ApiError(409, {
              code: 'target_accounts_version_conflict',
              message:
                'your list of accounts is at version 4, not 3. Reload before saving.',
              correlation_id: 'corr-1',
            }),
          ),
    );
    render(editor());

    await user.type(screen.getByLabelText('Company'), 'Contoso');
    await user.click(screen.getByRole('button', { name: 'Add' }));

    expect(await screen.findByRole('alert')).toHaveTextContent('version 4, not 3');
  });

  it('shows nothing as watched before the server accepted it', async () => {
    const user = userEvent.setup();
    let resolve: (value: TargetAccountList) => void = () => {};
    request.mockImplementation((path: string) =>
      String(path).includes('target-account-coverage')
        ? Promise.resolve([])
        : new Promise<TargetAccountList>((settle) => {
            resolve = settle;
          }),
    );
    render(editor());

    await user.type(screen.getByLabelText('Company'), 'Contoso');
    await user.click(screen.getByRole('button', { name: 'Add' }));

    expect(screen.queryByText('Contoso')).not.toBeInTheDocument();
    resolve(accounts({ version: 4 }));
  });
});

describe('whether Signora has actually looked — A7', () => {
  function checked(overrides: Partial<SubjectCoverage> = {}): SubjectCoverage {
    return {
      subject: 'Northwind Health',
      last_attempt: new Date(Date.now() - 3 * 86_400_000).toISOString(),
      stored_anything: true,
      ...overrides,
    };
  }

  it('says when a company was last checked', async () => {
    coverage = [checked()];
    render(editor());

    expect(await screen.findByText('Checked 3 days ago')).toBeInTheDocument();
  });

  it('says so when somebody looked and found nothing', async () => {
    /** **The sentence the whole slice exists for**, and the state that was
     * unrenderable before it. `position` advances only when records arrive, so
     * a completed read that stored nothing left no trace at all — a seller
     * could not tell it from an account nobody had ever checked. */
    coverage = [checked({ stored_anything: false })];
    render(editor());

    expect(
      await screen.findByText('Checked 3 days ago · nothing found'),
    ).toBeInTheDocument();
  });

  it('distinguishes never checked from checked and empty', async () => {
    /** **Acceptance ②, asserted as the comparison.** Two companies, two
     * different sentences, from the two states that used to be one. */
    coverage = [
      checked({ subject: 'Northwind Health', last_attempt: null, stored_anything: false }),
      checked({ subject: 'Contoso', stored_anything: false }),
    ];
    render(
      editor({
        accounts: [
          { id: NORTHWIND, name: 'Northwind Health' },
          { id: 'dddddddd-4444-4444-8444-444444444444', name: 'Contoso' },
        ],
      }),
    );

    expect(await screen.findByText('Not checked yet')).toBeInTheDocument();
    expect(screen.getByText('Checked 3 days ago · nothing found')).toBeInTheDocument();
  });

  it('does not claim nobody looked at a company it holds evidence for', async () => {
    /** **The fourth state, and the one easiest to get wrong.** Rows written
     * before `attempted_at` existed carry evidence and no time. Rendering
     * *"Not checked yet"* there would tell a customer something demonstrably
     * false about their own account. */
    coverage = [checked({ last_attempt: null, stored_anything: true })];
    render(editor());

    expect(await screen.findByText(/did not record when/i)).toBeInTheDocument();
    expect(screen.queryByText('Not checked yet')).not.toBeInTheDocument();
  });

  it('renders nothing at all until the answer has arrived', () => {
    /** **Loading is not an answer.** A line reading *"Not checked yet"* while
     * the request is still in flight would state a fact the screen does not
     * have — and it is the fact a seller would act on. */
    coverage = [];
    render(editor());

    expect(screen.queryByText(/checked/i)).not.toBeInTheDocument();
  });

  it('asks about the companies on the list, by the name that was typed', async () => {
    /** **The name is the key on both sides.** What a customer typed here is
     * what a sync is given, so nothing resolves anything to make the join —
     * there is no join. */
    coverage = [checked()];
    render(editor());

    await waitFor(() =>
      expect(
        request.mock.calls.some(([path]) =>
          String(path).includes(
            `/workspaces/${WORKSPACE}/target-account-coverage?subjects=Northwind%20Health`,
          ),
        ),
      ).toBe(true),
    );
  });

  it('asks nothing at all when no company has been declared', () => {
    /** A workspace watching nobody has nothing to ask about, and the endpoint
     * refuses an empty request rather than answering one. */
    render(editor({ version: 0, accounts: [], updated_at: null, updated_by: null }));

    expect(
      request.mock.calls.filter(([path]) =>
        String(path).includes('target-account-coverage'),
      ),
    ).toHaveLength(0);
  });
});
