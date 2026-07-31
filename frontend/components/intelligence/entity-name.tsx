'use client';

import { Info } from 'lucide-react';
import { useId, useState } from 'react';

import { Skeleton } from '@/components/ui';
import type { AccountIdentity } from '@/lib/api/types';
import { cn } from '@/lib/design/cn';

/**
 * How Signora renders a company. **The canonical one — every surface uses it.**
 *
 * An account's name is not a stored field. It is a `legal_name` claim, from a
 * provider, at a time, and providers can disagree — so this renders the name
 * *and*, when it matters, the fact that it is one of several.
 *
 * **Agreement is invisible; disagreement is not.** When sources agree, or when
 * only one has spoken, the row shows a name and nothing else: a marker on every
 * row saying *"everything is fine"* trains people to stop reading markers. A
 * disputed name is the one state worth a second of attention, so it is the only
 * one that gets a mark.
 *
 * ### Why the disclosure is a button and not a tooltip
 *
 * The first version put *"your sources disagree"* in a `title` attribute. That
 * is **invisible on touch, unreachable by keyboard, and a 500 ms delay away
 * from everyone else** — the one genuinely novel interaction in the product,
 * hidden in the weakest affordance the web has. The frontend foundation treats
 * an unreachable control as a *defect* rather than an enhancement (CLAUDE.md
 * §20c), so it is a real control: focusable, `aria-expanded`, operable by
 * Enter, Space and tap, and its content is in the accessibility tree whether or
 * not it is open.
 *
 * The disclosure expands **beneath** the name rather than floating over the
 * list. A popover would need to trap focus, escape a scroll container and
 * survive a virtualised row; an inline region needs none of that and reads
 * identically to a screen reader. When M12.3 builds the evidence surface this
 * becomes its entry point rather than a second pattern to unify.
 */
export function EntityName({
  identity,
  fallbackId,
  isLoading = false,
  className,
}: {
  identity: AccountIdentity | undefined;
  /** Shown when no source has named the account. **The real identifier, never
   * a placeholder** — a fabricated name is indistinguishable from a real one,
   * and being told the truth badly beats being told a fiction well. */
  fallbackId: string;
  /** While the identity request is in flight. **Reserves the same space the
   * name will occupy**, so the row does not rewrite itself under the reader —
   * a list that shifts costs more confidence than the extra moment saved. */
  isLoading?: boolean;
  className?: string;
}) {
  const detailId = useId();
  const [open, setOpen] = useState(false);

  if (isLoading && !identity) {
    return <Skeleton className={cn('h-5 w-40', className)} />;
  }

  if (!identity?.name) {
    return (
      <span className={cn('font-mono text-sm text-content-subtle', className)}>
        {fallbackId.slice(0, 8)}
        <span className="sr-only"> — no source has named this account yet</span>
      </span>
    );
  }

  const disputed = identity.agreement === 'disputed';
  const explanation = `Your sources disagree on this name. Showing what ${identity.source} reported most recently, of ${identity.source_count} sources that named this account.`;

  return (
    <span className={cn('flex flex-col gap-0.5', className)}>
      <span className="flex items-center gap-1.5">
        <span className="truncate text-[0.9375rem] font-medium leading-6 text-content">
          {identity.name}
        </span>

        {disputed ? (
          <button
            type="button"
            onClick={() => setOpen((was) => !was)}
            aria-expanded={open}
            aria-controls={detailId}
            className={cn(
              'inline-flex shrink-0 items-center rounded text-content-subtle',
              'transition-colors hover:text-content-muted',
              'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent',
            )}
          >
            <Info aria-hidden className="h-3.5 w-3.5" />
            <span className="sr-only">
              Sources disagree on this name. {open ? 'Hide' : 'Show'} details.
            </span>
          </button>
        ) : null}
      </span>

      {/* Rendered whether or not it is open, so the explanation is in the
          accessibility tree and findable by browser search — `hidden` removes
          it from both, which is the failure the `title` attribute had. */}
      {disputed ? (
        <span
          id={detailId}
          className={cn(
            'text-xs leading-5 text-content-muted',
            open ? 'block' : 'sr-only',
          )}
        >
          {explanation}
        </span>
      ) : null}
    </span>
  );
}
