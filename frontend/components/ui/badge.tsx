import type { HTMLAttributes } from 'react';

import { cn } from '@/lib/design/cn';

/**
 * **The status pill** — rebuilt against 📁 [Design System v2](../../../docs/design-snapshot/screens/)
 * §01 `critique` and §17 `a11y` ([D-138](../../../docs/DECISION_REGISTER.md)).
 *
 * ## 🔴 The dot was missing, and it is the accessibility half of the pill
 *
 * 📁 **The design's own critique row for status pills reads**: *"Softer pills at
 * `--r-sm` with a tint and no border; **the dot is kept for
 * colour-independence**."* ⚡ **And §17 states the rule it serves** — 📁 `1.4.1`:
 * ***"Status keeps its dot and word; AI keeps its glyph and label. Tint alone
 * never carries meaning."***
 *
 * ⛔ **This component rendered a tint and a word and nothing else**, so a
 * `success` pill and a `danger` pill differed by hue alone — **which is exactly
 * the failure `1.4.1` names**, on the component the product reaches for sixty
 * times.
 *
 * ## ⚡ Why the dot is defaulted by TONE rather than opted into
 *
 * ⛔ **An opt-in prop would have left every existing caller failing the rule**,
 * and a rule nothing adopts is a comment. ⚠️ **But the design does not put a dot
 * on every pill** — 📁 its `Enterprise`, `AI` and `Generated` chips carry none,
 * because those are *labels* rather than *states*.
 *
 * ✅ **So the default is derived from what the tone MEANS.** `success`,
 * `warning` and `danger` are the three where **the colour is the message**, so
 * they carry the dot; `neutral`, `accent`, `info` and `ai` are labels and do
 * not. ⚡ **A caller may still say either way**, which is what `dot` is for —
 * ⛔ and `dot={false}` on a status tone is a decision the caller has to write
 * down rather than one it can take by omission.
 */
export type BadgeTone =
  | 'neutral'
  | 'accent'
  | 'success'
  | 'warning'
  | 'danger'
  | 'info'
  /** §14's reserved hue — *"a machine produced this"*, and nothing else in
   * the product may use the pairing. Deliberately not `info`: a notice and a
   * generated claim are different things to a reader deciding whether to
   * trust what they are looking at. */
  | 'ai';

/**
 * ## 🔴 [B-1052](../../../docs/BUGS.md) — measured, and it asks for the opposite
 *
 * ⛔ **The row asks for a 1px `-line` border on every tone.** ⚠️ **Measured
 * across the 35 screen documents: of 180 badge-like tinted elements — a tint
 * fill, a radius and a font of 12.5px or under — **166 carry NO border and 14
 * do.** ✅ **The design's badge is borderless**, so adding one to all seven
 * tones would move away from the design rather than toward it. 📁 **The
 * `-line` roles serve the tinted PANEL** — 87 pairings — **and they now have
 * tokens and consumers there** (`system-state.tsx` and the Home strips).
 *
 * 🔴 **What the same measurement DOES find is the foreground**, and it is
 * unambiguous:
 *
 * | tint | the design's colour | ours, before |
 * |---|---|---|
 * | `--brand-tint` | `--brand-ink` ×55 of 55 | `--brand` |
 * | `--ai-tint` | `--ai-ink` ×47 of 48 | `--ai` |
 * | `--pos-tint` · `--warn-tint` · `--risk-tint` | `--pos` · `--warn` · `--risk` | ✅ already right |
 *
 * ⚡ **The `-ink` roles ARE the readable-on-tint step**, which is why `--ai-ink`
 * has 247 uses. ⛔ **In light `--brand` and `--brand-ink` are the same colour,
 * so this was invisible there and wrong only in dark** — the same shape as the
 * two token defects [B-1051](../../../docs/BUGS.md) turned up.
 */
const TONES: Record<BadgeTone, string> = {
  neutral: 'bg-surface-sunken text-content-muted',
  accent: 'bg-accent-subtle text-accent-ink',
  success: 'bg-success-subtle text-success',
  warning: 'bg-warning-subtle text-warning',
  danger: 'bg-danger-subtle text-danger',
  info: 'bg-info-subtle text-info',
  ai: 'bg-ai-subtle text-ai-ink',
};

/**
 * ⚡ **The three tones where the hue IS the claim.** ⛔ Not a style list — it is
 * the answer to *"would removing colour remove information?"*, and that is the
 * only question `1.4.1` asks.
 */
const STATUS_TONES: ReadonlySet<BadgeTone> = new Set<BadgeTone>(['success', 'warning', 'danger']);

export interface BadgeProps extends HTMLAttributes<HTMLSpanElement> {
  tone?: BadgeTone;
  /**
   * 📁 **The colour-independent marker.** ⚡ **Defaults to `true` for the status
   * tones and `false` for the label tones** — see the note above. ⛔ Set it
   * explicitly only where the default is wrong for what this pill states.
   */
  dot?: boolean;
}

export function Badge({ className, tone = 'neutral', dot, children, ...props }: BadgeProps) {
  const showDot = dot ?? STATUS_TONES.has(tone);

  return (
    <span
      className={cn(
        // 📁 *"Softer pills at `--r-sm` with a tint and no border"* — and the
        // design's pills are 600, not 500: *"600 replaces 800 for every
        // interface label."*
        'inline-flex items-center gap-1.5 rounded-sm px-2 py-0.5 text-xs font-semibold',
        // ⛔ **A pill never wraps mid-status.** ⚡ Its ROW wraps instead, which is
        // what keeps a status legible in a narrow card rather than broken across
        // two lines inside its own tint.
        'whitespace-nowrap',
        TONES[tone],
        className,
      )}
      {...props}
    >
      {showDot ? (
        // ♿ `aria-hidden` because the word beside it already carries the
        // meaning — the dot exists for a reader who cannot use the hue, not
        // for one who cannot see the pill at all.
        // 📁 §05 `radii` — *"999px · status dot"*, which `rounded-full` now is.
        <span aria-hidden className="h-1.5 w-1.5 shrink-0 rounded-full bg-current" />
      ) : null}
      {children}
    </span>
  );
}
