/**
 * 📁 **`card.agentqueue` and `card.agentruns`** —
 * `Fortune Signora Home.dc.html` §04 registry, produced by the research
 * request lifecycle (`agents.runs`).
 *
 * 🔴 **The properties worth asserting are the ones that would look fine
 * wrong**: a queue that reported a failure as *output*, a card that told
 * somebody nothing had happened while a run was in flight, and a row claiming
 * *you* asked for something somebody else did.
 */
import { render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

const runs = vi.hoisted(() => vi.fn());
const identities = vi.hoisted(() => vi.fn());
const session = vi.hoisted(() => vi.fn());

vi.mock('@/lib/state/workspace-provider', () => ({
  useWorkspaceContext: () => ({ activeWorkspace: { id: 'w1' } }),
}));
vi.mock('@/lib/query/hooks/research-runs', () => ({ useResearchRuns: runs }));
vi.mock('@/lib/query/hooks', () => ({ useAccountIdentities: identities }));
vi.mock('@/lib/auth/client', () => ({ useSession: session }));

import { AgentQueueCard, AgentRunsCard } from '@/components/home/agent-cards';

const DAY = 86_400_000;
const ME = 'u-me';

function run(overrides: Partial<Record<string, unknown>> = {}) {
  return {
    request_id: `r-${Math.random()}`,
    account_id: 'a1',
    requested_by: ME,
    requested_at: new Date(Date.now() - DAY).toISOString(),
    status: 'completed',
    updated_at: new Date().toISOString(),
    detail: null,
    sources: 9,
    ...overrides,
  };
}

function answered(data: unknown[]) {
  runs.mockReturnValue({ data, isPending: false, isError: false, error: null });
}

beforeEach(() => {
  vi.clearAllMocks();
  session.mockReturnValue({ data: { user: { id: ME } } });
  identities.mockReturnValue({
    data: new Map([
      ['a1', { name: 'Norvell Energy' }],
      ['a2', { name: 'Vantage Logistics' }],
    ]),
  });
});

describe('📁 the queue is agent OUTPUT awaiting a person', () => {
  it('✅ names the account, when it was asked for, and how much it read', () => {
    // 📁 The design's own row: "Research on Norvell finished · You requested
    // it Tuesday · 9 sources · Open".
    answered([run()]);

    render(<AgentQueueCard />);

    expect(screen.getByText(/Research on Norvell Energy finished/)).toBeInTheDocument();
    expect(screen.getByText(/You requested it yesterday · 9 sources/)).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /Norvell Energy/ })).toHaveAttribute(
      'href',
      '/accounts/a1',
    );
  });

  it('🔴 a FAILURE is not output and never appears here', () => {
    /**
     * ⛔ 📁 *"Nothing here has been sent or written"* is a promise about
     * OUTPUT. A failed run produced none, and reporting it as something to
     * review would offer a person a brief that does not exist.
     */
    answered([run({ status: 'failed', detail: 'The provider returned nothing.', sources: null })]);

    render(<AgentQueueCard />);

    expect(screen.queryByText(/Research on Norvell Energy finished/)).not.toBeInTheDocument();
    expect(screen.queryByText(/provider returned nothing/i)).not.toBeInTheDocument();
  });

  it('🔴 a run still going is not reported as nothing having happened', () => {
    /**
     * 📁 **[P-A]** — *"a batch that is still running and one that failed to
     * start must never render alike."* ⛔ Here the pair is **working** versus
     * **never asked**, and collapsing them tells somebody nothing happened
     * while Signora is mid-run.
     */
    answered([run({ status: 'running', sources: null })]);

    render(<AgentQueueCard />);

    expect(screen.getByText(/Signora is researching an account/)).toBeInTheDocument();
    expect(screen.queryByText(/has not been asked/)).not.toBeInTheDocument();
  });

  it('✅ an untouched organization says so, and says what was checked', () => {
    answered([]);

    render(<AgentQueueCard />);

    expect(screen.getByText(/has not been asked to research anything/i)).toBeInTheDocument();
  });

  it('⛔ the promise is on the card whether or not there is anything on it', () => {
    answered([]);

    render(<AgentQueueCard />);

    expect(
      screen.getByText(/Nothing here was sent or written. Agent output waits for a person./),
    ).toBeInTheDocument();
  });

  it('⛔ a failed read never says there was no output', () => {
    runs.mockReturnValue({ data: undefined, isPending: false, isError: true, error: null });

    render(<AgentQueueCard />);

    expect(screen.getByText(/could not read what its agents have been doing/i)).toBeInTheDocument();
    expect(screen.queryByText(/has not been asked/)).not.toBeInTheDocument();
  });
});

describe('📁 the runs card ranks failures first', () => {
  it('🔴 a failure outranks a newer success', () => {
    // ⚡ The server returns the order the runs happened; the ranking is this
    // card's, and it is a stable partition rather than a sort.
    answered([
      run({ account_id: 'a2', status: 'completed' }),
      run({ status: 'failed', detail: 'Mailbox auth expired.', sources: null }),
    ]);

    render(<AgentRunsCard />);

    const rows = screen.getAllByRole('link');
    expect(rows[0]).toHaveTextContent(/failed/);
    expect(rows[1]).toHaveTextContent(/Vantage Logistics/);
  });

  it('⛔ the failure carries its own reason, never a composed one', () => {
    answered([run({ status: 'failed', detail: 'Mailbox auth expired.', sources: null })]);

    render(<AgentRunsCard />);

    expect(screen.getByText(/Mailbox auth expired\./)).toBeInTheDocument();
  });

  it('⚠️ "found nothing" is an OUTCOME, not an error', () => {
    /**
     * 📁 The contract says so in terms: *"`nothing_to_research` is not a
     * failure — it means the run finished and found nothing worth comparing,
     * which is a real answer on an account with little evidence and must never
     * be shown as an error."*
     */
    answered([run({ status: 'nothing_to_research', sources: null })]);

    render(<AgentRunsCard />);

    expect(screen.getByText(/found nothing to compare/)).toBeInTheDocument();
    expect(screen.queryByText(/failed/)).not.toBeInTheDocument();
  });

  it('✅ every run appears here, including the ones the queue leaves out', () => {
    answered([
      run({ status: 'running', sources: null }),
      run({ account_id: 'a2', status: 'completed' }),
    ]);

    render(<AgentRunsCard />);

    expect(screen.getAllByRole('link')).toHaveLength(2);
  });
});

describe("🔴 a row must not claim you asked for somebody else's run", () => {
  it("⛔ says 'Requested' rather than 'You requested it' for a colleague", () => {
    /**
     * 📁 **[ADR-0026]** — Better Auth owns identity in the Next.js tier, so
     * the API has no NAME to give. ✅ Not naming a colleague is honest;
     * inventing one is not, and claiming they were you is worse.
     */
    answered([run({ requested_by: 'u-someone-else' })]);

    render(<AgentQueueCard />);

    expect(screen.getByText(/^Requested yesterday · 9 sources$/)).toBeInTheDocument();
  });

  it('⛔ claims nothing while the session is still unknown', () => {
    session.mockReturnValue({ data: undefined });
    answered([run()]);

    render(<AgentQueueCard />);

    expect(screen.queryByText(/You requested it/)).not.toBeInTheDocument();
  });
});
