'use client';

import { useState } from 'react';
import { Search } from 'lucide-react';

import { formatDay } from '@/components/intelligence/dates';
import { Badge, Button, Dialog } from '@/components/ui';
import type { AccountResearch, ResearchFinding, ResearchStatus } from '@/lib/api/types';

/**
 * *"Look into this one properly."*
 *
 * **The only place in the product where a person asks Signora to spend
 * something.** Everything else on this page reports what the pipeline had
 * already computed by the time the page loaded; this costs about a minute of a
 * worker and two model calls, and the design follows from that one fact.
 *
 * ### What research is, and what it is not
 *
 * It is **not another chat, and not another report.** It reaches nothing
 * outside Signora — the module has no HTTP client and no second provider path
 * by construction (the Internal Research ruling, 33-ai-research-engine-scope).
 * What it does is run comparisons across the evidence already beneath an
 * account that nothing else in the product performs: which conclusions rest on
 * a single provider, what the score preserved but outweighed, how far apart the
 * evidence falls in time.
 *
 * So the brief is shown in two parts, and **the deterministic half comes
 * first**:
 *
 *     what was compared    DERIVED   — recomputable by the customer
 *     what it means        INFERRED  — a model wrote this
 *
 * That order is the argument. A reader who scrolls no further has still seen
 * the checkable half, and a reader who does scroll reaches the model's
 * sentences already knowing what they rest on.
 *
 * ### The minute
 *
 * **The wait is stated in words before it is spent, not hidden behind a
 * spinner that implies seconds.** A spinner is a promise about duration, and a
 * product that makes that promise and takes a minute and a half has lied to the
 * person waiting. The status line says what is happening in a sentence.
 *
 * *"A minute or two"* is **measured, not estimated**: three real runs against
 * `llama3.1:8b` and the seeded Playground took 62s, 87s and 111s. The earlier
 * copy said *"about a minute"* from M10's recorded ~54s, and two of three runs
 * beat it.
 *
 * ### Finding nothing is an answer
 *
 * `nothing_to_research` is rendered as a result, never as an error. An account
 * with two events from one provider has nothing to corroborate; telling a
 * seller that *failed* would have the product apologising for behaving
 * correctly.
 */
export function ResearchPanel({
  research,
  onRequest,
  isRequesting,
}: {
  research: AccountResearch | null;
  onRequest: () => void;
  isRequesting: boolean;
}) {
  const [open, setOpen] = useState<ResearchFinding | null>(null);
  const artifact = research?.artifact ?? null;
  const findings = new Map((artifact?.findings ?? []).map((f) => [f.ref, f]));

  return (
    <section className="flex flex-col gap-3">
      <div className="flex items-baseline justify-between gap-4">
        <h2 className="text-sm font-semibold text-content">Deeper research</h2>
        <Ask research={research} onRequest={onRequest} isRequesting={isRequesting} />
      </div>

      <div className="flex flex-col gap-3 rounded-md border border-border bg-surface-raised px-4 py-3.5">
        {research === null ? <Invitation /> : <Status research={research} />}

        {artifact !== null ? (
          <>
            <Findings
              findings={artifact.findings}
              onOpen={(finding) => setOpen(finding)}
            />
            <Reading
              statements={artifact.statements}
              findings={findings}
              onOpen={(finding) => setOpen(finding)}
            />
            <Provenance artifact={artifact} />
          </>
        ) : null}
      </div>

      <FindingDialog finding={open} onClose={() => setOpen(null)} />
    </section>
  );
}

/**
 * What research would do, before anybody has asked for it.
 *
 * **Not an empty state advertising absence** (R8-02). It says what the thing
 * is, in the words the catalog uses for its own questions, so the button above
 * is a decision a reader can make rather than a gamble.
 */
function Invitation() {
  return (
    <p className="text-[0.9375rem] leading-6 text-content-muted">
      Signora can compare the evidence beneath this account against itself — which
      conclusions rest on a single provider, what the score outweighed, and how far apart
      the evidence falls. It usually takes a minute or two.
    </p>
  );
}

