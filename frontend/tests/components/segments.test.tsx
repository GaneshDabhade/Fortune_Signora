import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';

import { SegmentList, productNames } from '@/components/commercial/segments';
import type { IcpSegmentSummary, ProductCatalog } from '@/lib/api/types';

const REVENUE_CLOUD = '11111111-1111-4111-8111-111111111111';
const CPQ = '22222222-2222-4222-8222-222222222222';
const REMOVED = '33333333-3333-4333-8333-333333333333';

function catalog(): ProductCatalog {
  return {
    version: 1,
    products: [
      { id: REVENUE_CLOUD, name: 'Revenue Cloud', description: '' },
      { id: CPQ, name: 'CPQ', description: '' },
    ],
    updated_at: '2026-08-01T00:00:00Z',
    updated_by: 'someone',
  } as ProductCatalog;
}

function segment(overrides: Partial<IcpSegmentSummary> = {}): IcpSegmentSummary {
  return {
    id: crypto.randomUUID(),
    name: 'Mid-market Fintech',
    state: 'published',
    version: 1,
    product_ids: [REVENUE_CLOUD],
    last_changed_at: '2026-08-01T00:00:00Z',
    last_changed_by: 'someone',
    ...overrides,
  };
}

function renderList(segments: IcpSegmentSummary[], props = {}) {
  return render(
    <SegmentList
      segments={segments}
      catalog={catalog()}
      isLoading={false}
      isError={false}
      {...props}
    />,
  );
}

describe('the sentence the old model could not hold', () => {
  it('shows one segment buying several products', () => {
    // "Revenue Cloud + CPQ, sold together to mid-market fintech" — one row,
    // where the previous model needed two that drift apart.
    renderList([segment({ product_ids: [REVENUE_CLOUD, CPQ] })]);
    expect(screen.getByText(/Revenue Cloud · CPQ/)).toBeInTheDocument();
  });

  it('shows two segments buying the same product', () => {
    renderList([
      segment({ name: 'Mid-market Fintech', product_ids: [REVENUE_CLOUD] }),
      segment({ name: 'Enterprise Insurance', product_ids: [REVENUE_CLOUD] }),
    ]);
    expect(screen.getByText('Mid-market Fintech')).toBeInTheDocument();
    expect(screen.getByText('Enterprise Insurance')).toBeInTheDocument();
  });
});

describe('a product the customer no longer sells', () => {
  it('is counted rather than silently dropped', () => {
    // The segment keeps naming it — the reference is part of what the customer
    // said. Listing fewer products than the segment has would be the screen
    // quietly editing them.
    renderList([segment({ product_ids: [REVENUE_CLOUD, REMOVED] })]);
    expect(screen.getByText(/one product you no longer sell/)).toBeInTheDocument();
  });

  it('is pluralised honestly', () => {
    renderList([segment({ product_ids: [REMOVED, crypto.randomUUID()] })]);
    expect(screen.getByText(/2 products you no longer sell/)).toBeInTheDocument();
  });

  it('resolves names through the catalog and nowhere else', () => {
    const result = productNames(segment({ product_ids: [CPQ, REMOVED] }), catalog());
    expect(result).toEqual({ named: ['CPQ'], missing: 1 });
  });

  it('shows nothing rather than guessing when the catalog has not loaded', () => {
    expect(productNames(segment(), undefined)).toEqual({ named: [], missing: 0 });
  });
});

describe('what the row says about state', () => {
  it.each([
    ['published', 'In use'],
    ['draft', 'Not published yet'],
    ['archived', 'Archived'],
  ] as const)('%s reads as "%s"', (state, label) => {
    renderList([segment({ state })]);
    expect(screen.getByText(label)).toBeInTheDocument();
  });

  it('says how many times it changed rather than showing a version number', () => {
    // "v3" is our bookkeeping. "revised 2 times" is what the customer asked.
    renderList([segment({ version: 3 })]);
    expect(screen.getByText(/revised 2 times/)).toBeInTheDocument();
  });

  it('says nothing about revisions when there have been none', () => {
    renderList([segment({ version: 1 })]);
    expect(screen.queryByText(/revised/)).not.toBeInTheDocument();
  });
});

describe('the states at both ends of the range', () => {
  it('an organization that has said nothing gets a statement, not an apology', () => {
    renderList([]);
    expect(screen.getByText(/haven't described who buys from you yet/i)).toBeInTheDocument();
  });

  it('one segment uses the same layout as forty', () => {
    // A one-item list that becomes a different screen at two items is a
    // redesign the customer performs on our behalf.
    const { container } = renderList([segment()]);
    expect(container.querySelectorAll('li')).toHaveLength(1);
  });

  it('forty segments render as forty rows', () => {
    const many = Array.from({ length: 40 }, (_, i) => segment({ name: `Segment ${i}` }));
    const { container } = renderList(many);
    expect(container.querySelectorAll('li')).toHaveLength(40);
  });

  it('a failure says so rather than looking empty', () => {
    // B-006: an outage must not be indistinguishable from having no data.
    render(
      <SegmentList segments={[]} catalog={catalog()} isLoading={false} isError />,
    );
    expect(screen.getByRole('alert')).toHaveTextContent(/could not load who you sell to/i);
  });

  it('loading is not an empty state either', () => {
    render(<SegmentList segments={[]} catalog={catalog()} isLoading isError={false} />);
    expect(screen.queryByText(/haven't described/i)).not.toBeInTheDocument();
  });
});

describe('the screen holds no verdict', () => {
  it('says nothing about whether a segment is good, broad or effective', () => {
    renderList([segment({ product_ids: [REVENUE_CLOUD, CPQ] })]);
    expect(document.body.textContent ?? '').not.toMatch(
      /score|rank|fit|effective|too broad|quality|best|worst/i,
    );
  });

  it('uses the customer\u2019s words rather than the platform\u2019s', () => {
    renderList([segment()]);
    expect(document.body.textContent ?? '').not.toMatch(
      /aggregate|segment_id|version_id|supersedes|workspace|tenant/i,
    );
  });
});
