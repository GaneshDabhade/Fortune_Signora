'use client';

import { useState } from 'react';
import { ChevronDown, ChevronRight } from 'lucide-react';

import { formatDay } from '@/components/intelligence/dates';
import { EntityName } from '@/components/intelligence/entity-name';
import { Badge } from '@/components/ui';
import type { AccountIdentity, DecidedAccount, Stage } from '@/lib/api/types';

/**
 * *"Wait — what did I just dismiss?"* (**R4-04**)
 *
 * The attention list is open work and correctly leaves decided accounts out.
 * Until this section they were **unreachable from anywhere in the product**
 * once a reader navigated away, which made dismissal permanent in practice —
 * and a Sales Manager's answer to that was *"I'd tell my reps not to dismiss
 * anything."* A rep who will not dismiss produces no qualification-quality
 * signal at all, which is the one thing `dismissed` exists to capture.
 *
 * ### Three refusals
 *
 * **It is absent, not empty.** A workspace where nobody has decided anything
 * renders nothing here — no heading, no zero, no *"nothing yet"*. **D6**
 * rejected a *mine / everyone* filter because *"a control that always shows
 * the same thing teaches people to ignore controls"*, and that binds here: a
 * reader who never dismisses should never learn this exists.
 *
 * **It is closed by default.** The morning question is the list above; this is
 * a question asked occasionally and answered when asked. The count is on the
 * summary line so opening it is a decision rather than a look.
 *
 * **There is no undo button.** A dismissal is a recorded decision with a
 * reason. Un-recording it would edit history; reopening is a *transition* with
 * its own reason and its own actor, and the account's brief already offers
 * exactly that. A one-click undo would erase the distinction the module is
 * built on.
 *
 * ### And one thing it adds
 *
 * **The reason is on the row.** Every transition has required one since M12.3
 * and nothing has ever rendered one. It is the only place in Signora that
 * shows a customer their own judgement back to them, and it is what makes this
 * section worth opening rather than merely reachable.
 */
export function DecidedAccounts({
  accounts,
  identities,
  viewerId,
}: {
  accounts: DecidedAccount[];
  /** Keyed by account id, as `useAccountIdentities` returns them. */
  identities: Map<string, AccountIdentity> | undefined;
  viewerId: string | null;
}) {
  const [open, setOpen] = useState(false);

  if (accounts.length === 0) return null;

  const Chevron = open ? ChevronDown : ChevronRight;

  return (
    <section className="flex flex-col gap-2">
      <button
        type="button"
        onClick={() => setOpen(!open)}
        aria-expanded={open}
        className={[
          'inline-flex w-fit items-center gap-1.5 rounded py-1 text-sm',
          'text-content-muted transition-colors hover:text-content',
          'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent',
        ].join(' ')}
      >
        <Chevron aria-hidden className="h-4 w-4 shrink-0" />
        {accounts.length === 1
          ? '1 account you have decided about'
          : `${accounts.length} accounts you have decided about`}
      </button>

      {open ? (
        <ul className="flex flex-col gap-2">
          {accounts.map((account) => (
            <DecidedRow
              key={account.opportunity_id}
              account={account}
              identities={identities}
              viewerId={viewerId}
            />
          ))}
        </ul>
      ) : null}
    </section>
  );
}

/**
 * One decision: what it was, why, and the way back to the account.
 *
 * **Only the name is a link**, matching the attention row — a card-wide link
 * would have to contain the disputed-name disclosure the name carries, which
 * is invalid markup and lands in the wrong place in the keyboard order.
 * `EntityName` draws the link itself, so the row does not wrap one around it.
 */
function DecidedRow({
  account,
  identities,
  viewerId,
}: {
  account: DecidedAccount;
  identities: Map<string, AccountIdentity> | undefined;
  viewerId: string | null;
}) {
  const identity = identities?.get(account.account_id);

  return (
    <li className="flex flex-col gap-1 rounded-md border border-border bg-surface-raised px-4 py-3">
      <div className="flex flex-wrap items-baseline justify-between gap-x-4 gap-y-1">
        <EntityName
          identity={identity}
          fallbackId={account.account_id}
          href={`/accounts/${account.account_id}`}
        />

        <span className="flex items-center gap-2 text-xs text-content-subtle">
          <Outcome stage={account.stage} />
          {formatDay(account.decided_at)}
          {account.owner_id !== null && account.owner_id === viewerId ? ' · yours' : null}
        </span>
      </div>

      {/* **The customer's own words**, not a paraphrase and not a category.
          A reader deciding whether they were right needs the sentence they
          wrote, and a summary of it would be the product editing them. */}
      <p className="text-sm leading-5 text-content-muted">{account.reason}</p>
    </li>
  );
}

/**
 * What was decided, in the customer's vocabulary.
 *
 * **`dismissed` and `closed_lost` stay apart.** One says Signora should not
 * have surfaced this account and the other says it was worth pursuing and did
 * not close — collapsing them would destroy the only signal the platform gets
 * about its own qualification quality.
 *
 * `dismissed` is the only one marked, and it is marked `warning` rather than
 * `danger`: it is feedback about Signora, not something broken. The same rule
 * the attention row follows — the marked minority is the signal.
 */
const OUTCOME: Record<string, { label: string; tone: 'warning' | 'neutral' }> = {
  dismissed: { label: 'Not worth showing', tone: 'warning' },
  closed_lost: { label: 'Lost', tone: 'neutral' },
  closed_won: { label: 'Won', tone: 'neutral' },
};

function Outcome({ stage }: { stage: Stage }) {
  const outcome = OUTCOME[stage];
  if (outcome === undefined) return null;

  return <Badge tone={outcome.tone}>{outcome.label}</Badge>;
}
