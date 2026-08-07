import { Lock } from 'lucide-react';
import type { ReactNode } from 'react';

import { cn } from '@/lib/design/cn';

export interface LockedFieldProps {
  label: string;
  /**
   * What the field would hold. Rendered as text rather than in a disabled
   * input, because a disabled input invites clicking and a customer who
   * clicks a locked control learns nothing.
   */
  value?: ReactNode;
  /**
   * **Why it is locked, and it is required.** The whole point of showing a
   * locked field rather than hiding it is the sentence beside the padlock;
   * a lock with no reason is worse than an absent field, because the
   * customer now knows something is missing and not why.
   */
  reason: string;
  className?: string;
}

/**
 * A setting that exists and cannot be changed here, shown rather than hidden.
 *
 * **The approved design states the rule and the reasoning**: *"Locked is
 * shown, not hidden — region and policy settings render as disabled fields
 * with a padlock and a reason. Removing them from the page makes
 * administrators think the product lost a feature."*
 *
 * ⛔ **Not an empty state.** `EmptyState` says *there is nothing here yet and
 * here is how to start*. This says *there is something here, it is real, and
 * you cannot change it from this screen* — opposite messages, and collapsing
 * them would tell an administrator to go looking for a control that does not
 * exist.
 *
 * ⚡ **It renders no value when none is known**, which is the honest case
 * while a capability is designed and unbuilt: the field is named, the reason
 * is given, and nothing is invented to fill the gap
 * ([P-A](../../../docs/DOMAIN_DISCOVERY_REGISTER.md) — an absent read must
 * never render as a real one).
 */
export function LockedField({ label, value, reason, className }: LockedFieldProps) {
  return (
    <div className={cn('flex flex-col gap-1', className)}>
      <div className="flex items-center gap-1.5">
        <span className="text-sm font-medium text-content">{label}</span>
        {/* Decorative: the reason below carries the meaning, so a screen
            reader that announced "lock" twice would be reading furniture. */}
        <Lock aria-hidden className="h-3.5 w-3.5 text-content-subtle" />
      </div>
      {value === undefined ? null : (
        <p className="text-sm text-content-muted">{value}</p>
      )}
      <p className="text-sm text-content-subtle">{reason}</p>
    </div>
  );
}
