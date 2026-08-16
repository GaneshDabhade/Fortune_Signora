/**
 * **Sort and Group, over the page in hand** — 📁 the finalized Companies
 * design's *"Sort: Score ↑, then ACV ↓"* and *"Group: Renewal quarter"*.
 */
import { describe, expect, it } from 'vitest';

import {
  UNGROUPED,
  applySort,
  groupFromParam,
  groupRows,
  renewalQuarter,
  sortFromParam,
  sortSentence,
  withArrangement,
} from '@/lib/accounts/table';
import type { ListedAccount } from '@/lib/api/types';

function row(
  name: string | null,
  commercial: Partial<ListedAccount['commercial']> = {},
): ListedAccount {
  return {
    kind: 'company',
    account: {
      account_id: name ?? 'x',
      name,
      agreement: 'agreed',
      source_count: 1,
      source: 'hubspot',
      observed_at: null,
      last_observed_at: null,
    },
    commercial: { open_acv: null, renewal_date: null, stage: null, ...commercial },
  };
}

const USD = (amount: number) => ({ amount, currency: 'USD' });

describe('🔴 an unreported value sorts last, in both directions', () => {
  /**
   * ⛔ **Not treated as zero and not as infinity.** ⚡ **Sorting an unreported
   * account to the top of *highest value* would be exactly the fabrication the
   * column refuses to make in its own cell.**
   */
  it('sinks whichever way the arrow points', () => {
    const rows = [row('A'), row('B', { open_acv: USD(10) }), row('C', { open_acv: USD(90) })];

    expect(applySort(rows, [{ key: 'acv', direction: 'desc' }]).map((r) => r.account.name)).toEqual([
      'C',
      'B',
      'A',
    ]);
    expect(applySort(rows, [{ key: 'acv', direction: 'asc' }]).map((r) => r.account.name)).toEqual([
      'B',
      'C',
      'A',
    ]);
  });

  it("⛔ no sort leaves the endpoint's own order untouched", () => {
    const rows = [row('C'), row('A'), row('B')];
    expect(applySort(rows, [])).toBe(rows);
  });
});

describe('📁 the design’s grouped table', () => {
  it('⛔ ungrouped rows get their own stated group, and it comes last', () => {
    const groups = groupRows(
      [row('A', { renewal_date: '2026-08-01' }), row('B')],
      'renewal',
    );

    expect(groups?.map((g) => g.label)).toEqual(['Renewal in Q3 2026', UNGROUPED]);
  });

  it('✅ the header subtotals only the rows that have a figure', () => {
    const groups = groupRows(
      [
        row('A', { renewal_date: '2026-08-01', open_acv: USD(100) }),
        row('B', { renewal_date: '2026-08-02' }),
      ],
      'renewal',
    );

    expect(groups?.[0]?.openAcv).toEqual(USD(100));
  });

  it('⛔ a group nobody reported a figure for has no subtotal, never a zero', () => {
    const groups = groupRows([row('A', { renewal_date: '2026-08-01' })], 'renewal');

    expect(groups?.[0]?.openAcv).toBeNull();
  });

  it('🔴 two currencies do not add up, and the subtotal is withheld', () => {
    // 📁 **ADR-0409 §5: currency is carried, never converted.** ⚡ **Summing
    // them needs a rate applied at a moment**, which is correct briefly and
    // wrong permanently — so no figure is better than a plausible one.
    const groups = groupRows(
      [
        row('A', { renewal_date: '2026-08-01', open_acv: USD(100) }),
        row('B', { renewal_date: '2026-08-02', open_acv: { amount: 100, currency: 'EUR' } }),
      ],
      'renewal',
    );

    expect(groups?.[0]?.openAcv).toBeNull();
  });

  it('⚡ groups order by label and never by size', () => {
    // ⛔ **A group that moves when its results change makes the same query
    // render differently for a reason nobody asked about.**
    const groups = groupRows(
      [
        row('A', { renewal_date: '2026-11-01' }),
        row('B', { renewal_date: '2026-02-01' }),
        row('C', { renewal_date: '2026-02-02' }),
      ],
      'renewal',
    );

    expect(groups?.map((g) => g.label)).toEqual(['Renewal in Q1 2026', 'Renewal in Q4 2026']);
  });

  it('⛔ nothing grouped is null, never one group of everything', () => {
    expect(groupRows([row('A')], null)).toBeNull();
  });

  it('⚠️ an unreadable renewal date is said, not silently bucketed', () => {
    expect(renewalQuarter('not-a-date')).toMatch(/unreadable/);
  });
});

