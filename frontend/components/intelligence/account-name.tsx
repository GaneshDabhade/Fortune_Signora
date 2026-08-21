'use client';

import Link from 'next/link';

import { Skeleton } from '@/components/ui';
import { cn } from '@/lib/design/cn';

/**
 * **An account's name in a list row, or the space it will occupy** —
 * 🔴 [B-290](../../../docs/BUGS.md).
 *
 * ## ⛔ A read in flight is not an answer
 *
 * ⚠️ **Four surfaces rendered `name ?? 'Unnamed account'`**, and the identity
 * read is a **second** request that settles after the list does. **Measured on
 * Home: five rows read *"Unnamed account"* for over a second and then became
 * five real companies.** ⛔ **A reader was told a settled fact — *this account
 * has no name* — and then told a different one.**
 *
 * ⚡ **Same family as 📁 [P-A](../../../docs/DOMAIN_DISCOVERY_REGISTER.md)** —
 * *a failed read must never render as an empty result* — **one state along.**
 *
 * ## ⚠️ Why this is not `EntityName`
 *
 * 📁 **`entity-name.tsx` is *"the canonical one"* and already does this**,
 * including the skeleton and the reasoning for it. ⛔ **But it also decides the
 * type** — `text-md font-medium leading-6`, and a `font-mono` identifier for an
 * unnamed account — **and these four rows each carry their own role from the
 * design.** ⚡ **Adopting it would change the look of four surfaces inside a
 * defect fix**, which is the sweep [D-220](../../../docs/DECISION_REGISTER.md)
 * §10 warns against.
 *
 * ✅ **So this carries the LOADING rule and nothing else**, and the caller keeps
 * its own typography. ⛔ **The settled fallback is deliberately still the
 * caller's string**: 📁 `EntityName` shows the real identifier and these show
 * *"Unnamed account"*, and **choosing between two truthful copies is a product
 * decision** — recorded in B-290 rather than taken here.
 */
export function AccountName({
  name,
  pending,
  absent,
  href,
  className,
}: {
  /** ⛔ `null` means **the identity surface says nobody has named it** — not
   * that the answer has not arrived. That is `pending`. */
  name: string | null;
  pending: boolean;
  /** What to render when the read has settled and there is no name. */
  absent: string;
  /**
   * 🔴 **Where this account's record lives** — 📁 `Design Documents/Signora
   * Product Experience Map.html`: Account 360's entries are ***"row · search ·
   * citation · **signal** · deep link"***, and the Signal Center's own row
   * reads ***"the monitoring loop enters at the queue, **exits into
   * accounts**."***
   *
   * ⛔ **The exit did not exist.** The Signal Center rendered this name as
   * plain text, so a triager could disposition a signal and had no way to open
   * the company it was about — **an approved entry point that led nowhere.**
   *
   * ⚡ **Optional, because a name is not always a destination**: a row that is
   * already on the record it names must not link to itself, which is the same
   * rule `EntityName` states for the brief.
   */
  href?: string;
  className?: string;
}) {
  if (pending && name === null) {
    /* ⚡ **The width is a name's, not a guess**: a bar much shorter than the
       text it stands in for makes the row jump when the name lands, which is
       the reflow the skeleton exists to prevent. */
    return <Skeleton className={cn('inline-block h-4 w-32 align-middle', className)} />;
  }
  const label = name ?? absent;
  if (href === undefined) return <span className={className}>{label}</span>;

  return (
    // ⚡ **The same link treatment `EntityName` gives a name**, so one company
    // reads and behaves identically wherever it is offered.
    // ♿ 📁 §17 `2.5.8` — the 24px floor, as everywhere else.
    <Link
      href={href}
      className={cn(
        'inline-flex min-h-6 items-center rounded transition-colors hover:text-accent',
        'coarse:min-h-11',
        className,
      )}
    >
      {label}
    </Link>
  );
}
