/**
 * 📁 **The Companies context drawer** — `Fortune Signora Companies.dc.html`,
 * *"Context drawer · row preview"*.
 *
 * 🔴 **The design lists six facts and only three of them have a source.** ⛔ **The
 * three that do not are OMITTED, not dashed** — and the three that DO have a
 * read path but no answer **are** dashed. ⚡ **That distinction is the whole
 * commercial slice**, and it is invisible to anything that does not render.
 */
import { render, screen, within } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

import type { ListedAccount } from '@/lib/api/types';

import { ContextDrawer } from '@/app/(app)/accounts/context-drawer';

/**
 * ⚡ **Every field the contract declares.** 📁 [ADR-0409](../../../docs/architecture/adr/0409-commercial-account-facts.md)
 * §5 — *"absence is never inferred, defaulted or zero-filled"* — **so the
 * commercial object is always present even when all three fields are `null`.**
 * ⛔ **That is how a caller tells *nothing said* from *not asked***, and a
 * fixture that omitted it would erase the distinction under test.
 */
function listed(over: Partial<ListedAccount['commercial']> = {}): ListedAccount {
  return {
    account: {
      account_id: 'a-1',
      name: 'Northwind Global',
      agreement: 'agreed',
      source_count: 3,
      source: 'hubspot',
      observed_at: '2026-08-20T00:00:00Z',
      last_observed_at: '2026-08-20T00:00:00Z',
    },
    kind: 'company',
    commercial: { open_acv: null, renewal_date: null, stage: null, ...over },
  };
}

const NOTHING = {
  assignment: undefined,
  members: [],
  segments: undefined,
  vocabulary: [],
  tags: [],
} as const;

function drawer(row: ListedAccount | null = listed(), open = true) {
  return render(
    <ContextDrawer row={row} open={open} onClose={vi.fn()} {...NOTHING} />,
  );
}

/** 📁 One row of the design's fact list, found by its own label. */
function fact(label: string): HTMLElement {
  const dt = screen.getByText(label);
  const row = dt.parentElement;
  if (row === null) throw new Error(`no fact row around "${label}"`);
  return row;
}

describe('🔴 three of the design’s six facts have no source, and are ABSENT', () => {
  it('⛔ draws no Signora score, no Last touch and no Open opportunities', () => {
    drawer();

    // ✅ **The pin** — the drawer is open with facts in it.
    expect(screen.getByText('Open ACV')).toBeInTheDocument();

    // 📁 **The one design column with no source anywhere.**
    expect(screen.queryByText(/Signora score/i)).toBeNull();
    // ⚠️ **`Last touch` is an ENGAGEMENT; `Last observed` is when a source last
    // reported.** ⛔ **Relabelling one as the other would be the quietest lie
    // on the panel**, because both are dates and both look plausible.
    expect(screen.queryByText(/Last touch/i)).toBeNull();
    expect(screen.queryByText(/Open opportunit/i)).toBeNull();
  });

  it('⚡ and labels the date it DOES have as what it actually is', () => {
    drawer();
    expect(screen.getByText('Last observed')).toBeInTheDocument();
  });

  it('⛔ says Never rather than dashing a date nothing has ever reported', () => {
    // ⚠️ **A dash means *a source was asked and said nothing*.** ⛔ **Nothing has
    // ever reported here**, which is a different fact and gets a word.
    const row = listed();
    render(
      <ContextDrawer
        row={{ ...row, account: { ...row.account, last_observed_at: null } }}
        open
        onClose={vi.fn()}
        {...NOTHING}
      />,
    );
    expect(within(fact('Last observed')).getByText('Never')).toBeInTheDocument();
  });
});

describe('📁 the three facts that DO have a read path dash when nobody has answered', () => {
  it('⛔ renders a dash with a spoken reason, never a zero', () => {
    /**
     * 📁 **ADR-0409 §5**: *"a claim is only produced where the provider
     * supplies the fact."* 🔴 **A `0` ACV is a figure a seller would act
     * on** — ⛔ **rendering absence as zero is the fabrication this contract
     * exists to make impossible.**
     *
     * ♿ **And the dash is `aria-hidden` with `Not reported` beside it**, because
     * a screen reader announcing *"em dash"* has been told nothing.
     */
    drawer();

    for (const label of ['Open ACV', 'Renewal', 'Stage']) {
      const row = fact(label);
      expect(within(row).getByText('Not reported')).toBeInTheDocument();
      expect(row.textContent ?? '').not.toMatch(/(?:^|\s)0(?:$|\s)/);
    }
  });

  it('✅ and renders the values when a source HAS answered', () => {
    // ⚡ **The vacuity half** — without it, *never a zero* would pass on a
    // panel that cannot render a figure at all.
    drawer(
      listed({
        open_acv: { amount: 120000, currency: 'USD' },
        renewal_date: '2026-12-01T00:00:00Z',
      }),
    );

    expect(within(fact('Open ACV')).queryByText('Not reported')).toBeNull();
    expect(fact('Open ACV').textContent ?? '').toMatch(/120|120,000|120K/i);
    expect(within(fact('Renewal')).queryByText('Not reported')).toBeNull();
  });

  it('⚡ and the source count is a real number, so it renders as one', () => {
    drawer();
    expect(within(fact('Sources')).getByText('3')).toBeInTheDocument();
  });
});

describe('⛔ a heading over nothing is worse than no heading', () => {
  it('📁 renders neither Segments nor Tags when there is nothing to put under them', () => {
    /**
     * 🔴 **The first version rendered both labels unconditionally**, and the
     * screenshot showed `SEGMENTS` and `TAGS` over empty space — ⚡ **which
     * reads as a panel that failed to load**, not as an account with no
     * groupings.
     */
    drawer();
    expect(screen.queryByText('Segments')).toBeNull();
    expect(screen.queryByText('Tags')).toBeNull();
  });
});

describe('⚡ the drawer says what it IS, so it cannot be mistaken for the record', () => {
  it('📁 carries the eyebrow, the preview sentence and a way to the record', () => {
    drawer();

    expect(screen.getByText(/Row preview/i)).toBeInTheDocument();
    expect(screen.getByText('A preview. The record has everything.')).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Open record' })).toHaveAttribute(
      'href',
      '/accounts/a-1',
    );
  });

  it('⛔ draws no tab row and no recommendation, because neither has content', () => {
    /**
     * 📁 **The design shows four tabs and three have nothing this screen can
     * fill**; 📁 the *Recommended next step* block offers *Draft intro* and
     * *Evidence*, and **no frontend hook consumes the decision package yet.**
     * ⛔ [B-255](../../../docs/BUGS.md): *a control that silently does nothing
     * is worse than one that is absent.*
     */
    drawer();

    expect(screen.queryByRole('tablist')).toBeNull();
    expect(screen.queryByRole('tab')).toBeNull();
    expect(screen.queryByText(/Recommended next step/i)).toBeNull();
    expect(screen.queryByRole('button', { name: /Draft intro/i })).toBeNull();
  });

  it('⛔ and renders nothing at all when there is no row to preview', () => {
    // ⚠️ **`open` alone is not enough** — a drawer opened over a null row would
    // be a titled panel about no account.
    const { container } = drawer(null, true);
    expect(container.textContent ?? '').not.toContain('A preview.');
    expect(screen.queryByText('Open ACV')).toBeNull();
  });
});