describe('📁 up to two keys, stated in words', () => {
  /**
   * 📁 **The design's mechanic** — *"Up to two keys, stated in words in the
   * toolbar rather than as arrows to decode."*
   */
  it('✅ the second key breaks the first key’s ties, and only those', () => {
    const rows = [
      row('B', { open_acv: USD(10) }),
      row('A', { open_acv: USD(10) }),
      row('C', { open_acv: USD(90) }),
    ];

    const sorted = applySort(rows, [
      { key: 'acv', direction: 'desc' },
      { key: 'company', direction: 'asc' },
    ]);

    expect(sorted.map((r) => r.account.name)).toEqual(['C', 'A', 'B']);
  });

  it('⛔ absence sinks in EVERY term, not only the first', () => {
    // ⚡ A row with no ACV must not jump on the tie-break either.
    const rows = [row('A'), row('B', { open_acv: USD(10) })];

    expect(
      applySort(rows, [
        { key: 'renewal', direction: 'asc' },
        { key: 'acv', direction: 'desc' },
      ]).map((r) => r.account.name),
    ).toEqual(['B', 'A']);
  });

  it('📁 the sentence uses the design’s own word', () => {
    expect(
      sortSentence([
        { key: 'company', direction: 'asc' },
        { key: 'acv', direction: 'desc' },
      ]),
    ).toBe('Company ↑, then Open ACV ↓');
    expect(sortSentence([])).toBeNull();
  });
});

describe('🔴 the arrangement survives a refresh, because it is in the URL', () => {
  it('✅ round-trips through the URL', () => {
    const sort = [
      { key: 'company', direction: 'asc' },
      { key: 'acv', direction: 'desc' },
    ] as const;

    const params = withArrangement(new URLSearchParams(), sort, 'renewal');

    expect(params.get('sort')).toBe('company:asc,acv:desc');
    expect(sortFromParam(params.get('sort'))).toEqual(sort);
    expect(groupFromParam(params.get('group'))).toBe('renewal');
  });

  it('⚡ a default is left out, because a clean URL is the one a seller copies', () => {
    const params = withArrangement(new URLSearchParams('sort=acv:asc&group=stage'), [], null);

    expect(params.get('sort')).toBeNull();
    expect(params.get('group')).toBeNull();
  });

  it('⛔ an unreadable term is DROPPED, not refused — a URL is not a saved view', () => {
    // ⚠️ **The opposite of the saved-view rule, deliberately.** 📁 A stale or
    // hand-edited link should show a seller their accounts, not an error.
    expect(sortFromParam('score:asc,company:asc')).toEqual([{ key: 'company', direction: 'asc' }]);
    expect(sortFromParam('company:sideways')).toEqual([]);
    expect(sortFromParam('company:asc,company:desc')).toEqual([
      { key: 'company', direction: 'asc' },
    ]);
    expect(sortFromParam('company:asc,acv:asc,renewal:asc')).toHaveLength(2);
    expect(groupFromParam('nonsense')).toBeNull();
  });

  it('⛔ other query parameters survive', () => {
    // ⚡ The URL is shared with `owner`, and an arrangement change must not
    // drop somebody else's scope.
    const params = withArrangement(new URLSearchParams('owner=mine'), [], 'kind');

    expect(params.get('owner')).toBe('mine');
    expect(params.get('group')).toBe('kind');
  });
});
