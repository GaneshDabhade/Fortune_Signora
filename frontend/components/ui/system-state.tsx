import type { ReactNode } from 'react';

import { cn } from '@/lib/design/cn';
import { CopyableId } from './copyable-id';
import {
  IllegalScopeError,
  SEVERITY,
  isLegal,
  type Scope,
  type Severity,
  type SystemStateName,
} from '@/lib/system-states/ladder';

/**
 * **The one presentation of a system state** — [TASK-1409](../../../docs/BACKLOG.md),
 * against `docs/design-snapshot/screens/Fortune Signora System States.dc.html`
 * ([D-138](../../../docs/DECISION_REGISTER.md)).
 *
 * ## ⛔ What this is not
 *
 * ⚠️ **It is not [`EmptyState`](./empty-state.tsx), and the two must never
 * merge.** 📁 **[TASK-445](../../../docs/BACKLOG.md) built *stated absence*:
 * *"there is nothing"*. A system state says *"something failed"*.**
 * ⚡ **Conflating them is how a broken widget renders as an empty one** — a
 * seller reads *"No signals"* and believes the quiet queue, when in truth
 * Signora could not look.
 *
 * ⚡ **`empty-result` appears in the ladder anyway, at region scope**, because
 * the ladder must enumerate what is *legal* there — but it is
 * `EmptyState` that renders it. **The ladder classifies; it does not
 * monopolise.**
 *
 * ## 📁 The grammar, and it is four rules
 *
 * **① One illustration language** — *"a 44px rounded tile with a single
 * line-weight glyph, tinted to the severity. No spot illustrations, no
 * mascots, no oversized numerals — a 404 with a giant `404` tells you what a
 * machine knows, not what you need."*
 *
 * **② Severity picks the colour**, and 📁 *"the colour is never
 * decorative."* ⛔ It comes from {@link SEVERITY}, keyed by the state — never
 * from the scope, and never from the caller.
 *
 * **③ Identifiers are copyable** — *"the single thing that makes a support
 * conversation short."*
 *
 * **④ One primary action** — *"and it does the most likely useful thing
 * rather than `reload`."*
 *
 * ## ♿ Focus and announcement are decided by scope, not by the caller
 *
 * 📁 **`2.4.3`**: *"A page-level state moves focus to its heading. A
 * region-level state does not steal focus from what the person was doing."*
 * 📁 **`4.1.3`**: *"Region errors and retries announce politely. Only a state
 * that ends the session — 500, maintenance — announces assertively, once."*
 *
 * ⚡ **Both are derived here rather than passed in**, because a caller free to
 * choose will eventually choose the polite one for an outage and the rude one
 * for a widget.
 */

/** 📁 The grammar's severity → token map. ⛔ Tokens only, never a literal (§20c). */
const TINT: Record<Severity, { tile: string; glyph: string }> = {
  neutral: { tile: 'bg-surface-sunken border-border', glyph: 'text-content-subtle' },
  warn: { tile: 'bg-warning-subtle border-warning/30', glyph: 'text-warning' },
  risk: { tile: 'bg-danger-subtle border-danger/30', glyph: 'text-danger' },
  brand: { tile: 'bg-accent-subtle border-accent/30', glyph: 'text-accent' },
  positive: { tile: 'bg-success-subtle border-success/30', glyph: 'text-success' },
};

export interface SystemStateProps {
  /** Where on the ladder this failure claims its surface. */
  scope: Scope;
  /** ⛔ Must be a state `scope` owns — the component throws otherwise. */
  state: SystemStateName;
  /**
   * 📁 **`1.3.1`**: *"an h1 that names what happened — not 'Error' and not the
   * status code."* ⚡ **So this is prose, and the caller cannot pass `"404"`
   * meaningfully** — the design's own example is *"This account no longer
   * exists"*.
   *
   * ⚠️ **Optional at REGION scope only, and required everywhere else** —
   * [TASK-1428](../../../docs/BACKLOG.md). 📁 **`1.3.1` governs *"every
   * full-page state"***, and a region is not one. **A region failure inside a
   * card is one sentence**, which is what
   * [`stated-absence.tsx`](../feedback/stated-absence.tsx) has rendered across
   * nine call sites since [P-A](../../../docs/DOMAIN_DISCOVERY_REGISTER.md) —
   * ⛔ **splitting it into a heading and a body to satisfy this prop would
   * change text the row requires unchanged.**
   */
  title?: string;
  /**
   * 📁 **`3.3.1`**: *"Failures name the cause, the scope, what survived, and
   * the identifier — in that order, in text, not in a tooltip."*
   */
  description: string;
  /** 📁 *"the most likely useful thing rather than 'reload'"*. */
  primaryAction?: ReactNode;
  /** 📁 *"Secondary routes are outlined; a third option is a text link or nothing at all."* */
  secondaryAction?: ReactNode;
  /** 📁 *"Any state produced by a failure carries a copyable correlation ID."* */
  correlationId?: string;
  /** A lucide-react glyph, or any component taking `className`. */
  glyph?: React.ComponentType<{ className?: string }>;
  className?: string;
}

