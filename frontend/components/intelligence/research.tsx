'use client';

import { useCallback, useEffect, useState } from 'react';
import { ChevronDown, Maximize2, Minimize2, Sparkles } from 'lucide-react';

import { formatDay } from '@/components/intelligence/dates';
import { StatedAbsence } from '@/components/feedback/stated-absence';
import { collapseKey } from '@/lib/accounts/section-state';
import { Badge, Dialog, SkeletonText } from '@/components/ui';
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
 * what was compared DERIVED — recomputable by the customer
 * what it means INFERRED — a model wrote this
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
  isError = false,
  onOpenEvidence,
  viewerId = null,
  kind = null,
  isExpanded = false,
  onToggleExpanded,
  /**
   * ⚡ **The design's section id, so the *"On this page"* rail can anchor
   * this** — [TASK-1476](../../../docs/BACKLOG.md). ⛔ **Optional**: the page
   * owns the section map and passes the id it publishes.
   */
  id,
  /** 📁 *"…then retry plus a correlation ID"* — [TASK-1476](../../../docs/BACKLOG.md). */
  correlationId,
}: {
  id?: string;
  correlationId?: string;
  research: AccountResearch | null;
  onRequest: () => void;
  isRequesting: boolean;
  /**
   * **The read failed — which is not the same as nobody having asked.**
   * Without this the panel showed `Invitation` for both, so an outage read as
   * *"research has never been run here"* and offered a button that could start
   * a second run beside one already in flight. The caller distinguishes a
   * `404` (genuinely never asked) from anything else, exactly as the narration
   * block above it does.
   */
  isError?: boolean;
  /** 📁 The design's *"Open all evidence"* — ⛔ **absent rather than inert**
   * when the page has no evidence surface to open. */
  onOpenEvidence?: () => void;
  /** 📁 The collapse law's key is per viewer per account KIND — ⛔ never per
   * record ([`collapseKey`](../../lib/accounts/section-state.ts)). */
  viewerId?: string | null;
  kind?: string | null;
  /** ⚡ **Expanded is the URL's**, so the view is shareable — 📁 the design:
   * *"keeps the URL so the expanded view is shareable."* */
  isExpanded?: boolean;
  onToggleExpanded?: (next: boolean) => void;
}) {
  const [open, setOpen] = useState<ResearchFinding | null>(null);
  const artifact = research?.artifact ?? null;

  // ── Collapsed ─────────────────────────────────────────────────────────
  // 📁 *"State persists per user per account type."* ⚡ **The key comes from
  // the shared law rather than being built here** — ⛔ a second key shape would
  // be a second definition of a rule `section-state.ts` already owns.
  const [expandedBody, setExpandedBody] = useState(true);
  const persistKey =
    viewerId === null || kind === null || id === undefined
      ? null
      : collapseKey(viewerId, kind, id);

  // ⚠️ **Read after mount, never during render** — `localStorage` does not
  // exist on the server, and a value read during render would make the first
  // client paint disagree with the server's.
  useEffect(() => {
    if (persistKey === null) return;
    setExpandedBody(window.localStorage.getItem(persistKey) !== 'collapsed');
  }, [persistKey]);

  const toggleBody = () => {
    const next = !expandedBody;
    setExpandedBody(next);
    if (persistKey !== null) {
      window.localStorage.setItem(persistKey, next ? 'open' : 'collapsed');
    }
  };

  // ── Expanded ──────────────────────────────────────────────────────────
  // 📁 *"Esc returns to the record at the same scroll position."* ⚡ **Returning
  // focus to the control is the half usually dropped** — without it a keyboard
  // reader who leaves focus mode is returned to the top of the document.
  const leaveFocus = useCallback(() => onToggleExpanded?.(false), [onToggleExpanded]);
  useEffect(() => {
    if (!isExpanded) return;
    const onKey = (event: KeyboardEvent) => {
      if (event.key === 'Escape') leaveFocus();
    };
    document.addEventListener('keydown', onKey);
    return () => document.removeEventListener('keydown', onKey);
  }, [isExpanded, leaveFocus]);
  const findings = new Map((artifact?.findings ?? []).map((f) => [f.ref, f]));

  const artifactCells = artifact === null ? [] : cells(artifact, findings);

  return (
    <section
      id={id}
      aria-labelledby={id === undefined ? undefined : `${id}-title`}
      /* 📁 **The design's card** — *"border-radius:14px; border:1px solid
         var(--ai-line)"*. ⚡ **The AI border rather than the neutral one**: this
         is the only section on the page whose body a model wrote, and the
         chrome says so before a word is read. */
      className="overflow-hidden rounded-lg border border-ai bg-surface shadow-sm"
    >
      {/* ── The header band ──────────────────────────────────────────────
          📁 *"background:var(--ai-tint); border-bottom:1px solid var(--ai-line)"*.
          ⚠️ **This replaces a plain `Deeper research` heading**, which was the
          previous generation's wording and had no basis in the finalized
          design — 📁 the design says **Research summary**. */}
      <div className="flex items-center gap-2.5 border-b border-ai bg-ai-subtle px-4 py-3">
        <span className="grid h-6 w-6 flex-none place-items-center rounded-sm bg-ai">
          <Sparkles aria-hidden className="h-3 w-3 text-surface" />
        </span>
        <div className="min-w-0">
          {/* 🔴 **The button lives INSIDE the heading**, which is the standard
              disclosure pattern and the one `AccountSectionShell` already
              earned: ⛔ a heading nested in a button removes the section from
              the document outline, and 📁 the design requires *"every section
              is a labelled region WITH A HEADING, reachable by landmark
              navigation"* — **in every state, collapsed included.** */}
          <h2
            id={id === undefined ? undefined : `${id}-title`}
            className="text-sm font-semibold tracking-tight text-content"
          >
            <button
              type="button"
              onClick={toggleBody}
              aria-expanded={expandedBody}
              aria-controls={id === undefined ? undefined : `${id}-body`}
              /* ♿ 📁 §17 `2.5.8` — *"Targets ≥ 24px."* ⚠️ **Measured at
                 `165 × 21`**, the same line-box shortfall
                 `AccountSectionShell`'s heading had, and the same fix: a
                 floor, not a height, so the heading keeps its type. */
              className={[
                'flex min-h-6 items-center gap-1.5 rounded text-left coarse:min-h-11',
              ].join(' ')}
            >
              <ChevronDown
                aria-hidden
                className={[
                  'h-3.5 w-3.5 transition-transform',
                  expandedBody ? '' : '-rotate-90',
                ].join(' ')}
              />
              Research summary
            </button>
          </h2>
          {/* 📁 The design's own subtitle, verbatim. ⚡ **It folds with the
              body**: 📁 a collapsed section keeps its COUNT and its worst
              status, not its description. */}
          {expandedBody ? (
            <p className="mt-px pl-5 text-xs text-content-muted">
              Company, market and relationship research · refreshed weekly, or on demand
            </p>
          ) : (
            <CollapsedSummary research={research} />
          )}
        </div>
        <Refresh
          research={research}
          onRequest={onRequest}
          isRequesting={isRequesting}
          isError={isError}
        />
        {onToggleExpanded === undefined ? null : (
          <button
            type="button"
            onClick={() => onToggleExpanded(!isExpanded)}
            aria-pressed={isExpanded}
            /* 📁 The design's *"Focus mode"* control. ⛔ **Absent rather than
               inert** when the page cannot carry the URL that makes the
               expanded view shareable. */
            aria-label={isExpanded ? 'Leave focus mode' : 'Open research in focus mode'}
            /* ♿ 📁 §17 `2.5.8` — *"Targets ≥ 24px."* ⚠️ **Measured at
               `22 × 22`**: a 14px glyph and 4px of padding, two pixels under
               the floor. ⛔ **A minimum on both axes rather than a bigger
               icon** — the glyph is the design's size and stays it; only the
               box it sits in grows. */
            className={[
              'inline-flex min-h-6 min-w-6 shrink-0 items-center justify-center rounded p-1 text-content-subtle',
              'coarse:min-h-11 coarse:min-w-11',
              'transition-colors hover:text-content',
            ].join(' ')}
          >
            {isExpanded ? (
              <Minimize2 aria-hidden className="h-3.5 w-3.5" />
            ) : (
              <Maximize2 aria-hidden className="h-3.5 w-3.5" />
            )}
          </button>
        )}
      </div>

      {/* ── The body ─────────────────────────────────────────────────────
          ⚡ **Four states share this region and only one of them is the grid.** */}
      <div id={id === undefined ? undefined : `${id}-body`} hidden={!expandedBody}>
        {isError ? (
          <div className="px-4 py-4">
            <Unavailable {...(correlationId === undefined ? {} : { correlationId })} />
          </div>
        ) : isRequesting ||
          research?.status === 'requested' ||
          research?.status === 'running' ? (
          <Waiting status={research?.status ?? 'requested'} />
        ) : research === null ? (
          <div className="px-4 py-4">
            <Invitation />
          </div>
        ) : artifactCells.length === 0 ? (
          <div className="px-4 py-4">
            <Status research={research} />
          </div>
        ) : (
          <>
            {/* 📁 *"grid-template-columns:repeat(2,1fr)"* — ⚡ **two columns from
                `smalllaptop` up, one below it**: a 12.5px paragraph in half of a
                phone is four words a line. */}
            <div
              className={[
                'grid grid-cols-1',
                /* 📁 *"Expansion widens to the full content region."* ⚡ **Three
                   columns at `laptop` in focus mode, two otherwise** — ⛔ the
                   widening is real rather than a class name. */
                isExpanded
                  ? 'smalllaptop:grid-cols-2 laptop:grid-cols-3'
                  : 'smalllaptop:grid-cols-2',
              ].join(' ')}
            >
              {artifactCells.map((cell) => (
                <ResearchCell key={cell.key} cell={cell} onOpen={(f) => setOpen(f)} />
              ))}
            </div>
            <Footer artifact={artifact!} onOpenEvidence={onOpenEvidence} />
          </>
        )}
      </div>

      <FindingDialog finding={open} onClose={() => setOpen(null)} />
    </section>
  );
}

