import { render, screen } from '@testing-library/react';
import { readFileSync } from 'node:fs';
import { join } from 'node:path';
import { describe, expect, it } from 'vitest';

import { BarSeries, CHART_SERIES, Sparkline, seriesAt } from '@/components/ui';

/**
 * **The chart ramp and its primitives** — [TASK-1450](../../../docs/BACKLOG.md),
 * 📁 Design System v2 `chartRamp`.
 */

describe('🔴 the ramp is tokens, in BOTH themes', () => {
  it('⛔ eight series exist in light and in dark', () => {
    /**
     * 📁 **The design gives a SEPARATE dark ramp, not a filter.** ⚡
     * Lightening the light ramp algorithmically produces muddy mid-tones on a
     * dark surface, which is why the design draws eight different values.
     *
     * ⚠️ **This was the ONE part of the token layer that did not match** —
     * [D-217](../../../docs/DECISION_REGISTER.md) measured the colour tokens
     * as exact and they are; these were simply absent.
     */
    const css = readFileSync(join(process.cwd(), 'app', 'globals.css'), 'utf8');
    const light = css.slice(css.indexOf(':root {'), css.indexOf("[data-theme='dark']"));
    const dark = css.slice(css.indexOf("[data-theme='dark']"));

    for (let n = 1; n <= 8; n += 1) {
      expect(light, `--color-c${n} missing from the light theme`).toContain(`--color-c${n}:`);
      expect(dark, `--color-c${n} missing from the dark theme`).toContain(`--color-c${n}:`);
    }
  });

  it('⛔ and the two ramps differ, which is the point of having two', () => {
    // ⚡ **Vacuity guard.** If the dark block simply repeated the light values,
    // the assertion above would pass over a ramp that is unreadable on dark.
    const css = readFileSync(join(process.cwd(), 'app', 'globals.css'), 'utf8');
    const value = (block: string, n: number) =>
      block.match(new RegExp(`--color-c${n}:\\s*([^;]+);`))?.[1]?.trim();
    const light = css.slice(css.indexOf(':root {'), css.indexOf("[data-theme='dark']"));
    const dark = css.slice(css.indexOf("[data-theme='dark']"));

    for (let n = 1; n <= 8; n += 1) {
      expect(value(dark, n), `--color-c${n} is identical in both themes`).not.toBe(
        value(light, n),
      );
    }
  });
});

describe('🔴 a series is a POSITION, never a colour a caller picks', () => {
  it('⛔ there is no colour prop, and that is deliberate', () => {
    /**
     * 📁 **The ramp's order is the design's**: it opens on the brand and moves
     * away from it, so a two-series chart reads as *ours versus theirs*.
     * ⚡ **A caller that could choose would eventually choose `--c5` first**,
     * and the meaning the ordering carries would be gone with nothing to
     * detect it.
     */
    const source = readFileSync(join(process.cwd(), 'components/ui/chart.tsx'), 'utf8');
    expect(source).not.toMatch(/\bcolor\??:\s*string/);
    expect(source).toMatch(/series\??: number/);
  });

  it('✅ positions wrap rather than throwing', () => {
    // ⛔ A ninth series is a design problem, not a crash — refusing to render
    // would hide the data entirely.
    expect(seriesAt(0)).toBe('c1');
    expect(seriesAt(7)).toBe('c8');
    expect(seriesAt(8)).toBe('c1');
    expect(CHART_SERIES).toHaveLength(8);
  });
});

describe('♿ a chart says what it shows, because an SVG says nothing', () => {
  it('✅ the sparkline carries its range in its accessible name', () => {
    // ⛔ **A screen reader meets an SVG as a blank rectangle.** A chart with no
    // text alternative simply is not there.
    render(<Sparkline values={[3, 5, 4, 9]} label="Committed forecast" />);
    const chart = screen.getByRole('img', { name: /Committed forecast/ });
    expect(chart).toHaveAccessibleName(/from 3 to 9/);
  });

  it('✅ the bar series renders its data as a list, and hides the bars', () => {
    // ⚡ The bars are the same facts drawn; announcing both reads every figure
    // twice.
    const { container } = render(
      <BarSeries label="By owner" values={[{ label: 'M. Reinhardt', value: 412 }]} />,
    );
    expect(screen.getByText(/M\. Reinhardt: 412/)).toBeInTheDocument();
    expect(container.querySelector('[aria-hidden="true"]')).not.toBeNull();
  });

  it('⛔ one point is not a trend and renders nothing', () => {
    // ⚡ A flat line for a single value would assert a direction the data does
    // not have.
    const { container } = render(<Sparkline values={[5]} label="One" />);
    expect(container).toBeEmptyDOMElement();
  });

  it('⛔ a flat series does not divide by zero', () => {
    // A real case: a metric that has not moved all week.
    render(<Sparkline values={[4, 4, 4]} label="Flat" />);
    expect(screen.getByRole('img', { name: /Flat/ })).toBeInTheDocument();
  });
});
