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
/**
 * The account after this one in the ranked order.
 *
 * **Exported so the decision dialog and this nav agree.** *Next* is a single
 * rule — *next most pressing*, read from the same cached ranking the attention
 * list holds — and two places computing it separately is how a product ends up
 * offering a reader two different "next"s in one visit.
 *
 * `undefined` when this account is last, or is not on the list at all: a
 * dismissed account keeps its brief and loses its position (**D27**), and the
 * honest answer there is no next rather than the top of the list.
 */
export function nextInSequence(
  accounts: AccountAttention[],
  accountId: string,
): AccountAttention | undefined {
  const index = accounts.findIndex((account) => account.account_id === accountId);
  return index >= 0 ? accounts[index + 1] : undefined;
}

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
  const next = nextInSequence(accounts, accountId);

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
      /* ♿ 📁 §17 `2.5.8` — *"Targets ≥ 24px."* ⚠️ **Measured at `h:21` at every
         width from 320 to 1920** — a line box, and the last two controls on
         Company 360 under the floor. ⛔ **`min-h-6` rather than padding**: the
         pager sits on a hairline and padding would move it off the rhythm the
         design draws; a minimum grows the box a pointer lands in and leaves
         the type where it is. */
      className={[
        'inline-flex min-h-6 min-w-0 flex-1 items-center gap-1.5 rounded text-sm text-content-muted',
        'coarse:min-h-11',
        'transition-colors hover:text-content',
        forwards ? 'justify-end text-right' : '',
      ].join(' ')}
    >
      {forwards ? null : <ArrowLeft aria-hidden className="h-3.5 w-3.5 shrink-0" />}
      {forwards ? null : <Key hint="k" />}
      <span className="truncate">{name}</span>
      {forwards ? <Key hint="j" /> : null}
      {forwards ? <ArrowRight aria-hidden className="h-3.5 w-3.5 shrink-0" /> : null}
    </Link>
  );
}

/**
 * The key that does this, shown beside the thing it does.
 *
 * **`j` and `k` have moved through accounts since D41 and nothing has ever
 * said so.** A shortcut nobody knows about is functionality that exists and
 * delivers nothing — the same shape as a field on the wire that no screen
 * reads, in a different layer.
 *
 * **Beside the control, not in a help panel.** A shortcut is learned where it
 * is used; a keyboard-shortcuts dialog is read by people who already know
 * there are shortcuts to look for.
 *
 * **`aria-hidden`, deliberately.** The link's accessible name is the account
 * and its direction — a screen-reader user navigates by landmark and link, and
 * hearing *"k Snowflake Inc"* would make the name harder to hear, not easier.
 * The keycap is an affordance for the people who can see it.
 */
function Key({ hint }: { hint: 'j' | 'k' }) {
  return (
    <kbd
      aria-hidden
      className="hidden shrink-0 rounded border border-border px-1 font-sans text-2xs leading-4 text-content-subtle phone:inline"
    >
      {hint}
    </kbd>
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
