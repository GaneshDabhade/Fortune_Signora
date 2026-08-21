'use client';

import { Info } from 'lucide-react';
import Link from 'next/link';
import { useId, useState, type ReactNode } from 'react';

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
 * The disclosure expands **inline** rather than floating over the list. A
 * popover would need to trap focus, escape a scroll container and survive a
 * virtualised row; an inline region needs none of that and reads identically to
 * a screen reader. When M12.3 builds the evidence surface this becomes its
 * entry point rather than a second pattern to unify.
 *
 * ⚡ **The mark itself is {@link NameDispute}**, extracted so Company 360's
 * record header can carry it in the header's `status` slot — where §04 draws
 * the chips — without a second copy of the wording.
 *
 * ### Why `href` links the name and not the whole row
 *
 * A card-wide link is the larger target, and it would have to **contain** the
 * disclosure button — a control inside a link is invalid, unreachable by
 * keyboard in the order a reader expects, and activates the wrong thing on
 * touch. The alternative is an absolutely-positioned overlay with the button
 * raised above it, which trades a real structural problem for a stacking-order
 * one that breaks silently.
 *
 * Linking the name keeps the two controls siblings, gives the link the account
 * name as its accessible name for free, and is what every list a seller already
 * uses does.
 */
export function EntityName({
  identity,
  fallbackId,
  href,
  isLoading = false,
  className,
}: {
  identity: AccountIdentity | undefined;
  /** Shown when no source has named the account. **The real identifier, never
   * a placeholder** — a fabricated name is indistinguishable from a real one,
   * and being told the truth badly beats being told a fiction well. */
  fallbackId: string;
  /** Where this account's brief lives. Omitted on the brief itself — a link to
   * the page you are already on is a control that does nothing. */
  href?: string;
  /** While the identity request is in flight. **Reserves the same space the
   * name will occupy**, so the row does not rewrite itself under the reader —
   * a list that shifts costs more confidence than the extra moment saved. */
  isLoading?: boolean;
  className?: string;
}) {
  if (isLoading && !identity) {
    return <Skeleton className={cn('h-5 w-40', className)} />;
  }

  if (!identity?.name) {
    // Still reachable. An account nobody has named is exactly the one a seller
    // most wants to open, and withholding the link because the label is poor
    // would hide the page that explains why.
    return (
      <span className={cn('font-mono text-sm text-content-subtle', className)}>
        <Openable href={href}>
          {fallbackId.slice(0, 8)}
          <span className="sr-only"> — no source has named this account yet</span>
        </Openable>
      </span>
    );
  }

  return (
    <span className={cn('flex items-center gap-1.5', className)}>
      <span className="truncate text-md font-medium leading-6 text-content">
        <Openable href={href}>{identity.name}</Openable>
      </span>
      <NameDispute identity={identity} />
    </span>
  );
}

/**
 * ⚡ **The disputed-name disclosure, on its own.**
 *
 * 🔴 **Extracted so the record header and the list share ONE implementation** —
 * [§2](../../../CLAUDE.md), *behaviour exists exactly once.* 📁 Company 360's
 * title is a `string` on the approved `RecordHeader` (§04's `Title` role, which
 * truncates), **so the mark cannot travel inside the name any more** — it
 * travels in the header's `status` slot, beside the other chips the design
 * draws there. ⛔ **A second copy of the disclosure would have been a second
 * chance to word the explanation differently.**
 *
 * ⚠️ **Everything the original argued for is unchanged**: a real control rather
 * than a `title` attribute, `aria-expanded`, operable by Enter, Space and tap,
 * and the explanation **rendered whether or not it is open** so it is in the
 * accessibility tree and findable by browser search. ⛔ **Still not a popover**
 * — the note above says why, and none of those reasons stopped applying.
 *
 * ⛔ **Silent unless the sources actually disagree.** *"Everything is fine"* on
 * every row trains people to stop reading marks.
 */
export function NameDispute({ identity }: { identity: AccountIdentity }) {
  const detailId = useId();
  const [open, setOpen] = useState(false);

  if (identity.agreement !== 'disputed') return null;

  const explanation = `Your sources disagree on this name. Showing what ${identity.source} reported most recently, of ${identity.source_count} sources that named this account.`;

  return (
    // ⚡ **The explanation stacks under the mark rather than under the name.**
    // ⛔ **`min-w-0` and no fixed width**, so opening it inside a table cell
    // shrinks the disclosure rather than widening the row.
    <span className="inline-flex min-w-0 flex-col items-start gap-0.5">
      <button
        type="button"
        onClick={() => setOpen((was) => !was)}
        aria-expanded={open}
        aria-controls={detailId}
        /* ♿ 📁 §17 `2.5.8` — *"Targets ≥ 24px."* ⚠️ **A bare 14px glyph.**
           ⛔ **Not reachable by the Playground sweep** — no seeded account has
           a disputed name — **so it is measured from the markup rather than
           from a screenshot**, which is the only honest way to check a control
           the data cannot currently produce. */
        className={cn(
          'inline-flex min-h-6 min-w-6 shrink-0 items-center justify-center rounded text-content-subtle',
          'coarse:min-h-11 coarse:min-w-11',
          'transition-colors hover:text-content-muted',
        )}
      >
        <Info aria-hidden className="h-3.5 w-3.5" />
        <span className="sr-only">
          Sources disagree on this name. {open ? 'Hide' : 'Show'} details.
        </span>
      </button>

      <span
        id={detailId}
        className={cn(
          'text-xs font-normal leading-5 text-content-muted',
          open ? 'block' : 'sr-only',
        )}
      >
        {explanation}
      </span>
    </span>
  );
}

/**
 * Wraps a name in a link, or leaves it alone.
 *
 * A component rather than a ternary at each call site, so the two renderings
 * cannot drift — and so *"no href means no anchor"* stays true rather than
 * becoming a disabled-looking link somebody adds later.
 */
function Openable({ href, children }: { href?: string; children: ReactNode }) {
  if (!href) return <>{children}</>;
  return (
    <Link
      href={href}
      /* ♿ 📁 **Design System v2 §17 `2.5.8`** — *"Targets ≥ 24px."* ⚠️
       **Measured at `126 × 18`** on every row of the book of accounts: a link
         is as tall as its line box and nothing more. ⛔ **`min-h-6`, not
         padding** — padding here would push the name off the 44px row's optical
         centre, and the row height is one of the two numbers the Design Review
         names as why this product beats a CRM. */
      className="inline-flex min-h-6 items-center rounded transition-colors hover:text-accent coarse:min-h-11 "
    >
      {children}
    </Link>
  );
}