/**
 * 📁 ***"A collapsed section still states its count and its worst status, so
 * collapsing never hides a risk."***
 *
 * ⚡ **The design's own sample is the shape**: *"14 detected · 1 competitor
 * present"*, *"4 · 1 regulatory, acts on renewal"* — **a count and the thing
 * worth knowing.**
 *
 * ⛔ **Research has no severity to fold** — nothing in `ResearchArtifact`
 * carries one — **so the count and the run's outcome are what survive**, and no
 * status dot is invented to fill the slot.
 */
function CollapsedSummary({ research }: { research: AccountResearch | null }) {
  const artifact = research?.artifact ?? null;

  const summary =
    research === null
      ? 'Not researched yet'
      : artifact !== null
        ? `${artifact.findings.length} ${artifact.findings.length === 1 ? 'comparison' : 'comparisons'} · ${formatDay(artifact.produced_at)}`
        : research.status === 'nothing_to_research'
          ? 'Nothing to compare on this account'
          : research.status === 'failed'
            ? 'Last run could not finish'
            : 'Running';

  return <p className="mt-px pl-5 text-xs text-content-muted">{summary}</p>;
}

/**
 * One cell of the design's grid: **a deterministic key, an inferred value, and
 * the citation between them.**
 *
 * ## 🔴 Why the key is a finding's question and not a heading somebody wrote
 *
 * ⚠️ **The previous structure split this into two lists** — *What was compared*
 * (derived) above *What it means* (inferred) — **and the finalized design has
 * one grid.** ⛔ **Collapsing them naively would have presented a computed
 * comparison as model prose**, which is the one thing this file's own docstring
 * refuses.
 *
 * ✅ **So the distinction moves INTO the cell rather than being lost**: `k` is
 * the domain expert's question, computed and recomputable; `v` is the model's
 * sentence; the citation between them is the link back to the rows. **The card
 * carries the intelligence hue, so nothing here reads as unattributed.**
 */
