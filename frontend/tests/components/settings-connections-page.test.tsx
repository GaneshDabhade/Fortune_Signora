/**
 * 📁 **Settings → Connections**, the Connection Center's route.
 *
 * ⚠️ **Both of this page's children already have tests** —
 * `connection-center.test.tsx` and `disconnect-dialog.test.tsx` — ⛔ **and the
 * page itself had none.** ⚡ **What the page owns is exactly what neither child
 * can see**: the breadcrumb it publishes, which of the two absences it renders,
 * and **which row is allowed to say it is checking.**
 */
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import type { Connection, IntegrationSystem } from '@/lib/api/types';
import { outcomeFor } from '@/lib/integrations/outcomes';

const publishBreadcrumb = vi.hoisted(() => vi.fn());
const useIntegrations = vi.hoisted(() => vi.fn());
const checkMutate = vi.hoisted(() => vi.fn());
const disconnectMutate = vi.hoisted(() => vi.fn());
const workspaceState = vi.hoisted(() => ({
  activeWorkspace: { id: 'w-1', name: 'Northwind' } as { id: string; name: string } | null,
  isLoading: false,
}));
const search = vi.hoisted(() => ({ value: new URLSearchParams() }));

vi.mock('next/navigation', () => ({
  useSearchParams: () => search.value,
  useRouter: () => ({ push: vi.fn() }),
}));
vi.mock('@/components/shell/breadcrumb-trail', () => ({
  usePublishBreadcrumb: publishBreadcrumb,
}));
vi.mock('@/lib/query/hooks/integrations', () => ({
  useIntegrations,
  useCheckConnection: () => ({ mutate: checkMutate, isPending: false }),
  useDisconnect: () => ({
    mutate: disconnectMutate,
    reset: vi.fn(),
    isPending: false,
    isError: false,
    data: undefined,
  }),
}));
vi.mock('@/lib/state/workspace-provider', () => ({
  useWorkspaceContext: () => workspaceState,
}));

import ConnectionsPage from '@/app/(app)/settings/connections/page';

/**
 * 🔴 **The FOURTH fixture-manufactured failure of this session, and the same
 * root cause every time.**
 *
 * ⛔ **The first draft built `Connection` and handed it to `useIntegrations`,
 * which returns `IntegrationSystem[]`** — a different shape that WRAPS
 * `Connection[]`. **Eight of ten tests crashed on
 * `system.capabilities.length`** and it read exactly like a product defect.
 *
 * ⚠️ **`tsc` could not see it**: `useIntegrations` is a bare `vi.fn()`, so its
 * return type is `any` and nothing checked what the page was handed. ⚡ **A
 * test double is the one place a lie to the compiler survives to look like
 * evidence.**
 *
 * ✅ **Both builders are annotated with the contract's own types**, so a
 * mismatch is now a compile error rather than a red suite.
 */
function connection(over: Partial<Connection> = {}): Connection {
  return {
    id: 'c-1',
    integration: 'hubspot',
    label: 'HubSpot',
    state: 'connected',
    connected_at: '2026-08-01T00:00:00Z',
    attention: 'none',
    reason: null,
    health: 'healthy',
    ...over,
  };
}

function system(over: Partial<IntegrationSystem> = {}): IntegrationSystem {
  return {
    integration: 'hubspot',
    // ⚠️ **From the closed union** — `'crm'` is not a member, and a loose
    // fixture reached past it earlier today.
    capabilities: ['crm_activity'],
    connectable: true,
    working: true,
    needs_attention: false,
    connections: [connection()],
    ...over,
  };
}

beforeEach(() => {
  vi.clearAllMocks();
  workspaceState.activeWorkspace = { id: 'w-1', name: 'Northwind' };
  workspaceState.isLoading = false;
  search.value = new URLSearchParams();
  useIntegrations.mockReturnValue({ data: [system()], isLoading: false, isError: false });
});

describe('📁 §05 — a screen below the first level publishes a way back up', () => {
  it('⛔ names Settings as a link and Connections as the current record', () => {
    /**
     * 📁 *"Mandatory below the first level, because most sessions start from a
     * deep link in Slack or email."* 🔴 **Six routes below the first level
     * published nothing**, so the top bar's slot rendered empty and somebody
     * arriving from a link had no route back up.
     *
     * ⚡ *"They mirror the data hierarchy, not the click path"*, and **the last
     * crumb is the current record and is not a link.**
     */
    render(<ConnectionsPage />);

    expect(publishBreadcrumb).toHaveBeenCalledWith([
      { label: 'Settings', kind: 'link', href: '/settings' },
      { label: 'Connections', kind: 'current' },
    ]);
  });
});

