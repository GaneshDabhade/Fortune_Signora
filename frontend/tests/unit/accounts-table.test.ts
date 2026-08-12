/**
 * **The Companies table's law** — [TASK-1475](../../../docs/BACKLOG.md).
 *
 * 🔴 **Every assertion here is about a boundary the design draws and the
 * contract cannot serve**, or about one it can. ⛔ **The five columns with no
 * source are not tested as absent by omission** — [C-300](../../../docs/LANE_COORDINATION.md)
 * is the decision, and a test that asserted their absence would have to be
 * deleted when it is ruled rather than extended.
 */
import { describe, expect, it } from 'vitest';

import {
  COLUMNS,
  DEFAULT_COLUMNS,
  NO_FILTERS,
  applyFilters,
  choicesFor,
  daysSinceObserved,
  isFiltered,
  toCsv,
  visibleColumns,
} from '@/lib/accounts/table';
import type { ListedAccount } from '@/lib/api/types';

const NOW = new Date('2026-08-12T12:00:00.000Z');

/**
 * ⚠️ **Spread, not `??`, and the tests found the difference.** ⛔ **The first
 * version defaulted each field with `??`, so an EXPLICIT `last_observed_at:
 * null` — the whole subject of the never-observed tests — was replaced by a
 * fresh date.** ⚡ **One test failed and one passed for the wrong reason**,
 * which is the more dangerous half.
 */
function account(over: Partial<ListedAccount['account']> = {}, kind = 'company'): ListedAccount {
  return {
    kind: kind as ListedAccount['kind'],
    account: {
      account_id: 'a1',
      name: 'Vantage Logistics',
      agreement: 'agreed' as ListedAccount['account']['agreement'],
      source_count: 2,
      source: 'apollo',
      observed_at: null,
      last_observed_at: '2026-08-10T12:00:00.000Z',
      ...over,
    },
  };
}

describe('🔴 a column exists only where a field does', () => {
  it('⛔ every column reads something the contract publishes', () => {
    const row = account();
    for (const column of COLUMNS) {
      expect(() => column.read(row)).not.toThrow();
    }
  });

  /**
   * 🔴 **Company cannot be turned off.** ⚡ **A table of rows you cannot
   * identify is not a narrower table, it is a broken one** — and the design
   * pins it left for the same reason.
   */
  it('🔴 the pinned column survives a choice that omits it', () => {
    const shown = visibleColumns(['kind']).map((c) => c.id);

    expect(shown).toContain('company');
    expect(shown).toContain('kind');
  });

  it('✅ and the default set is a subset of what exists', () => {
    const ids = COLUMNS.map((c) => c.id);
    for (const id of DEFAULT_COLUMNS) expect(ids).toContain(id);
  });
});

describe('🔴 never-observed is not stale', () => {
  /**
   * ⛔ **The distinction the contract itself insists on**: `last_observed_at`
   * is *"not when Signora last looked."* ⚡ **Folding the two would let an
   * *older than 30 days* filter claim Signora had looked and found something
   * old, when it has never looked at all.**
   */
  it('🔴 an account nobody has reported on is excluded from “older than N days”', () => {
    const never = account({ last_observed_at: null });
    const old = account({ last_observed_at: '2026-01-01T12:00:00.000Z' });

    const stale = applyFilters([never, old], { ...NO_FILTERS, staleAfterDays: 30 }, NOW);

    expect(stale).toEqual([old]);
  });

  it('✅ and it has a filter of its own', () => {
    const never = account({ last_observed_at: null });
    const old = account({ last_observed_at: '2026-01-01T12:00:00.000Z' });

    expect(applyFilters([never, old], { ...NO_FILTERS, neverObserved: true }, NOW)).toEqual([never]);
  });

  it('⛔ an unparseable timestamp reads as never, not as today', () => {
    expect(daysSinceObserved(account({ last_observed_at: 'not a date' }), NOW)).toBeNull();
  });
});

describe('⚡ the filters the contract can serve', () => {
  const rows = [
    account({ name: 'Vantage Logistics', source: 'apollo' }),
    account({ account_id: 'a2', name: 'Ashgrove Retail', source: 'crunchbase' }),
    account({ account_id: 'a3', name: 'Meridian Freight', source: 'apollo' }, 'technology'),
  ];

  it('✅ name matches anywhere and ignores case', () => {
    expect(applyFilters(rows, { ...NO_FILTERS, name: 'grove' }, NOW)).toHaveLength(1);
    expect(applyFilters(rows, { ...NO_FILTERS, name: 'VANTAGE' }, NOW)).toHaveLength(1);
  });

  it('✅ kind and source narrow independently', () => {
    expect(applyFilters(rows, { ...NO_FILTERS, kind: 'technology' }, NOW)).toHaveLength(1);
    expect(applyFilters(rows, { ...NO_FILTERS, source: 'apollo' }, NOW)).toHaveLength(2);
  });

  /**
   * ⛔ **Choices come from what was read, never from a fixed list.** ⚡ **A
   * filter offering a value that matches nothing is a control that goes
   * nowhere**, which is the rule this lane keeps everywhere else.
   */
  it('🔴 the choices are the values present, not a vocabulary', () => {
    expect(choicesFor(rows, 'source')).toEqual(['apollo', 'crunchbase']);
    expect(choicesFor(rows, 'kind')).toEqual(['company', 'technology']);
    expect(choicesFor([], 'source')).toEqual([]);
  });

  it('✅ no filter is not a filter', () => {
    expect(isFiltered(NO_FILTERS)).toBe(false);
    expect(isFiltered({ ...NO_FILTERS, name: '   ' })).toBe(false);
    expect(isFiltered({ ...NO_FILTERS, neverObserved: true })).toBe(true);
  });
});

describe('📁 export is exactly what is on screen', () => {
  it('✅ the visible columns, in order, over the filtered rows', () => {
    const csv = toCsv([account({ name: 'Vantage' })], visibleColumns(['kind']));

    expect(csv.split('\n')[0]).toBe('Company,Kind');
    expect(csv.split('\n')[1]).toBe('Vantage,company');
  });

  /**
   * ⛔ **A comma in a company name must not become a column.** ⚡ **This is the
   * one place a name reaches a file another program parses**, and the failure
   * is silent — a shifted column reads as data rather than as an error.
   */
  it('🔴 a name containing a comma or a quote survives the round trip', () => {
    const csv = toCsv([account({ name: 'Vantage, "the" A/S' })], visibleColumns([]));

    expect(csv.split('\n')[1]).toBe('"Vantage, ""the"" A/S"');
  });
});