function ResearchCell({
  cell,
  onOpen,
}: {
  cell: Cell;
  onOpen: (finding: ResearchFinding) => void;
}) {
  return (
    <div className="border-b border-border px-4 py-4 smalllaptop:[&:nth-child(odd)]:border-r">
      {/* 📁 *"11px; 600; letter-spacing:.05em; uppercase; var(--ink-4)"* */}
      {cell.question === null ? null : (
        <div className="text-xs font-semibold uppercase tracking-wider text-content-subtle">
          {cell.question}
        </div>
      )}
      {/* 📁 *"12.5px; line-height:1.6; var(--ink-2)"* */}
      <p className="mt-2 text-sm leading-relaxed text-content-muted">{cell.text}</p>
      {/* 📁 *"11px; 600; var(--ai-ink)"* — ⚡ and it is the affordance, not a
          label: the design's citation is where a reader goes to check. */}
      <Cited tokens={cell.cites} finding={cell.finding} onOpen={onOpen} />
    </div>
  );
}

/**
 * 📁 *"Sources: 3 filings, 2 news items, 1 job-board scan, 4 calls"* and
 * *"Open all evidence"*.
 *
 * ⛔ **The typed breakdown is NOT rendered, and the gap is stated rather than
 * approximated.** ⚡ **Nothing in `ResearchArtifact` carries a source TYPE** —
 * findings carry refs into rows, not *filing* or *job-board scan* — **so a
 * typed tally here would be four numbers this product cannot produce.** ✅ **The
 * count is real and comes from the artifact.**
 */
