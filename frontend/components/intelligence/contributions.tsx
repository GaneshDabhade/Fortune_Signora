'use client';

import { formatDay } from '@/components/intelligence/dates';
import { Badge } from '@/components/ui';
import type { AccountScore, Posture, ScoreContribution } from '@/lib/api/types';
import { cn } from '@/lib/design/cn';

/**
 * How Signora shows the arithmetic behind a score.
 *
 * **The account brief's whole reason to exist.** A ranked list can be built by
 * anyone; a number a customer can take apart, disagree with line by line, and
 * reproduce with a division is the thing no competitor's summary survives.
 *
 * Three rules govern everything here:
 *
 * **Nothing is calculated in the browser.** Every figure — the point total, the
 * ceiling, the per-posture split, which lines dissent — arrives computed. The
 * ledger exists so the arithmetic has exactly one implementation, and a screen
 * that re-derived any of it would quietly become a second.
 *
 * **Nothing is reworded.** `reason` is rendered by the pipeline from the same
 * fields an auditor checks. The screen places it; it never paraphrases it,
 * because a friendlier sentence that blurs two lines together makes the number
 * uncheckable against the record.
 *
 * **Nothing that counted is hidden.** A line worth zero points stays on the
 * page with the reason it counted nothing. A zero you can read is information;
 * a row that vanished is a mystery.
 */

const POSTURE_WORDING: Record<Posture, string> = {
  expansionary: 'Expansion',
  contractionary: 'Risk',
  neutral: 'Context',
};

/**
 * The score, and the two integers that produce it.
 *
 * **Shown as a division, not a gauge.** `68 of 120 points` is a claim a
 * customer can check on paper in four seconds; a filled ring is a claim about a
 * maximum that would have to be invented. This is the moment the product either
 * earns trust or asks for it, and asking is what every other tool does.
 */
export function ScoreArithmetic({ score }: { score: AccountScore }) {
  return (
    <div className="flex items-baseline gap-3">
      {/* **The number and its arithmetic are hidden from assistive technology
          and replaced by one sentence.** As two adjacent fragments they read
          out concatenated: Twilio's score of 1 beside its 2 points announced
          as *"attention score 12 of 120 points"* — a different number, stated
          confidently. A screen reader must never be able to report a figure
          the screen does not show. */}
      <span
        aria-hidden
        className="text-4xl font-semibold tabular-nums leading-none text-content"
      >
        {score.score}
      </span>
      <span aria-hidden className="text-sm tabular-nums text-content-muted">
        {score.points} of {score.ceiling} points
      </span>
      <span className="sr-only">
        Attention score {score.score} out of 100, from {score.points} of {score.ceiling}{' '}
        points.
      </span>
    </div>
  );
}

/**
 * How long this reading is correct for.
 *
 * A buying score is **a reading with a stated validity, not a live gauge** —
 * between the moment it was computed and `valid_until` it is exactly correct
 * rather than merely recent. Saying so is what separates Signora's number from
 * a dashboard metric that is silently a day old.
 *
 * `is_current` arrives from the server. Comparing a timestamp to the browser's
 * clock would make the answer depend on the reader's machine.
 */
export function ReadingValidity({ score }: { score: AccountScore }) {
  const until = score.valid_until ? formatDay(score.valid_until) : null;

  if (!score.is_current) {
    return (
      <p className="text-sm text-content-muted">
        This reading expired{until ? ` on ${until}` : ''}. It is shown as it stood —
        nothing has replaced it yet.
      </p>
    );
  }

  return (
    <p className="text-sm text-content-muted">
      {until
        ? `Exactly correct until ${until}, when the oldest evidence beneath it changes band.`
        : 'Nothing is contributing, so this cannot change until new evidence arrives.'}
    </p>
  );
}

/**
 * Attention split by what it implies commercially.
 *
 * **Deliberately never summed.** Two accounts can score identically and mean
 * opposite things; the scalar cannot carry that and this is the only place the
 * difference survives. Shown for every account rather than only contested ones,
 * because *"all of this is expansion"* is as much a finding as a split is.
 */
export function PostureSplit({ score }: { score: AccountScore }) {
  const present = (Object.keys(POSTURE_WORDING) as Posture[])
    .map((posture) => [posture, score.attention_by_posture[posture] ?? 0] as const)
    .filter(([, points]) => points > 0);

  if (present.length === 0) return null;

  return (
    <dl className="flex flex-wrap gap-x-6 gap-y-2">
      {present.map(([posture, points]) => (
        <div key={posture} className="flex items-baseline gap-1.5">
          <dt className="text-sm text-content-muted">{POSTURE_WORDING[posture]}</dt>
          <dd className="text-sm font-medium tabular-nums text-content">{points}</dd>
        </div>
      ))}
    </dl>
  );
}

/**
 * Every line that produced the score, in the order that explains it.
 *
 * Ordered largest-first by the pipeline, so the first line a reader sees is the
 * one that most explains the number. **The screen does not re-sort**: storage
 * order is the explanation's order, and re-ranking here would answer a
 * different question from the one the ledger recorded.
 */
export function ContributionList({
  score,
  onOpenEvidence,
}: {
  score: AccountScore;
  /** Opens the readings beneath a line. **Optional on purpose** — the ledger
   * renders identically without it, so a caller with nowhere to send the
   * reader draws no affordance rather than a dead one. */
  onOpenEvidence?: (businessEventId: string) => void;
}) {
  return (
    <ol className="flex flex-col">
      {score.contributions.map((line) => (
        <li
          key={`${line.business_event_id}:${line.signal_id}`}
          className="border-b border-border py-3 last:border-b-0"
        >
          <ContributionRow line={line} onOpenEvidence={onOpenEvidence} />
        </li>
      ))}
    </ol>
  );
}

function ContributionRow({
  line,
  onOpenEvidence,
}: {
  line: ScoreContribution;
  onOpenEvidence?: (businessEventId: string) => void;
}) {
  const reason = (
    <span
      className={cn(
        'text-sm leading-6',
        // An uncounted line is subordinate, never absent. It explains why
        // evidence a customer can see did not move the number, which is
        // the question they would otherwise ask support.
        line.counted ? 'text-content' : 'text-content-muted',
      )}
    >
      {line.reason}
    </span>
  );

  return (
    <div className="flex items-start gap-4">
      <div className="min-w-0 flex-1">
        <p>
          {onOpenEvidence ? (
            <button
              type="button"
              onClick={() => onOpenEvidence(line.business_event_id)}
              className={cn(
                'rounded text-left underline decoration-border underline-offset-4',
                'transition-colors hover:decoration-content-muted',
                'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent',
              )}
            >
              {reason}
              <span className="sr-only"> — show the provider readings behind this</span>
            </button>
          ) : (
            reason
          )}
        </p>
        {line.dissenting ? (
          <div className="mt-1.5">
            <Badge tone="accent">Disagrees with the majority reading</Badge>
          </div>
        ) : null}
      </div>

      <span
        className={cn(
          'w-10 shrink-0 pt-0.5 text-right text-sm font-medium tabular-nums',
          line.counted ? 'text-content' : 'text-content-subtle',
        )}
      >
        {line.points}
      </span>
    </div>
  );
}
