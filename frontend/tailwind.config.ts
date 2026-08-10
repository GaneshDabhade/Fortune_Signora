import type { Config } from 'tailwindcss';

/**
 * Tailwind is wired to the design tokens in `app/globals.css`, not to its
 * own palette. Semantic names resolve to CSS custom properties, so a theme
 * change is a value swap rather than a component edit (AC-15).
 *
 * Tailwind's default palette remains reachable, but no shared component
 * uses it — asserted by `tests/components/design-tokens.test.ts`, because
 * a convention that is only written down is a convention that erodes.
 */
export default {
  content: ['./app/**/*.{ts,tsx}', './components/**/*.{ts,tsx}', './lib/**/*.{ts,tsx}'],
  darkMode: ['class', '[data-theme="dark"]'],
  theme: {
    /* 🔴 **The design's four bands, REPLACING Tailwind's defaults** —
     * TASK-1443, App Shell `breakpoints`.
     *
     * ⛔ **`screens` at this level OVERRIDES rather than extends**, and that is
     * the point: `md:` and `sm:` were 768 and 640, and the design names 1600,
     * 1280, 1024 and 640. Leaving Tailwind's set beside these would give the
     * frame two vocabularies for one question, and every future decision would
     * be taken at whichever width the author happened to reach for.
     *
     * ⚡ **Named for the band, not the number** — `laptop:` says which of the
     * design's four rows a rule belongs to; `min-[1280px]:` says nothing and
     * drifts the moment the design moves a boundary.
     *
     * 📁 The bands, in the design's own words:
     *   `desktop`      ≥1600  — rail 232, panel 360, both open
     *   `laptop`       1280+  — THE REFERENCE LAYOUT, rail 232, panel 300
     *   `smalllaptop`  1024+  — rail collapses to 56px icons with tooltips
     *   (below 1024)          — rail becomes a sheet; `phone` is the <640 floor
     */
    screens: {
      phone: '640px',
      smalllaptop: '1024px',
      laptop: '1280px',
      desktop: '1600px',
    },
    extend: {
      colors: {
        canvas: 'rgb(var(--color-canvas) / <alpha-value>)',
        backdrop: 'rgb(var(--color-backdrop) / <alpha-value>)',
        surface: {
          DEFAULT: 'rgb(var(--color-surface) / <alpha-value>)',
          raised: 'rgb(var(--color-surface-raised) / <alpha-value>)',
          sunken: 'rgb(var(--color-surface-sunken) / <alpha-value>)',
        },
        content: {
          DEFAULT: 'rgb(var(--color-content) / <alpha-value>)',
          muted: 'rgb(var(--color-content-muted) / <alpha-value>)',
          subtle: 'rgb(var(--color-content-subtle) / <alpha-value>)',
          inverted: 'rgb(var(--color-content-inverted) / <alpha-value>)',
        },
        border: {
          /* The design specifies two hairline weights; `soft` is the quiet
           * one (TASK-491 gap ③). A divider between rows of one list is
           * `soft`; a divider between two regions is the default. */
          soft: 'rgb(var(--color-border-soft) / <alpha-value>)',
          DEFAULT: 'rgb(var(--color-border) / <alpha-value>)',
          strong: 'rgb(var(--color-border-strong) / <alpha-value>)',
        },
        accent: {
          DEFAULT: 'rgb(var(--color-accent) / <alpha-value>)',
          hover: 'rgb(var(--color-accent-hover) / <alpha-value>)',
          contrast: 'rgb(var(--color-accent-contrast) / <alpha-value>)',
          soft: 'rgb(var(--color-accent-soft) / <alpha-value>)',
          subtle: 'rgb(var(--color-accent-subtle) / <alpha-value>)',
        },
        success: {
          DEFAULT: 'rgb(var(--color-success) / <alpha-value>)',
          subtle: 'rgb(var(--color-success-subtle) / <alpha-value>)',
        },
        warning: {
          DEFAULT: 'rgb(var(--color-warning) / <alpha-value>)',
          subtle: 'rgb(var(--color-warning-subtle) / <alpha-value>)',
        },
        danger: {
          DEFAULT: 'rgb(var(--color-danger) / <alpha-value>)',
          hover: 'rgb(var(--color-danger-hover) / <alpha-value>)',
          subtle: 'rgb(var(--color-danger-subtle) / <alpha-value>)',
        },
        info: {
          DEFAULT: 'rgb(var(--color-info) / <alpha-value>)',
          subtle: 'rgb(var(--color-info-subtle) / <alpha-value>)',
        },
        /* §14's reserved hue. Named `ai` rather than `indigo` because the
         * token names a role — what produced the content — and a hue name
         * would make the next theme's choice of colour a rename. */
        /* ⚡ **The chart ramp as colours** — TASK-1450. ⛔ Named `c1`…`c8`
         * rather than by hue: **a series is a position in the ramp, not a
         * colour a caller chooses**, and naming them `blue`/`green` would
         * invite exactly that choice. */
        c1: 'rgb(var(--color-c1) / <alpha-value>)',
        c2: 'rgb(var(--color-c2) / <alpha-value>)',
        c3: 'rgb(var(--color-c3) / <alpha-value>)',
        c4: 'rgb(var(--color-c4) / <alpha-value>)',
        c5: 'rgb(var(--color-c5) / <alpha-value>)',
        c6: 'rgb(var(--color-c6) / <alpha-value>)',
        c7: 'rgb(var(--color-c7) / <alpha-value>)',
        c8: 'rgb(var(--color-c8) / <alpha-value>)',
        ai: {
          DEFAULT: 'rgb(var(--color-ai) / <alpha-value>)',
          subtle: 'rgb(var(--color-ai-subtle) / <alpha-value>)',
        },
      },
      borderRadius: {
        sm: 'var(--radius-sm)',
        md: 'var(--radius-md)',
        DEFAULT: 'var(--radius)',
        lg: 'var(--radius-lg)',
        /* The 16px plane §11 and §12 both specify. Added by slice 3, which
         * is the first slice with a component that needs it. */
        xs: 'var(--radius-xs)',
        xl: 'var(--radius-xl)',
        '2xl': 'var(--radius-2xl)',
        /* 📁 §05 `radii` — *"999px · Avatar, status dot, count badge,
         * progress track."* ⛔ **This SHADOWS Tailwind's own `rounded-full`
         * (9999px), and that is the point**: the utility already existed and
         * no token controlled it, so `rounded-full` now resolves to the
         * design's value everywhere it is already written — including the
         * avatar TASK-1440 shipped. */
        full: 'var(--radius-full)',
      },
      /* **The type scale becomes tokens** (TASK-448). Declared here rather
       * than left to Tailwind's defaults so that `design-tokens.test.tsx` can
       * assert membership: an arbitrary `text-[0.9375rem]` is to the type
       * scale exactly what `bg-slate-100` is to the colour scale. */
      fontSize: {
        '2xs': 'var(--text-2xs)',
        xs: 'var(--text-xs)',
        sm: 'var(--text-sm)',
        md: 'var(--text-md)',
        base: 'var(--text-base)',
        lg: 'var(--text-lg)',
        xl: 'var(--text-xl)',
        /* ⚡ **The design's roles carry four numbers, not one** — 📁 §04
         * `typeRows` gives size / leading / weight / tracking, and a
         * size-only entry silently drops three of them. **Tailwind's tuple
         * form carries all four**, so `text-title` produces the design's
         * type rather than the design's size at whatever leading it
         * inherits. TASK-1453.
         *
         * ⛔ **Only the roles this row adds or corrects use the tuple.** The
         * entries above stay size-only: widening them is a sweep across every
         * surface in the product, and 📁 [D-220](../docs/DECISION_REGISTER.md)
         * §10's *do not create churn for a faithful implementation* applies to
         * this file as much as to a rename. */
        display: ['var(--text-display)', { lineHeight: '1.05', letterSpacing: '-0.032em', fontWeight: '700' }],
        title: ['var(--text-title)', { lineHeight: '1.15', letterSpacing: '-0.026em', fontWeight: '700' }],
        /* 📁 *"30 / 1.05 / 700 / **tabular**"* — ⚠️ **the tabular half is NOT
         * here.** `fontVariantNumeric` is not a `fontSize` option in Tailwind,
         * so it cannot ride on the token; **`tabular-nums` is applied at the
         * call site.** ⛔ **Recorded rather than silently dropped**: a metric
         * rendered with proportional figures jitters as it updates, which is
         * the whole reason the design specifies it. */
        metric: ['var(--text-metric)', { lineHeight: '1.05', letterSpacing: '-0.028em', fontWeight: '700' }],
        label: ['var(--text-label)', { lineHeight: '1.45', letterSpacing: '-0.002em', fontWeight: '600' }],
      },
      boxShadow: {
        sm: 'var(--shadow-sm)',
        DEFAULT: 'var(--shadow)',
        lg: 'var(--shadow-lg)',
        /* The design's fourth elevation (TASK-491 gap ⑤) — what a surface
         * cast *over the page* looks like, rather than one sitting on it. */
        xl: 'var(--shadow-xl)',
      },
      maxWidth: {
        /* *"A single 400px card carries all 24 screens."* Named so the
         * arbitrary value it replaces becomes refusable rather than only
         * discouraged (TASK-491 gap ⑦). */
        card: 'var(--card-width)',
      },
      spacing: {
        sidebar: 'var(--sidebar-width)',
        topbar: 'var(--topbar-height)',
        /* **Control heights** (TASK-448). In `spacing` so they read as
         * `h-control-md`, which says what the number is for at the call
         * site — `h-10` said only how tall it happened to be. */
        'control-sm': 'var(--control-sm)',
        'control-md': 'var(--control-md)',
        'control-lg': 'var(--control-lg)',
      },
    },
  },
  plugins: [],
} satisfies Config;
