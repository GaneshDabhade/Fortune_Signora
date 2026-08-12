'use client';

import { useState } from 'react';

import { formatDay } from '@/components/intelligence/dates';
import { StatedAbsence } from '@/components/feedback/stated-absence';
import { AttributionStrip, Badge, Dialog, SkeletonText } from '@/components/ui';
import { skeletonRows } from '@/lib/accounts/section-state';
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
 * ### Since D42, the citations open
 *
 * *"3 facts"* was a count for two milestones because there was nowhere for it
 * to go. It is now the affordance, and it opens **what the model was actually
 * given** — not a record fetched afterwards, which would be a summary vouching
 * for a summary.
 *
 * ### Absence used to render nothing at all — B-010
 *
 * The original rule was *"a box saying no narration yet would advertise a gap
 * rather than fill one, and would appear on every account until a worker had
 * caught up."* **The reasoning was sound and the outcome was not**: a reviewer
 * opened twelve briefs, found no explanation on any of them, and could not tell
 * whether the feature was broken or simply had nothing to say. It was broken.
 *
 * **Three states used to be one blank space**, and they are now three sentences:
 * *nothing has been written yet* · *this did not load* · *this was written
 * against evidence that has since moved*. The panel is still quiet — a line of
 * muted text, never an illustrated empty state — because the objection to
 * advertising a gap was right about **volume** and wrong about **silence**.
 */
