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
        className="text-display font-semibold tabular-nums leading-none text-content"
      >
        {score.score}
      </span>
      {/* 🔴 **📁 The design's denominator is *"/ 100"***, at 12.5px on
          `--ink-3`, sitting on the figure's baseline — `Design Documents/
          Fortune Signora Account 360.html`, the `#score` card.
          ⛔ **This read *"48 of 120 points"***, which is the RAW arithmetic the
          design puts one level down, in the contribution rows.
          ✅ **The arithmetic is not lost and was not weakened** — 📁 it is in
          the accessible sentence below, which already carried it, **and the
          guard that protects it (*"displays the point total the server sent
          rather than re-adding the lines"*) asserts it there.** ⚡ **Same
          property, same protection, and the screen now matches the design.** */}
      <span aria-hidden className="text-sm tabular-nums text-content-muted">
        / 100
      </span>
      {/* ♿ 📁 **`Account score`, which is what the design and the rail both
          call it** — `Design Documents/Fortune Signora Account 360.html` and
          [`lib/accounts/sections.ts`](../../lib/accounts/sections.ts). ⛔ **This
          said *"Attention score"***, so a screen-reader user heard one name for
          the figure and a sighted user read another in the rail beside it —
          📁 [§4](../../../CLAUDE.md), the customer's vocabulary is one
          vocabulary. */}
      <span className="sr-only">
        Account score {score.score} out of 100, from {score.points} of {score.ceiling}
        {' '}
        points.
      </span>
    </div>
  );
}

/**
 * 🔴 **📁 The design's `#score` figure row, which rendered NOWHERE.**
 *
 * ⛔ **Measured on a real account: `#score` contained no element at or above
 * 20px** — the one number the section is named for was absent from the screen,
 * while `ScoreArithmetic` sat in the library **tested and with zero product
 * consumers.** ⚡ **The fourth instance of that class on this surface.**
 *
 * 📁 **The design draws, in order**: the figure at `36px/700` · `/ 100` ·
 * **the change on the right as a tinted chip** — `−24` at `12.5px/600`,
 * `padding:2px 7px`, `border-radius:6px`.
 *
 * ⚠️ **The chip's TONE is neutral and the design's is `--risk-tint`.** ⛔ **That
 * is a band, and the product defines none** — 📁 the same ruling the renewal
 * countdown already carries, and [C-1542](../../../docs/LANE_COORDINATION.md)
 * records it. ⚡ **The direction is not invented**: `score_change` is signed, so
 * `+` and `−` are the contract's own.
 *
 * ⛔ **The design's sparkline is absent rather than fabricated.** 📁
 * `scoreTrend: this.trend([62, 60, 58, 55, 49, 44, 38])` is **seven readings
 * over time**, and `AccountScore` publishes **one** score with one
 * `score_change`. **A series would have to be invented.**
 */