/** The sentence that says what is happening. One line, no spinner. */
function Status({ research }: { research: AccountResearch }) {
  const { status, detail, updated_at: updatedAt } = research;

  if (status === 'requested' || status === 'running') {
    return (
      <p aria-live="polite" className="text-[0.9375rem] leading-6 text-content-muted">
        {status === 'requested'
          ? 'Queued. This usually takes a minute or two — you can leave this page and come back.'
          : 'Comparing the evidence on this account. Usually a minute or two.'}
      </p>
    );
  }

  if (status === 'nothing_to_research') {
    return (
      <p className="text-[0.9375rem] leading-6 text-content-muted">
        There was nothing to compare here. This account&rsquo;s evidence comes from one
        source and one period, so none of the comparisons research performs had anything
        to say.
      </p>
    );
  }

  if (status === 'failed') {
    return (
      <div className="flex flex-col gap-1.5">
        <p className="text-[0.9375rem] leading-6 text-warning">
          Research could not finish. Nothing was recorded about this account.
        </p>
        {/* **The reason, verbatim.** A customer who cannot see why cannot
            decide whether asking again is worth another minute. */}
        <p className="text-xs leading-5 text-content-subtle">{detail}</p>
      </div>
    );
  }

  return (
    <p className="text-xs leading-5 text-content-subtle">
      Researched {formatDay(updatedAt)}.
    </p>
  );
}

/**
 * The button, and what it says at each point.
 *
 * **Disabled while a run is in flight, and the label says why.** A button that
 * stayed live would invite a second click the server answers by returning the
 * first run — correct, and confusing to somebody who thought they had started
 * something.
 */
function Ask({
  research,
  onRequest,
  isRequesting,
}: {
  research: AccountResearch | null;
  onRequest: () => void;
  isRequesting: boolean;
}) {
  const status: ResearchStatus | null = research?.status ?? null;
  const inFlight = status === 'requested' || status === 'running';

  return (
    <Button
      variant="secondary"
      size="sm"
      onClick={onRequest}
      disabled={inFlight || isRequesting}
    >
      <Search aria-hidden className="h-3.5 w-3.5" />
      {inFlight
        ? 'Researching…'
        : status === null
          ? 'Research this account'
          : 'Research again'}
    </Button>
  );
}

/**
 * What was compared. **The deterministic half, and it comes first.**
 *
 * Each row is a question a domain expert wrote and an answer code computed —
 * no model authored a word of this. The row opens to the rows it compared,
 * which is where the chain rejoins the evidence drawer.
 */
function Findings({
  findings,
  onOpen,
}: {
  findings: ResearchFinding[];
  onOpen: (finding: ResearchFinding) => void;
}) {
  return (
    <div className="flex flex-col gap-2">
      <h3 className="text-xs font-medium uppercase tracking-wide text-content-subtle">
        What was compared
      </h3>
      <ul className="flex flex-col gap-2">
        {findings.map((finding) => (
          <li key={finding.id}>
            <button
              type="button"
              onClick={() => onOpen(finding)}
              className={[
                'w-full rounded text-left',
                'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent',
              ].join(' ')}
            >
              <span className="block text-sm text-content-muted">{finding.question}</span>
              <span className="block text-[0.9375rem] leading-6 text-content underline decoration-dotted underline-offset-4">
                {summarise(finding)}
              </span>
            </button>
          </li>
        ))}
      </ul>
    </div>
  );
}

/**
 * What the model made of it. **INFERRED, and it says so.**
 *
 * Statements in the order they were written, never joined into prose: joining
 * would discard the mapping from claim to evidence, which is the only reason to
 * trust any of it. The same refusal `NarrativeBlock` makes, for the same reason.
 */
function Reading({
  statements,
  findings,
  onOpen,
}: {
  statements: { text: string; cites: string[] }[];
  findings: Map<string, ResearchFinding>;
  onOpen: (finding: ResearchFinding) => void;
}) {
  return (
    <div className="flex flex-col gap-2 border-t border-border pt-3">
      <h3 className="text-xs font-medium uppercase tracking-wide text-content-subtle">
        What it means
      </h3>
      <ol className="flex flex-col gap-2.5">
        {statements.map((statement, index) => (
          <li
            key={`${index}:${statement.cites.join(',')}`}
            className="flex items-baseline justify-between gap-4"
          >
            <p className="text-[0.9375rem] leading-6 text-content">{statement.text}</p>
            <Cited tokens={statement.cites} findings={findings} onOpen={onOpen} />
          </li>
        ))}
      </ol>
    </div>
  );
}

