import type { ReactNode } from 'react';

import { cn } from '@/lib/design/cn';

/**
 * **The layout container the design specifies and the repository has never
 * had** — [TASK-1460](../../../docs/BACKLOG.md), against 📁
 * [Design System v2](../../../docs/design-snapshot/screens/)'s `inherited`
 * block ([D-138](../../../docs/DECISION_REGISTER.md)):
 *
 * > ⚡ ***"12-column grid, 24px gutters, 1600px content maximum"***
 *
 * ## 🔴 The measurement this exists to fix, and it was ONE line
 *
 * ⛔ **`grid-cols-12` appeared ZERO times in `frontend/`.** ⛔ **`1600` appeared
 * only as a breakpoint and never as a content maximum.** ⚡ **A 38-component
 * library had no `Grid`, `Container`, `PageLayout` or `Stack`** — **so every
 * screen invented its own width.**
 *
 * 📁 **Measured across `frontend/app` before this component existed** —
 * **eight different width models**: `max-w-3xl` ×9 · `max-w-md` ×2 ·
 * `max-w-card` ×2 · `max-w-[57.5rem]` ×2 · `max-w-2xl` · `max-w-4xl` ·
 * `max-w-5xl` · `max-w-[35rem]`. ⚠️ **The dominant one is `max-w-3xl` —
 * 768px.**
 *
 * 🔴 **The screens are not independently wrong.** 📁 The root cause is
 * [`app-shell.tsx`](../shell/app-shell.tsx)'s content region: **`flex-1` with
 * no maximum**, so on a wide monitor content ran edge to edge and **every
 * screen constrained itself instead.** ⚡ **On a 1600px screen the current
 * model uses 48% of the width**, which is what *"components designed for
 * desktop but squeezed"* looks like from the outside.
 *
 * ## ⚠️ What this component deliberately does NOT do
 *
 * ⛔ **It does not migrate the eleven route directories that carry an ad-hoc
 * `max-w-*`.** 📁 [455 §4](../../../docs/architecture/455-context-definitions-r02-r03.md):
 * ***"a port with seven simultaneous first callers has no chance of being
 * corrected cheaply."*** ✅ **One consumer, measured, then the migration** —
 * and the migration list is already written down on the row.
 *
 * ⛔ **It does not touch the colour tokens or the four breakpoints.** ⚡ **Both
 * were verified correct against Design System v2 before this row**, and the
 * row's own sharpest line is that they must not be renumbered or "migrated".
 */

/**
 * ⚡ **How many of the twelve columns a region occupies.**
 *
 * ⛔ **A closed union rather than `number`** — 📁 [§2](../../../CLAUDE.md)
 * prefers a violation that is *unrepresentable* over one that is merely
 * discouraged, **and `span={13}` on a twelve-column grid is exactly the kind of
 * ordinary code that happens to be wrong.**
 *
 * ⚠️ **Tailwind is the second reason and it is a practical one**: the class
 * names are generated at build time from source text, so **a computed
 * `col-span-${n}` produces a class that does not exist** and the region
 * silently spans one column. **The lookup below is what makes that impossible.**
 */
export type ColumnSpan = 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 | 12;

/**
 * 🔴 **The span applies from 1024 up, and below it every column is the full
 * twelve** — 📁 the App Shell's `breakpoints` and Home's `viewports`, which
 * agree on the number.
 *
 * ⚠️ **Measured on `/settings/team` at 390 × 844 before this line**: a
 * `span={8}` column was **221px wide inside a 375px content region**, holding a
 * card holding a table — **so the People table was legible in a 177px slot with
 * 154px of the viewport left empty beside it.** ⛔ **The grid was a coordinate
 * system that never changed coordinates**: `col-span-8` means eight twelfths at
 * 1920 and eight twelfths at 320, and eight twelfths of a phone is not a
 * column, it is a gutter with content in it.
 *
 * 📁 **The design states the transition twice and at the same width.** Home §09
 * `viewports`: **`390` → *"1 col"*, `768` → *"1 col … the two-column split is
 * dropped rather than compressed"*, `1024` → *"2 col"*.** App Shell §20 puts
 * the same boundary at 1024 for the rail and the utility panel. ✅ **So
 * `smalllaptop:` is the design's own answer, not a number chosen to fix a
 * screenshot.**
 *
 * ⚡ **Every consumer inherits it.** 📁 `ReadingColumn` is nine screens —
 * Settings and its five children, Business, Help and the account record — and
 * none of them needed a change.
 */
const SPAN_CLASS: Readonly<Record<ColumnSpan, string>> = {
  1: 'smalllaptop:col-span-1',
  2: 'smalllaptop:col-span-2',
  3: 'smalllaptop:col-span-3',
  4: 'smalllaptop:col-span-4',
  5: 'smalllaptop:col-span-5',
  6: 'smalllaptop:col-span-6',
  7: 'smalllaptop:col-span-7',
  8: 'smalllaptop:col-span-8',
  9: 'smalllaptop:col-span-9',
  10: 'smalllaptop:col-span-10',
  11: 'smalllaptop:col-span-11',
  12: 'smalllaptop:col-span-12',
};