describe('🔴 two different absences, and the page must not confuse them', () => {
  it('⛔ a workspace read still in flight shows a placeholder, never “no organization”', () => {
    /**
     * ⚠️ **This is [P-A](../../../docs/DOMAIN_DISCOVERY_REGISTER.md) at the
     * route level.** ⛔ **Telling an owner they belong to no organization while
     * the read is still running** is a claim about their account, not about
     * our latency — **and it is the state they would act on.**
     */
    workspaceState.isLoading = true;
    workspaceState.activeWorkspace = null;
    const { container } = render(<ConnectionsPage />);

    expect(container.querySelectorAll('[data-skeleton]').length).toBeGreaterThan(0);
    expect(screen.queryByRole('heading', { name: 'Connections' })).toBeNull();
    expect(document.body.textContent ?? '').not.toMatch(/no organization|not in a/i);
  });

  it('✅ and a SETTLED read with no organization says so — the vacuity half', () => {
    workspaceState.isLoading = false;
    workspaceState.activeWorkspace = null;
    const { container } = render(<ConnectionsPage />);

    expect(container.querySelectorAll('[data-skeleton]').length).toBe(0);
    expect(screen.queryByRole('heading', { name: 'Connections' })).toBeNull();
  });

  it('📁 and an ordinary page renders its heading and what it is for', () => {
    render(<ConnectionsPage />);
    expect(screen.getByRole('heading', { name: 'Connections' })).toBeInTheDocument();
    expect(
      screen.getByText(/The systems Signora reads from to work out which accounts/),
    ).toBeInTheDocument();
  });
});

describe('⚡ the return trip from a provider is answered where the result is visible', () => {
  it('📁 renders the outcome above the list, so the result and the state are on one screen', () => {
    search.value = new URLSearchParams('outcome=connected');
    render(<ConnectionsPage />);

    /**
     * ⚠️ **The first draft of this asserted `not.toMatch(/^\s*$/)`** — ⛔ **that
     * the page rendered SOMETHING — **which is true of every render and
     * therefore evidence of nothing.** ✅ **Asserted through the module's own
     * resolver instead**, so the page is checked against `outcomes.ts` rather
     * than against a sentence retyped here.
     */
    const expected = outcomeFor('connected');
    expect(screen.getByText(expected.what)).toBeInTheDocument();
    // ⛔ **And never the raw code**, which is the query string leaking through.
    expect(document.body.textContent ?? '').not.toContain('outcome=connected');
  });

  it('⛔ an unknown outcome code still says something, rather than rendering the code', () => {
    // ⚡ **`outcomeFor` falls back to `unknown`** — ⛔ a raw query-string value
    // on screen is the platform leaking through the front door.
    search.value = new URLSearchParams('outcome=wat_is_this');
    render(<ConnectionsPage />);

    expect(document.body.textContent ?? '').not.toContain('wat_is_this');
  });

  it('✅ and says nothing at all when nobody has just returned', () => {
    // ⚠️ **The vacuity half** — without it, the two assertions above would pass
    // on a page that renders no banner in any circumstance.
    render(<ConnectionsPage />);
    expect(document.body.textContent ?? '').not.toMatch(/wat_is_this|outcome=/);
  });
});

describe('🔴 only the row being checked may say it is checking', () => {
  it('⛔ a single boolean would make every row on the page claim to be checking', async () => {
    const user = userEvent.setup();
    useIntegrations.mockReturnValue({
      data: [
        system(),
        system({
          integration: 'salesforce',
          connections: [connection({ id: 'c-2', label: 'Salesforce', integration: 'salesforce' })],
        }),
      ],
      isLoading: false,
      isError: false,
    });
    render(<ConnectionsPage />);

    // ⚡ **Named per connection** — `aria-label={`Check ${label}`}` — which is
    // itself the property: a control that named no row could not be per-row.
    await user.click(screen.getByRole('button', { name: 'Check HubSpot' }));
    expect(screen.getByRole('button', { name: 'Check Salesforce' })).toBeInTheDocument();

    expect(checkMutate).toHaveBeenCalledTimes(1);
    expect(checkMutate.mock.calls[0]?.[0]).toBe('c-1');
  });

  it('🔴 a check that never reaches the server still RELEASES the row', async () => {
    /**
     * ⛔ **`onSettled`, not `onSuccess`.** ⚡ **A check that fails to reach the
     * server must still release the row, or it says *Checking…* forever** —
     * 📁 **the same shape as onboarding's slug field**, which said *Checking…*
     * permanently when its availability read failed: **a read that finished,
     * rendered as one still running.**
     *
     * ⚠️ **`Checking…` reads as *working*, not as *broken***, so nobody
     * reports it.
     */
    const user = userEvent.setup();
    render(<ConnectionsPage />);

    await user.click(screen.getByRole('button', { name: 'Check HubSpot' }));

    const options = checkMutate.mock.calls[0]?.[1] as
      | { onSettled?: () => void; onSuccess?: () => void }
      | undefined;
    expect(options?.onSettled, 'a failure path must release the row').toBeTypeOf('function');
    expect(options?.onSuccess, 'onSuccess alone would strand a failed check').toBeUndefined();
  });
});

describe('⛔ the disconnect confirmation exists only once somebody has chosen a target', () => {
  it('📁 renders no dialog until a row asks for one, and sends nothing by opening it', async () => {
    const user = userEvent.setup();
    render(<ConnectionsPage />);

    expect(screen.queryByRole('dialog')).toBeNull();

    await user.click(screen.getByRole('button', { name: 'Disconnect HubSpot' }));

    await waitFor(() => expect(screen.getByRole('dialog')).toBeInTheDocument());
    // ⚡ **Opening a confirmation is not confirming.**
    expect(disconnectMutate).not.toHaveBeenCalled();
  });
});
