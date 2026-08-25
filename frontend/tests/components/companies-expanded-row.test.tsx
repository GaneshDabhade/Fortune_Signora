/**
 * **The design's expanded row** — 📁 `Fortune Signora Companies.dc.html`,
 * *"Expanded · Vantage Logistics"*.
 *
 * 🔴 **Two of these assertions exist because a screenshot found the defect and
 * every gate was green.** ⚠️ The first version drove the expanded row and the
 * context drawer from one piece of state, so **dismissing the preview silently
 * collapsed the row underneath it** — a customer who wanted the panel out of
 * the way lost the thing they had opened.
 *
 * ⛔ **And the panel a seller can type into is the one that must not exist.**
 * 📁 [ADR-0409](../../../docs/architecture/adr/0409-commercial-account-facts.md)
 * §5: *"a claim is only produced where the provider supplies the fact"* — so an
 * ACV input here would be a control that silently does nothing
 * ([B-255](../../../docs/BUGS.md)), on the one figure a seller would act on.
 */
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { beforeEach, describe, expect, it, vi } from 'vitest';

const apiRequest = vi.fn();
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
import { ApiError } from '@/lib/api/client';
import type { AccountOpportunity, DecisionPackage, ListedAccount } from '@/lib/api/types';

function listed(id: string, name: string): ListedAccount {
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
    commercial: { open_acv: null, renewal_date: null, stage: null },
  };
}

const OPPORTUNITY: AccountOpportunity = {
  id: 'o1',
  account_id: 'a1',
  stage: 'tracking',
  owner_id: null,
  opened_at: '2026-07-01T09:00:00Z',
  opened_by: 'automatic',
  score_at_open: 61,
  contested_at_open: false,
  score: 68,
  score_change_since_open: 7,
  evidence: 'current',
  history: [],
  allowed_next: ['engaged'],
};

const CONCLUSION: DecisionPackage = {
  account_id: 'a1',
  proposition: { text: 'Worth a conversation now.', evidence: ['signal:1'] },
  summary: {
    text: 'Hiring in two revenue teams while the current tool went quiet.',
    evidence: ['signal:1', 'event:9'],
  },
  stated_reasoning: [],
  supporting_evidence: ['two roles posted'],
  support: {
    level: 'strong',
    corroborating_providers: ['hubspot'],
    contributing_events: 4,
    evidence_state: 'current',
    contested: false,
    dissenting_signals: 0,
  },
  temporal: {
    trigger: 'scheduled',
    basis_at: '2026-08-01T00:00:00Z',
    computed_at: '2026-08-01T06:00:00Z',
    delta: 7,
    trend: 'rising',
    evidence_state: 'current',
    valid_until: null,
    supersedes: null,
  },
  alternative_readings: [],
  limitations: ['No pricing evidence.'],
  suggested_validation: ['Ask who owns renewals.'],
  catalog_version: 3,
  model: 'claude-opus-5',
  vendor: 'anthropic',
  prompt_name: 'decision',
  prompt_version: 2,
};

/** ⛔ **The ordinary state of both reads**, and neither is retried. */
const notFound = () =>
  new ApiError(404, { code: 'not_found', message: 'none', correlation_id: 'c1' });

/**
 * ⚡ **Routed by path, never by call order.** ⛔ The expanded row adds two reads
 * that fire *after* the list has settled, so a queue of `mockResolvedValueOnce`
 * would hand one of them the next page of accounts.
 */
function serve(options: { opportunity?: unknown; conclusion?: unknown } = {}): void {
  apiRequest.mockImplementation((path: unknown) => {
    const at = typeof path === 'string' ? path : '';
    if (at.includes('/account-tags')) return Promise.resolve({ tags: [], assignments: {} });
    if (at.includes('/opportunity')) {
      return options.opportunity === undefined
        ? Promise.reject(notFound())
        : Promise.resolve(options.opportunity);
    }
    if (at.includes('/decision-package')) {
      return options.conclusion === undefined
        ? Promise.reject(notFound())
        : Promise.resolve(options.conclusion);
    }
    return Promise.resolve({
      items: [listed('a1', 'Vantage Logistics'), listed('a2', 'Calderwood Analytics')],
      next_cursor: null,
      has_more: false,
    });
  });
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

async function expand(name: string) {
  const user = userEvent.setup();
  renderPage();
  await screen.findByText(name);
  await user.click(screen.getByRole('button', { name: `Expand ${name}` }));
  return user;
}

beforeEach(() => apiRequest.mockReset());

describe('✅ the design’s three panels, each carrying what the repository actually has', () => {
  it('📁 the account’s opportunity, its conclusion, and the commercial figures', async () => {
    serve({ opportunity: OPPORTUNITY, conclusion: CONCLUSION });
    await expand('Vantage Logistics');

    expect(await screen.findByText(/Expanded · Vantage Logistics/)).toBeInTheDocument();
    expect(screen.getByText('Open opportunity')).toBeInTheDocument();
    expect(await screen.findByText(/Opened at/)).toBeInTheDocument();
    expect(
      await screen.findByText(/Hiring in two revenue teams while the current tool went quiet\./),
    ).toBeInTheDocument();
    // ⚡ **The provenance travels with the sentence**, not behind a hover.
    expect(screen.getByText(/2 cited facts · claude-opus-5/)).toBeInTheDocument();
  });

  it('⛔ and it never offers a way to type an ACV', async () => {
    serve({ opportunity: OPPORTUNITY, conclusion: CONCLUSION });
    await expand('Vantage Logistics');
    await screen.findByText(/Expanded · Vantage Logistics/);

    // 🔴 `OPEN_ACV` has exactly one producer, and it is the CRM mapper.
    expect(screen.queryByRole('textbox', { name: /acv/i })).not.toBeInTheDocument();
    expect(screen.getByText(/does not author them/)).toBeInTheDocument();
  });
});

describe('⛔ absence is stated, never rendered as a failure', () => {
  it('✅ nothing open and nothing concluded are both sentences', async () => {
    serve();
    await expand('Vantage Logistics');

    expect(await screen.findByText(/Nothing is open here/)).toBeInTheDocument();
    expect(
      await screen.findByText(/has not reached a conclusion about this account yet/),
    ).toBeInTheDocument();
  });
});

describe('🔴 what the screenshot caught and the gates did not', () => {
  it('⛔ dismissing the preview leaves the expanded row where it was', async () => {
    serve({ opportunity: OPPORTUNITY, conclusion: CONCLUSION });
    const user = await expand('Vantage Logistics');
    await screen.findByText(/Expanded · Vantage Logistics/);

    await user.click(screen.getByRole('button', { name: /close/i }));

    await waitFor(() => expect(screen.queryByText('Row preview')).not.toBeInTheDocument());
    expect(screen.getByText(/Expanded · Vantage Logistics/)).toBeInTheDocument();
  });

  it('⚡ and a row nobody expanded costs nothing to read', async () => {
    serve({ opportunity: OPPORTUNITY, conclusion: CONCLUSION });
    await expand('Vantage Logistics');
    await screen.findByText(/Expanded · Vantage Logistics/);

    // ⛔ **Forty rows are never forty conclusions.** The panel MOUNTS on
    // expansion, which is what gates the read.
    const read = apiRequest.mock.calls.map(([path]) => String(path));
    expect(read.filter((p) => p.includes('/decision-package'))).toHaveLength(1);
    expect(read.some((p) => p.includes('/accounts/a2/decision-package'))).toBe(false);
  });
});
