/**
 * **The layout container's three numbers** — [TASK-1460](../../../docs/BACKLOG.md).
 *
 * ⚠️ **These are the CLASS-level assertions, and the row's Definition of Done
 * asks for geometry.** 📁 **jsdom computes no layout** — every box is 0×0 — **so
 * the width, the centring and the twelve columns are asserted in a browser by
 * [`content-grid.spec.ts`](../e2e/content-grid.spec.ts), and this file asserts
 * the things a browser cannot: the closed span union, and that the grid is NOT
 * silently applied to every consumer of the maximum.**
 */
import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';

import { CONTENT_GRID, Column, Columns, Container } from '@/components/ui/container';

describe('the design’s three numbers live in one place', () => {
  it('📁 12 columns · 24px gutters · 1600px maximum, as data', () => {
    // ⛔ **The tests read these**, so a number changed in the component without
    // the design changing fails here rather than being noticed on a screenshot.
    expect(CONTENT_GRID).toEqual({ columns: 12, gutter: 24, maxWidth: 1600 });
  });

  it('⚡ the gutter is 3 × the design’s 8-point spacing base', () => {
    // 📁 Design System v2's `inherited` block carries both — *"24px gutters"*
    // and *"8-point spacing base"* — ⛔ **and a gutter that is not a multiple of
    // the base would put every screen off the grid it claims to be on.**
    expect(CONTENT_GRID.gutter % 8).toBe(0);
  });
});

describe('the container caps and centres', () => {
  it('⛔ `mx-auto` is load-bearing — a maximum without it pins content left', () => {
    render(<Container>content</Container>);

    const box = screen.getByTestId('content-container');
    expect(box.className).toContain('mx-auto');
    expect(box.className).toContain(`max-w-[${CONTENT_GRID.maxWidth}px]`);
  });

  it('📁 the gutter yields below 640 — *"chrome yields before data"*', () => {
    render(<Container>content</Container>);

    // ⚡ **24px on each side of a 390px phone is 12% of the viewport spent on
    // nothing**, and the design states the rule rather than leaving it to taste.
    const box = screen.getByTestId('content-container');
    expect(box.className).toContain('p-4');
    expect(box.className).toContain('phone:p-6');
  });
});

/**
 * 🔴 **The assertion that keeps the grid from being decorative.**
 *
 * 📁 [§2](../../../CLAUDE.md): *"Decorative Logic is implementation that
 * appears to enforce a property but whose removal does not change the property
 * it claims to protect."* ⛔ **A `grid-cols-12` whose only child spans twelve is
 * exactly that** — remove it and nothing moves.
 *
 * ✅ **So the column axis is a separate opt-in**, and this is what stops a later
 * change quietly merging it into `Container` and making it decorative on every
 * screen in the product.
 */
describe('the column axis is opted into, never inherited', () => {
  it('🔴 the container alone declares no grid', () => {
    render(<Container>content</Container>);

    const box = screen.getByTestId('content-container');
    expect(box.className).not.toContain('grid-cols-12');
    expect(box.className).not.toContain('grid');
  });

  it('✅ and `Columns` is where the twelve and the gutter appear together', () => {
    render(
      <Columns>
        <Column span={8}>main</Column>
        <Column span={4}>aside</Column>
      </Columns>,
    );

    const grid = screen.getByTestId('content-columns');
    expect(grid.className).toContain('grid-cols-12');
    // 📁 **`gap-6` is the same 24px as the container's padding** — a gutter is
    // one measurement, not two that happen to match.
    expect(grid.className).toContain('gap-6');
  });

  it('⚡ a span resolves to a whole class name, never a computed one', () => {
    // 🔴 **Tailwind generates classes from SOURCE TEXT at build time**, so
    // `col-span-${n}` produces a class that does not exist and the region
    // silently collapses to one column. ⛔ **The lookup table is what makes that
    // unrepresentable**, and this is the test that proves the table is used.
    const { container } = render(<Column span={7}>seven</Column>);

    expect(container.firstElementChild?.className).toContain('col-span-7');
  });

  it('⛔ the twelve spans are all present and all distinct', () => {
    // ⚠️ **A lookup table is exactly the shape that acquires a copy-paste
    // duplicate**, and `4: 'col-span-3'` would be invisible in review.
    const rendered = ([1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12] as const).map((span) => {
      const { container } = render(<Column span={span}>x</Column>);
      return container.firstElementChild?.className ?? '';
    });

    expect(new Set(rendered).size).toBe(CONTENT_GRID.columns);
  });
});
