/**
 * **The Signal Center's queue** — [TASK-439](../../../docs/BACKLOG.md), against
 * `docs/design-snapshot/screens/Fortune Signora Signal Center.dc.html`.
 *
 * > 📁 ***"A triage queue, not a notification list · every signal ends in a
 * > decision."***
 *
 * ⚡ **The two properties worth protecting are both about restraint**: the
 * screen must not invent the words for a signal type, and it must not print a
 * field the platform does not publish.
 */
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it, vi, beforeEach } from 'vitest';

import type { QueueEntry, SignalTypeName } from '@/lib/api/types';

const triage = vi.hoisted(() => vi.fn());
const resolveMutate = vi.hoisted(() => vi.fn());
const catalog = vi.hoisted(() => vi.fn());
const identities = vi.hoisted(() => vi.fn());

vi.mock('@/lib/query/hooks/triage', () => ({
  useWorkspaceTriage: triage,
  useResolveSignal: () => ({ mutate: resolveMutate, isPending: false }),
}));
vi.mock('@/lib/query/hooks', () => ({
  useSignalCatalog: catalog,
  useAccountIdentities: identities,
}));
vi.mock('@/lib/state/workspace-provider', () => ({
  useWorkspaceContext: () => ({ activeWorkspace: { id: 'ws-1' } }),
}));

import { SignalQueue } from '@/app/(app)/signals/signal-queue';

const ACME = 'acc-1';
const GLOBEX = 'acc-2';

function entry(over: Partial<QueueEntry> = {}): QueueEntry {
  return {
    signal_id: 'sig-1',
    signal_type: 'pricing_objection',
    entity_id: ACME,
    rationale: 'Two buyers raised list price on the renewal thread this week.',
    state: 'open',
    resolution: null,
    ...over,
  };
}

/**
 * ⚡ **The catalog's real shape**, including `why_it_matters` — because one of
 * the assertions below is that it never reaches a row.
 */
const TYPES: SignalTypeName[] = [
  {
    key: 'pricing_objection',
    title: 'Pricing objection',
    why_it_matters: 'A pricing objection from an economic buyer often precedes a close-date slip.',
  },
  {
    key: 'champion_left',
    title: 'Champion left',
    why_it_matters: 'A departed champion removes the internal advocate for the renewal.',
  },
];

beforeEach(() => {
  resolveMutate.mockClear();
  catalog.mockReturnValue({
    data: new Map(TYPES.map((t) => [t.key, t])),
    isError: false,
    isPending: false,
  });
  identities.mockReturnValue({
    data: new Map([[ACME, { account_id: ACME, name: 'Vantage Logistics A/S' }]]),
  });
  triage.mockReturnValue({ data: { items: [entry()] }, isPending: false, isError: false });
});

describe('the queue says what is waiting', () => {
  it('⚡ takes its words from the catalog, never from a table in the screen', () => {
    /**
     * 📁 **The architecture's rule**: *"`signal_type` is a catalog key and
     * never a title… the key travels and `useSignalCatalog` supplies the
     * words. A translation table here would be a second vocabulary, and two
     * representations of one truth become contradictory truth."*
     */
    render(<SignalQueue />);
    expect(screen.getAllByText('Pricing objection').length).toBeGreaterThan(0);
    // ⛔ The raw key never reaches the screen when the catalog knows it.
    expect(screen.queryByText('pricing_objection')).not.toBeInTheDocument();
  });

  it('names the account, and says so plainly when nobody has named it', () => {
    render(<SignalQueue />);
    expect(screen.getByText('Vantage Logistics A/S')).toBeInTheDocument();

    // ⚠️ *"`name` is null when nobody has named the account."* ⛔ The id is not
    // printed as a fallback — an id is not a name and nobody can act on one.
    identities.mockReturnValue({ data: new Map() });
    triage.mockReturnValue({
      data: { items: [entry({ entity_id: GLOBEX })] },
      isPending: false,
      isError: false,
    });
    render(<SignalQueue />);
    expect(screen.getAllByText('Unnamed account').length).toBeGreaterThan(0);
    expect(screen.queryByText(GLOBEX)).not.toBeInTheDocument();
  });

  it('📁 groups and counts — the design says "grouped and counted"', () => {
    triage.mockReturnValue({
      data: {
        items: [
          entry({ signal_id: 'a' }),
          entry({ signal_id: 'b' }),
          entry({ signal_id: 'c', signal_type: 'champion_left' }),
        ],
      },
      isPending: false,
      isError: false,
    });
    render(<SignalQueue />);
    // Two groups, the larger first, each with its count beside its heading.
    const headings = screen.getAllByRole('heading', { level: 2 });
    expect(headings[0]).toHaveTextContent(/Pricing objection\s*2/);
    expect(headings[1]).toHaveTextContent(/Champion left\s*1/);
  });
});