/**
 * 📁 **`4.1.3`** — only a state that ends the session announces assertively.
 * ⛔ **A region error interrupting a screen reader mid-sentence is the defect
 * this prevents**, and it is not the caller's call.
 */
function politeness(scope: Scope): { role: 'alert' | 'status'; live: 'assertive' | 'polite' } {
  return scope === 'app' || scope === 'platform'
    ? { role: 'alert', live: 'assertive' }
    : { role: 'status', live: 'polite' };
}

export function SystemState({
  scope,
  state,
  title,
  description,
  primaryAction,
  secondaryAction,
  correlationId,
  glyph: Glyph,
  className,
}: SystemStateProps) {
  // ⛔ **The ladder's refusal, at the only place it can be enforced.** A
  // silent downgrade would render something plausible and ship the mistake.
  if (!isLegal(scope, state)) throw new IllegalScopeError(scope, state);

  const severity = SEVERITY[state];
  const tint = TINT[severity];
  const { role, live } = politeness(scope);

  // 📁 **`2.4.3`** — a page-level state moves focus to its heading; a region
  // one does not. `tabIndex={-1}` makes the heading focusable without
  // putting it in the tab order.
  const pageLevel = scope !== 'region';
  const Heading = pageLevel ? 'h1' : 'p';

  // ⛔ **A page-level state without a heading is `1.3.1`'s exact defect.**
  // Loud in development rather than rendered headless.
  if (pageLevel && title === undefined && process.env.NODE_ENV !== 'production') {
    throw new Error(`A ${scope}-scope state needs a title that names what happened (1.3.1).`);
  }

  return (
    <div
      role={role}
      aria-live={live}
      data-scope={scope}
      data-state={state}
      data-severity={severity}
      className={cn(
        'flex flex-col items-start gap-3 rounded-lg border border-border bg-surface p-6',
        pageLevel && 'items-center px-6 py-12 text-center',
        className,
      )}
    >
      {/* 📁 ① — 44px rounded tile, one glyph, tinted to severity. ⛔ Never a
          numeral: *"a 404 with a giant 404 tells you what a machine knows"*. */}
      <span
        aria-hidden
        className={cn(
          'flex h-11 w-11 shrink-0 items-center justify-center rounded-lg border',
          tint.tile,
        )}
      >
        {Glyph ? <Glyph className={cn('h-5 w-5', tint.glyph)} /> : null}
      </span>

      <div className={cn('flex flex-col gap-1', pageLevel && 'items-center')}>
        {title === undefined ? null : (
        <Heading
          // ♿ Focus target for a page-level state, inert for a region one.
          {...(pageLevel ? { tabIndex: -1 } : {})}
          className={cn(
            'font-semibold text-content',
            pageLevel ? 'text-xl tracking-tight' : 'text-sm',
          )}
        >
          {title}
        </Heading>
        )}
        <p className={cn('text-sm leading-6 text-content-muted', pageLevel && 'max-w-md')}>
          {description}
        </p>
      </div>

      {primaryAction ?? secondaryAction ? (
        <div className="mt-1 flex flex-wrap items-center gap-3">
          {primaryAction}
          {secondaryAction}
        </div>
      ) : null}

      {/* 📁 ③ — copyable, and `CopyableId` owns how. */}
      {correlationId ? <CopyableId value={correlationId} /> : null}
    </div>
  );
}