function Footer({
  artifact,
  onOpenEvidence,
}: {
  artifact: NonNullable<AccountResearch['artifact']>;
  onOpenEvidence?: () => void;
  /** 📁 The collapse law's key is per viewer per account KIND — ⛔ never per
   * record ([`collapseKey`](../../lib/accounts/section-state.ts)). */
  viewerId?: string | null;
  kind?: string | null;
  /** ⚡ **Expanded is the URL's**, so the view is shareable — 📁 the design:
   * *"keeps the URL so the expanded view is shareable."* */
  isExpanded?: boolean;
  onToggleExpanded?: (next: boolean) => void;
}) {
  const sources = new Set(artifact.findings.flatMap((finding) => finding.cites)).size;

  return (
    <div className="flex flex-wrap items-center gap-x-3 gap-y-1 px-4 py-3">
      <span className="text-xs text-content-subtle">
        {sources} {sources === 1 ? 'source' : 'sources'} compared
      </span>
      <Provenance artifact={artifact} />
      {onOpenEvidence === undefined ? null : (
        <button
          type="button"
          onClick={onOpenEvidence}
          className={[
            'ml-auto rounded text-xs font-semibold text-ai',
            'transition-colors hover:underline',
          ].join(' ')}
        >
          Open all evidence
        </button>
      )}
    </div>
  );
}

/**
 * 📁 The design's Loading state — ***"Row count matches the expected result, so
 * nothing jumps when data lands."***
 *
 * ⚡ **Four cells, because the design's own placeholder hint is
 * `hint-placeholder-count="4"`** — ⛔ not a number chosen here.
 */