describe('🔴 the two fields with no source are absent, not invented — C-251', () => {
  it('⛔ never renders why_it_matters as a per-signal summary', () => {
    /**
     * **The tempting wrong move.** The catalog carries `why_it_matters` and it
     * would sit perfectly where the design puts `{{ s.summary }}` — ⛔ **but
     * its own contract says it is *"a fact about the TYPE, true before any
     * account exhibits it"*.** **Rendering it per row prints one sentence
     * under every signal of that type**, where the design puts a per-instance
     * finding, and it would read as though Signora had examined this account.
     */
    render(<SignalQueue />);
    expect(
      screen.queryByText(/often precedes a close-date slip/i),
    ).not.toBeInTheDocument();
  });

  it('⛔ prints no confidence, because nothing computes one', () => {
    // 📁 The design prints *"6 sources · confidence 4 of 5"* — both halves are
    // MEASUREMENTS, and `confidence` appears nowhere in the API contract.
    render(<SignalQueue />);
    expect(screen.queryByText(/confidence/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/\bof 5\b/)).not.toBeInTheDocument();
  });
});

describe('every signal leaves by a decision', () => {
  it('records an action', async () => {
    render(<SignalQueue />);
    await userEvent.click(screen.getByRole('button', { name: 'Actioned' }));
    expect(resolveMutate).toHaveBeenCalledWith({
      signalId: 'sig-1',
      outcome: { kind: 'actioned' },
    });
  });

  it('🔴 refuses a dismissal with no reason, and the type says why', async () => {
    /**
     * ⛔ **`ResolveOutcome` makes a reasonless dismissal unconstructable** —
     * this keeps that true at the edge rather than leaving the server to
     * refuse it. 📁 **And the design gives the product reason**: *"Dismissal
     * reasons feed rule precision."* **An empty one is a lost measurement.**
     */
    render(<SignalQueue />);
    await userEvent.click(screen.getByRole('button', { name: 'Dismiss' }));

    const confirm = screen.getByRole('button', { name: 'Dismiss signal' });
    expect(confirm).toBeDisabled();

    // ⛔ Whitespace is not a reason.
    await userEvent.type(screen.getByLabelText(/reason/i), '   ');
    expect(confirm).toBeDisabled();

    await userEvent.type(screen.getByLabelText(/reason/i), 'Already handled on the call');
    await waitFor(() => expect(confirm).toBeEnabled());
    await userEvent.click(confirm);

    expect(resolveMutate).toHaveBeenCalledWith({
      signalId: 'sig-1',
      outcome: { kind: 'dismissed', reason: 'Already handled on the call' },
    });
  });

  it('offers no decision on a signal that has already left the queue', () => {
    triage.mockReturnValue({
      data: {
        items: [
          entry({ state: 'closed', resolution: { outcome: 'dismissed' } as never }),
        ],
      },
      isPending: false,
      isError: false,
    });
    render(<SignalQueue />);
    expect(screen.queryByRole('button', { name: 'Actioned' })).not.toBeInTheDocument();
    expect(screen.getByText('dismissed')).toBeInTheDocument();
  });
});