export function NarrativeBlock({
  narration,
  notNarrated = false,
  isError = false,
  /**
   * ⚡ **The design's section id, so the *"On this page"* rail can anchor
   * this** — [TASK-1476](../../../docs/BACKLOG.md). ⛔ **Optional, because a
   * component does not get to assume it is a whole section of a screen**: the
   * page owns the map and passes the id it uses.
   */
  id,
  /**
   * 📁 ***"…then retry plus a correlation ID."*** ⚡ **The API already returns
   * one on every failure and no section passed it** —
   * [TASK-1476](../../../docs/BACKLOG.md). ⛔ **A reader who reports *"it
   * failed"* with no reference makes the failure unfindable in a log that
   * already recorded it.**
   */
  correlationId,
}: {
  /** Undefined while in flight, and while either flag below is set. */
  narration: AccountNarration | undefined;
  /** Signora has never written one for this account — the request 404'd.
   * **A real answer, not a failure**, and worded so a reader can tell. */
  notNarrated?: boolean;
  id?: string;
  correlationId?: string;
  /** The request failed for any other reason. */
  isError?: boolean;
}) {
  const [open, setOpen] = useState<string[] | null>(null);

  if (narration === undefined) {
    if (notNarrated) return <Aside id={id}>{NOT_WRITTEN}</Aside>;
    // ⛔ **The error state keeps the section and its id.** ⚠️ It used to return
    // a bare `StatedAbsence`, so the rail's *Summary* entry pointed at nothing
    // **exactly when a reader was trying to find out what had gone wrong** —
    // 📁 [TASK-1476](../../../docs/BACKLOG.md), and the third branch of this
    // component to lose the anchor.
    if (isError) {
      return (
        <section id={id} className="flex flex-col gap-3">
          <h2 className="text-sm font-semibold text-content">In plain language</h2>
          <StatedAbsence
            subject="the explanation for this account"
            reassurance="Nothing has changed about the account"
            {...(correlationId === undefined ? {} : { correlationId })}
          />
        </section>
      );
    }

    /**
     * 📁 ***"Header, title and counts paint from cache; only the body
     * skeletons."***
     *
     * ⛔ **This returned `null`**, so the whole section appeared when the read
     * landed and **everything below it moved down the page** — ⚡ which is the
     * jump the design's stable-height rule exists to prevent, and it happened
     * on the section a reader looks at first.
     *
     * ⚠️ **Three rows, and the number is the law's** — 📁
     * [`skeletonRows`](../../lib/accounts/section-state.ts): a narration is
     * prose rather than a list, **so nothing knows a previous count** and the
     * first-visit default is the honest answer for every visit.
     */
    return (
      <section id={id} className="flex flex-col gap-3">
        <h2 className="text-sm font-semibold text-content">In plain language</h2>
        <div className="flex flex-col gap-2 rounded-md border border-border bg-surface-raised px-4 py-3.5" aria-hidden>
          {Array.from({ length: skeletonRows(null) }, (_, row) => (
            <SkeletonText key={row} />
          ))}
        </div>
      </section>
    );
  }

  const facts = new Map(narration.facts.map((fact) => [fact.token, fact]));
  // **The one condition that strands a reader.** When nothing resolves, every
  // citation renders as a plain count rather than a button — so the dialog that
  // would explain *why* has no way to be opened. The sentence moves onto the
  // panel exactly then, and stays in the dialog the rest of the time: one
  // explanation, placed wherever the reader can actually reach it.
  const stranded = !narration.evidence_unchanged && narration.facts.length === 0;

  return (
    <section id={id} className="flex flex-col gap-3">
      <h2 className="text-sm font-semibold text-content">In plain language</h2>

      <div className="flex flex-col gap-3 rounded-md border border-border bg-surface-raised px-4 py-3.5">
        <ol className="flex flex-col gap-2.5">
          {narration.statements.map((statement, index) => (
            <li
              key={`${index}:${statement.evidence.join(',')}`}
              className="flex items-baseline justify-between gap-4"
            >
              <p className="text-md leading-6 text-content">{statement.text}</p>
              <Grounding
                tokens={statement.evidence}
                resolvable={statement.evidence.some((token) => facts.has(token))}
                onOpen={() => setOpen(statement.evidence)}
              />
            </li>
          ))}
        </ol>

        {stranded ? (
          <p className="border-t border-border pt-3 text-xs leading-5 text-content-muted">
            The evidence behind this account has changed since{' '}
            {formatDay(narration.generated_at)}, so the facts these sentences cite can no
            longer be opened. They describe what was true when they were written — a
            narration is never rewritten to catch up.
          </p>
        ) : null}

        {/**
         * ⚡ **[TASK-1411](../../../docs/BACKLOG.md) — the attribution strip,
         * and this is its first consumer.**
         *
         * 📁 **Account 360 draws exactly this line beneath its summary**:
         * *"Show reasoning · 6 sources · Confidence 4 of 5 · Generated
         * 09:14"*. ⛔ **The fact count on each sentence is NOT that line** —
         * it says what one claim rests on; the strip says what the whole
         * answer rests on, and 📁 the design carries both.
         *
         * ⛔ **`confidence` is absent because nothing publishes one.**
         * 📁 `AccountNarration` carries `statements`, `facts`,
         * `evidence_unchanged`, `prompt`, `model`, `vendor` and
         * `generated_at` — **and no confidence.** ✅ **So the strip states the
         * absence**, which is the row's instruction and the reason
         * [C-267](../../../docs/LANE_COORDINATION.md) stays open.
         *
         * ⛔ **And `note` is omitted deliberately.** 📁 Account 360's phrase is
         * *"updates on new evidence"* — ⚠️ **which would be a false promise
         * here**: this panel's own rule is that *"a narration is never
         * rewritten to catch up"*, so it does not update, it dates.
         */}
        <AttributionStrip
          sources={narration.facts.map((fact) => ({
            id: fact.token,
            title: fact.summary,
            ...(KIND_WORDING[fact.kind] === undefined
              ? {}
              : { meta: KIND_WORDING[fact.kind] }),
            // ⚡ **Every fact here arrived inside THIS reader's response**, so
            // the workspace scope and Casbin already decided they may see it.
            // ⛔ The flag is not a second authorization — it is the strip
            // refusing to list one that a caller knows is out of reach.
            readable: true,
            onOpen: () => setOpen([fact.token]),
          }))}
          generatedAt={narration.generated_at}
        />

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

const NOT_WRITTEN =
  'Signora has not written one for this account yet. Everything above stands on its own — an explanation is written separately, and appears here once it has been.';


/**
 * The panel with nothing in it, said in one line.
 *
 * **Deliberately not an `EmptyState`.** The illustrated component is for a
 * screen whose whole subject is missing; this is one section of a page that
 * has already answered the reader's question. The original objection — *a box
 * advertising a gap* — was about volume, and a muted sentence is the version
 * that survives it.
 */
function Aside({ children, id }: { children: string; id?: string }) {
  return (
    // ⚡ **The id belongs here too, and that is not incidental.** ⛔ This IS the
    // Summary section when nothing has been narrated — **a rail anchor that
    // worked only when the section had content would break exactly when a
    // reader most needs to find out why it is empty.**
    <section id={id} className="flex flex-col gap-3">
      <h2 className="text-sm font-semibold text-content">In plain language</h2>
      <p className="text-sm leading-6 text-content-muted">{children}</p>
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
      <span className="text-content-muted">{narration.prompt}</span>. Every sentence is
      restricted to facts the
      pipeline computed —{' '}
      <span className="text-content-muted">the model chose the words, not the facts</span>
      .
    </p>
  );
}
