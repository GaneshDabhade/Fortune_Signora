/**
 * **The Companies toolbar** — 📁 `Fortune Signora Companies.dc.html`.
 *
 * 🔴 **666 lines, the largest file in the repository that nothing rendered.**
 * ⚡ It carries the sort chips, the filter conditions, the column disclosure,
 * the density switch and the count — **every one of which is a control, and
 * none of which had a witness.**
 */
import { render, screen, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it, vi } from 'vitest';

import { AccountsToolbar } from '@/app/(app)/accounts/toolbar';
import { DEFAULT_COLUMNS, NO_FILTERS } from '@/lib/accounts/table';

const NEVER = ['undefined', 'null', 'NaN', '[object Object]', '/**', '*/'];

function toolbar(overrides: Record<string, unknown> = {}) {
  const onSort = vi.fn();
  const onFilters = vi.fn();
  const onColumns = vi.fn();
  const view = render(
    <AccountsToolbar
      density="comfortable"
      onDensity={vi.fn()}
      sort={[]}
      onSort={onSort}
      group={null}
      onGroup={vi.fn()}
      columns={DEFAULT_COLUMNS}
      onColumns={onColumns}
      /**
       * 🔴 **`NO_FILTERS`, not a hand-built object, and the first draft of this
       * file proves why.**
       *
       * ⛔ **It passed `{ name: '', kind: null, source: null } as never`** —
       * omitting `staleAfterDays` and `neverObserved` — **and the toolbar
       * rendered *"older than undefined days"*.** ⚠️ **That is not a product
       * defect**: `Filters` types the field `number | null`, so `undefined` is
       * unconstructable in TypeScript and **only the `as never` cast made it
       * reachable.** ⚡ **The type made the defect impossible and my fixture
       * cast the type away** — 📁 [§2](../../../CLAUDE.md), *types should make
       * incorrect architecture impossible*, working exactly as intended.
       *
       * ✅ **So the fixture uses the exported constant the product uses.** ⛔ **A
       * test fixture that reconstructs a contract by hand is a second
       * representation of it**, and it will drift.
       */
      filters={NO_FILTERS}
      onFilters={onFilters}
      kinds={['company']}
      sources={['hubspot']}
      total={8412}
      shown={312}
      loaded={312}
      onSave={vi.fn()}
      saving={false}
      {...overrides}
    />,
  );
  return { onSort, onFilters, onColumns, view };
}

describe('⛔ the toolbar prints no absence, comment or object', () => {
  it('✅ with nothing sorted, filtered or grouped', () => {
    const { view } = toolbar();
    const text = view.container.textContent ?? '';
    expect(text.trim().length).toBeGreaterThan(20);
    for (const forbidden of NEVER) expect(text).not.toContain(forbidden);
  });

  it('✅ and with a two-key sort applied', () => {
    // ⚡ **The `then` branch** — 📁 the design's *"Sort: Score ↑, then ACV ↓"*
    // reads as one sentence, and that second term had never been rendered.
    const { view } = toolbar({
      sort: [
        { key: 'name', direction: 'asc' },
        { key: 'observed_at', direction: 'desc' },
      ],
    });
    const text = view.container.textContent ?? '';
    expect(text).toContain('then');
    for (const forbidden of NEVER) expect(text).not.toContain(forbidden);
  });
});

describe('📁 the count says which number is which', () => {
  it('🔴 it names both, because one number alone is ambiguous', () => {
    /**
     * 📁 **The design's own row**: *"312 of 8,412"*. ⛔ **A single figure
     * cannot say whether it is what was filtered, what was loaded, or what
     * exists** — and the file's own docstring says the count beside them is
     * what settles it.
     */
    const { view } = toolbar();
    const text = view.container.textContent ?? '';

    expect(text).toContain('312');
    expect(text).toContain('8,412');
  });
});

describe('♿ every control in the row is reachable and named', () => {
  it('🔴 nothing is announced as a bare control', () => {
    /**
     * ⚡ **`getByRole` computes the name the way a screen reader does** — 📁
     * the instrument this lane settled on after a source sweep reported
     * eighteen correct files as offenders.
     */
    toolbar();
    const controls = [
      ...screen.queryAllByRole('button'),
      ...screen.queryAllByRole('combobox'),
      ...screen.queryAllByRole('checkbox'),
    ];
    expect(controls.length).toBeGreaterThan(1);

    for (const control of controls) {
      const named =
        (control.getAttribute('aria-label') ?? '').trim() !== '' ||
        control.hasAttribute('aria-labelledby') ||
        (control.textContent ?? '').trim() !== '' ||
        control.closest('label') !== null;
      expect(named, `${control.tagName} with no accessible name`).toBe(true);
    }
  });

  it('📁 the sort group and the filter group each name themselves', () => {
    // ⛔ **Two unlabelled groups of chips are one long row to a screen
    // reader** — the design draws them as *Sort* and *Filters*.
    toolbar();
    expect(screen.getByRole('group', { name: 'Sort' })).toBeInTheDocument();
    expect(screen.getByRole('group', { name: 'Filters' })).toBeInTheDocument();
  });
});

describe('⚡ the column disclosure keeps the row identifiable', () => {
  it('⛔ Company cannot be turned off', async () => {
    /**
     * 📁 **The design pins it left**, and the file states the reason: *"a row
     * you cannot identify is not a narrower table."* ⚡ **Disabled rather than
     * absent**, so the rule is visible instead of mysterious.
     */
    toolbar();
    // ⚡ **The summary names the count too** — *"Columns · 2 of 11"* — so the
    // query matches the prefix rather than an exact string that moves whenever
    // a column is added.
    const summary = screen.getByText(/^Columns · /);
    const columns = summary.closest('details') as HTMLElement;
    await userEvent.click(summary);

    const pinned = within(columns)
      .getAllByRole('checkbox')
      .filter((box) => (box as HTMLInputElement).disabled);
    expect(pinned.length).toBeGreaterThan(0);
    expect(pinned.every((box) => (box as HTMLInputElement).checked)).toBe(true);
  });
});