/**
 * 📁 **The design's three numbers, as data rather than as classes typed in a
 * template.**
 *
 * ⛔ **Exported because the tests assert the GEOMETRY against them** — 📁 the
 * row's Definition of Done: ***"the design's three numbers asserted from
 * geometry rather than class names."*** ⚡ **A test reading `max-w-[1600px]`
 * off a `className` proves somebody typed a string; a test reading
 * `getBoundingClientRect().width` proves the browser agreed.**
 */
export const CONTENT_GRID = {
  /** 📁 *"12-column grid"* */
  columns: 12,
  /** 📁 *"24px gutters"* — and 24 is 3 × the design's 8-point base. */
  gutter: 24,
  /** 📁 *"1600px content maximum"* */
  maxWidth: 1600,
} as const;

export interface ContainerProps {
  children: ReactNode;
  className?: string;
}

/**
 * ⚡ **The content region's frame: centred, capped at the design's maximum, and
 * gutter-padded.**
 *
 * ⛔ **`mx-auto` is load-bearing, not cosmetic.** **A maximum without centring
 * pins content to the left edge of a wide monitor**, which is a different
 * defect from the one being fixed rather than a partial fix for it.
 *
 * ⚠️ **The gutter yields below 640px and that is the design's own rule**, not a
 * concession: 📁 `inherited` also carries ***"the rule that chrome yields
 * before data."*** **24px of padding on each side of a 390px phone is 12% of
 * the viewport spent on nothing.**
 */
export function Container({ children, className }: ContainerProps) {
  return (
    <div
      data-testid="content-container"
      className={cn(
        // 📁 *"1600px content maximum"* — ⛔ **an arbitrary value on purpose.**
        // ⚠️ **`1600` already exists in `tailwind.config.ts` as the `desktop`
        // BREAKPOINT**, and reusing that name here would make one number mean
        // two things — [§2](../../../CLAUDE.md), *truth has exactly one
        // authoritative representation.* **They are numerically equal and
        // conceptually unrelated: one is when the layout changes, the other is
        // how wide content may ever get.**
        'mx-auto w-full max-w-[1600px]',
        // 📁 *"24px gutters"* — `p-6` on the 8-point base. **`p-4` below 640
        // because chrome yields before data.**
        'p-4 phone:p-6',
        className,
      )}
    >
      {children}
    </div>
  );
}

export interface ColumnsProps {
  children: ReactNode;
  className?: string;
}

/**
 * ⚡ **The twelve columns, with the design's gutter between them.**
 *
 * 🔴 **Separate from {@link Container} rather than merged into it, and the
 * reason is [§2](../../../CLAUDE.md)'s *decorative logic* rule.**
 *
 * ⛔ **A `grid-cols-12` whose only child spans all twelve is indistinguishable
 * from a plain block** — **remove the grid and nothing changes**, which is the
 * definition this repository uses for logic that *appears* to enforce something
 * and does not. ⚠️ **Merging the two would have made every consumer of the
 * content maximum silently a grid consumer too**, and the grid would then have
 * been decorative on every screen that does not lay out on columns.
 *
 * ✅ **So the maximum and the gutters ship composed into the shell — where they
 * fix a measured defect on every screen — and the column axis is opted into by
 * a region that genuinely needs it.** ⚡ **It is a coordinate system, and a
 * coordinate system with no coordinates on it is a comment.**
 */
export function Columns({ children, className }: ColumnsProps) {
  return (
    <div
      data-testid="content-columns"
      // 📁 *"24px gutters"* — ⛔ **`gap-6` is the SAME 24px as the edge padding
      // above, and that is the design's intent**: a gutter is one measurement,
      // not two that happen to match.
      className={cn('grid grid-cols-12 gap-6', className)}
    >
      {children}
    </div>
  );
}

export interface ColumnProps {
  children: ReactNode;
  span: ColumnSpan;
  className?: string;
}

/**
 * ⚡ **One region on the twelve-column axis, from 1024 up.**
 *
 * ⛔ **`col-span-12` is the base and is unconditional**, so a column is full
 * width on every viewport the design draws as one column — **and `min-w-0` is
 * what lets a wide child (a table, a long word, a code block) shrink the column
 * rather than push the grid past the viewport.** ⚠️ **Without it a `grid` track
 * takes its `auto` minimum from its content**, which is the mechanism behind
 * most *"a table broke the page"* reports.
 */
export function Column({ children, span, className }: ColumnProps) {
  return <div className={cn('col-span-12 min-w-0', SPAN_CLASS[span], className)}>{children}</div>;
}