describe('the states the queue can be in', () => {
  it('⚡ a quiet queue is a success state, not a broken page', () => {
    triage.mockReturnValue({ data: { items: [] }, isPending: false, isError: false });
    render(<SignalQueue />);
    expect(screen.getByText(/Nothing needs review/i)).toBeInTheDocument();
  });

  it('🔴 says when it could not find out — P-A, and never renders as empty', () => {
    /**
     * ⛔ **An empty queue and an unreachable one are different facts.** A page
     * that renders the success state on a failed read tells a seller there is
     * nothing waiting when Signora simply could not look.
     */
    triage.mockReturnValue({ data: undefined, isPending: false, isError: true });
    render(<SignalQueue />);
    expect(screen.getByText(/could not be loaded/i)).toBeInTheDocument();
    expect(screen.queryByText(/Nothing needs review/i)).not.toBeInTheDocument();
  });
});

describe('🔴 the summary is the signal’s own, never the type’s', () => {
  /**
   * **This is the whole of [TASK-1427](../../../docs/BACKLOG.md), stated as a
   * test.** 📁 The row's own Playwright line: *"two rows of the same
   * `signal_type` render DIFFERENT summaries"* — ⛔ **that assertion is the
   * defect**, because the failure mode it catches is silent: rendering the
   * catalog's `why_it_matters` puts one sentence under fifty rows and **every
   * one of them looks right.**
   */
  it('⛔ two rows of the SAME type render different summaries', () => {
    const first = 'Two buyers raised list price on the renewal thread this week.';
    const second = 'Procurement asked for a discount schedule before signing.';
    triage.mockReturnValue({
      data: {
        items: [
          entry({ signal_id: 'a', rationale: first }),
          entry({ signal_id: 'b', rationale: second }),
        ],
      },
      isPending: false,
      isError: false,
    });
    render(<SignalQueue />);

    // Same type — one group, so a per-type sentence would satisfy the grouping
    // and still be wrong. The two summaries are what distinguishes them.
    expect(screen.getAllByRole('heading', { level: 2 })).toHaveLength(1);
    expect(screen.getByText(first)).toBeInTheDocument();
    expect(screen.getByText(second)).toBeInTheDocument();
  });

  it('⚡ and the guard can fail — identical rationales collapse to one node', () => {
    // 📁 B-162's lesson: a scan proved only by passing is a scan nobody has
    // seen work. If the component rendered a per-TYPE sentence, both rows
    // would carry the same text — this asserts that case is distinguishable.
    const same = 'The same sentence under every row.';
    triage.mockReturnValue({
      data: {
        items: [
          entry({ signal_id: 'a', rationale: same }),
          entry({ signal_id: 'b', rationale: same }),
        ],
      },
      isPending: false,
      isError: false,
    });
    render(<SignalQueue />);
    expect(screen.getAllByText(same)).toHaveLength(2);
  });

  it('📱 clamped to two lines, and complete in the DOM', () => {
    /**
     * ⛔ 📁 *"a truncated rationale must not read as the whole reason"*. The
     * clamp is visual only — **the full sentence stays in the document**, so a
     * screen reader hears all of it and `title` carries it on hover.
     */
    const long =
      'Procurement asked for a discount schedule before signing, and two buyers ' +
      'raised list price on the renewal thread in the same week, which together ' +
      'read as a budget conversation rather than an objection to the product.';
    triage.mockReturnValue({
      data: { items: [entry({ rationale: long })] },
      isPending: false,
      isError: false,
    });
    render(<SignalQueue />);
    const node = screen.getByText(long);
    expect(node).toHaveClass('line-clamp-2');
    expect(node).toHaveAttribute('title', long);
  });
});
