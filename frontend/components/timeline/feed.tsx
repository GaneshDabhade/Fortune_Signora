'use client';

import { useMemo } from 'react';

import { Button } from '@/components/ui';
import type { TimelineEntry, TimelineEntryKind } from '@/lib/api/types';
import { cn } from '@/lib/design/cn';

/**
 * What has happened with this account.
 *
 * **The translation boundary, and the only place it exists.** The API sends
 * `observation_recorded` and structured detail; a seller reads *"Headcount
 * moved"*. ADR-0034 puts that translation at the presentation edge and keeps
 * it from travelling inward — which is why nothing here is stored, and why
 * improving a sentence is a deploy rather than a migration over immutable rows.
 *
 * ### Emphasis is presentation, and ranking is not
 *
 * The projection ranks nothing: it stores what happened, in time order, with no
 * opinion. **This component still has to make a busy feed readable**, and at a
 * thousand entries a wall of identical rows is unusable — which is a rendering
 * problem, not a reason to put a score in the database.
 *
 * So `PROMINENCE` below is a property of the *kind*, fixed for every account
 * and every workspace, applied at render time and stored nowhere. It changes
 * type size and nothing else: **no entry is hidden, reordered, or filtered
 * out.** A seller scanning a year of history sees the deal moving before they
 * see a headcount reading, and still sees both, in the order they happened.
 *
 * ### Days, because that is how people remember accounts
 *
 * Entries are grouped by the day they happened. *"Three things happened the
 * week they raised"* is the shape of the question; a flat list of timestamps
 * makes the reader do that grouping themselves on every read.
 */

type Prominence = 'lead' | 'normal' | 'quiet';

/**
 * How loudly each kind reads. **Static knowledge about the kind, never about
 * the account** — identical in every workspace, which is what keeps it a
 * phrasing decision rather than an inference.
 */
const PROMINENCE: Record<TimelineEntryKind, Prominence> = {
  opportunity_created: 'lead',
  opportunity_stage_changed: 'lead',
  business_event_detected: 'lead',
  signal_generated: 'normal',
  buying_score_updated: 'normal',
  observation_recorded: 'quiet',
  // A correction matters less than the thing it corrects, and burying it would
  // be the product hiding its own second thoughts. Quiet, never absent.
  observation_superseded: 'quiet',
  business_event_superseded: 'quiet',
  signal_superseded: 'quiet',
};

/**
 * What a seller reads. **Every sentence here is the customer's vocabulary**,
 * and none of it names a module, a table, an entity or a signal type.
 */
const HEADLINE: Record<TimelineEntryKind, string> = {
  opportunity_created: 'Opportunity opened',
  opportunity_stage_changed: 'Opportunity moved',
  business_event_detected: 'Something happened at this company',
  business_event_superseded: 'An earlier reading was corrected',
  signal_generated: 'New reason to pay attention',
  signal_superseded: 'A reason to pay attention was updated',
  buying_score_updated: 'Priority changed',
  observation_recorded: 'A detail changed',
  observation_superseded: 'A detail was corrected',
};

/**
 * The headline, which one kind cannot state on its own.
 *
 * **A hand-over is a workflow state whose stage did not move**, so it arrives
 * here as `opportunity.stage_changed` with both stages equal and would have
 * read *"Opportunity moved — Working it to Working it"*: a sentence that says
 * nothing twice, on the feed a seller uses to understand an account. Found by
 * asking what the new capability would project, rather than after somebody saw
 * it (LO-04).
 *
 * **No owner is named, and that is the feed's own rule rather than a gap.**
 * This surface answers *what happened to this account* and names nobody; *who
 * did what to whom* is the decision history's question, and it has the whole
 * state to answer it with. The reason is what a reader needs here, and it is
 * already on the wire.
 */
function headlineOf(entry: TimelineEntry): string {
  return isHandover(entry) ? 'Account handed over' : HEADLINE[entry.kind];
}

function isHandover(entry: TimelineEntry): boolean {
  return (
    entry.kind === 'opportunity_stage_changed' &&
    typeof entry.detail.previous_stage === 'string' &&
    entry.detail.previous_stage === entry.detail.new_stage
  );
}

