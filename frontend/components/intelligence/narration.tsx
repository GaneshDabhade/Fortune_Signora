'use client';

import { formatDay } from '@/components/intelligence/dates';
import type { AccountNarration } from '@/lib/api/types';

/**
 * How Signora renders model-authored language.
 *
 * **The first generated content in the product**, and the design problem it
 * poses is not layout — it is whether a reader can tell which parts of the
 * screen a machine wrote and how far to trust them.
 *
 * Four rules, and each one is a refusal:
 *
 * **No un-cited sentence appears.** The API cannot return one — grounding
 * refuses it before storage — and this component would have nowhere to put it
 * if it did. There is no summary line, no headline, no "key takeaway": the one
 * sentence a reader looks at first must not be the one exempt from evidence.
 *
 * **Nothing is rewritten, reordered or joined.** The statements arrive in the
 * order they were written and are placed in that order. Joining them into a
 * paragraph would discard the mapping from claim to evidence, which is the only
 * reason to trust any of it.
 *
 * **Provenance is on the page, not behind a tooltip.** Which model, which
 * prompt, when. A customer reading generated language is entitled to know what
 * generated it *while they are reading it*, not after following a link nobody
 * follows.
 *
 * **Absence renders nothing at all.** An account with no narration shows no
 * panel — not an empty state. The brief explains itself without this; a box
 * saying *"no narration yet"* would advertise a gap rather than fill one, and
 * would appear on every account until a worker had caught up.
 */
export function NarrativeBlock({ narration }: { narration: AccountNarration }) {
  return (
    <section className="flex flex-col gap-3">
      <h2 className="text-sm font-semibold text-content">In plain language</h2>

      <div className="flex flex-col gap-3 rounded-md border border-border bg-surface-raised px-4 py-3.5">
        <ol className="flex flex-col gap-2.5">
          {narration.statements.map((statement, index) => (
            <li
              key={`${index}:${statement.evidence.join(',')}`}
              className="flex items-baseline justify-between gap-4"
            >
              <p className="text-[0.9375rem] leading-6 text-content">{statement.text}</p>
              <Grounding count={statement.evidence.length} />
            </li>
          ))}
        </ol>

        <Provenance narration={narration} />
      </div>
    </section>
  );
}

/**
 * How many recorded facts this sentence rests on.
 *
 * **Not a link, because nothing can be opened yet.** Evidence resolution is
 * M12.3's; a citation rendered as clickable and going nowhere costs more trust
 * than the missing feature does. What is honest today is the *count* — it says
 * the sentence is anchored without pretending the anchor is reachable, and it
 * becomes the affordance that opens the evidence the day there is any.
 *
 * Never zero: the API cannot produce an uncited statement.
 */
function Grounding({ count }: { count: number }) {
  return (
    <span className="shrink-0 whitespace-nowrap pt-0.5 text-xs tabular-nums text-content-subtle">
      {count} {count === 1 ? 'fact' : 'facts'}
    </span>
  );
}

/**
 * What wrote this, and the sentence that says what that does and does not mean.
 *
 * *"The model chose the words, not the facts."* — the whole of Signora's AI
 * claim, and the reason this product is not a summarizer. It is stated on every
 * narration rather than once in documentation, because the reader who needs it
 * is the one who has just been surprised by a sentence.
 */
function Provenance({ narration }: { narration: AccountNarration }) {
  return (
    <p className="border-t border-border pt-3 text-xs leading-5 text-content-subtle">
      Written by <span className="text-content-muted">{narration.model}</span> using{' '}
      <span className="text-content-muted">{narration.prompt}</span> on{' '}
      {formatDay(narration.generated_at)}. Every sentence is restricted to facts the
      pipeline computed —{' '}
      <span className="text-content-muted">the model chose the words, not the facts</span>
      .
    </p>
  );
}
