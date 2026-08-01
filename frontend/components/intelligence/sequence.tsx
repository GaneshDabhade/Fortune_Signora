'use client';

import { ArrowLeft, ArrowRight } from 'lucide-react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useEffect } from 'react';

import type { AccountAttention, AccountIdentity } from '@/lib/api/types';

/**
 * Moving through the list rather than back to it.
 *
 * **Where the morning's momentum stopped.** The brief had exactly one exit —
 * *All accounts* — so a seller working twelve accounts made twenty-four
 * navigations, and each return scrolled the list back to row 1 and left them
 * hunting for where they had been (**R10-01**, **D41**).
 *
 * Every product built for people who live in it all day lets you reach the
 * next item without returning to the list, because returning is where
 * attention leaks.
 *
 * ### It costs no request
 *
 * `useAccounts` is the same query with the same cache key the attention page
 * holds, so the brief reads the order rather than fetching it. **The order is
 * the ranking**, which means *next* is *next most pressing* — the sequence a
 * seller is actually working.
 *
 * ### It is honest when the account has left the list
 *
 * Dismiss an account and it is no longer open work, so it is no longer on the
 * list — but its brief survives (**D27**). The sequence says it has no
 * position rather than inventing one.
 */
export function AccountSequence({
  accountId,
  accounts,
  identities,
}: {
  accountId: string;
  /** The attention list, in ranked order. Empty while it loads. */
  accounts: AccountAttention[];
  identities: Map<string, AccountIdentity> | undefined;
}) {
  const index = accounts.findIndex((account) => account.account_id === accountId);
  const previous = index > 0 ? accounts[index - 1] : undefined;
  const next = index >= 0 ? accounts[index + 1] : undefined;

  useAccountKeys({
    previous: previous?.account_id,
    next: next?.account_id,
  });

  if (accounts.length === 0) return null;

  return (
    <nav
      aria-label="Move through your accounts"
      className="flex items-center justify-between gap-4 border-t border-border pt-4"
    >
      <Step account={previous} identities={identities} direction="previous" />
      <span className="shrink-0 text-xs tabular-nums text-content-subtle">
        {/* An account that has left the list keeps its brief and loses its
            place. Saying so beats inventing a position it no longer has. */}
        {index >= 0 ? `${index + 1} of ${accounts.length}` : 'No longer on your list'}
      </span>
      <Step account={next} identities={identities} direction="next" />
    </nav>
  );
}

/**
 * One end of the sequence.
 *
 * **Named, not numbered.** *"Next: Snowflake Inc."* tells a reader where they
 * are going; *"Next →"* asks them to find out by arriving. The name is the
 * whole value of putting this on the brief rather than a back link.
 */
function Step({
  account,
  identities,
  direction,
}: {
  account: AccountAttention | undefined;
  identities: Map<string, AccountIdentity> | undefined;
  direction: 'previous' | 'next';
}) {
  // A disabled control at the end of a list teaches a reader that controls
  // here can be dead. An empty slot keeps the position centred and says
  // nothing.
  if (account === undefined) return <span className="min-w-0 flex-1" />;

  const name =
    identities?.get(account.account_id)?.name ?? `${account.account_id.slice(0, 8)}`;
  const forwards = direction === 'next';

  return (
    <Link
      href={`/accounts/${account.account_id}`}
      className={[
        'inline-flex min-w-0 flex-1 items-center gap-1.5 rounded text-sm text-content-muted',
        'transition-colors hover:text-content',
        'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent',
        forwards ? 'justify-end text-right' : '',
      ].join(' ')}
    >
      {forwards ? null : <ArrowLeft aria-hidden className="h-3.5 w-3.5 shrink-0" />}
      <span className="truncate">{name}</span>
      {forwards ? <ArrowRight aria-hidden className="h-3.5 w-3.5 shrink-0" /> : null}
    </Link>
  );
}

/**
 * `j` and `k`, the convention every list-with-detail product uses.
 *
 * **They must never fire while somebody is typing.** A reason field containing
 * `jkjk` instead of a sentence would be the product eating the customer's
 * words — and the workflow reason is the one piece of text in Signora that
 * nothing can reproduce if it is lost.
 */
function useAccountKeys({ previous, next }: { previous?: string; next?: string }) {
  const router = useRouter();

  useEffect(() => {
    const handle = (event: KeyboardEvent) => {
      if (event.metaKey || event.ctrlKey || event.altKey) return;

      const target = event.target as HTMLElement | null;
      const typing =
        target?.isContentEditable === true ||
        ['INPUT', 'TEXTAREA', 'SELECT'].includes(target?.tagName ?? '');
      // The decision dialog is a native `<dialog>`; while one is open the
      // reader is answering a question, not navigating.
      if (typing || document.querySelector('dialog[open]') !== null) return;

      const to = event.key === 'j' ? next : event.key === 'k' ? previous : undefined;
      if (to === undefined) return;

      event.preventDefault();
      router.push(`/accounts/${to}`);
    };

    window.addEventListener('keydown', handle);
    return () => window.removeEventListener('keydown', handle);
  }, [previous, next, router]);
}
