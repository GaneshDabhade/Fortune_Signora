import type { Config } from 'tailwindcss';
import plugin from 'tailwindcss/plugin';

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
          /* 📁 The design's fourth ink step — [B-1064](../docs/BUGS.md). */
          faint: 'rgb(var(--color-content-faint) / <alpha-value>)',
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
        /* 🔴 **[B-1051](../../docs/BUGS.md) — the design draws a tinted surface
         * as a TRIPLET**: a `-tint` fill, a `-line` edge and an `-ink`
         * foreground. ⛔ **Only the fill had a token**, so every edge in the
         * product was an invented alpha (`border-warning/30`) and every
         * foreground was the full-strength hue. */
        accent: {
          DEFAULT: 'rgb(var(--color-accent) / <alpha-value>)',
          hover: 'rgb(var(--color-accent-hover) / <alpha-value>)',
          contrast: 'rgb(var(--color-accent-contrast) / <alpha-value>)',
          /** 📁 `--brand-ink` — the foreground the design puts ON `--brand-tint`. */
          ink: 'rgb(var(--color-accent-ink) / <alpha-value>)',
          line: 'rgb(var(--color-accent-line) / <alpha-value>)',
          soft: 'rgb(var(--color-accent-soft) / <alpha-value>)',
          subtle: 'rgb(var(--color-accent-subtle) / <alpha-value>)',
        },
        success: {
          DEFAULT: 'rgb(var(--color-success) / <alpha-value>)',
          line: 'rgb(var(--color-success-line) / <alpha-value>)',
          subtle: 'rgb(var(--color-success-subtle) / <alpha-value>)',
        },
        warning: {
          DEFAULT: 'rgb(var(--color-warning) / <alpha-value>)',
          line: 'rgb(var(--color-warning-line) / <alpha-value>)',
          subtle: 'rgb(var(--color-warning-subtle) / <alpha-value>)',
        },
        danger: {
          DEFAULT: 'rgb(var(--color-danger) / <alpha-value>)',
          hover: 'rgb(var(--color-danger-hover) / <alpha-value>)',
          line: 'rgb(var(--color-danger-line) / <alpha-value>)',
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
          /** 📁 `--ai-ink` — **247 uses across 25 of 35 screens**, and no token. */
          ink: 'rgb(var(--color-ai-ink) / <alpha-value>)',
          line: 'rgb(var(--color-ai-line) / <alpha-value>)',
          subtle: 'rgb(var(--color-ai-subtle) / <alpha-value>)',
        },
      },
      height: {
        /* 📁 Design System v2 — the two table row heights, as tokens. */
        row: 'var(--row-h)',
        'row-compact': 'var(--row-h-compact)',
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
      /* 🔴 **THE MOTION SCALE THE DESIGN PUBLISHES AND THIS CONFIG NEVER
       * CARRIED** — 📁 Design System v2 §18, verbatim:
       * `transitionDuration: { fast: "120ms", DEFAULT: "160ms", slow: "220ms" }`
       * and `transitionTimingFunction: { premium: "cubic-bezier(.32,.72,0,1)" }`.
       *
       * ⛔ **Its absence was not theoretical.** 📁
       * [`onboarding/rail.tsx:86`](./app/(onboarding)/onboarding/rail.tsx)
       * already wrote `duration-slow ease-premium` — **the design's own names —
       * and Tailwind generated NEITHER**, so that progress bar carried
       * `transition-[width]` with no duration and did not animate at all.
       * ⚡ **Measured in the built CSS**: `.duration-150` and `.duration-200`
       * are the only two duration classes the product emits.
       *
       * ⚠️ **And it is why `workspace-strip.tsx` chose `duration-150` against a
       * design that says `160`**: its comment reasoned that *"the motion scale
       * is a token here"* and **a bespoke step would be the defect** — the
       * reasoning was right and the premise was false.
       *
       * ✅ **`premium` resolves to `var(--ease)`** rather than restating the
       * curve, so it has one representation ([§2](../CLAUDE.md)). **The value
       * already in `globals.css` is the design's, character for character.**
       *
       * 📁 **The same shape as the type scale's three missing roles**
       * (TASK-1453) — a role the design names that the token layer lacks, so
       * every call site silently falls back to a framework default. */
      transitionDuration: {
        fast: '120ms',
        DEFAULT: '160ms',
        slow: '220ms',
      },
      transitionTimingFunction: {
        premium: 'var(--ease)',
      },
      maxWidth: {
        /* *"A single 400px card carries all 24 screens."* Named so the
         * arbitrary value it replaces becomes refusable rather than only
         * discouraged (TASK-491 gap ⑦). */
        card: 'var(--card-width)',
      },
      spacing: {
        /* ⛔ **`sidebar` is gone with `--sidebar-width`.** ⚠️ It aliased a token
         * that held 240px against the design's 232px rail and had no caller;
         * the rail's two widths live in `lib/shell/rail.ts`, which is the one
         * place that knows the collapsed state exists. */
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
  plugins: [
    /* 🔴 **The design's touch rule is a POINTER rule, not a width rule** — 📁
     * §17 `2.5.8`: *"Every top-bar control is a 32px target with 8px
     * separation; **44px on touch**."*
     *
     * ⛔ **A `phone:` breakpoint would be the wrong question.** A 1280px
     * touchscreen is touch and a 600px desktop window is not, and sizing the
     * targets by viewport width answers neither. ⚡ **`pointer: coarse` is the
     * medium the design is describing**, so it is the medium the variant
     * queries — which is also why this is a variant rather than a value baked
     * into a control height every mouse user would inherit. */
    plugin(({ addVariant }) => {
      addVariant('coarse', '@media (pointer: coarse)');
    }),
  ],
} satisfies Config;
