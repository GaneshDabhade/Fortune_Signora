'use client';

import { useState } from 'react';

import { formatDay } from '@/components/intelligence/dates';
import { Badge, Dialog } from '@/components/ui';
import type { AccountNarration, EvidenceFact } from '@/lib/api/types';

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
 *
 * ### Since D42, the citations open
 *
 * *"3 facts"* was a count for two milestones because there was nowhere for it
 * to go. It is now the affordance, and it opens **what the model was actually
 * given** — not a record fetched afterwards, which would be a summary vouching
 * for a summary.
 */
export function NarrativeBlock({ narration }: { narration: AccountNarration }) {
  const [open, setOpen] = useState<string[] | null>(null);
  const facts = new Map(narration.facts.map((fact) => [fact.token, fact]));

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
              <Grounding
                tokens={statement.evidence}
                resolvable={statement.evidence.some((token) => facts.has(token))}
                onOpen={() => setOpen(statement.evidence)}
              />
            </li>
          ))}
        </ol>

        <Provenance narration={narration} />
      </div>

      <FactsDialog
        tokens={open}
        facts={facts}
        unchanged={narration.evidence_unchanged}
        writtenOn={narration.generated_at}
        onClose={() => setOpen(null)}
      />
    </section>
  );
}

/**
 * How many recorded facts this sentence rests on — and, now, the way to read them.
 *
 * **A button only when something opens.** A citation drawn as clickable and
 * going nowhere costs more trust than the missing feature does, which is why
 * this was a bare count until D42. When the evidence cannot be re-derived —
 * a closed opportunity has no current explanation (**D27**) — it goes back to
 * being a count, because the sentence is still anchored even though the anchor
 * is momentarily out of reach.
 *
 * Never zero: the API cannot produce an uncited statement.
 */
function Grounding({
  tokens,
  resolvable,
  onOpen,
}: {
  tokens: string[];
  resolvable: boolean;
  onOpen: () => void;
}) {
  const label = `${tokens.length} ${tokens.length === 1 ? 'fact' : 'facts'}`;

  if (!resolvable) {
    return (
      <span className="shrink-0 whitespace-nowrap pt-0.5 text-xs tabular-nums text-content-subtle">
        {label}
      </span>
    );
  }

  return (
    <button
      type="button"
      onClick={onOpen}
      className={[
        'shrink-0 whitespace-nowrap rounded pt-0.5 text-xs tabular-nums',
        'text-content-muted underline decoration-dotted underline-offset-4',
        'transition-colors hover:text-content',
        'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent',
      ].join(' ')}
    >
      {label}
    </button>
  );
}

/**
 * What the model was given, for one sentence.
 *
 * **A modal for the same reason the evidence drawer is one** — it is a
 * different subject reached from the middle of a long page, and inlining it
 * would push everything below out from under the reader's finger. Escape
 * closes it and you are exactly where you were, which R10-05 recorded as the
 * bar every transition in this product is measured against.
 */
function FactsDialog({
  tokens,
  facts,
  unchanged,
  writtenOn,
  onClose,
}: {
  tokens: string[] | null;
  facts: Map<string, EvidenceFact>;
  unchanged: boolean;
  writtenOn: string;
  onClose: () => void;
}) {
  const resolved = (tokens ?? [])
    .map((token) => facts.get(token))
    .filter((fact): fact is EvidenceFact => fact !== undefined);

  return (
    <Dialog
      open={tokens !== null}
      onClose={onClose}
      title="What this sentence rests on"
      description="The facts the model was given, in the words of the part of Signora that computed them."
    >
      <div className="flex flex-col gap-3">
        {resolved.map((fact) => (
          <Fact key={fact.token} fact={fact} />
        ))}

        {!unchanged ? (
          // **Said here rather than on the panel.** A reader who has opened a
          // citation is checking something; that is the moment the difference
          // between *what was true then* and *what is true now* matters.
          <p className="border-t border-border pt-3 text-xs leading-5 text-content-muted">
            The evidence behind this account has changed since {formatDay(writtenOn)}.
            These sentences describe what was true when they were written — a narration is
            never rewritten to catch up.
          </p>
        ) : null}
      </div>
    </Dialog>
  );
}

/** One fact: what it is, what it says, and the figures underneath. */
function Fact({ fact }: { fact: EvidenceFact }) {
  const attributes = Object.entries(fact.attributes);

  return (
    <div className="flex flex-col items-start gap-1.5">
      <Badge tone="neutral">{KIND_WORDING[fact.kind] ?? fact.kind}</Badge>
      <p className="text-sm leading-6 text-content">{fact.summary}</p>
      {attributes.length > 0 ? (
        <dl className="flex flex-wrap gap-x-4 gap-y-1 text-xs text-content-subtle">
          {attributes.map(([name, value]) => (
            <div key={name} className="flex gap-1.5">
              <dt>{name.replaceAll('_', ' ')}</dt>
              <dd className="tabular-nums text-content-muted">{value}</dd>
            </div>
          ))}
        </dl>
      ) : null}
    </div>
  );
}

/**
 * What each cited kind is called, in a seller's words.
 *
 * **A translation, never a paraphrase** — each maps to exactly one kind the
 * pipeline emits, so what a reader saw can be checked against the citation. An
 * unrecognised kind renders its raw key rather than being hidden: a new kind
 * arriving is something a reader should see, not something the browser should
 * quietly swallow.
 */
const KIND_WORDING: Record<string, string> = {
  opportunity: 'The commitment',
  buying_score: 'The score',
  signal_contribution: 'A hypothesis',
};

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
