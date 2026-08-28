/**
 * **Home's activation cards** — 📁 `Fortune Signora Home.dc.html`, states 01
 * and 02, with [TASK-1424](../../../docs/BACKLOG.md).
 *
 * 🔴 **Nothing rendered these.** ⚡ **And this is the card that decides whether
 * somebody is shown SETUP**, so a failed read rendering as an absence tells a
 * customer whose CRM is connected and working that they have connected
 * nothing.
 */
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

const useIntegrations = vi.hoisted(() => vi.fn());
const useActivationState = vi.hoisted(() => vi.fn());

vi.mock('@/lib/state/workspace-provider', () => ({
  useWorkspaceContext: () => ({ activeWorkspace: { id: 'w1', name: 'Northwind' } }),
}));
// ⚡ **Mocked at the modules the component actually imports** — ⛔ the barrel
// re-exports both, and mocking the barrel leaves the direct imports untouched.
vi.mock('@/lib/query/hooks/integrations', () => ({ useIntegrations }));
vi.mock('@/lib/query/hooks/home', () => ({ useActivationState }));

import { ConnectCallsCard, ConnectCrmCard } from '@/components/home/activation-cards';

const NEVER = ['undefined', 'null', 'NaN', '[object Object]', '/**', '*/'];

function draw(element: React.ReactElement) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(<QueryClientProvider client={client}>{element}</QueryClientProvider>);
}

beforeEach(() => {
  vi.clearAllMocks();
  useIntegrations.mockReturnValue({
    isError: false,
    error: null,
    isFetching: false,
    refetch: vi.fn(),
    data: [],
  });
  useActivationState.mockReturnValue({ complete: new Set<string>() });
});

describe('🔴 a failed read is a failure, never an absence', () => {
  it('⛔ it says what could not be read, and that nothing was lost', () => {
    /**
     * 📁 **[P-A](../../../docs/DOMAIN_DISCOVERY_REGISTER.md)** — *a failed read
     * must never render as an empty result.* ⚡ **The component's own note says
     * why it matters more here than anywhere else on Home**: this card decides
     * whether somebody is shown SETUP, so *"there is nothing"* reads as *"you
     * have connected nothing"* to a customer whose CRM is working.
     */
    useIntegrations.mockReturnValue({
      isError: true,
      error: new Error('down'),
      isFetching: false,
      refetch: vi.fn(),
      data: undefined,
    });
    const { container } = draw(<ConnectCrmCard />);

    expect(
      screen.getByText(/could not be read/),
    ).toBeInTheDocument();
    // ⛔ **And the reassurance is not decoration** — it is the sentence that
    // stops a working integration reading as a lost one.
    expect(screen.getByText(/has been lost or disconnected/)).toBeInTheDocument();
    for (const forbidden of NEVER) {
      expect(container.textContent ?? '').not.toContain(forbidden);
    }
  });

  it('✅ and it offers a retry, because asking again is the useful thing', () => {
    useIntegrations.mockReturnValue({
      isError: true,
      error: new Error('down'),
      isFetching: false,
      refetch: vi.fn(),
      data: undefined,
    });
    draw(<ConnectCrmCard />);

    // ⚡ **`Retry`, which is `CardFailure`'s word rather than this test's** —
    // ⛔ a matcher spelling its own guess is a second copy of the copy.
    expect(screen.getByRole('button', { name: 'Retry' })).toBeInTheDocument();
  });
});

describe('📁 the card states the cost before the control that spends it', () => {
  it('⚡ "About 4 minutes · needs admin consent" is on screen with the button', () => {
    /**
     * ⛔ **A setup step whose cost is discovered halfway through is a step
     * people abandon.** 📁 The design puts the estimate and the consent
     * requirement in the card, not behind the click.
     */
    const { container } = draw(<ConnectCrmCard />);

    expect(screen.getByText(/About 4 minutes/)).toBeInTheDocument();
    expect(screen.getByText(/needs admin consent/)).toBeInTheDocument();
    expect(screen.getByText('Connect a CRM')).toBeInTheDocument();
    for (const forbidden of NEVER) {
      expect(container.textContent ?? '').not.toContain(forbidden);
    }
  });

  it('✅ and the calls card is a different step, not the same one relabelled', () => {
    // ⚡ **Two cards, two copies, one component** — 📁 §2: the shape is shared
    // and the words are not, which is the opposite of the usual drift.
    const crm = draw(<ConnectCrmCard />);
    const crmText = crm.container.textContent ?? '';
    crm.unmount();

    const { container } = draw(<ConnectCallsCard />);
    expect(container.textContent).not.toBe(crmText);
    for (const forbidden of NEVER) {
      expect(container.textContent ?? '').not.toContain(forbidden);
    }
  });
});
