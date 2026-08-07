'use client';

import { useState, type ComponentType, type ReactNode } from 'react';

import { cn } from '@/lib/design/cn';

export interface ErrorStateProps {
  icon?: ComponentType<{ className?: string }>;
  /** What failed, named as the region rather than as the system: §13 titles
   * its example *"Score trend unavailable"*, not *"Request failed"*. */
  title: string;
  /** What happened and — the half that is usually missing — **what is still
   * true**. §13: *"Everything else on this page is current as of 4 minutes
   * ago."* */
  description: string;
  /** The id an engineer can search for. §13 requires it be **copyable**, so
   * this component copies it rather than only rendering it. */
  correlationId?: string;
  /** §13's *"Retry"* — the first route out. */
  onRetry?: () => void;
  /** §13's second route, *"Ask what changed"*: offered *"when the failure is
   * a data question rather than an outage"*. ⛔ **Optional on purpose** — a
   * caller whose scoring service is down should not offer to explain it. */
  assistantAction?: ReactNode;
  className?: string;
}

/**
 * §13's third state, and the one that did not exist.
 *
 * **Design System v2 §13 names three** — empty, loading and error.
 * `EmptyState` and `Skeleton` were built; the error presentation was not, and
 * `ErrorBoundary` is not it: **a boundary is the mechanism that catches a
 * throw, and this is what the region shows afterwards.** The two compose —
 * a boundary renders one of these — and neither substitutes for the other.
 *
 * ### Scoped to the smallest failing region
 *
 * §13: *"Errors are scoped to the smallest failing region"*. So this is a
 * block that sits **where the failed content would have been**, not a page
 * takeover — and that is why `description` is asked to say what is *still*
 * current. ⚡ **A whole-page error tells a user nothing about which half of
 * the page to trust**, which is the failure mode the scoping rule exists to
 * prevent.
 *
 * ### Why the correlation id copies rather than displays
 *
 * ⚠️ **§13 says *copyable*, and a `<code>` element is not.** An id that must
 * be retyped from a screen is an id that reaches support with a transposed
 * character, and the first thing anybody does with a wrong id is conclude the
 * event was never logged. **The clipboard write can fail** — permissions, a
 * non-secure context — and it is reported rather than swallowed, because a
 * silent failure here produces a user who pastes the previous clipboard
 * contents into a support ticket.
 */
export function ErrorState({
  icon: Icon,
  title,
  description,
  correlationId,
  onRetry,
  assistantAction,
  className,
}: ErrorStateProps) {
  const [copied, setCopied] = useState<'idle' | 'done' | 'failed'>('idle');

  const copy = async () => {
    if (!correlationId) return;
    try {
      await navigator.clipboard.writeText(correlationId);
      setCopied('done');
    } catch {
      // Reported, not swallowed. The id stays on screen either way, so the
      // user's fallback is to select it by hand — which they can only choose
      // to do if they know the copy did not happen.
      setCopied('failed');
    }
  };

  return (
    <div
      // `alert` rather than `status`: this reports a failure the user did not
      // ask for and should hear about without moving focus here.
      role="alert"
      className={cn(
        'flex flex-col items-center justify-center gap-3 rounded-lg',
        'border border-danger-subtle bg-surface px-6 py-10 text-center',
        className,
      )}
    >
      {Icon ? <Icon className="h-8 w-8 text-danger" /> : null}
      <div className="flex flex-col gap-1">
        <p className="text-sm font-semibold text-content">{title}</p>
        <p className="mx-auto max-w-sm text-sm text-content-muted">{description}</p>
      </div>

      {onRetry ?? assistantAction ? (
        <div className="mt-1 flex items-center gap-2">
          {onRetry ? (
            <button
              type="button"
              onClick={onRetry}
              className={cn(
                'h-control-sm rounded border border-border-strong bg-surface px-3',
                'text-sm font-medium text-content transition-colors hover:bg-surface-sunken',
              )}
            >
              Retry
            </button>
          ) : null}
          {assistantAction}
        </div>
      ) : null}

      {correlationId ? (
        <button
          type="button"
          onClick={copy}
          className={cn(
            'mt-1 rounded px-2 py-1 font-mono text-2xs text-content-subtle',
            'transition-colors hover:bg-surface-sunken hover:text-content-muted',
          )}
        >
          {correlationId}
          <span className="ml-2 font-sans">
            {copied === 'done' ? 'Copied' : copied === 'failed' ? 'Copy failed' : 'Copy'}
          </span>
        </button>
      ) : null}
    </div>
  );
}
