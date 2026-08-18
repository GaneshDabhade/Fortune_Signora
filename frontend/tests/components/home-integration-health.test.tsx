/**
 * 📁 **`card.inthealth` renders per-CONNECTION state** —
 * `Fortune Signora Home.dc.html` §04.
 */
import { render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

const integrations = vi.hoisted(() => vi.fn());
vi.mock('@/lib/state/workspace-provider', () => ({
  useWorkspaceContext: () => ({ activeWorkspace: { id: 'w1' } }),
}));
vi.mock('@/lib/query/hooks/integrations', () => ({ useIntegrations: integrations }));

import { IntegrationHealthCard } from '@/components/home/integration-health-card';

function connection(id: string, label: string, state: string, health: string, reason: string | null = null) {
  return { id, integration: 'salesforce', label, state, connected_at: null, attention: 'none', reason, health };
}

beforeEach(() => vi.clearAllMocks());

describe('📁 "per-connection state", not per-system', () => {
  it('🔴 two connections on one system are two rows', () => {
    /**
     * ⛔ **Rolling up to one row per integration loses the fact the card exists
     * for**: a workspace with two Salesforce connections, one revoked, would
     * read as *"Salesforce: needs attention"* and never say which.
     */
    integrations.mockReturnValue({
      data: [
        {
          integration: 'salesforce',
          capabilities: [],
          connectable: true,
          working: true,
          needs_attention: true,
          connections: [
            connection('c1', 'Salesforce — EMEA', 'connected', 'healthy'),
            connection('c2', 'Salesforce — NA', 'revoked', 'degraded', 'The token was revoked.'),
          ],
        },
      ],
      isPending: false,
      isError: false,
      error: null,
    });

    render(<IntegrationHealthCard />);

    expect(screen.getByText('Salesforce — EMEA')).toBeInTheDocument();
    expect(screen.getByText('Salesforce — NA')).toBeInTheDocument();
    expect(screen.getAllByRole('link', { name: 'Open the integration' })).toHaveLength(2);
  });

  it('✅ the reason is shown only when the read supplies one', () => {
    integrations.mockReturnValue({
      data: [
        { integration: 'salesforce', capabilities: [], connectable: true, working: true, needs_attention: false,
          connections: [connection('c1', 'Salesforce', 'connected', 'healthy')] },
      ],
      isPending: false, isError: false, error: null,
    });

    render(<IntegrationHealthCard />);

    // ⛔ **No sentence is composed to fill the space.**
    expect(screen.getByText('connected')).toBeInTheDocument();
    expect(screen.queryByText(/revoked/i)).not.toBeInTheDocument();
  });
});

describe('📁 contract 13 and state 07 stay inside the footprint', () => {
  it('⛔ a failed read renders the error in this card, not the page', () => {
    integrations.mockReturnValue({ data: undefined, isPending: false, isError: true, error: null });
    render(<IntegrationHealthCard />);
    expect(screen.getByTestId('home-integration-health')).toBeInTheDocument();
    expect(screen.getByText(/could not read your connections/i)).toBeInTheDocument();
    /* 📁 State 08's drawn action. ⛔ **A reload would discard every sibling
       card that succeeded**, which is the opposite of what the design asks. */
    expect(screen.getByRole('button', { name: 'Retry' })).toBeInTheDocument();
  });

  it('⛔ a pending read skeletons rather than claiming nothing is connected', () => {
    integrations.mockReturnValue({ data: undefined, isPending: true, isError: false, error: null });
    render(<IntegrationHealthCard />);
    expect(screen.queryByText(/No system is connected yet/i)).not.toBeInTheDocument();
  });

  it('✅ an empty result names what was looked for, and uses no banned string', () => {
    integrations.mockReturnValue({ data: [], isPending: false, isError: false, error: null });
    render(<IntegrationHealthCard />);
    // 📁 Banned on Home: "No data available".
    expect(screen.getByText(/No system is connected yet/i)).toBeInTheDocument();
    expect(screen.queryByText(/No data available/i)).not.toBeInTheDocument();
  });
});
