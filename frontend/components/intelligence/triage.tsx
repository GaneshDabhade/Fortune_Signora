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
 */

'use client';

import Link from 'next/link';

import { cn } from '@/lib/design/cn';
import { withScope, type OwnerScope } from '@/lib/state/owner-scope';
import {
  RAISED_MEANING,
  RAISED_WORDS,
  withRaised,
  type Raised,
  type TriageGroup,
} from '@/lib/state/triage';

interface TriageStripProps {
  groups: TriageGroup[];
  /** Which question the list is currently narrowed to, if any. */
  active: Raised | null;
  /** Preserved on every link, so filtering never drops the seller's scope. */
  scope: OwnerScope;
}

export function TriageStrip({ groups, active, scope }: TriageStripProps) {
  // **Nothing at all when the list raises nothing**, rather than an empty
  // container with a heading. A reader who sees this strip knows before reading
  // it that something on the list needs a second look.
  if (groups.length === 0) {
    return null;
  }

  const base = withScope('/', scope);

  return (
    <nav aria-label="What these accounts are raising" className="flex flex-col gap-1">
      {groups.map(({ question, accounts }) => (
        <TriageLine
          key={question}
          question={question}
          count={accounts.length}
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
  count: number;
  active: boolean;
  href: string;
}

function TriageLine({ question, count, active, href }: TriageLineProps) {
  return (
    <Link
      href={href}
      aria-current={active ? 'true' : undefined}
      className={cn(
        'group flex items-baseline gap-2 rounded-md px-2 py-1.5 text-sm',
        'focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2',
        'focus-visible:outline-accent',
        active ? 'bg-surface-raised text-content' : 'text-content-muted hover:bg-surface-raised',
      )}
    >
      <span className="font-medium tabular-nums text-content">{count}</span>
      <span className={cn(active && 'font-medium')}>{RAISED_WORDS[question]}</span>
      {/* The sentence is what stops the label being guessed at, and a guess is
          where a filter starts being ignored. Muted rather than hidden behind a
          tooltip: a seller reading at a glance should not have to hover. */}
      <span className="text-content-subtle">{RAISED_MEANING[question]}</span>
    </Link>
  );
}