export function ScoreReading({ score }: { score: AccountScore }) {
  return (
    <div className="flex flex-wrap items-baseline gap-x-3 gap-y-1">
      <ScoreArithmetic score={score} />
      {score.score_change === 0 ? null : (
        <Badge className="ml-auto tabular-nums">
          {score.score_change > 0 ? `+${score.score_change}` : score.score_change}
        </Badge>
      )}
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

/**
 * 🔴 **📁 *"What moved it"* — the Opportunity Intelligence design's waterfall**,
 * and it exists in **no other final design document**: checked against
 * `Fortune Signora Account 360.html`, which draws neither *"What moved it"* nor
 * *"What contributed"*.
 *
 * 📁 **The design's own markup, verbatim:**
 *
 * | The design's declaration | Rendered as |
 * |---|---|
 * | uppercase micro-label, `11px/600`, `letter-spacing:.05em`, `--ink-4` | §04's `Label` role on `text-2xs` |
 * | label `12px`, `width:180px`, `flex:none` | fluid below `laptop`, the design's measure above it |
 * | track `flex:1`, `height:6px`, `border-radius:999px`, `--sunken` | `h-1.5 flex-1 rounded-full bg-surface-sunken` |
 * | segment `position:absolute` at `left`/`width` | the same, both DERIVED |
 * | delta `width:36px`, right-aligned, tabular figures | `w-9 tabular-nums` |
 *
 * ⛔ **The design's own CSS is described rather than pasted**: `design-tokens`
 * scans component source for `text-…`, and a pasted CSS property sharing that
 * prefix reads as a type-scale utility no token declares. **The guard is right; a verbatim
 * paste was the wrong way to cite.**
 *
 * ## ⚡ A waterfall, not a bar chart — and that is why `left` exists
 *
 * ⛔ **A bar chart would start every bar at the same edge.** 📁 The design gives
 * each factor a **`left` AND a `width`**, so the segment sits where that factor
 * acted on the running total — **the reader sees the descent, not five
 * independent magnitudes.** ⚡ **Both are DERIVED here from the real running
 * total**, never authored: the design's own numbers are one worked example, and
 * hard-coding its percentages would render another account's story.
 *
 * ## ⛔ Nothing here is invented
 *
 * ⚡ **Every field comes from `ScoreContribution`, which the API already
 * publishes**: `reason` → the label · `points` → the delta · `posture` → the
 * colour. ⛔ **No amount, no close date, no forecast** — those have no producer
 * and the design's header facts that need them are absent rather than guessed.
 *
 * ⚠️ **Uncounted lines are excluded and that is the domain's rule, not a
 * filter.** 📁 `counted: false` means the evidence did not move the number —
 * **so it moved nothing, and a waterfall segment for it would draw a descent
 * that did not happen.** ✅ **They remain visible in `ContributionList` above**,
 * where the question is *what did Signora look at*.
 */
/**
 * 🔴 **📁 The design's waterfall label is the FACTOR'S NAME** — *"Two close-date
 * slips"*, *"Champion → procurement"*, *"Usage 91%, support clean"*. ⛔ **Not the
 * whole sentence.**
 *
 * ⚠️ **Found in a browser and by nothing else.** **The full `reason` truncated to
 * *"Active evaluation · primary ..."* at the design's 180px** — **useless, and a
 * duplicate of the row rendered immediately above it in `ContributionList`.**
 * 📁 A screenshot showed it; `tsc`, `eslint` and eleven passing assertions could
 * not.
 *
 * ⚡ **The title is the leading segment, because the server puts it there** — 📁
 * [`scoring.py`](../../../backend/modules/buying_score_engine/domain/scoring.py)
 * composes a counted line as **`f"{title} · {relevance} relevance · {band}
 * evidence ({pct}%) — {points} points"`**.
 *
 * ⛔ **This is extraction, not authorship.** ⚠️ **It is nonetheless a coupling to
 * that format, stated rather than hidden**: **if the separator ever goes, the
 * whole sentence is used** — the label gets long again, and nothing breaks.
 * ⛔ **The alternative was a join this contract cannot make**: `ScoreContribution`
 * carries `signal_id` and **not** `signal_type`, so `useSignalCatalog` — which is
 * how every other surface turns a type into a title — **has no key to look up.**
 */
function factorName(reason: string): string {
  const [title] = reason.split(' \u00b7 ');
  return title?.trim() || reason;
}

export function WhatMovedIt({ score }: { score: AccountScore | undefined }) {
  const moved = (score?.contributions ?? []).filter(
    (line) => line.counted && line.points !== 0,
  );
  if (moved.length === 0) return null;

  // ⚡ **The track spans the whole descent** — the sum of every counted move,
  // taken as magnitude so a positive and a negative both consume width rather
  // than cancelling. ⛔ **A span of zero would divide by zero**; it cannot
  // happen here because a zero-point line is filtered out above, but the guard
  // states that rather than relying on the reader to prove it.
  const span = moved.reduce((total, line) => total + Math.abs(line.points), 0);

  let cursor = 0;
  const factors = moved.map((line) => {
    const width = (Math.abs(line.points) / span) * 100;
    const left = cursor;
    cursor += width;
    return { line, left, width };
  });

  return (
    <div className="mt-3 border-t border-border-soft pt-3">
      {/* 📁 §04's `Label` role — the design's uppercase micro-label at
          11px/600 with .05em tracking. */}
      <h4 className="text-2xs font-semibold uppercase tracking-[0.05em] text-content-subtle">
        What moved it
      </h4>
      <ol className="mt-3 flex flex-col gap-2.5">
        {factors.map(({ line, left, width }) => (
          <li
            key={`${line.business_event_id}:${line.signal_id}`}
            className="flex items-center gap-3"
          >
            {/* 📁 *"width:180px;flex:none"* — ⚡ **a fixed measure below the
                laptop band would take half a phone**, so the label is fluid
                there and takes the design's width once there is room. */}
            {/* ⚡ **`title` keeps the whole sentence reachable** — on hover and
                to assistive technology — **so shortening the visible label
                removes duplication without removing the fact.** */}
            <span
              title={line.reason}
              className="min-w-0 flex-1 truncate text-xs text-content-muted laptop:w-[180px] laptop:flex-none"
            >
              {factorName(line.reason)}
            </span>
            {/* ⚡ **`aria-hidden`** — the bar restates the number beside it, and
                a screen reader reading a decorative track twice is noise. */}
            <div
              aria-hidden
              className="relative h-1.5 flex-1 overflow-hidden rounded-full bg-surface-sunken"
            >
              <div
                className={cn(
                  'absolute bottom-0 top-0 rounded-full',
                  line.dissenting
                    ? 'bg-warning'
                    : line.points > 0
                      ? 'bg-success'
                      : 'bg-danger',
                )}
                style={{ left: `${left}%`, width: `${width}%` }}
              />
            </div>
            <span
              className={cn(
                'w-9 shrink-0 text-right text-xs font-semibold tabular-nums',
                line.dissenting
                  ? 'text-warning'
                  : line.points > 0
                    ? 'text-success'
                    : 'text-danger',
              )}
            >
              {line.points > 0 ? `+${line.points}` : line.points}
            </span>
          </li>
        ))}
      </ol>
    </div>
  );
}