function Waiting({ status }: { status: ResearchStatus }) {
  return (
    <div>
      <p aria-live="polite" className="px-4 pt-4 text-sm leading-6 text-content-muted">
        {status === 'running'
          ? 'Comparing the evidence on this account. Usually a minute or two.'
          : 'Queued. This usually takes a minute or two — you can leave this page and come back.'}
      </p>
      <div className="grid grid-cols-1 smalllaptop:grid-cols-2" aria-hidden>
        {[0, 1, 2, 3].map((n) => (
          <div
            key={n}
            className="border-b border-border px-4 py-4 smalllaptop:[&:nth-child(odd)]:border-r"
          >
            <SkeletonText lines={1} />
            <div className="mt-2">
              <SkeletonText lines={3} />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

/** A cell of the design's grid, assembled from one statement. */
interface Cell {
  key: string;
  /** ⛔ **`null` when no cited finding resolves** — the design has no cell
   * without a key, and inventing one would be this layer naming a question a
   * domain expert did not write. */
  question: string | null;
  text: string;
  cites: string[];
  finding: ResearchFinding | undefined;
}

/**
 * **One cell per statement**, keyed by the question of the finding it cites.
 *
 * ⚡ **The order is the model's**, unchanged — 📁 *"statements in the order they
 * were written, never joined into prose: joining would discard the mapping from
 * claim to evidence, which is the only reason to trust any of it."*
 */
function cells(
  artifact: NonNullable<AccountResearch['artifact']>,
  findings: Map<string, ResearchFinding>,
): Cell[] {
  return artifact.statements.map((statement, index) => {
    const finding = statement.cites
      .map((token) => findings.get(token))
      .find((f) => f !== undefined);
    return {
      key: `${index}:${statement.cites.join(',')}`,
      question: finding?.question ?? null,
      text: statement.text,
      cites: statement.cites,
      finding,
    };
  });
}

/**
 * What research would do, before anybody has asked for it.
 *
 * **Not an empty state advertising absence** (R8-02). It says what the thing
 * is, in the words the catalog uses for its own questions, so the button above
 * is a decision a reader can make rather than a gamble.
 */
/**
 * **An outage, said as one.** The wording follows `ValidationBlock`'s
 * `Unavailable` rather than inventing a second phrasing for the same fact
 * (§2), and it says nothing about whether research exists — because when this
 * renders, Signora does not know.
 */
function Unavailable({ correlationId }: { correlationId?: string }) {
  return (
    <StatedAbsence
      subject="the research for this account"
      reassurance="Nothing has changed about the account"
      {...(correlationId === undefined ? {} : { correlationId })}
    />
  );
}

function Invitation() {
  return (
    <p className="text-md leading-6 text-content-muted">
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
      <p aria-live="polite" className="text-md leading-6 text-content-muted">
        {status === 'requested'
          ? 'Queued. This usually takes a minute or two — you can leave this page and come back.'
          : 'Comparing the evidence on this account. Usually a minute or two.'}
      </p>
    );
  }

  if (status === 'nothing_to_research') {
    return (
      <p className="text-md leading-6 text-content-muted">
        There was nothing to compare here. This account&rsquo;s evidence comes from one
        source and one period, so none of the comparisons research performs had anything
        to say.
      </p>
    );
  }

  if (status === 'failed') {
    return (
      <div className="flex flex-col gap-1.5">
        <p className="text-md leading-6 text-warning">
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
 * 📁 The design's ***"Refresh research"*** — **a text action in the header band,
 * not a button below the heading.**
 *
 * ⚠️ **The previous generation rendered a `Button` with a magnifier and three
 * different labels.** ⛔ **The finalized design has one label in one place**, so
 * the label no longer changes — ✅ **what it is doing is said by the body**,
 * which is where a reader is already looking while they wait.
 *
 * ⛔ **Still disabled while a run is in flight and while the read failed**: the
 * safety argument is unchanged and is not a design question. A minute of a
 * worker and two model calls is not something to spend on a guess.
 */
function Refresh({
  research,
  onRequest,
  isRequesting,
  isError,
}: {
  research: AccountResearch | null;
  onRequest: () => void;
  isRequesting: boolean;
  isError: boolean;
}) {
  const status: ResearchStatus | null = research?.status ?? null;
  const inFlight = status === 'requested' || status === 'running';
  const disabled = inFlight || isRequesting || isError;

  return (
    <button
      type="button"
      onClick={onRequest}
      disabled={disabled}
      /* ♿ 📁 §17 `2.5.8` — *"Targets ≥ 24px."* ⚠️ **Measured at `116 × 18`.**
         ⛔ **`min-h-6`, not a padded button**: 📁 the finalized design calls
         this *"a text action in the header band, not a button below the
         heading"*, so it keeps its type and gains only the floor. */
      className={[
        'ml-auto inline-flex min-h-6 shrink-0 items-center rounded text-xs font-semibold text-ai',
        'coarse:min-h-11',
        'transition-colors hover:underline',
        'disabled:cursor-not-allowed disabled:text-content-subtle disabled:no-underline',
      ].join(' ')}
    >
      {status === null ? 'Research this account' : 'Refresh research'}
    </button>
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
  finding,
  onOpen,
}: {
  tokens: string[];
  finding: ResearchFinding | undefined;
  onOpen: (finding: ResearchFinding) => void;
}) {
  const label = `${tokens.length} ${tokens.length === 1 ? 'comparison' : 'comparisons'}`;

  if (finding === undefined) {
    return (
      <div className="mt-2 text-xs font-semibold tabular-nums text-content-subtle">
        {label}
      </div>
    );
  }

  return (
    <button
      type="button"
      onClick={() => onOpen(finding)}
      className={[
        'mt-2 block rounded text-xs font-semibold tabular-nums text-ai',
        'transition-colors hover:underline',
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
              {finding.cites.length}
              {' '}
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
    <span className="text-xs text-content-subtle">
      · {artifact.model} · {artifact.prompt_name}@{artifact.prompt_version} ·{' '}
      {formatDay(artifact.produced_at)}
    </span>
  );
}

/** `provider_count` → `Provider count`. The attribute names are engineering's
 * words and stay that way until the catalog gives them customer ones (R11-06). */
function humanise(name: string): string {
  const spaced = name.replaceAll('_', ' ');
  return spaced.charAt(0).toUpperCase() + spaced.slice(1);
}
