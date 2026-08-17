import { cn } from '@/lib/design/cn';

export interface InferredProps {
  readonly className?: string;
  /**
   * 📁 **Where the value came from, in the design's own two words.**
   *
   * ⚡ `'inference'` wears §14's reserved hue, because a value derived from an
   * enrichment record is generated content and that is the one thing the hue is
   * for. ⛔ `'browser'` does NOT — 📁 the design tints it `--sunken`, and it is
   * right to: a timezone read from `Intl` was not inferred by anything, it was
   * **reported**, and dressing it as intelligence would overstate what happened.
   */
  readonly from?: 'inference' | 'browser';
}

/**
 * **The *Inferred* marking** — [TASK-469](../../../docs/BACKLOG.md).
 *
 * The design's requirement in its own words: ***"every inferred value marked
 * as inferred and correctable"***, and the reason it works: *"Confirming four
 * pre-filled fields is a fundamentally different task from filling a form."*
 *
 * ### ⚠️ It is a label, never a warning
 *
 * ⛔ **No `warning` tone, no icon of alarm.** An inferred value is not a
 * suspect one — it is an *unconfirmed* one, and eleven of the design's fifteen
 * values arrive this way on the happy path. **Marking the ordinary case as a
 * problem would make the whole screen read as a list of things gone wrong.**
 *
 * ### ⛔ It never appears where nothing was inferred
 *
 * *"Enrichment unavailable: fields stay empty and editable, **the Inferred
 * badge is absent**, and the step is never blocked by it."* So this renders
 * only where a caller has a value whose provenance says `inferred` — a badge
 * on an empty field would claim the product knew something it did not.
 */
export function Inferred({ className, from = 'inference' }: InferredProps) {
  return (
    <span
      className={cn(
        // 📁 *"font-size:10.5px; font-weight:600; padding:1px 7px; border-radius:6px"*.
        'inline-flex items-center rounded-md px-[7px] py-px text-2xs font-semibold',
        from === 'inference' ? 'bg-ai-subtle text-ai' : 'bg-surface-sunken text-content-muted',
        className,
      )}
    >
      {/* The word, not an icon. Somebody meeting this on their first screen
          has no legend to look it up in. */}
      {from === 'inference' ? 'Inferred' : 'From your browser'}
    </span>
  );
}
