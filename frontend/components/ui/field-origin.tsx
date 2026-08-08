import { cn } from '@/lib/design/cn';

/**
 * Where a profile field's value comes from, and therefore who may change it.
 *
 * **[TASK-470](../../../docs/BACKLOG.md) · Workflow 9**, and the design draws
 * exactly three kinds — *Yours* · *From directory* · *Workspace policy*.
 *
 * ### 🔴 This is the screen's invariant, not a decoration
 *
 * **The design's headline number on this screen is `0`:** *"Edits accepted
 * that a sync would undo."* ⚡ **The three tags exist to keep it true.** A
 * field a directory owns must not offer an edit, because accepting one that
 * the next sync silently reverses is worse than refusing it — the customer
 * believes they changed something and the product knows they did not.
 *
 * ### ⛔ The tag never appears without the rule behind it
 *
 * **`directory` is not rendered by anything today**, and that is
 * [C-248](../../../docs/LANE_COORDINATION.md): no directory integration exists
 * in the repository, so a field labelled *From directory* would be asserting a
 * sync that cannot undo anything. **The variant is defined because `policy`
 * and `account` need the same shape and the third is what the design draws** —
 * ⚠️ **and it stays unused until the sync exists**, which is
 * [D-156](../../../docs/DECISION_REGISTER.md) ④: *a state whose business rule
 * is missing is not built at all.*
 */
export type FieldOrigin = 'yours' | 'account' | 'policy' | 'directory';

const LABELS: Record<FieldOrigin, string> = {
  yours: 'Yours',
  // ⚡ **Not *From directory*.** Work email is locked because changing it
  // creates a new sign-in identity (§13, Better Auth is the sole
  // Authentication Authority) — a real rule, and a different one from a sync.
  account: 'Sign-in identity',
  policy: 'Organization policy',
  directory: 'From directory',
};

const TONES: Record<FieldOrigin, string> = {
  yours: 'bg-surface-sunken text-content-muted',
  account: 'bg-warning-subtle text-warning',
  policy: 'bg-warning-subtle text-warning',
  directory: 'bg-warning-subtle text-warning',
};

export interface FieldOriginTagProps {
  readonly origin: FieldOrigin;
  readonly className?: string;
}

export function FieldOriginTag({ origin, className }: FieldOriginTagProps) {
  return (
    <span
      className={cn(
        'inline-flex items-center rounded-sm px-1.5 py-0.5 text-xs font-medium',
        TONES[origin],
        className,
      )}
    >
      {LABELS[origin]}
    </span>
  );
}
