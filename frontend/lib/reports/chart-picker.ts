/**
 * **The picker that recommends a chart and says why** —
 * [TASK-1417](../../../docs/BACKLOG.md).
 *
 * ## 📁 The design's sentence, and both halves are load-bearing
 *
 * > ***"The picker recommends a type from the shape of the data and explains
 * > why. No doughnuts, no dual axes, no 3D."***
 *
 * ⚡ **The explanation is not decoration.** 📁 The design puts it inside the
 * block itself — *"Chosen because the data is a set of signed contributions to
 * one total — the picker explains that choice inline"* — ⛔ **because a
 * recommendation nobody can argue with is one nobody can correct**, and the
 * author is the one who knows whether the shape was read right.
 *
 * ## ⛔ The three refusals are refused by the TYPE, not by a rule
 *
 * ⚠️ **There is no doughnut, no dual axis and no 3D in `ChartType`**, so a
 * caller cannot ask for one and no check has to remember to say no
 * ([§2](../../../CLAUDE.md): *prefer a violation that is unrepresentable over
 * one that is merely discouraged*). ⚡ **A guard that cannot fail is
 * documentation pretending to be code** — **this is the version with nothing
 * to guard.**
 *
 * ## ⚡ Why this is a pure function over a SHAPE and not over the data
 *
 * ⛔ **Passing rows would make the picker able to read a customer's figures to
 * choose a chart**, and it does not need them: **the shape is what decides**.
 * ✅ **It is therefore testable with no query engine, which matters because
 * there is not one yet.**
 */

/**
 * 📁 **The design's eight, in its order.** ⛔ **A ninth is a design change, not
 * a caller's choice** — the same rule `chart.tsx` already applies to the
 * colour ramp: *"a ninth is a different chart."*
 */
export const CHART_TYPES = [
  'line',
  'bar',
  'waterfall',
  'funnel',
  'cohort',
  'distribution',
  'pace',
  'table',
] as const;

export type ChartType = (typeof CHART_TYPES)[number];

/** 📁 **The design's own `use` copy**, verbatim — it is the picker's list. */
export const CHART_USE: Record<ChartType, string> = {
  line: 'A measure over time, one or two series',
  bar: 'Comparison across categories',
  waterfall: 'Signed contributions to one total',
  funnel: 'Conversion through fixed stages',
  cohort: 'Two dimensions, one density',
  distribution: 'Where deals cluster, and the tail',
  pace: 'Actual against required, same axes',
  table: 'When the numbers are the point',
};

/**
 * ⚡ **What is true of the data**, and nothing about what it contains.
 *
 * ⛔ **Every field is a fact somebody can check**, so a wrong recommendation is
 * traceable to a wrong shape rather than to a judgement nobody can inspect.
 */
export interface DataShape {
  /** ⚡ **How many things are being measured against each other.** */
  readonly series: number;
  /** **The dimension is time.** */
  readonly overTime: boolean;
  /** 📁 *"signed contributions to one total"* — a plan-to-commit bridge. */
  readonly signedContributionsToOneTotal: boolean;
  /** 📁 *"conversion through fixed stages"* — ordered, and each contains the next. */
  readonly fixedStages: boolean;
  /** 📁 *"two dimensions, one density"*. */
  readonly dimensions: number;
  /** 📁 *"actual against required, same axes"* — a required-pace reference. */
  readonly hasRequiredPace: boolean;
  /** 📁 *"where deals cluster, and the tail"* — a continuous measure. */
  readonly continuous: boolean;
}

export interface Recommendation {
  readonly type: ChartType;
  /** ⚡ **The sentence shown inline**, in the design's register. */
  readonly why: string;
}

/**
 * 🔴 **Ordered from most specific to least, and the order IS the logic.**
 *
 * ⚠️ **A waterfall's data is also a comparison across categories, and a pace
 * chart's is also a measure over time.** ⛔ **Testing the general case first
 * would recommend `bar` for a bridge and `line` for a pace chart** — **both
 * defensible, both wrong**, and neither would ever be reported as a defect
 * because a chart drew fine.
 */
export function recommend(shape: DataShape): Recommendation {
  if (shape.signedContributionsToOneTotal) {
    return { type: 'waterfall', why: 'the data is a set of signed contributions to one total' };
  }
  if (shape.fixedStages) {
    return { type: 'funnel', why: 'the data is a conversion through fixed, ordered stages' };
  }
  if (shape.hasRequiredPace) {
    return { type: 'pace', why: 'the data compares what happened against what was required, on the same axes' };
  }
  if (shape.dimensions >= 2) {
    return { type: 'cohort', why: 'the data has two dimensions and one density between them' };
  }
  if (shape.continuous) {
    return { type: 'distribution', why: 'the data is a continuous measure, so where it clusters and where it tails are the point' };
  }
  if (shape.overTime) {
    /**
     * 📁 **The design's own qualifier**: *"A measure over time, **one or two
     * series**"*. ⛔ **A line chart of nine series is a plate of spaghetti**,
     * and the ramp only distinguishes eight anyway (`chart.tsx`).
     */
    if (shape.series <= 2) {
      return { type: 'line', why: 'the data is a measure over time, with few enough series to follow' };
    }
    return {
      type: 'table',
      why: `the data is a measure over time across ${shape.series} series, which is more lines than anybody can follow`,
    };
  }
  if (shape.series >= 1) {
    return { type: 'bar', why: 'the data is a comparison across categories' };
  }

  /**
   * ⛔ **The fallback is a TABLE, never a chart.** 📁 *"When the numbers are
   * the point"* — ⚡ **and a shape this function cannot read is exactly the
   * case where drawing something would assert a structure nobody established.**
   */
  return { type: 'table', why: 'nothing about the shape of this data suggests a chart, so the numbers are the point' };
}

/**
 * ⚡ **The picker's list, with the recommendation marked.**
 *
 * ⛔ **Every type is offered, not only the recommended one.** 📁 The design
 * shows all eight with one highlighted — **a picker that hid the alternatives
 * would make the recommendation a decision rather than advice**, which is the
 * opposite of *"explains why"*.
 */
export function pickerOptions(
  shape: DataShape,
): readonly { type: ChartType; use: string; recommended: boolean }[] {
  const { type } = recommend(shape);
  return CHART_TYPES.map((candidate) => ({
    type: candidate,
    use: CHART_USE[candidate],
    recommended: candidate === type,
  }));
}
