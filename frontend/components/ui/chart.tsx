import { cn } from '@/lib/design/cn';

/**
 * **Charts** — [TASK-1450](../../../docs/BACKLOG.md), against 📁
 * [Design System v2](../../../docs/design-snapshot/screens/) `chartRamp`
 * ([D-138](../../../docs/DECISION_REGISTER.md)).
 *
 * ## ⚡ The tokens came first, and the row says why
 *
 * ⛔ **A chart built before `--c1`…`--c8` existed would have hardcoded eight
 * hex values** — the [§20c](../../../CLAUDE.md) violation
 * `design-tokens.test.tsx` already refuses, eight times over. ✅ **They exist
 * now, in both themes**, and 📁 **the design gives a SEPARATE dark ramp rather
 * than a filter**: lightening the light ramp algorithmically produces muddy
 * mid-tones on a dark surface.
 *
 * ## 🔴 A series is a POSITION, never a colour a caller picks
 *
 * ⛔ **There is no `color` prop and there will not be one.** 📁 The ramp's
 * order is the design's: **it opens on the brand and moves away from it**, so
 * a two-series chart reads as *ours versus theirs* rather than as two
 * arbitrary colours. ⚡ **A caller that could choose would eventually choose
 * `--c5` for the first series**, and the meaning the ordering carries would be
 * gone with nothing to detect it.
 *
 * ## ⚠️ What this deliberately is NOT
 *
 * 📁 **The row is explicit**: *"not every chart type; the ones those two
 * screens draw."* ⛔ **A charting library built ahead of its callers
 * generalises the wrong axis** ([§6](../../../CLAUDE.md)) — **and this
 * repository has found a component with no caller six times.**
 *
 * ✅ **So: a sparkline and a bar series**, which are what the Executive
 * Dashboard's metric cards and Reports draw. **Anything else arrives with the
 * screen that needs it.**
 *
 * ## ♿ A chart is not readable, so it says what it shows
 *
 * ⛔ **Colour alone never carries the message** — the rule this product applies
 * everywhere. ⚡ **Each chart takes a `label` and renders its data as an
 * accessible summary**, because **a screen reader meets an SVG as a blank
 * rectangle** and a chart with no text alternative simply is not there.
 */

/** 📁 Eight series, and the eighth is the last — a ninth is a different chart. */
export const CHART_SERIES = ['c1', 'c2', 'c3', 'c4', 'c5', 'c6', 'c7', 'c8'] as const;

export type ChartSeries = (typeof CHART_SERIES)[number];

/**
 * ⚡ **The ramp position for the nth series.** ⛔ **Wraps rather than throwing**
 * — a chart with nine series is a design problem, not a crash, and refusing to
 * render would hide the data entirely.
 */
export function seriesAt(index: number): ChartSeries {
  return CHART_SERIES[index % CHART_SERIES.length] as ChartSeries;
}

const STROKE: Record<ChartSeries, string> = {
  c1: 'stroke-c1',
  c2: 'stroke-c2',
  c3: 'stroke-c3',
  c4: 'stroke-c4',
  c5: 'stroke-c5',
  c6: 'stroke-c6',
  c7: 'stroke-c7',
  c8: 'stroke-c8',
};

const FILL: Record<ChartSeries, string> = {
  c1: 'fill-c1',
  c2: 'fill-c2',
  c3: 'fill-c3',
  c4: 'fill-c4',
  c5: 'fill-c5',
  c6: 'fill-c6',
  c7: 'fill-c7',
  c8: 'fill-c8',
};

export interface SparklineProps {
  values: readonly number[];
  /** ♿ Required — see the note above. An unlabelled chart is not there. */
  label: string;
  /** 📁 Which series this is. ⛔ A position in the ramp, not a colour. */
  series?: number;
  className?: string;
}

/**
 * 📁 **The metric card's trend line** — the Executive Dashboard draws one on
 * every card.
 */
export function Sparkline({ values, label, series = 0, className }: SparklineProps) {
  // ⛔ **One point is not a trend**, and rendering a flat line for it would
  // assert a direction the data does not have.
  if (values.length < 2) return null;

  const min = Math.min(...values);
  const max = Math.max(...values);
  // ⚡ **A flat series is real and must not divide by zero.**
  const span = max - min || 1;
  const step = 100 / (values.length - 1);

  const points = values
    .map((value, index) => `${index * step},${30 - ((value - min) / span) * 30}`)
    .join(' ');

  return (
    <svg
      viewBox="0 0 100 30"
      preserveAspectRatio="none"
      role="img"
      aria-label={`${label}. ${values.length} points, from ${values[0]} to ${values[values.length - 1]}.`}
      className={cn('h-8 w-full', className)}
    >
      <polyline
        points={points}
        fill="none"
        strokeWidth={1.5}
        vectorEffect="non-scaling-stroke"
        className={STROKE[seriesAt(series)]}
      />
    </svg>
  );
}

export interface BarSeriesProps {
  values: readonly { label: string; value: number }[];
  /** ♿ Required. */
  label: string;
  series?: number;
  className?: string;
}

/** 📁 **The bar series Reports draws.** */
export function BarSeries({ values, label, series = 0, className }: BarSeriesProps) {
  if (values.length === 0) return null;
  const max = Math.max(...values.map((v) => v.value)) || 1;

  return (
    <div className={cn('flex flex-col gap-1.5', className)}>
      {/* ♿ **The data as a list, which is what a screen reader reads.** ⛔ The
          bars below are `aria-hidden`: they are the same facts drawn, and
          announcing both reads every figure twice. */}
      <ul className="sr-only">
        {values.map((v) => (
          <li key={v.label}>
            {v.label}: {v.value}
          </li>
        ))}
      </ul>
      <div aria-hidden className="flex flex-col gap-1.5" aria-label={label}>
        {values.map((v, index) => (
          <div key={v.label} className="flex items-center gap-2">
            <span className="w-24 shrink-0 truncate text-2xs text-content-muted">{v.label}</span>
            <span className="h-2 flex-1 overflow-hidden rounded-full bg-surface-sunken">
              <span
                className={cn('block h-full rounded-full', FILL[seriesAt(series + index)])}
                style={{ width: `${(v.value / max) * 100}%` }}
              />
            </span>
            <span className="w-14 shrink-0 text-right text-2xs tabular-nums text-content">
              {v.value.toLocaleString()}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
