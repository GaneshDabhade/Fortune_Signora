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
import type { TargetAccount, TargetAccountList } from '@/lib/api/types';

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
  const call = request.mock.calls[0];
  expect(call, 'nothing was sent to the API').toBeDefined();
  const [path, options] = call as [
    string,
    { method?: string; body: Record<string, unknown> },
  ];
  return { path, method: options.method, body: options.body };
}

beforeEach(() => {
  request.mockReset();
  request.mockResolvedValue(accounts({ version: 4 }));
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

    await waitFor(() => expect(request).toHaveBeenCalled());
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

    await waitFor(() => expect(request).toHaveBeenCalled());
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

    await waitFor(() => expect(request).toHaveBeenCalled());
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

    await waitFor(() => expect(request).toHaveBeenCalled());
    const body = sent().body as { accounts: TargetAccount[] };
    expect(body.accounts[0]?.name).toBe('ACME Corp.');
  });

  it('gives each entry an id, so a rename is not a re-add', async () => {
    const user = userEvent.setup();
    render(editor({ accounts: [] }));

    await user.type(screen.getByLabelText('Company'), 'Contoso');
    await user.click(screen.getByRole('button', { name: 'Add' }));

    await waitFor(() => expect(request).toHaveBeenCalled());
    const body = sent().body as { accounts: TargetAccount[] };
    expect(body.accounts[0]?.id).toMatch(/^[0-9a-f-]{36}$/i);
  });

  it('does not add the same company twice', async () => {
    const user = userEvent.setup();
    render(editor());

    await user.type(screen.getByLabelText('Company'), 'northwind health');
    await user.click(screen.getByRole('button', { name: 'Add' }));

    expect(request).not.toHaveBeenCalled();
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
  it('reports no synchronization status', () => {
    // **The field that would arrive first.** A watch list looks like a job
    // queue; whether Signora has looked at an account, what it found, and
    // when it will look again are another module's facts.
    const { container } = render(editor());

    for (const promise of [
      /\bsyncing\b/i,
      /\blast checked\b/i,
      /\bmonitoring\b/i,
      /\bup to date\b/i,
      /\bin progress\b/i,
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
    request.mockRejectedValue(
      new ApiError(409, {
        code: 'target_accounts_version_conflict',
        message: 'your list of accounts is at version 4, not 3. Reload before saving.',
        correlation_id: 'corr-1',
      }),
    );
    render(editor());

    await user.type(screen.getByLabelText('Company'), 'Contoso');
    await user.click(screen.getByRole('button', { name: 'Add' }));

    expect(await screen.findByRole('alert')).toHaveTextContent('version 4, not 3');
  });

  it('shows nothing as watched before the server accepted it', async () => {
    const user = userEvent.setup();
    let resolve: (value: TargetAccountList) => void = () => {};
    request.mockReturnValue(
      new Promise<TargetAccountList>((settle) => {
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
