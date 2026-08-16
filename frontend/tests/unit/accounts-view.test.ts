/**
 * **Companies as the third saved-view consumer** —
 * [455 §4](../../../docs/architecture/455-context-definitions-r02-r03.md).
 *
 * ⛔ **Nothing on the server will ever tell this screen that a declaration is
 * wrong**, so the refusals are the deliverable.
 */
import { describe, expect, it } from 'vitest';

import { NO_FILTERS, type Filters } from '@/lib/accounts/table';
import {
  COMPANIES_DECLARATION_VERSION,
  apply,
  declare,
  whyNotReadableHere,
  type CompaniesDeclaration,
} from '@/lib/accounts/view';

const NARROWED: Filters = { ...NO_FILTERS, name: 'vantage', kind: 'company' };

describe('🔴 a view this screen cannot read is refused, never partly applied', () => {
  it('✅ its own declaration reads back', () => {
    expect(whyNotReadableHere(declare(NARROWED, 'renewal', { key: 'acv', direction: 'desc' }))).toBeNull();
  });

  it("⛔ another screen's view is refused, and that is the commonest case", () => {
    // 📁 The store is workspace-wide and holds four screens' declarations, so a
    // Reports definition in this tab row is ordinary rather than an error.
    expect(whyNotReadableHere({ kind: 'report', version: 1 })).toMatch(/different screen/);
    expect(whyNotReadableHere({ kind: 'working-list', version: 1 })).toMatch(/different screen/);
  });

  it('⛔ a view from a newer Signora is refused rather than partly applied', () => {
    expect(
      whyNotReadableHere({ kind: 'companies', version: COMPANIES_DECLARATION_VERSION + 1 }),
    ).toMatch(/newer version/);
  });

  it('⛔ anything that is not a declaration is refused', () => {
    for (const junk of [null, 'a view', [], 42]) {
      expect(whyNotReadableHere(junk)).not.toBeNull();
    }
  });

  it('⛔ a grouping this build no longer offers is refused, not dropped', () => {
    // 🔴 **Silently ignoring it is the worst outcome**: the customer gets a list
    // that is neither what they saved nor what they asked for.
    expect(
      whyNotReadableHere({ ...declare(NO_FILTERS, null, null), group: 'renewal_quarter_fy' }),
    ).toMatch(/no longer offers/);
  });

  it('⛔ a sort this build no longer offers is refused, not dropped', () => {
    expect(
      whyNotReadableHere({
        ...declare(NO_FILTERS, null, null),
        sort: { key: 'score', direction: 'asc' },
      }),
    ).toMatch(/no longer offers/);
    expect(
      whyNotReadableHere({
        ...declare(NO_FILTERS, null, null),
        sort: { key: 'acv', direction: 'sideways' },
      }),
    ).toMatch(/no longer offers/);
  });

  it('✅ an OLDER view stays readable, and a missing condition means *not narrowed*', () => {
    // ⚡ **The version bumps only when an old declaration would be MISREAD** —
    // never when a filter is added. A view written before `neverObserved`
    // existed meant *not narrowed by it*, and still does.
    const older = { kind: 'companies', version: 1, filters: { name: 'acme' } };

    expect(whyNotReadableHere(older)).toBeNull();
    const applied = apply(older as unknown as CompaniesDeclaration);
    expect(applied.filters.name).toBe('acme');
    expect(applied.filters.neverObserved).toBe(false);
    expect(applied.group).toBeNull();
  });
});

describe('✅ applying a view restores what was saved', () => {
  it('carries the conditions, the grouping and the sort', () => {
    const applied = apply(declare(NARROWED, 'stage', { key: 'renewal', direction: 'desc' }));

    expect(applied.filters.name).toBe('vantage');
    expect(applied.filters.kind).toBe('company');
    expect(applied.group).toBe('stage');
    expect(applied.sort).toEqual({ key: 'renewal', direction: 'desc' });
  });

  it('⛔ carries no column choice or density', () => {
    // ⚠️ **The views are SHARED** — everybody in the workspace sees the same
    // list — **so a saved column choice would reach across a colleague's own
    // preference.** A view names a set of companies; a preference stays with
    // the person.
    expect(Object.keys(declare(NO_FILTERS, null, null))).toEqual([
      'kind',
      'version',
      'filters',
      'group',
      'sort',
    ]);
  });
});