/**
 * How many comparisons this sentence rests on, and the way to read them.
 *
 * **Always resolvable, unlike a narration citation.** The findings arrive on
 * the same response, so there is no case where this is a bare count — which is
 * the difference between citing something the platform holds and citing
 * something it has to re-derive.
 */
function Cited({
  tokens,
  findings,
  onOpen,
}: {
  tokens: string[];
  findings: Map<string, ResearchFinding>;
  onOpen: (finding: ResearchFinding) => void;
}) {
  const first = tokens.map((token) => findings.get(token)).find((f) => f !== undefined);
  const label = `${tokens.length} ${tokens.length === 1 ? 'comparison' : 'comparisons'}`;

  if (first === undefined) {
    return (
      <span className="shrink-0 whitespace-nowrap pt-0.5 text-xs tabular-nums text-content-subtle">
        {label}
      </span>
    );
  }

  return (
    <button
      type="button"
      onClick={() => onOpen(first)}
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
 * One comparison, opened: the question, the answer, and what it compared.
 *
 * A modal for the reason the evidence drawer is one — Escape closes it and you
 * are exactly where you were, which R10-05 recorded as the bar.
 */
function FindingDialog({
  finding,
  onClose,
}: {
  finding: ResearchFinding | null;
  onClose: () => void;
}) {
  return (
    <Dialog
      open={finding !== null}
      onClose={onClose}
      title="What this comparison found"
      description="Computed from recorded rows. No model wrote any of it — open the rows and the arithmetic is yours to repeat."
    >
      {finding !== null ? (
        <div className="flex flex-col gap-3">
          <p className="text-sm text-content-muted">{finding.question}</p>

          <dl className="flex flex-col gap-1">
            {Object.entries(finding.attributes).map(([name, value]) => (
              <div key={name} className="flex items-baseline justify-between gap-4">
                <dt className="text-xs text-content-subtle">{humanise(name)}</dt>
                <dd className="text-sm tabular-nums text-content">{value}</dd>
              </div>
            ))}
          </dl>

          <div className="flex flex-col items-start gap-1.5 border-t border-border pt-3">
            <Badge tone="neutral">
              {finding.cites.length}{' '}
              {finding.cites.length === 1 ? 'record compared' : 'records compared'}
            </Badge>
            <p className="text-xs leading-5 text-content-muted">
              Each is a recorded event or a reading beneath this account&rsquo;s score.
              They appear on the account&rsquo;s own evidence, where the providers behind
              each one can be read.
            </p>
          </div>
        </div>
      ) : null}
    </Dialog>
  );
}

/** Which prompt, which model, when — on the page, not behind a tooltip. */
function Provenance({
  artifact,
}: {
  artifact: NonNullable<AccountResearch['artifact']>;
}) {
  return (
    <p className="border-t border-border pt-3 text-xs leading-5 text-content-subtle">
      Written by {artifact.model} using {artifact.prompt_name}@{artifact.prompt_version}
      {' · '}
      {formatDay(artifact.produced_at)}
      {' · '}
      the comparisons above were computed, not written
    </p>
  );
}

/**
 * A finding's answer, in one line.
 *
 * **Joins the values the derivation produced; invents nothing.** A sentence
 * written here about what the numbers *mean* would be this component authoring
 * a conclusion, which is the model's job and the one thing a presentational
 * layer must never quietly take over.
 */
function summarise(finding: ResearchFinding): string {
  return Object.entries(finding.attributes)
    .map(([name, value]) => `${humanise(name)}: ${value}`)
    .join(' · ');
}

/** `provider_count` → `Provider count`. The attribute names are engineering's
 * words and stay that way until the catalog gives them customer ones (R11-06). */
function humanise(name: string): string {
  const spaced = name.replaceAll('_', ' ');
  return spaced.charAt(0).toUpperCase() + spaced.slice(1);
}
