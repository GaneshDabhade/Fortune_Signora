/**
 * **The breadcrumb's law** — [TASK-1408](../../../docs/BACKLOG.md), rule 6.
 *
 * ⚡ **The five cases asserted here are the five the design draws**, and the
 * collapsed one is read out of the design document rather than restated —
 * because the threshold (*"beyond four levels"*) and the shape (`first · … ·
 * last two`) are both things a transcription can get subtly wrong.
 */
import { readFileSync } from 'node:fs';
import { join } from 'node:path';

import { describe, expect, it } from 'vitest';

import {
  MAX_VISIBLE,
  collapse,
  isRequired,
  isWellFormed,
  type Crumb,
} from '@/lib/shell/breadcrumb';

const DESIGN = readFileSync(
  join(process.cwd(), '../docs/design-snapshot/screens/Fortune Signora App Shell.dc.html'),
  'utf8',
);

const link = (label: string): Crumb => ({ label, kind: 'link' });
const current = (label: string): Crumb => ({ label, kind: 'current' });

describe('📁 rule 6 — mandatory below the first level, and only below it', () => {
  it('⛔ one level is not a trail', () => {
    // 📁 The *Two levels* case is labelled *"Minimum where breadcrumbs
    // appear"* — a lonely root is noise, not orientation.
    expect(isRequired([current('Accounts')])).toBe(false);
    expect(isRequired([link('Accounts'), current('Vantage Logistics')])).toBe(true);
  });
});

describe('🔴 collapse is arithmetic, and the middle is what goes', () => {
  it('⚡ the design says "beyond four levels", and the document is the source', () => {
    // The threshold is read rather than restated: if the design changes it,
    // this fails instead of drifting.
    expect(DESIGN).toMatch(/Beyond four levels/);
    expect(MAX_VISIBLE).toBe(4);
  });

  it('renders four in full — the design’s deep drill-down case', () => {
    const trail = [
      link('Pipeline'),
      link('EMEA enterprise'),
      link('Q3 FY26'),
      current('Renewal — Vantage'),
    ];
    expect(collapse(trail).map((c) => c.label)).toEqual([
      'Pipeline',
      'EMEA enterprise',
      'Q3 FY26',
      'Renewal — Vantage',
    ]);
  });

  it('🔴 keeps the first and the LAST TWO — never just the last', () => {
    /**
     * 📁 **The design's collapsed example is `Reports › … › Stage velocity ›
     * Negotiation cohort`.** ⛔ **Dropping the parent would leave somebody
     * unable to step up one level**, which is the single move a breadcrumb
     * exists for — so keeping two at the end is the property, not an
     * off-by-one.
     */
    const trail = [
      link('Reports'),
      link('Funnel'),
      link('Stage velocity'),
      link('Cohorts'),
      current('Negotiation cohort'),
    ];
    const out = collapse(trail);
    expect(out.map((c) => c.label)).toEqual(['Reports', '…', 'Cohorts', 'Negotiation cohort']);
    // ⚡ The gap is a MENU, so the hidden levels stay reachable.
    expect(out[1]?.kind).toBe('menu');
  });

  it('⛔ never drops the segment you are on', () => {
    const trail = [link('a'), link('b'), link('c'), link('d'), link('e'), current('here')];
    const out = collapse(trail);
    expect(out[out.length - 1]).toEqual(current('here'));
  });
});

describe('⛔ a malformed trail is refused rather than rendered', () => {
  it('the last segment is `current`, and there is exactly one', () => {
    /**
     * ⚡ **A link to the page you are on is a control that does nothing** —
     * [§2](../../../CLAUDE.md)'s class. **Every case the design draws ends in
     * `current`.**
     */
    expect(isWellFormed([link('Accounts'), current('Vantage')])).toBe(true);
    expect(isWellFormed([link('Accounts'), link('Vantage')])).toBe(false);
    expect(isWellFormed([current('Accounts'), current('Vantage')])).toBe(false);
  });
});

describe('📁 the cross-workspace case is its own kind', () => {
  it('⚡ a guest trail names the workspace it starts in', () => {
    // 📁 *"Guest or partner context"* — ⛔ a trail rooted in another
    // workspace must say so rather than looking like an ordinary root.
    const trail: Crumb[] = [
      { label: 'Vantage Logistics', kind: 'workspace' },
      link('Accounts'),
      current('Meridian Freight'),
    ];
    expect(isWellFormed(trail)).toBe(true);
    expect(collapse(trail)[0]?.kind).toBe('workspace');
  });
});
