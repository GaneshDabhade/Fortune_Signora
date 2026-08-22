import { forwardRef, type ButtonHTMLAttributes } from 'react';

import { cn } from '@/lib/design/cn';

export type ButtonVariant = 'primary' | 'secondary' | 'ghost' | 'danger';
export type ButtonSize = 'sm' | 'md' | 'lg';

const VARIANTS: Record<ButtonVariant, string> = {
  primary: 'bg-accent text-accent-contrast hover:bg-accent-hover',
  secondary:
    'bg-surface text-content border border-border-strong hover:bg-surface-sunken',
  ghost: 'text-content-muted hover:bg-surface-sunken hover:text-content',
  danger: 'bg-danger text-accent-contrast hover:bg-danger-hover',
};

/**
 * 📁 **§10 Controls** — *"Buttons and inputs move to 8px radius and 34px default
 * height."* ⚡ **The heights are the control tokens**, corrected by this row from
 * an invented 32/40/44 to the design's 32/34/40; ⛔ **no literal appears here**,
 * which is what keeps a height change one edit rather than three.
 *
 * ♿ **`coarse:min-h-11` is the design's other sentence about size** — 📁 §17
 * `2.5.8`, *"44px on touch"*, and 📁 Home `1.4.10`, *"on mobile every primary
 * action is 44px tall."* ⛔ **A `min-height`, not a `height`**: it raises the
 * control on a touch screen and leaves the design's 34px everywhere a mouse is
 * pointing, so one component satisfies both sentences instead of choosing.
 */
/**
 * ⚠️ **`sm` IS NOT THE DESIGN'S *Compact*, and a reader would reasonably assume
 * it is.** 📁 **§10 names three buttons — `Compact 26px` · default `34px` ·
 * `Large 40px`.** ✅ **`md` and `lg` are those two exactly** (`--control-md`
 * 34px, `--control-lg` 40px, both verified in §10's markup and not only its
 * prose). ⛔ **`sm` is `--control-sm`, `32px`, which comes from a DIFFERENT
 * document** — 📁 the App Shell's *"a 32px target with 8px separation"* — and
 * it is what `FilterChip`, `SystemStatus` and `OfflineStatus` are sized by.
 *
 * ⛔ **So §10's `Compact 26px` has no token and is not built.** ⚡ **Measured
 * before deciding: `26px` controls appear 8 times across the 35 documents**,
 * against 129 at `30px`, 109 at `32px` and 94 at `34px` — **the corpus does not
 * hold a clean three-step scale**, and building a size nothing asks for is the
 * speculation [§6](../../../CLAUDE.md) forbids. ✅ **Recorded here so the next
 * reader does not infer it from the name.**
 *
 * 🔴 **The radius is 8px at every size, and the design's own two documents
 * disagree about that.** 📁 **§05 `radii` assigns `8px --r-md` to *"Button,
 * input, select, nav item, segmented option"*** — no size variation. 📁 **§10's
 * markup draws `6px` compact, `8px` default, `10px` large.** ⛔ **`10px` is not
 * a step on §05's scale at all** (`4 · 6 · 8 · 12 · 16 · 20`), **so the scale
 * is the rule and §10's demo radii are the drawing.** ⚡ Same reading as
 * [C-1547](../../../docs/LANE_COORDINATION.md).
 */
const SIZES: Record<ButtonSize, string> = {
  sm: 'h-control-sm px-3 text-sm coarse:min-h-11',
  md: 'h-control-md px-4 text-sm coarse:min-h-11',
  lg: 'h-control-lg px-6 text-base coarse:min-h-11',
};

export interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
  size?: ButtonSize;
  /** Shows a spinner and blocks interaction. Disables the button too, so a
   * caller cannot express "busy but clickable" — the state that produces
   * duplicate submissions. */
  loading?: boolean;
}

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(function Button(
  {
    className,
    variant = 'primary',
    size = 'md',
    loading = false,
    disabled,
    children,
    ...props
  },
  ref,
) {
  return (
    <button
      ref={ref}
      // `aria-busy` rather than only a spinner: a screen reader user gets
      // no information from a rotating border.
      aria-busy={loading || undefined}
      disabled={disabled ?? loading}
      className={cn(
        // 📁 §10 — *"Labels are 600 and sentence case, and centred inside the
        // control."* ⛔ **`font-medium` is 500**, and the design says 600 for
        // every interface label; the critique's own line is *"600 replaces 800
        // for every interface label — the difference between a system that
        // whispers and one that shouts."*
        'inline-flex items-center justify-center gap-2 rounded font-semibold',
        // ⚡ **`shrink-0` and `whitespace-nowrap` are the layout half.** ⛔ A
        // button in a flex row with neither is squeezed to its ellipsis by a
        // long sibling, and its label wraps to two lines inside a fixed height —
        // which is the *"buttons wrapping incorrectly"* class of defect rather
        // than a styling preference. **The row wraps; the control does not.**
        'shrink-0 whitespace-nowrap',
        'transition-colors disabled:pointer-events-none disabled:opacity-50',
        VARIANTS[variant],
        SIZES[size],
        className,
      )}
      {...props}
    >
      {loading ? (
        <span
          aria-hidden
          className="h-4 w-4 animate-spin rounded-full border-2 border-current border-t-transparent"
        />
      ) : null}
      {children}
    </button>
  );
});
