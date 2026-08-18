/**
 * **`card.risks` and `card.opps` partition one queue by a ratified posture** —
 * 📁 `Fortune Signora Home.dc.html` §05.
 *
 * 🔴 **These assert the PARTITION and the two ways it can lie**, because that
 * is the whole of what these cards add: the rows, the ranking and the empty
 * copy are the queue's and are covered where they are owned.
 */
import { render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

const triage = vi.hoisted(() => vi.fn());
const scoring = vi.hoisted(() => vi.fn());
const catalog = vi.hoisted(() => vi.fn());
const identities = vi.hoisted(() => vi.fn());
const commercials = vi.hoisted(() => vi.fn());

vi.mock('@/lib/state/workspace-provider', () => ({
  useWorkspaceContext: () => ({ activeWorkspace: { id: 'w1' } }),
}));
vi.mock('@/lib/query/hooks/triage', () => ({ useWorkspaceTriage: triage }));
vi.mock('@/lib/query/hooks/scoring', () => ({
  useScoringModel: scoring,
  useAccountCommercials: commercials,
}));
vi.mock('@/lib/query/hooks', () => ({
  useSignalCatalog: catalog,
  useAccountIdentities: identities,
}));

import { TopOpportunitiesCard, TopRisksCard } from '@/components/home/posture-cards';

function entry(id: string, type: string) {
  return { signal_id: id, signal_type: type, entity_id: `a-${id}`, rationale: `because ${id}`, state: 'open', resolution: null };
}

const QUEUE = [
  entry('1', 'contraction_risk'),
  entry('2', 'expansion_opportunity'),
  entry('3', 'competitor_entry'),
  entry('4', 'new_decision_maker'),
  entry('5', 'budget_unlocked'),
];

/** 📁 The postures exactly as `scoring_model@1.json` declares them. */
const POSTURES = new Map<string, string>([
  ['contraction_risk', 'contractionary'],
  ['competitor_entry', 'contractionary'],
  ['expansion_opportunity', 'expansionary'],
  ['budget_unlocked', 'expansionary'],
  ['new_decision_maker', 'neutral'],
]);

beforeEach(() => {
  vi.clearAllMocks();
  triage.mockReturnValue({ data: { items: QUEUE }, isPending: false, isError: false, error: null });
  scoring.mockReturnValue({ data: POSTURES, isPending: false, isError: false });
  catalog.mockReturnValue({ data: new Map() });
  identities.mockReturnValue({ data: new Map() });
  commercials.mockReturnValue({ data: new Map() });
});

describe('📁 the partition is the posture, and it comes from the scoring model', () => {
  it('✅ risks shows only contractionary signals', () => {
    render(<TopRisksCard />);
    expect(screen.getByText('because 1')).toBeInTheDocument();
    expect(screen.getByText('because 3')).toBeInTheDocument();
    expect(screen.queryByText('because 2')).not.toBeInTheDocument();
  });

  it('✅ opportunities shows only expansionary signals', () => {
    render(<TopOpportunitiesCard />);
    expect(screen.getByText('because 2')).toBeInTheDocument();
    expect(screen.getByText('because 5')).toBeInTheDocument();
    expect(screen.queryByText('because 1')).not.toBeInTheDocument();
  });

  it('⛔ a NEUTRAL posture appears in neither card', () => {
    /**
     * 📁 `card.opps` asks for *"ranked **positive** signals"*, and
     * `new_decision_maker` is one of the two the model declines to call either
     * way. ⛔ **Filing it under either heading would assert a reading the domain
     * refuses to make.**
     */
    const { unmount } = render(<TopRisksCard />);
    expect(screen.queryByText('because 4')).not.toBeInTheDocument();
    unmount();
    render(<TopOpportunitiesCard />);
    expect(screen.queryByText('because 4')).not.toBeInTheDocument();
  });
});

describe('🔴 an unresolved posture map must not read as "nothing is wrong"', () => {
  it('⛔ renders the skeleton rather than the success copy while the model is pending', () => {
    scoring.mockReturnValue({ data: undefined, isPending: true, isError: false });
    render(<TopRisksCard />);
    // 📁 Contract item 4 — state 06b's success copy standing in for a load is
    // the shared-empty-component violation, one card over.
    expect(screen.queryByTestId('home-top-risks-quiet')).not.toBeInTheDocument();
  });

  it('📁 contract 13 — a failed read stays inside its own footprint', () => {
    scoring.mockReturnValue({ data: undefined, isPending: false, isError: true });
    render(<TopRisksCard />);
    /* ⚡ **The panel carries the failing card's own test id**, so *"inside its
       own footprint"* stays assertable when the frame is replaced. */
    expect(screen.getByTestId('home-top-risks')).toBeInTheDocument();
    expect(screen.getByText(/Top risks could not be read/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Retry' })).toBeInTheDocument();
  });
});

describe('📁 the population, and the ceiling', () => {
  it('✅ states the size of the set it ranked, not the number of rows drawn', () => {
    render(<TopRisksCard />);
    // 📁 *"with the population each was derived from"* — two contractionary.
    expect(screen.getByTestId('home-top-risks')).toHaveTextContent('2');
  });

  it('⛔ never more than five rows, and the overflow goes to Signals', () => {
    const many = Array.from({ length: 7 }, (_, i) => entry(`r${i}`, 'contraction_risk'));
    triage.mockReturnValue({ data: { items: many }, isPending: false, isError: false, error: null });
    render(<TopRisksCard />);
    expect(screen.getAllByRole('link', { name: 'Open the deal' })).toHaveLength(5);
    expect(screen.getByRole('link', { name: /See all 7 in Signals/ })).toBeInTheDocument();
  });
});