function detailLine(entry: TimelineEntry): string | null {
  const d = entry.detail;
  const text = (key: string): string | null =>
    typeof d[key] === 'string' && d[key] ? String(d[key]) : null;

  switch (entry.kind) {
    case 'opportunity_stage_changed': {
      // The reason, because on a hand-over it is the entire content of the
      // entry — *"Ana is on leave until March"* is what a colleague opening
      // this account next week actually needs.
      if (isHandover(entry)) return text('reason');
      const from = text('previous_stage');
      const to = text('new_stage');
      return from && to ? `${humanise(from)} to ${humanise(to)}` : null;
    }
    case 'opportunity_created':
      return text('qualification') ? humanise(text('qualification') as string) : null;
    case 'business_event_detected':
    case 'business_event_superseded':
      return text('type_key') ? humanise(text('type_key') as string) : null;
    case 'signal_generated':
    case 'signal_superseded':
      return text('signal_type') ? humanise(text('signal_type') as string) : null;
    case 'buying_score_updated':
      return typeof d.score === 'number' ? `Now ${d.score} out of 100` : null;
    case 'observation_recorded':
    case 'observation_superseded':
      return text('attribute') ? humanise(text('attribute') as string) : null;
    default:
      return null;
  }
}

/** `funding_round` reads as *Funding round*. Engineering's keys, said aloud. */
function humanise(value: string): string {
  const spaced = value.replace(/[_-]+/g, ' ').trim();
  return spaced.charAt(0).toUpperCase() + spaced.slice(1);
}

function dayOf(iso: string): string {
  return new Date(iso).toLocaleDateString(undefined, {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  });
}

function timeOf(iso: string): string {
  return new Date(iso).toLocaleTimeString(undefined, { hour: '2-digit', minute: '2-digit' });
}

interface FeedProps {
  entries: readonly TimelineEntry[];
  hasMore: boolean;
  isLoading: boolean;
  isLoadingMore: boolean;
  isError: boolean;
  onLoadMore: () => void;
}

export function AccountHistory({
  entries,
  hasMore,
  isLoading,
  isLoadingMore,
  isError,
  onLoadMore,
}: FeedProps) {
  const days = useMemo(() => groupByDay(entries), [entries]);

  if (isError) {
    // Rendered rather than absent. A section that vanishes on failure reads as
    // a feature the customer does not have — the defect B-006 was.
    return (
      <p className="text-sm text-content-muted">
        This account&rsquo;s history could not be loaded. Try again in a moment.
      </p>
    );
  }

  if (isLoading) {
    return <p className="text-sm text-content-muted">Loading history&hellip;</p>;
  }

  if (entries.length === 0) {
    return (
      <p className="text-sm text-content-muted">
        Nothing has been recorded about this company yet. Anything Signora finds will appear
        here, most recent first.
      </p>
    );
  }

  return (
    <div className="flex flex-col gap-6">
      {days.map(([day, dayEntries]) => (
        <section key={day} className="flex flex-col gap-2">
          <h3 className="text-xs font-medium uppercase tracking-wide text-content-muted">
            {day}
          </h3>
          <ol className="flex flex-col gap-2">
            {dayEntries.map((entry) => (
              <li
                key={entry.id}
                className="flex items-baseline justify-between gap-4 border-l-2 border-border pl-3"
              >
                <div className="flex flex-col gap-0.5">
                  <span
                    className={cn(
                      'text-content',
                      PROMINENCE[entry.kind] === 'lead' && 'text-sm font-medium',
                      PROMINENCE[entry.kind] === 'normal' && 'text-sm',
                      PROMINENCE[entry.kind] === 'quiet' && 'text-xs text-content-muted',
                    )}
                  >
                    {headlineOf(entry)}
                  </span>
                  {detailLine(entry) ? (
                    <span className="text-xs text-content-muted">{detailLine(entry)}</span>
                  ) : null}
                </div>
                <time
                  className="shrink-0 text-xs text-content-muted"
                  dateTime={entry.occurred_at}
                >
                  {timeOf(entry.occurred_at)}
                </time>
              </li>
            ))}
          </ol>
        </section>
      ))}

      {hasMore ? (
        <Button variant="ghost" onClick={onLoadMore} disabled={isLoadingMore}>
          {isLoadingMore ? 'Loading…' : 'Show earlier activity'}
        </Button>
      ) : (
        // Said out loud rather than left to a scrollbar. A feed that simply
        // stops leaves a reader unsure whether they have seen everything.
        <p className="text-xs text-content-muted">That is the whole history.</p>
      )}
    </div>
  );
}

/** Newest day first, and newest within each day — the order the API returns. */
export function groupByDay(
  entries: readonly TimelineEntry[],
): Array<[string, TimelineEntry[]]> {
  const days = new Map<string, TimelineEntry[]>();
  for (const entry of entries) {
    const day = dayOf(entry.occurred_at);
    const bucket = days.get(day);
    if (bucket) bucket.push(entry);
    else days.set(day, [entry]);
  }
  return [...days.entries()];
}

export { HEADLINE, PROMINENCE, detailLine, headlineOf };
