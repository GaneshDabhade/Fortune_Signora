import { cn } from '@/lib/design/cn';

export interface InferredProps {
  readonly className?: string;
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
export function Inferred({ className }: InferredProps) {
  return (
    <span
      className={cn(
        'inline-flex items-center rounded-sm bg-surface-sunken px-1.5 py-0.5 text-xs font-medium text-content-muted',
        className,
      )}
    >
      {/* The word, not an icon. Somebody meeting this on their first screen
          has no legend to look it up in. */}
      Inferred
    </span>
  );
}
