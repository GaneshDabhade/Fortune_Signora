'use client';

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
  className,
}: {
  /** ⛔ `null` means **the identity surface says nobody has named it** — not
   *  that the answer has not arrived. That is `pending`. */
  name: string | null;
  pending: boolean;
  /** What to render when the read has settled and there is no name. */
  absent: string;
  className?: string;
}) {
  if (pending && name === null) {
    /* ⚡ **The width is a name's, not a guess**: a bar much shorter than the
       text it stands in for makes the row jump when the name lands, which is
       the reflow the skeleton exists to prevent. */
    return <Skeleton className={cn('inline-block h-4 w-32 align-middle', className)} />;
  }
  return <span className={className}>{name ?? absent}</span>;
}
