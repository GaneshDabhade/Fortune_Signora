import { cn } from '@/lib/design/cn';

export interface ConfidenceProps {
  /** How confident, 1–5. §14 renders it as *"4 of 5"* beside its pips. */
  level: number;
  /** §14 pairs the figure with what it was drawn from — *"4 of 5 · 6
   * sources"*. ⛔ **Optional, and never invented**: a caller that does not
   * know the count must not be made to guess one. */
  sources?: number;
  className?: string;
}

const SCALE = 5;

/**
 * §14's confidence figure — the fourth term of the AI grammar.
 *
 * **Design System v2 §14** gives intelligence *"a 6px glyph tile, a tint
 * field, a hairline in the same family, and a confidence figure"*, and shows
 * it as pips beside *"4 of 5 · 6 sources"*.
 *
 * ### The pips are decoration and the sentence is the content
 *
 * ⚠️ **Five filled shapes convey nothing to a screen reader, and nothing at
 * all in high-contrast mode** — §17 is explicit that *"radius and shadow are
 * decorative layers only — nothing depends on them to be understood"*, and
 * the same reasoning governs a row of dots. **So the text is the value and
 * the pips are `aria-hidden`.** A reader who cannot see them still hears
 * *"confidence 4 of 5"*.
 *
 * ### Why the level is clamped rather than trusted
 *
 * A caller passing `7` would render seven pips against a five-point scale and
 * silently redefine what the figure means. **Clamping keeps the scale fixed**
 * — the reader's calibration between screens is the only thing that makes a
 * confidence figure useful at all.
 */
export function Confidence({ level, sources, className }: ConfidenceProps) {
  const filled = Math.max(0, Math.min(SCALE, Math.round(level)));
  const label = `Confidence ${filled} of ${SCALE}`;

  return (
    <span className={cn('inline-flex items-center gap-2 text-xs text-content-muted', className)}>
      <span aria-hidden className="inline-flex gap-0.5">
        {Array.from({ length: SCALE }, (_, index) => (
          <span
            key={index}
            className={cn(
              'h-1.5 w-1.5 rounded-full',
              index < filled ? 'bg-ai' : 'bg-border-strong',
            )}
          />
        ))}
      </span>
      <span>
        {label}
        {sources === undefined ? null : ` · ${sources} ${sources === 1 ? 'source' : 'sources'}`}
      </span>
    </span>
  );
}
