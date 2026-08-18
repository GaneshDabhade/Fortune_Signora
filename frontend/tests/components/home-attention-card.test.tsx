/**
 * **Home's attention card reads signals and deals** —
 * 📁 `Fortune Signora Home.dc.html` §04, `card.attention`, dependency
 * *"signals + deals"*.
 *
 * 🔴 **The product owner ruled `AccountAttention` out of Home on 2026-08-17.**
 * ⛔ These assert the rules that would be invisible if the card quietly drifted
 * back: **which reads it uses**, that the reason is the signal's own, that five
 * is the ceiling, and that state 05 and state 06b stay separate.
 */
import { render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

const triage = vi.hoisted(() => vi.fn());
const catalog = vi.hoisted(() => vi.fn());
const identities = vi.hoisted(() => vi.fn());
const postures = vi.hoisted(() => vi.fn());
const commercials = vi.hoisted(() => vi.fn());
const count = vi.hoisted(() => vi.fn());
const pipeline = vi.hoisted(() => vi.fn());

vi.mock('@/lib/state/workspace-provider', () => ({
  useWorkspaceContext: () => ({ activeWorkspace: { id: 'w1', name: 'Northwind' } }),
}));
vi.mock('@/lib/query/hooks/triage', () => ({ useWorkspaceTriage: triage }));
vi.mock('@/lib/query/hooks', () => ({
  useSignalCatalog: catalog,
  useAccountIdentities: identities,
}));
vi.mock('@/lib/query/hooks/scoring', () => ({
  useScoringModel: postures,
  useAccountCommercials: commercials,
}));
vi.mock('@/lib/query/hooks/accounts-count', () => ({ useAccountsCount: count }));
vi.mock('@/lib/query/hooks/commercial', () => ({ usePipelineHealth: pipeline }));

import { AttentionCard } from '@/components/home/attention-card';

function entry(n: number, type = 'decision_maker_departed') {
  return {
    signal_id: `s${n}`,
    signal_type: type,
    entity_id: `e${n}`,
    rationale: `Their champion moved on ${n} August and nobody has been re-engaged.`,
    state: 'open' as const,
    resolution: null,
  };
}

beforeEach(() => {
  vi.clearAllMocks();
  triage.mockReturnValue({
    data: { items: [], next_cursor: null, has_more: false },
    isPending: false,
    isError: false,
    dataUpdatedAt: Date.UTC(2026, 7, 17, 7, 0),
    refetch: () => {},
  });
  catalog.mockReturnValue({
    data: new Map([
      ['decision_maker_departed', {
        key: 'decision_maker_departed',
        title: 'Decision maker departed',
        why_it_matters: 'The person who sponsored this has gone.',
      }],
      ['active_evaluation', {
        key: 'active_evaluation',
        title: 'Active evaluation',
        why_it_matters: 'They are looking now.',
      }],
    ]),
  });
  postures.mockReturnValue({
    data: new Map([
      ['decision_maker_departed', 'contractionary'],
      ['active_evaluation', 'expansionary'],
    ]),
  });
  identities.mockReturnValue({ data: new Map([['e1', { account_id: 'e1', name: 'Corrigan Health' }]]) });
  commercials.mockReturnValue({
    data: new Map([['e1', { open_acv: { amount: 2110000, currency: 'USD' }, renewal_date: null, stage: null }]]),
  });
  count.mockReturnValue({ data: { total: 41 } });
  pipeline.mockReturnValue({ data: { ageing: [{ stage: 'tracking', open_count: 7 }, { stage: 'engaged', open_count: 4 }] } });
});

describe('📁 the row is composed from signals and deals', () => {
  it('🔴 names the company, never eight characters of a UUID', () => {
    /**
     * ⚠️ **The defect this rewrite fixes.** ⛔ The `AccountAttention` version
     * rendered `account_id.slice(0, 8)` because the Opportunity Engine is
     * forbidden from reaching entity names; **the identity batch is the
     * composition the design always required.**
     */
    triage.mockReturnValue({ ...triage(), data: { items: [entry(1)] }, isPending: false, isError: false });

    render(<AttentionCard />);

    expect(screen.getByText('Corrigan Health')).toBeInTheDocument();
    expect(screen.queryByText('e1')).not.toBeInTheDocument();
  });

  it("📁 the reason is the SIGNAL's own rationale, not the type's why_it_matters", () => {
    /**
     * 📁 The contract: *"per signal, not per type — the catalog's
     * `why_it_matters` is a fact about the TYPE, so rendering that as the
     * summary would put the same sentence under every row."*
     */
    triage.mockReturnValue({ ...triage(), data: { items: [entry(1)] }, isPending: false, isError: false });

    render(<AttentionCard />);

    expect(screen.getByText(/champion moved on 1 August/)).toBeInTheDocument();
    expect(screen.queryByText(/The person who sponsored this has gone/)).not.toBeInTheDocument();
  });

  it('📁 the tag word comes from the catalog', () => {
    triage.mockReturnValue({ ...triage(), data: { items: [entry(1)] }, isPending: false, isError: false });

    render(<AttentionCard />);

    expect(screen.getByText('Decision maker departed')).toBeInTheDocument();
  });

  it("📁 the value is Open ACV with its currency — the design's $2.11M", () => {
    triage.mockReturnValue({ ...triage(), data: { items: [entry(1)] }, isPending: false, isError: false });

    render(<AttentionCard />);

    expect(screen.getByText(/2,110,000|2\.11M|\$2,110,000/)).toBeInTheDocument();
  });

  it('⛔ a value nobody has stated is omitted, never zero-filled', () => {
    /**
     * 📁 [ADR-0409](../../../docs/architecture/adr/0409-commercial-account-facts.md)
     * §5. ⛔ **A `$0` beside an account name is a figure a seller would act on.**
     */
    triage.mockReturnValue({ ...triage(), data: { items: [entry(1)] }, isPending: false, isError: false });
    commercials.mockReturnValue({
      data: new Map([['e1', { open_acv: null, renewal_date: null, stage: null }]]),
    });

    render(<AttentionCard />);

    expect(screen.queryByText(/\$0|0\.00/)).not.toBeInTheDocument();
  });

  it('♿ severity is carried by the tag word as well as the tint', () => {
    /**
     * 📁 1.4.1: *"Removing colour leaves the tag and the order intact."* ⚡ The
     * posture comes from the Buying Score Engine — ⛔ **never a table in the
     * browser**, which would be the second vocabulary the catalog exists to
     * prevent.
     */
    triage.mockReturnValue({
      ...triage(),
      data: { items: [entry(1), entry(2, 'active_evaluation')] },
      isPending: false,
      isError: false,
    });

    render(<AttentionCard />);

    expect(screen.getByText('Decision maker departed')).toBeInTheDocument();
    expect(screen.getByText('Active evaluation')).toBeInTheDocument();
  });
});

describe('📁 five, and the sixth is a link', () => {
  it('⛔ renders at most five rows', () => {
    triage.mockReturnValue({
      ...triage(),
      data: { items: [1, 2, 3, 4, 5, 6, 7, 8].map((n) => entry(n)) },
      isPending: false,
      isError: false,
    });

    render(<AttentionCard />);

    expect(screen.getAllByRole('link', { name: 'Open the account' })).toHaveLength(5);
  });

  it('📁 the sixth becomes one link to Signals, naming the total', () => {
    triage.mockReturnValue({
      ...triage(),
      data: { items: [1, 2, 3, 4, 5, 6, 7, 8].map((n) => entry(n)) },
      isPending: false,
      isError: false,
    });

    render(<AttentionCard />);

    expect(screen.getByRole('link', { name: 'See all 8 in Signals' })).toHaveAttribute(
      'href',
      '/signals',
    );
  });
});

describe('🔴 state 05 and state 06b are different states', () => {
  it('✅ 06b names what was checked and when — HM-COPY-06', () => {
    render(<AttentionCard />);

    expect(
      screen.getByText(/Signora checked 41 accounts and 11 open deals at/),
    ).toBeInTheDocument();
  });

  it('⛔ 05 is not HM-COPY-06 — an empty workspace has not been checked', () => {
    count.mockReturnValue({ data: { total: 0 } });

    render(<AttentionCard />);

    expect(screen.queryByText(/Nothing needs you this morning/)).not.toBeInTheDocument();
    expect(screen.getByText(/no records to work from yet/)).toBeInTheDocument();
  });

  it('🔴 a count that could not be read does not become a count of zero', () => {
    /**
     * 🔴 [P-A](../../../docs/DOMAIN_DISCOVERY_REGISTER.md), extended: **a read
     * that could not happen must not render as a read that happened.** ⛔
     * `HM-COPY-06` asserts what Signora checked, and asserting *"0 accounts"*
     * because a request failed is a false claim, not a smaller one.
     */
    pipeline.mockReturnValue({ data: undefined });

    render(<AttentionCard />);

    expect(screen.queryByText(/0 open deals/)).not.toBeInTheDocument();
    expect(screen.getByText(/could not say how much it checked/)).toBeInTheDocument();
  });
});

describe('📁 state 08 — the card fails inside its own footprint', () => {
  it('states the failure, offers one retry, and says nothing about siblings', () => {
    triage.mockReturnValue({
      data: undefined,
      isPending: false,
      isError: true,
      error: new Error('boom'),
      dataUpdatedAt: 0,
      refetch: () => {},
    });

    render(<AttentionCard />);

    /**
     * ⚠️ **`status`, not `alert`, and the change is a correction.**
     *
     * 📁 System States `4.1.3`: *"Region errors and retries announce POLITELY.
     * Only a state that ends the session — 500, maintenance — announces
     * assertively, once."* ⛔ **This card asserted `role="alert"`**, which
     * interrupts a screen-reader user mid-sentence for one card that failed
     * while four others rendered. 📁 `SystemState` decides politeness from
     * scope rather than from the caller, *"because a caller free to choose will
     * eventually choose the polite one for an outage and the rude one for a
     * widget."*
     */
    expect(screen.getByRole('status')).toHaveTextContent('What needs you could not be loaded');
    expect(screen.getByRole('button', { name: 'Retry' })).toBeInTheDocument();
    expect(screen.getByText(/Everything else on this page is unaffected/)).toBeInTheDocument();
  });
});
