/**
 * **The picker recommends a type from the shape of the data, and explains why**
 * — [TASK-1417](../../../docs/BACKLOG.md).
 */
import { describe, expect, it } from 'vitest';

import {
  CHART_TYPES,
  pickerOptions,
  recommend,
  type DataShape,
} from '@/lib/reports/chart-picker';

const PLAIN: DataShape = {
  series: 1,
  overTime: false,
  signedContributionsToOneTotal: false,
  fixedStages: false,
  dimensions: 1,
  hasRequiredPace: false,
  continuous: false,
};

describe('📁 the design’s eight, and the three it refuses', () => {
  it('⛔ offers no doughnut, no dual axis and no 3D — refused by the type', () => {
    // ⚡ There is nothing to guard, because there is nothing to ask for.
    expect([...CHART_TYPES]).toEqual([
      'line',
      'bar',
      'waterfall',
      'funnel',
      'cohort',
      'distribution',
      'pace',
      'table',
    ]);
  });

  it('offers every type with exactly one marked, never only the recommendation', () => {
    // ⛔ A picker that hid the alternatives would make advice a decision.
    const options = pickerOptions({ ...PLAIN, signedContributionsToOneTotal: true });

    expect(options).toHaveLength(8);
    expect(options.filter((o) => o.recommended).map((o) => o.type)).toEqual(['waterfall']);
  });
});

describe('🔴 specific before general — the order IS the logic', () => {
  it("recommends a waterfall for a bridge, not the bar chart its data also is", () => {
    // ⚠️ A bridge is *also* a comparison across categories. Testing the
    // general case first recommends `bar` — defensible, wrong, and never
    // reported as a defect because a chart drew fine.
    const { type, why } = recommend({
      ...PLAIN,
      signedContributionsToOneTotal: true,
      series: 5,
    });

    expect(type).toBe('waterfall');
    expect(why).toContain('signed contributions to one total');
  });

  it('recommends a pace chart over a line chart, though the data is also over time', () => {
    const { type } = recommend({ ...PLAIN, overTime: true, hasRequiredPace: true });

    expect(type).toBe('pace');
  });

  it('recommends a funnel for fixed ordered stages', () => {
    expect(recommend({ ...PLAIN, fixedStages: true }).type).toBe('funnel');
  });

  it('recommends a cohort heatmap for two dimensions and one density', () => {
    expect(recommend({ ...PLAIN, dimensions: 2 }).type).toBe('cohort');
  });

  it('recommends a distribution for a continuous measure', () => {
    expect(recommend({ ...PLAIN, continuous: true }).type).toBe('distribution');
  });

  it('recommends a line for a measure over time with few enough series', () => {
    expect(recommend({ ...PLAIN, overTime: true, series: 2 }).type).toBe('line');
  });

  it('⚡ refuses a line chart of nine series and says how many', () => {
    // 📁 *"one or two series"* is the design's own qualifier, and the ramp
    // distinguishes only eight anyway.
    const { type, why } = recommend({ ...PLAIN, overTime: true, series: 9 });

    expect(type).toBe('table');
    expect(why).toContain('9');
  });

  it('recommends a bar for a plain comparison across categories', () => {
    expect(recommend(PLAIN).type).toBe('bar');
  });

  it('⛔ falls back to a TABLE rather than drawing something', () => {
    // ⚡ A shape nothing can read is exactly where drawing would assert a
    // structure nobody established.
    expect(recommend({ ...PLAIN, series: 0 }).type).toBe('table');
  });

  it('every recommendation explains itself', () => {
    for (const shape of [
      PLAIN,
      { ...PLAIN, signedContributionsToOneTotal: true },
      { ...PLAIN, fixedStages: true },
      { ...PLAIN, dimensions: 2 },
      { ...PLAIN, continuous: true },
      { ...PLAIN, overTime: true },
      { ...PLAIN, hasRequiredPace: true },
      { ...PLAIN, series: 0 },
    ]) {
      expect(recommend(shape).why.length).toBeGreaterThan(20);
    }
  });
});
