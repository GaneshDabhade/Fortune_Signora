'use client';

import { Info } from 'lucide-react';

import type { AccountIdentity } from '@/lib/api/types';
import { cn } from '@/lib/design/cn';

/**
 * How Signora renders a company. **The canonical one — every surface uses it.**
 *
 * An account's name is not a stored field. It is a `legal_name` claim, from a
 * provider, at a time, and providers can disagree — so this renders the name
 * *and*, when it matters, the fact that it is one of several.
 *
 * **The design rule is that agreement is invisible and disagreement is not.**
 * When sources agree, or when only one has spoken, the row shows a name and
 * nothing else: a marker on every row saying *"everything is fine"* is the
 * noise the attention list already refused, and it trains people to stop
 * reading markers. A disputed name is the one state worth a second of a
 * seller's attention, so it is the only one that gets a mark.
 *
 * **This is *prove it* applied to the most ordinary field on the screen.** A
 * competitor's list shows a company name as though it were a fact. Signora's
 * shows what it is: the newest of several claims, with who said what available.
 */
export function EntityName({
  identity,
  fallbackId,
  className,
}: {
  identity: AccountIdentity | undefined;
  /** Shown while the name is unknown. **The real account identifier, never a
   * placeholder** — a fabricated name would be indistinguishable from a real
   * one, and being told the truth badly beats being told a fiction well. */
  fallbackId: string;
  className?: string;
}) {
  if (!identity?.name) {
    return (
      <span
        className={cn('font-mono text-sm text-content-subtle', className)}
        title="No source has named this account yet"
      >
        {fallbackId.slice(0, 8)}
      </span>
    );
  }

  return (
    <span className={cn('inline-flex items-baseline gap-1.5', className)}>
      <span className="truncate font-medium text-content">{identity.name}</span>
      {identity.agreement === 'disputed' ? (
        <span
          className="inline-flex shrink-0 items-center text-content-subtle"
          title={`Your sources disagree on this name. Showing what ${identity.source} reported most recently, of ${identity.source_count} sources.`}
          aria-label="Sources disagree on this name"
        >
          <Info aria-hidden className="h-3.5 w-3.5" />
        </span>
      ) : null}
    </span>
  );
}
