/**
 * What the attention list is asking, above the list that answers it.
 *
 * **Not a card, not a chart, not a counter.** The homepage retired an Overview
 * page of three permanently-empty counters at M12.3 (**D38**), and a strip of
 * KPI tiles would be that page returning in a smaller font. This is one line
 * per question the list actually raises, and nothing when it raises none.
 *
 * **It is a filter, not a summary.** A count a seller cannot act on is a
 * statistic; a count that narrows the list below it is a way of working. Each
 * line is a link, and the link travels in the URL beside the owner scope — so
 * the view survives a refresh, survives browser back, and can be opened in a
 * second tab as a different view.
 *
 * **The list keeps its order inside every question.** The attention ranking
 * decides what matters most; this decides nothing.
 *
 * ---
 *
 * ### SW-05 · recognition before reading
 *
 * **A seller scans before they read**, so the question line is built to be
 * recognised rather than parsed:
 *
 * ```
 *   count · question · who it is about        ← scanned in about a second
 *          the sentence explaining it          ← read only if the first line
 *                                                did not settle it
 * ```
 *
 * **The accounts are named on the line itself**, up to three, because *which
 * companies* is the fact a seller recognises fastest and the one that decides
 * whether they open the question at all. A count with no names is a number to
 * act on trust; three names is a decision.
 *
 * **Progressive disclosure, in one step rather than three.** There is no
 * expander here: the disclosure is the list below, which the line filters. An
 * accordion would put a second copy of the list inside a control that summarises
 * it, and a seller would then have two places to read the same rows.
 */

'use client';

import Link from 'next/link';

import { cn } from '@/lib/design/cn';
import { EmptyState } from '@/components/ui';
import type { AccountAttention, AccountIdentity } from '@/lib/api/types';
import { withScope, type OwnerScope } from '@/lib/state/owner-scope';
import {
  RAISED_MEANING,
  RAISED_WORDS,
  withRaised,
  type Raised,
  type TriageGroup,
} from '@/lib/state/triage';

/** How many companies a question names before it stops naming them.
 *
 * **Three, because a line has to be scanned rather than read.** A fourth name
 * pushes the line to wrap on a laptop, and a wrapped line is read rather than
 * recognised — which is the property this whole strip is optimising for. */
const NAMED = 3;

interface TriageStripProps {
  groups: TriageGroup[];
  /** Which question the list is currently narrowed to, if any. */
  active: Raised | null;
  /** Preserved on every link, so filtering never drops the seller's scope. */
  scope: OwnerScope;
  /** Names, where they have arrived. **The strip never waits for them** — the
   * count and the question are the decision, and blocking on a label would
   * trade the decision for the word. */
  identities?: Map<string, AccountIdentity>;
}

export function TriageStrip({ groups, active, scope, identities }: TriageStripProps) {
  // **Nothing at all when the list raises nothing**, rather than an empty
  // container with a heading. A reader who sees this strip knows before reading
  // it that something on the list needs a second look.
  if (groups.length === 0) {
    return null;
  }

  const base = withScope('/', scope);

  return (
    <nav aria-label="What these accounts are raising" className="flex flex-col gap-0.5">
      {groups.map(({ question, accounts }) => (
        <TriageLine
          key={question}
          question={question}
          accounts={accounts}
          identities={identities}
          active={active === question}
          // Clicking the active question clears it. A filter a seller cannot
          // switch off is a filter they will navigate away from.
          href={active === question ? base : withRaised(base, question)}
        />
      ))}
    </nav>
  );
}

interface TriageLineProps {
  question: Raised;
  accounts: AccountAttention[];
  identities?: Map<string, AccountIdentity>;
  active: boolean;
  href: string;
}

function TriageLine({ question, accounts, identities, active, href }: TriageLineProps) {
  const named = accounts
    .slice(0, NAMED)
    .map((one) => identities?.get(one.account_id)?.name)
    .filter((name): name is string => Boolean(name));
  const remaining = accounts.length - named.length;

  return (
    <Link
      href={href}
      aria-current={active ? 'true' : undefined}
      className={cn(
        'group flex flex-col gap-0.5 rounded-md px-2 py-1.5',
        'focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2',
        'focus-visible:outline-accent',
        active ? 'bg-surface-raised' : 'hover:bg-surface-raised',
      )}
    >
      <span className="flex flex-wrap items-baseline gap-x-2 gap-y-1 text-sm">
        <span className="font-medium tabular-nums text-content">{accounts.length}</span>
        <span className={cn('text-content', active && 'font-medium')}>
          {RAISED_WORDS[question]}
        </span>
        {named.length > 0 ? (
          <span className="text-content-muted">
            {/* **Which companies, on the line itself.** The fact a seller
                recognises fastest, and the one that decides whether they open
                the question at all. */}
            {named.join(' · ')}
            {remaining > 0 ? (
              <span className="text-content-subtle"> and {remaining} more</span>
            ) : null}
          </span>
        ) : null}
      </span>
      {/* The sentence is what stops the label being guessed at, and a guess is
          where a filter starts being ignored. Second line and subtle: read only
          when the first line did not settle it. */}
      <span className="text-xs text-content-subtle">{RAISED_MEANING[question]}</span>
    </Link>
  );
}

/**
 * A question the list no longer raises.
 *
 * **Not an error, and not "no results".** The evidence moved, which is the
 * product working.
 *
 * **It exists because the strip is absent-when-empty and the page is not.** A
 * shared link, a bookmark or browser-back can name a question nothing raises
 * any more: the strip correctly hides it, the *unfiltered* list is not empty so
 * the quiet state does not fire, and the list renders no rows at all. **A page
 * that renders nothing is indistinguishable from a broken one** (D36) — the
 * defect this page fixed once already, reintroduced by SW-03's filter and
 * closed here.
 */
export function NothingRaises({ raised, scope }: { raised: Raised; scope: OwnerScope }) {
  return (
    <EmptyState
      title={`Nothing is ${RAISED_WORDS[raised].toLowerCase()} any more`}
      description="The evidence has moved since this view was opened."
      action={
        <Link
          href={withScope('/', scope)}
          className="text-sm font-medium text-accent hover:text-accent-hover"
        >
          Show every account
        </Link>
      }
    />
  );
}
